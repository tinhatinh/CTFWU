import sys, os, random, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from final_lib import load, tilings, shape_of, HALT_PC
from semantics import select_namings, build_path, byte_domain_ok, target_bytes, sample_keys
from solve2 import W, NM

GOOD = ['f6f11ad133cab21c96e0185e3411ddc4', '080ec62d7daef51f2e635d17f9b8e075',
        '3e3a0fc9a5c28e964f9ba37bb499e742', 'cfa1fa34718c426f23e2318dfe8b330d']
NS = 4000
rng = random.Random(1234)
KEYS = sample_keys(NS, rng)

for name in GOOD:
    sh = load(name)
    code, tbl, sbox = sh['code'], sh['tbl'], sh['sbox']
    tl, nodes = tilings(code, lane_max=7, imm1=True)
    print('=' * 92)
    print('%s tilings=%d' % (name[:12], len(tl)))
    for bwset, tiles in tl.items():
        pos, span = shape_of(tiles, code)
        namings, info = select_namings(pos, span, code)
        if namings is None:
            print('  no namings:', info)
            continue
        tgt = target_bytes(code, pos, info['cmpb'])
        print('  namings=%d cmpb=%02x keyb=%s padb=%s target=%s' % (
            len(namings), info['cmpb'], hex(info['keyb']),
            hex(info['padb']) if info['padb'] else None, ''.join('%02x' % t for t in tgt)))
        survivors = []
        for mop in namings:
            path = build_path(tiles, mop, code)
            byteval, seen = byte_domain_ok(path, code, mop, sbox, KEYS, tgt)
            hits = sum(1 for i in range(8) if tgt[i] in seen[i])
            if byteval and hits == 8:
                survivors.append((mop, hits))
        print('  semantic survivors (byte-domain + all 8 targets reachable): %d' % len(survivors))
        for mop, h in survivors[:6]:
            print('     %s' % ' '.join('%02x:%s' % (b, NM[u]) for b, u in sorted(mop.items())))
        if name.startswith('f6f1'):
            real = {b: tbl[b] for b in pos}
            print('  REAL naming:  %s' % ' '.join('%02x:%s' % (b, NM[u]) for b, u in sorted(real.items())))
            print('  real reproduced exactly: %s' % any(mop == real for mop, h in survivors))
            print('  real in namings list: %s' % (real in namings))
