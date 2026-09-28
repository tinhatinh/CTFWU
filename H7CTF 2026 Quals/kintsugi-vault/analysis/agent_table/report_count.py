"""Ambiguity accounting + final deliverable check.

(A) hard constraints only (the task's bullet list): count tilings, namings, distinct
    target strings;
(B) plus the byte-domain shape of the generator (register operands are lanes 0..7,
    every immediate is a single byte): count tilings (expected: 1) and namings;
(C) satisfiability sieve on the shape-rule namings: how of them admit an 8-byte key
    that passes all 8 CMPs (backward preimage + forward run on analysis/vm.py's VM).
"""
import sys, os, collections, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from final_lib import load, tilings, shape_of, HALT_PC
from semantics import select_namings, byte_domain_ok, sample_keys
from produce import classify, hard_check, canon_table
from backward import backward
from solve2 import W, NM
from vm import VM

REF = 'f6f11ad133cab21c96e0185e3411ddc4'
NAMES = [REF, '080ec62d7daef51f2e635d17f9b8e075', '3e3a0fc9a5c28e964f9ba37bb499e742',
         'cfa1fa34718c426f23e2318dfe8b330d']
rng = random.Random(99)
KEYS = sample_keys(600, rng)


def hard_namings(pos, span, code):
    """All injective namings satisfying only the task bullets."""
    cands = {}
    for b in pos:
        sp = span[b]
        if sp == 0:
            cands[b] = {0}
        elif sp == 1:
            s = set(range(1, 11))
            if not all(code[pc + 2] <= 11 for pc in pos[b]):
                s = {9}
            cands[b] = s
        else:
            s = {2, 11, 12, 13}
            if not (len(pos[b]) == 8 and all(code[pc + 3] == code[pc + 4] == code[pc + 5] == 0
                                             for pc in pos[b])):
                s.discard(11)
            cands[b] = s
    if any(not v for v in cands.values()):
        return []
    # op 11 must be used exactly once (8 CMPs) -> at least one byte keeps 11
    order = sorted(cands, key=lambda b: (len(cands[b]), -len(pos[b])))
    out, used, cur = [], set(), {}

    def rec(k):
        if len(out) > 400000:
            return
        if k == len(order):
            if 11 in cur.values():
                out.append(dict(cur))
            return
        b = order[k]
        for u in sorted(cands[b]):
            if u in used:
                continue
            used.add(u)
            cur[b] = u
            rec(k + 1)
            used.discard(u)
            del cur[b]

    rec(0)
    return out


def tiles_to_pos(tiles, code):
    return shape_of(tiles, code)


for name in NAMES:
    sh = load(name)
    code, sbox = sh['code'], sh['sbox']
    print('=' * 92)
    print(name)
    # (A)
    tlA, _ = tilings(code, lane_max=11, imm1=False)
    nA, tA = 0, collections.Counter()
    for bw, tiles in tlA.items():
        pos, span = tiles_to_pos(tiles, code)
        ns = hard_namings(pos, span, code)
        nA += len(ns)
        for mop in ns[:4000]:
            tA[''.join('%02x' % code[pc + 2] for pc, u in
                       sorted((pc, mop[b]) for pc, b, sp in tiles if mop[b] == 11))] += 1
    print('  (A) hard-only: tilings=%d namings=%d distinct-target-strings=%d %s' % (
        len(tlA), nA, len(tA), [t for t, _ in tA.most_common(4)]))
    # (B)
    tlB, _ = tilings(code, lane_max=7, imm1=True)
    tiles = list(tlB.values())[0]
    pos, span = tiles_to_pos(tiles, code)
    nsB, info = select_namings(pos, span, code)
    print('  (B) + byte-domain shape: tilings=%d shape-rule namings=%d' % (len(tlB), len(nsB or [])))
    # (C) satisfiability of the 26 shape namings + the classified naming
    mop_ref, why = classify(tiles, code)
    path_ref, probs = hard_check(mop_ref, tiles, code)
    tab_ref = canon_table(mop_ref)
    targets = [code[pc + 2] for pc, u in path_ref if u == 11]
    sat = []
    for mop in (nsB or []) + [mop_ref]:
        path, pr = hard_check(mop, tiles, code)
        if pr:
            continue
        t = [code[pc + 2] for pc, u in path if u == 11]
        if any(u not in (0, 1, 3, 4, 10, 11, 12, 13) for _, u in path):
            continue
        states, reqs, err = backward(code, path, sbox, t)
        if not states:
            continue
        tab = canon_table(mop)
        ok = None
        for s, rq in zip(states, reqs):
            if len(rq) != 8:
                continue
            key = bytes(rq[i] for i in range(8))
            if VM(tab, bytes(sbox), code, key).run()[0] == 'HALT':
                ok = key
                break
        if ok:
            sat.append((tuple(sorted(mop.items())), ok.hex(), ''.join('%02x' % x for x in t)))
    uniq = collections.Counter(t for _, _, t in sat)
    print('  (C) satisfiable namings: %d distinct assignments, targets=%s, ref-classified satisfiable=%s' % (
        len(set(sat)), dict(uniq), any(k == tuple(sorted(mop_ref.items())) for k, _, _ in sat)))
    for k, keyhex, t in sorted(set(sat))[:6]:
        print('      %s key=%s tgt=%s%s' % (' '.join('%02x:%s' % (b, NM[u]) for b, u in k), keyhex, t,
                                            '   <== chosen' if k == tuple(sorted(mop_ref.items())) else ''))
    if name == REF:
        real = tuple(sorted((b, sh['tbl'][b]) for b in pos))
        print('  SELF-TEST: real in-file table among chosen namings: %s' % (real == tuple(sorted(mop_ref.items()))))
