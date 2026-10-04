import struct, sys

INC = {0x0001: 'compression', 0x0002: 'filetype', 0x0004: 'recover', 0x0008: 'journal_dev',
       0x0010: 'meta_bg', 0x0040: 'extents', 0x0080: '64bit', 0x0100: 'mmp',
       0x0200: 'flex_bg', 0x0400: 'ea_inode', 0x1000: 'dirdata', 0x2000: 'csum_seed',
       0x4000: 'largedir', 0x8000: 'inline_data', 0x10000: 'encrypt'}
RO = {0x01: 'sparse_super2', 0x02: 'largedir', 0x04: 'gdt_csum', 0x08: 'readonly',
      0x10: 'project', 0x20: 'orphan_prealloc', 0x40: 'metadata_csum',
      0x80: 'csum_seed', 0x100: 'verbatim', 0x200: 'bigalloc'}
COMPAT = {0x1: 'dir_prealloc', 0x2: 'imagic_inodes', 0x4: 'has_journal', 0x8: 'sparse_super',
          0x10: 'large_file', 0x20: 'tiny_extent', 0x40: 'huge_file', 0x80: 'dir_nlink',
          0x100: 'extra_isize'}
IFLAG_EXTENTS = 0x00080000
IFLAG_INLINE = 0x00000008 << 16


class Ext:
    def __init__(self, path, force_ds=None):
        self.f = open(path, 'rb')
        self.size = __import__('os').path.getsize(path)
        self.f.seek(1024)
        self.sb = self.f.read(1024)
        s = self.sb
        d = lambda o, n: struct.unpack(n, s[o:o + len(n) - 1])[0] if False else None
        self.inodes_count = self._u32(0)
        self.blocks_count = self._u32(4)
        self.free_blocks = self._u32(12)
        self.first_data = self._u32(20)
        self.bs = 1024 << self._u32(24)
        self.bpg = self._u32(32)
        self.ipg = self._u32(40)
        self.rev = self._u32(76)
        self.inode_size = self._u16(88)
        self.feat_c, self.feat_i, self.feat_r = struct.unpack('<3I', s[92:104])
        self.label = s[120:136].split(b'\x00')[0].decode('latin1')
        self.uuid = s[104:120]
        self.groups = (self.blocks_count + self.bpg - 1) // self.bpg
        self.has_ext = bool(self.feat_i & 0x40)
        self.is64 = bool(self.feat_i & 0x80)
        self.desc_size = force_ds
        print('EXT label=%r bs=%d blocks=%d (%d MiB) inodes=%d ipg=%d bpg=%d groups=%d rev=%d inode_size=%d'
              % (self.label, self.bs, self.blocks_count, self.blocks_count * self.bs >> 20,
                 self.inodes_count, self.ipg, self.bpg, self.groups, self.rev, self.inode_size))
        print('  compat=%08x [%s]' % (self.feat_c, ' '.join(v for k, v in COMPAT.items() if self.feat_c & k)))
        print('  incompat=%08x [%s]' % (self.feat_i, ' '.join(v for k, v in INC.items() if self.feat_i & k)))
        print('  ro_compat=%08x [%s]' % (self.feat_r, ' '.join(v for k, v in RO.items() if self.feat_r & k)))
        for cand in ((64, 32) if self.is64 else (32,)) if not force_ds else ():
            self.desc_size = cand
            try:
                ents = self.dir_entries(2)[2]
                if any(e[1] == b'.' for e in ents):
                    print('  -> using desc_size=%d, root entries=%d' % (cand, len(ents)))
                    break
            except Exception:
                continue
        else:
            print('  WARN: root dir parse failed, keeping desc_size=%d' % self.desc_size)

    def _u32(self, o):
        return struct.unpack('<I', self.sb[o:o + 4])[0]

    def _u16(self, o):
        return struct.unpack('<H', self.sb[o:o + 2])[0]

    def r(self, off, n):
        self.f.seek(off)
        return self.f.read(n)

    def bg(self, i):
        off = (self.first_data + 1) * self.bs + i * self.desc_size
        d = self.r(off, self.desc_size)
        inode_blk = struct.unpack('<I', d[8:12])[0]
        if self.desc_size >= 64:
            inode_blk |= struct.unpack('<I', d[40:44])[0] << 32
        used = struct.unpack('<H', d[16:18])[0]
        return inode_blk, used

    def inode(self, ino):
        g, idx = (ino - 1) // self.ipg, (ino - 1) % self.ipg
        iblk, _ = self.bg(g)
        raw = self.r(iblk * self.bs + idx * self.inode_size, self.inode_size)
        mode, = struct.unpack('<H', raw[0:2])
        vals = struct.unpack('<6I', raw[4:28])
        size_lo, at, ct, mt, dt, gl = vals
        blocks512, = struct.unpack('<I', raw[28:32])
        flags, = struct.unpack('<I', raw[32:36])
        iblock = struct.unpack('<15I', raw[40:100])
        gid, links = gl & 0xFFFF, (gl >> 16) & 0xFFFF
        size = size_lo | (struct.unpack('<I', raw[108:112])[0] << 32 if mode >= 0x8000 else 0)
        return dict(ino=ino, raw=raw, mode=mode, size=size, dtime=dt, mtime=mt, links=links,
                    blocks=blocks512, flags=flags, iblock=iblock)

    def blocklist(self, ino):
        n = self.inode(ino)
        if self.has_ext and (n['flags'] & IFLAG_EXTENTS):
            out = []
            stack = [(n['raw'][40:], 12)]
            while stack:
                blk, hdr_at = stack.pop()
                magic, cnt, maxe, depth, gen = struct.unpack('<HHHHI', blk[0:12])
                if magic != 0xF30A:
                    break
                for e in range(cnt):
                    o = 12 + e * 12
                    lblk, alen, ahi = struct.unpack('<IHH', blk[o:o + 8])
                    alo, = struct.unpack('<I', blk[o + 8:o + 12])
                    start = (ahi << 32) | alo
                    if depth == 0:
                        out.append((lblk, start, alen & 0xFFFF, bool(alen & 0x8000)))
                    else:
                        stack.append((self.r(start * self.bs, self.bs), 12))
            return n, out
        out = []
        for k in range(12):
            if n['iblock'][k]:
                out.append((k, n['iblock'][k], 1, False))
        per = self.bs // 4
        b12 = n['iblock'][12]
        if b12:
            tbl = self.r(b12 * self.bs, self.bs)
            for i in range(per):
                x, = struct.unpack('<I', tbl[i * 4:i * 4 + 4])
                if x:
                    out.append((12 + i, x, 1, False))
        b13 = n['iblock'][13]
        if b13:
            tbl = self.r(b13 * self.bs, self.bs)
            for i in range(per):
                x, = struct.unpack('<I', tbl[i * 4:i * 4 + 4])
                if not x:
                    continue
                t2 = self.r(x * self.bs, self.bs)
                for j in range(per):
                    y, = struct.unpack('<I', t2[j * 4:j * 4 + 4])
                    if y:
                        out.append((12 + per + i * per + j, y, 1, False))
        return n, out

    def read(self, ino, cap=None):
        n, bl = self.blocklist(ino)
        buf = bytearray()
        for lblk, blk, cnt, uninit in sorted(bl):
            buf += bytes(cnt * self.bs) if uninit else self.r(blk * self.bs, cnt * self.bs)
        lim = n['size'] if cap is None else min(n['size'], cap)
        return n, bytes(buf[:lim])

    def dir_entries(self, ino):
        n, data = self.read(ino)
        ents = []
        p = 0
        while p + 8 <= len(data):
            ei, reclen, namelen, tlen = struct.unpack('<IHBB', data[p:p + 8])
            if reclen < 8 or p + reclen > len(data):
                break
            nm = data[p + 8:p + 8 + namelen]
            ents.append((ei, nm, tlen & 0xF, ei == 0))
            p += reclen
        return n, data, ents


def ftype(t):
    return {1: 'reg', 2: 'dir', 5: 'blk', 6: 'chr', 7: 'symlink', 10: 'sock'}.get(t, '?')


def walk(fs, ino, depth=0, seen=None, prefix=''):
    seen = seen or set()
    if ino in seen:
        return
    seen.add(ino)
    for ei, nm, t, delrec in fs.dir_entries(ino)[2]:
        if nm in (b'.', b'..') or not ei:
            continue
        info = fs.inode(ei) if ei else {}
        print('%s%-4s ino=%-6d %-9s size=%-10d dtime=%-11d links=%s mode=%04o %r'
              % ('  ' * depth, 'DEL' if (delrec or info.get('dtime')) else '   ',
                 ei, ftype(t), info.get('size', -1), info.get('dtime', 0),
                 info.get('links', 0), info.get('mode', 0) & 0o7777, nm))
        if t == 2 and not info.get('dtime'):
            walk(fs, ei, depth + 1, seen, prefix + '/' + nm.decode('utf8', 'replace'))


fn = sys.argv[1]
fs = Ext(fn)
walk(fs, 2)
mode = sys.argv[2] if len(sys.argv) > 2 else None
if mode == 'extract':
    import os
    seen = set()

    def ex(ino):
        if ino in seen:
            return
        seen.add(ino)
        for ei, nm, t, d in fs.dir_entries(ino)[2]:
            if nm in (b'.', b'..') or not ei:
                continue
            if t == 2:
                ex(ei)
            else:
                n, data = fs.read(ei)
                p = 'x_%s_%d_%s' % (os.path.basename(fn).replace('.img', ''), ei, nm.decode('utf8', 'replace').strip())
                open(p, 'wb').write(data)
                print('SAVED %-46s size=%8d head=%s' % (p, n['size'], data[:8].hex()))
    ex(2)
elif mode == 'dumpdel':
    # scan all inodes, report ones with dtime set
    for i in range(1, fs.inodes_count + 1):
        try:
            n = fs.inode(i)
        except Exception:
            continue
        if n['dtime'] and n['size']:
            print('DELETED ino=%d size=%d blocks=%d dtime=%d mode=%o' %
                  (i, n['size'], n['blocks'], n['dtime'], n['mode'] & 0o7777))
