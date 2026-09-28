"""Template transfer + verification -> final answers.

f6f11ad1's decoded program is the generator template (its true table is known):
  KEY r_i,r_i (x8) | (XORI,ANDI) x m | 3 x [ LUT sweep (x8) , XOR mixing round (x16) ,
  XORI sweep (x8) ] | MOV r0,r0 padding | CMP r0..r7 (x8) | HALT
with m = 4 for f6f11ad1.  The reconstructed tilings of the three scrambled shards
reproduce this tile layout (byte-for-byte position-identical for two of them, and
m = 5 with 4 fewer padding tiles for the third), so the opcode *names* transfer by
region; every transferred naming is then re-checked against all hard constraints
and against the sampling satisfiability test.
"""
import sys, os, struct, collections, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from final_lib import load, tilings, shape_of, HALT_PC
from semantics import select_namings, build_path, byte_domain_ok, target_bytes, sample_keys
from solve2 import W, NM

REF = 'f6f11ad133cab21c96e0185e3411ddc4'
BAD = ['080ec62d7daef51f2e635d17f9b8e075', '3e3a0fc9a5c28e964f9ba37bb499e742',
       'cfa1fa34718c426f23e2318dfe8b330d']


def real_walk(sh):
    code, tbl = sh['code'], sh['tbl']
    seq, pc = [], 0
    while pc < HALT_PC:
        u = tbl[code[pc]]
        seq.append((pc, u))
        pc += W[u]
    seq.append((HALT_PC, 0))
    return seq


def runs(seq):
    out, last = [], None
    for pc, u in seq:
        if u != last:
            out.append([u, 1])
            last = u
        else:
            out[-1][1] += 1
    return [(NM[u], c) for u, c in out]


def transfer(tiles, code, reftiles_by_region):
    """Assign ops to tiles by region: the k-th tile of the shard takes the op of the
    k-th tile of the reference template, walking the reference run-length list."""
    refseq = reftiles_by_region
    if len(refseq) != len(tiles) + 1:
        return None
    mop = {}
    for (pc, b, sp), (rpc, ru) in zip(tiles, refseq):
        if mop.setdefault(b, ru) != ru:
            return None            # byte would need two different ops
    if mop.get(code[HALT_PC], 0) != 0:
        return None
    mop[code[HALT_PC]] = 0
    return mop


ref = load(REF)
refseq = real_walk(ref)
print('REF template runs:', runs(refseq))
rng = random.Random(7)
KEYS = sample_keys(4000, rng)

for name in [REF] + BAD:
    sh = load(name)
    code, tbl, sbox = sh['code'], sh['tbl'], sh['sbox']
    tl, _ = tilings(code, lane_max=7, imm1=True)
    print('=' * 92)
    print(name)
    assert len(tl) == 1, len(tl)
    tiles = list(tl.values())[0]
    pos, span = shape_of(tiles, code)
    namings, info = select_namings(pos, span, code)
    tr = transfer(tiles, code, refseq)
    tag = 'self' if name == REF else 'transferred'
    print('  tiles=%d namings(shape)=%d  %s naming valid=%s' % (len(tiles), len(namings), tag, tr is not None))
    cand = tr if tr is not None else (namings[0] if namings else None)
    if name == REF:
        print('  recovered == real table at every opcode byte:', cand == {b: tbl[b] for b in pos})
    print('  naming: %s' % ' '.join('%02x:%s' % (b, NM[u]) for b, u in sorted(cand.items())))
    print('  runs:', runs(build_path(tiles, cand, code)))
    path = build_path(tiles, cand, code)
    tgt = target_bytes(code, pos, info['cmpb'])
    byteval, seen = byte_domain_ok(path, code, cand, sbox, KEYS, tgt)
    hits = sum(1 for i in range(8) if tgt[i] in seen[i])
    print('  target=%s  byte-domain=%s  reachable-lanes=%d/8' % (''.join('%02x' % t for t in tgt), byteval, hits))
    incmp = [(pc, u) for pc, u in path if u == 11]
    print('  CMP count=%d  ops<=13 ok=%s  operand<=7 ok=%s' % (
        len(incmp), all(u <= 13 for _, u in path),
        all(code[pc + 1] <= 7 and (W[u] != 3 or code[pc + 2] <= 7) for pc, u in path if u)))
    print('  also in shape-namings list: %s' % (cand in namings))
