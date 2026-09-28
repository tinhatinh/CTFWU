import glob, struct, os, collections
F = r"C:\Users\Administrator\Documents\Qoder\2026-09-23\1788d23b\CTF-Writeups\kintsugi-vault\files"
S = {0:1,1:3,2:6,3:3,4:3,5:3,6:3,7:3,8:3,9:3,10:3,11:6,12:6,13:6}
REGOP = {3:(0,1),4:(0,1),5:(0,1),6:(0,1),7:(0,1),8:(0,1),10:(0,1)}   # (dst_off, src_off)
for f in sorted(glob.glob(F + r"\*.shard")):
    raw = open(f, 'rb').read(); t, plen = struct.unpack_from('<2H', raw, 8)
    dec = raw[0x32:0x132]; P = 0x32 + t + 256; prog = raw[P:P+plen]
    pc = 0; dst = collections.Counter(); src = collections.Counter(); ki = collections.Counter()
    while pc < len(prog):
        d = dec[prog[pc]]
        if d > 13: break
        if d == 0: break
        if d == 1: dst[prog[pc+1]] += 1; ki[prog[pc+2]] += 1
        elif d == 9: dst[prog[pc+1]] += 1
        elif d in (2, 11, 12, 13): dst[prog[pc+1]] += 1
        elif d in REGOP: dst[prog[pc+1]] += 1; src[prog[pc+2]] += 1
        pc += S[d]
    n = os.path.basename(f)[:8]
    print(n, "dst:", sorted(dst), "src:", sorted(src), "key:", sorted(ki),
          "| any operand >=12:", sorted([x for x in list(dst)+list(src)+list(ki) if x >= 12]))
