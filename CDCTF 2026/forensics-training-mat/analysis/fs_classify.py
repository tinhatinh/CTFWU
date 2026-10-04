import struct

EXT_MAGIC = 0xEF53
BTRFS_MAGIC = 0x4D536652425F4852

INCOMPAT = {0x1: 'filetype', 0x2: 'has_journal(ext3)', 0x4: 'sparse_super',
            0x8: 'large_file', 0x10: 'huge_file', 0x20: 'gdt_backup',
            0x40: 'extents(ext4)', 0x80: 'flex_bg(ext4)', 0x100: 'meta_bg',
            0x200: 'dir_nlink', 0x400: '64bit(ext4)', 0x800: 'imalloc',
            0x1000: 'has_snapshot', 0x2000: 'orphan_file(ext4.5)',
            0x4000: 'fast_commit'}
RO = {0x1: 'sparse_super2', 0x2: 'largedir', 0x4: 'gga', 0x8: 'readonly',
      0x10: 'project', 0x20: 'orphan_pbl', 0x40: 'metadata_csum(ext4)',
      0x80: 'metadata_csum_seed'}


def report(fn):
    b = open(fn, 'rb').read(1 << 20)
    print('==', fn, 'size=%d' % os.path.getsize(fn))
    hit = False

    # VFAT / FAT
    bs = b[:512]
    if bs[510:512] == b'\x55\xaa' and bs[54:62] in (b'FAT12   ', b'FAT16   ', b'FAT32   ', b'MSDOS5  ') or bs[3:11].startswith(b'mkfs'):
        hit = True
        by_sec, = struct.unpack('<H', bs[11:13])
        spc = bs[13]
        resv, = struct.unpack('<H', bs[14:16])
        nfats = bs[16]
        rootent, tot16 = struct.unpack('<HH', bs[17:21])
        fatsec16, = struct.unpack('<H', bs[22:24])
        sect32, = struct.unpack('<I', bs[32:36])
        fat32sec, = struct.unpack('<I', bs[36:40])
        root32, = struct.unpack('<I', bs[44:48])
        tot = sect32 or tot16
        ftype = bs[54:62].decode('latin1').strip()
        print('  VFAT  label=%r type=%s bytes/sec=%d sec/clus=%d resv=%d fat=%d totsec=%d (%d MiB) '
              'root=%d' % (bs[43:54].decode('latin1').strip(), ftype or ('FAT32' if root32 else '?'),
                           by_sec, spc, resv, fat32sec or fatsec16, tot, tot * by_sec // 1048576,
                           root32 or (resv + nfats * (fatsec16 or fat32sec))))

    # EXT
    s = b[1024:1024 + 256]
    if len(s) == 256 and struct.unpack('<H', s[56:58])[0] == EXT_MAGIC:
        hit = True
        inodes, blocks = struct.unpack('<II', s[0:8])
        free_blocks, = struct.unpack('<I', s[12:16])
        log_bs, = struct.unpack('<I', s[24:28])
        bsz = 1024 << log_bs
        rev, = struct.unpack('<I', s[76:80])
        inode_size, = struct.unpack('<H', s[88:90])
        c, i, r = struct.unpack('<3I', s[92:104])
        label = s[120:136].split(b'\x00')[0].decode('latin1')
        uuid = ':'.join('%02x' % x for x in s[104:120])
        names = [v for k, v in INCOMPAT.items() if i & k] + [v for k, v in RO.items() if r & k]
        print('  EXT   label=%r uuid=%s rev=%d bs=%d blocks=%d (%d MiB) inodes=%d inode_size=%d'
              % (label, uuid, rev, bsz, blocks, blocks * bsz // 1048576, inodes, inode_size))
        print('        compat=%08x incompat=%08x ro=%08x -> %s' % (c, i, r, ', '.join(names) or '-'))

    # BTRFS (primary sb @65536, copy @64M, @64G)
    for off in (65536, 1 << 26):
        if len(b) < off + 512:
            continue
        sb = b[off:off + 512]
        if struct.unpack('<Q', sb[64:72])[0] != BTRFS_MAGIC:
            continue
        hit = True
        gen, root, chunk_root = struct.unpack('<QQQ', sb[72:96])
        nodesize, sectorsize, = struct.unpack('<II', sb[112:120])
        label = sb[132:244].split(b'\x00')[0].decode('utf-8', 'replace')
        print('  BTRFS @%d label=%r fsid=%s gen=%d' % (off, label, sb[32:48].hex(), gen))
        print('        raw 0x70-0x100:', sb[112:256].hex())

    if not hit:
        print('  no known FS signature in first 1 MiB; head=', b[:64].hex())


for fn in ['part0_billy.img', 'part1_astrid.img', 'part2_hwk.img', 'part3_main.img']:
    report(fn)
