import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from solve3 import analyse
from solve2 import load, tilings, W, NM

REF = 'f6f11ad133cab21c96e0185e3411ddc4'
sh = load(REF)
code, tbl = sh['code'], sh['tbl']
seq, pc = [], 0
while pc < 648:
    u = tbl[code[pc]]
    seq.append((pc, u))
    pc += W[u]
seq.append((648, 0))
runs = []
last = None
for p, u in seq:
    if u != last:
        runs.append([u, 1, p])
        last = u
    else:
        runs[-1][1] += 1
print('REF runs:', ['%s x%d@%d' % (NM[u], c, p) for u, c, p in runs])
sig = collections.Counter()
for p, u in seq:
    sig[(code[p], u)] += 1
print('REF per-byte: ', ' '.join('%02x->%s:%d' % (b, NM[u], c) for (b, u), c in sorted(sig.items())))
print('REF signature (span,count) multiset:', sorted(((W[u] // 3 if W[u] != 1 else 0, c) for (b, u), c in sig.items())))
print('REF width-sum check:', sum(W[u] for _, u in seq))
for p, u in seq[:60]:
    if u == 0:
        continue
    if W[u] == 3:
        print('   %4d %02x %s r%d,r%d' % (p, code[p], NM[u], code[p + 1], code[p + 2]))
    else:
        print('   %4d %02x %s r%d,imm=%02x %02x %02x %02x' % (p, code[p], NM[u], code[p + 1],
              code[p + 2], code[p + 3], code[p + 4], code[p + 5]))
