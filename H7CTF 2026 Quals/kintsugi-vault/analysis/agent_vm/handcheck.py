import struct
BASE = r"C:\Users\Administrator\Documents\Qoder\2026-09-23\1788d23b\CTF-Writeups\kintsugi-vault"
raw = open(BASE + r"\files\f6f11ad133cab21c96e0185e3411ddc4.shard", 'rb').read()
t, plen = struct.unpack_from('<2H', raw, 8)
P = 0x32 + t + 256
DEC = raw[0x32:0x132]
print("program off=0x%x len=%d" % (P, plen))
for i in range(0, 130, 16):
    print('%03x: ' % (P+i) + raw[P+i:P+i+16].hex(' '), '-> dec:', ' '.join('%d' % DEC[b] for b in raw[P+i:P+i+16]))
print()
print("decode table entries for the raw opcodes used:")
for b in (0x23, 0x6b, 0xaa, 0x08, 0x0f, 0xd8, 0xee, 0xc8):
    print("  raw 0x%02x -> %2d" % (b, DEC[b]))
