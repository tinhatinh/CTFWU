import glob, struct, sys, collections
sys.path.insert(0, r"C:\Users\Administrator\Documents\Qoder\2026-09-23\1788d23b\CTF-Writeups\kintsugi-vault\analysis\agent_vm")
from vm_isa import VM, SIZE, NAME
BASE = r"C:\Users\Administrator\Documents\Qoder\2026-09-23\1788d23b\CTF-Writeups\kintsugi-vault\files"
for f in sorted(glob.glob(BASE + r"\*.shard")):
    raw = open(f, 'rb').read()
    t, plen = struct.unpack_from('<2H', raw, 8)
    dec = raw[0x32:0x132]
    P = 0x32 + t + 256
    prog = raw[P:P+plen]
    pc = 0; ops = collections.Counter(); regs = {}; bad = None; n = 0
    while pc < len(prog):
        d = dec[prog[pc]]
        if d > 13: bad = ('badoptc', pc, d); break
        s = SIZE[d]
        if pc + s > len(prog): bad = ('truncated', pc); break
        n += 1; ops[NAME[d]] += 1
        if d: regs[prog[pc+1]] = regs.get(prog[pc+1], 0) + 1
        if d in (1,): regs['k%d' % prog[pc+2]] = 1
        if d == 0: break
        pc += s
    print("%s size=%d t=0x%x plen=%d instrs=%d tail_ok=%s" % (
        f.split('\\')[-1][:8], len(raw), t, plen, n, pc == len(prog)-1 or pc+1 == len(prog)))
    print("   ops:", dict(ops))
    print("   dest reg idxs:", sorted(k for k in regs if isinstance(k, int)),
          " key idxs:", sorted(int(k[1:]) for k in regs if isinstance(k, str)))
    print("   max dest cell =", max([k for k in regs if isinstance(k, int)] or [-1]), bad or '')
    v = VM(raw); print("   run with zero key ->", v.run(), "pc=", v.pc)
