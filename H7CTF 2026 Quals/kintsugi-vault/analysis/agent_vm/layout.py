import struct, sys
BASE = r"C:\Users\Administrator\Documents\Qoder\2026-09-23\1788d23b\CTF-Writeups\kintsugi-vault"
SH = BASE + r"\files\f6f11ad133cab21c96e0185e3411ddc4.shard"
raw = open(SH, 'rb').read()
print("file size", len(raw), "magic", raw[:4])
hdr = list(struct.unpack_from('<8H', raw, 8))
b5 = raw[5]
t = hdr[0]          # u16 @8
plen = hdr[1]       # u16 @10
print("bytes[4:16]:", raw[4:16].hex())
print("flag@5=%02x  u16@8 (t) = 0x%x  u16@10 (proglen) = 0x%x" % (b5, t, plen))
DECOFF = 0x32
dec = raw[DECOFF:DECOFF+256]
LUT_off = DECOFF + t
LUT = raw[LUT_off:LUT_off + 256]
PROG = LUT_off + 256
PROG = DECOFF+t+256
print("LUT_off=0x%x PROG_off=0x%x  proglen field=0x%x  bytes to EOF=%d" % (DECOFF+t, PROG, plen, len(raw)-PROG))
print("mined decode values:", sorted(set(dec)))

# quick histogram of decoded values over the program
from collections import Counter
c = Counter(dec[b] for b in raw[PROG:PROG+plen])
print("decoded-value histogram over program:", dict(sorted(c.items())))
open(BASE + r"\analysis\agent_vm\tables.bin", 'wb').write(dec + LUT + raw[PROG:PROG+plen])
print("PROG_off,plen,t written")
