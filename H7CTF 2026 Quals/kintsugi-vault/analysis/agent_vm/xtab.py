import glob, struct
BASE = r"C:\Users\Administrator\Documents\Qoder\2026-09-23\1788d23b\CTF-Writeups\kintsugi-vault\analysis\agent_vm"
F = r"C:\Users\Administrator\Documents\Qoder\2026-09-23\1788d23b\CTF-Writeups\kintsugi-vault\files"
SIZE = {0:1,1:3,2:6,3:3,4:3,5:3,6:3,7:3,8:3,9:3,10:3,11:6,12:6,13:6}
sh = {f.split('\\')[-1][:8]: open(f,'rb').read() for f in sorted(glob.glob(F+r"\*.shard"))}
for n, raw in sh.items():
    print(n, "flag@5=%02x bit0=%d" % (raw[5], raw[5]&1), "b4=%02x" % raw[4], "hdr16:", raw[:16].hex())
def parses(raw, dec):
    t, plen = struct.unpack_from('<2H', raw, 8); pc = 0; P = 0x32+t+256
    prog = raw[P:P+plen]
    while pc < len(prog):
        d = dec[prog[pc]]
        if d > 13: return None
        if pc+SIZE[d] > len(prog): return None
        if d == 0: return pc+1
        pc += SIZE[d]
    return pc
print("\ncross-table test (row=program shard, col=table shard):")
print("        " + " ".join("%8s" % n for n in sh))
for pn, praw in sh.items():
    row = []
    for tn, traw in sh.items():
        r = parses(praw, traw[0x32:0x132])
        row.append("%8s" % ("OK@%d" % r if r else "-"))
    print("%8s" % pn + " ".join(row))
