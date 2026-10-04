import struct, sys


class FAT:
    def __init__(self, path):
        self.f = open(path, 'rb')
        bs = self.f.read(512)
        self.bps, self.spc = struct.unpack('<H', bs[11:13])[0], bs[13]
        self.resv, self.nfats = struct.unpack('<H', bs[14:16])[0], bs[16]
        self.rootent, self.tot16 = struct.unpack('<HH', bs[17:21])
        self.fat16, = struct.unpack('<H', bs[22:24])
        self.sect32, = struct.unpack('<I', bs[32:36])
        self.fat32, = struct.unpack('<I', bs[36:40])
        self.fsinfo, = struct.unpack('<H', bs[48:50])
        self.bkboot, = struct.unpack('<H', bs[48:50])
        self.root32, = struct.unpack('<I', bs[44:48])
        self.tot = self.sect32 or self.tot16
        self.fatsec = self.fat32 or self.fat16
        self.type = 32 if self.fat32 else (16 if self.tot * self.spc > 655252 else 12)
        self.rs = self.resv
        self.data = self.rs + self.nfats * self.fatsec
        if self.fat32:
            self.data = self.rs + self.nfats * self.fat32
        print('FAT%d bps=%d spc=%d resv=%d fatsec=%d root=%d data_sec=%d cluster_base=%d'
              % (self.type, self.bps, self.spc, self.rs, self.fatsec,
                 self.root32, self.data, self.data * self.bps))
        self.f.seek(self.rs * self.bps)
        self.fat = self.f.read(self.fatsec * self.bps)
        pass

    def entry(self, c):
        if self.type == 32:
            return struct.unpack('<I', self.fat[c * 4:c * 4 + 4])[0] & 0x0FFFFFFF
        if self.type == 16:
            return struct.unpack('<H', self.fat[c * 2:c * 2 + 2])[0]
        off = c + c // 2
        v = struct.unpack('<H', self.fat[off:off + 2])[0]
        return (v >> 4) if c == 0 else (v & 0xFFF) if c & 1 else (v >> 4) & 0xFFF

    def chain(self, c):
        out = []
        while c < (0xFF8 if self.type != 32 else 0x0FFFFFF8):
            out.append(c)
            c = self.entry(c)
            if len(out) > 100000:
                break
        return out

    def clus(self, c):
        return (self.data + (c - 2) * self.spc) * self.bps

    def readchain(self, start, size):
        b = bytearray()
        for c in self.chain(start):
            self.f.seek(self.clus(c))
            b += self.f.read(self.spc * self.bps)
            if len(b) >= size:
                break
        return bytes(b[:size])


def walk(fs, path, dirclus, depth=0):
    seen = set()
    for c in fs.chain(dirclus):
        if c in seen:
            break
        seen.add(c)
        fs.f.seek(fs.clus(c))
        blk = fs.f.read(fs.spc * fs.bps)
        for i in range(0, len(blk), 32):
            e = blk[i:i + 32]
            if e[:1] == b'\x00':
                break
            attr = e[11]
            if attr in (0x0F,):
                continue
            if e[0] in (0x2E,):
                continue
            delflag = e[0] == 0xE5
            name = e[0:11].decode('cp437', 'replace')
            if delflag:
                name = '[DEL]' + name
            hi = struct.unpack('<H', e[20:22])[0]
            lo = struct.unpack('<H', e[26:28])[0]
            size = struct.unpack('<I', e[28:32])[0]
            clus = (hi << 16) | lo
            mtime = struct.unpack('<H', e[14:16])[0]
            print('%s%s %-14s attr=%02x clus=%d size=%d' % ('  ' * depth,
                  ('x' if delflag else ' '), name, attr, clus, size))
            if attr & 0x10 and not delflag:
                walk(fs, path + '/' + name, clus, depth + 1)
            if (attr & 0x10) == 0 and size and fs.type == 32:
                data = fs.readchain(clus, size)
                yield path + '/' + name, clus, size, data, delflag


fn = sys.argv[1] if len(sys.argv) > 1 else 'part0_billy.img'
fs = FAT(fn)
rootclus = fs.root32 if fs.fat32 else None
if fs.fat32:
    items = list(walk(fs, '', rootclus))
else:
    fs.f.seek(fs.data * fs.bps)
    blk = fs.f.read(32 * fs.rootent)
    items = []
    for i in range(0, len(blk), 32):
        e = blk[i:i + 32]
        if e[:1] == b'\x00':
            break
        if e[11] == 0x0F or e[0] == 0x2E:
            continue
        size = struct.unpack('<I', e[28:32])[0]
        clus = struct.unpack('<H', e[26:28])[0]
        nm = e[0:11].decode('cp437', 'replace')
        items.append(('/' + nm, clus, size, fs.readchain(clus, size), e[0] == 0xE5))
        print('%-16s size=%d clus=%d' % (nm, size, clus))

import os
for path, clus, size, data, deleted in items:
    out = 'fat_%s%s%s' % (os.path.basename(fn), ('_DEL' if deleted else ''),
                          path.replace('/', '_') or '_root')
    open(out, 'wb').write(data)
    print('WROTE', out, size, 'head=', data[:16].hex(), 'ascii=', data[:24])
