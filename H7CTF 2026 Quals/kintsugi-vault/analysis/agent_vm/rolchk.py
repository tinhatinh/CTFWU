import glob, struct, os
F = r"C:\Users\Administrator\Documents\Qoder\2026-09-23\1788d23b\CTF-Writeups\kintsugi-vault\files"
S = {0:1,1:3,2:6,3:3,4:3,5:3,6:3,7:3,8:3,9:3,10:3,11:6,12:6,13:6}
for f in sorted(glob.glob(F + r"\*.shard")):
    raw = open(f, 'rb').read()
    t, plen = struct.unpack_from('<2H', raw, 8)
    dec = raw[0x32:0x132]; P = 0x32 + t + 256; prog = raw[P:P+plen]
    pc = 0; rols = []; keys = []; mx = 0; ok = True
    while pc < len(prog):
        d = dec[prog[pc]]
        if d > 13: ok = False; break
        if d == 0: break
        if d == 9: rols.append(prog[pc+2])
        if d == 1: keys.append(prog[pc+2])
        if d > 1: mx = max(mx, prog[pc+1], prog[pc+2] if S[d] == 3 else 0)
        pc += S[d]
    n = os.path.basename(f)[:8]
    if not ok:
        print(n, "flag=%02x -> decode table comes from EXTERNAL file (bit0 of flag@5 clear)" % raw[5])
        continue
    print(n, "flag=%02x self-table OK len=%d" % (raw[5], pc + 1),
          "| rol counts:", ['0x%02x' % x for x in rols],
          "| rol>=32:", ['0x%02x' % x for x in rols if x >= 32],
          "| max operand:", mx, "| key idx>7:", [x for x in keys if x > 7])
