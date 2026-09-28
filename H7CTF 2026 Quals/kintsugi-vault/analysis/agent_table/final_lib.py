"""Final decoder-reconstruction pipeline.

Phase 1  tilings(code, ...): walk the program as a tiling of 3-byte groups
         (span 1 = width-3 op, span 2 = width-6 op) with a persistent
         byte -> span function, <= 14 opcode bytes, ending exactly on the final
         byte pc=648 (which must therefore decode to HALT).
         Optional shape checks, both true for every good shard:
            lane:  the two register operand bytes are <= lane_max
            imm1:  width-6 immediates occupy a single byte (bytes pc+3..pc+5 are 0)
Phase 2  naming: injective raw -> op within the width classes, plus
            CMP    : exactly one span-2 byte, 8 tiles, destination r0..r7 in order
            KEY    : span-1 byte whose 8 tiles are r_i, r_i (i = 0..7 each once)
            LUT    : span-1 byte whose tiles are all r_i, r_i (self lookup)
            counts : every opcode byte's tile count divisible by `div`
"""
import os, sys, struct, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from solve2 import load, W, NM, REGPAIR, OPS3, OPS6, NG

HALT_PC = 648


def tilings(code, lane_max=7, imm1=True, max_out=2_000_000):
    res = {}
    bw, tiles, halt = {}, [], code[HALT_PC]
    nodes = [0]

    def rec(i):
        nodes[0] += 1
        if len(res) > max_out:
            return
        if i == NG:
            res[frozenset(bw.items())] = list(tiles)
            return
        pc = 3 * i
        b = code[pc]
        for span in (1, 2):
            if i + span > NG or code[pc + 1] > lane_max:
                continue
            if span == 1:
                if code[pc + 2] > lane_max:
                    continue
            else:
                if pc + 6 > HALT_PC:
                    continue
                if imm1 and (code[pc + 3] or code[pc + 4] or code[pc + 5]):
                    continue
            known = bw.get(b)
            if known is not None:
                if known != span:
                    continue
            else:
                if len(bw) >= 14 or b == halt:
                    continue
                bw[b] = span
            tiles.append((pc, b, span))
            rec(i + span)
            tiles.pop()
            if known is None:
                del bw[b]

    rec(0)
    return res, nodes[0]


def shape_of(tiles, code):
    pos = collections.defaultdict(list)
    span = {}
    for pc, b, sp in tiles:
        pos[b].append(pc)
        span[b] = sp
    halt = code[HALT_PC]
    pos[halt].append(HALT_PC)
    span[halt] = 0
    return pos, span


def lane_seq(code, pcs):
    return [code[pc + 1] for pc in sorted(pcs)]


def naming_candidates(pos, span, code, div=4, key_shape=True, lut_shape=True):
    """byte -> set of admissible ops (shape filters included); None if impossible."""
    halt = code[HALT_PC]
    cands, info = {}, {}
    # CMP byte: span 2, exactly 8 tiles, destinations r0..r7 in walk order
    cmpc = [b for b in pos if span[b] == 2 and len(pos[b]) == 8 and lane_seq(code, pos[b]) == list(range(8))]
    if len(cmpc) != 1:
        return None, None
    cmpb = cmpc[0]
    # KEY byte: span 1, exactly 8 tiles, r_i,r_i covering 0..7 once
    keyc = [b for b in pos if span[b] == 1 and len(pos[b]) == 8 and
            all(code[pc + 1] == code[pc + 2] for pc in pos[b]) and
            sorted(code[pc + 1] for pc in pos[b]) == list(range(8))]
    if key_shape and len(keyc) != 1:
        return None, None
    keyb = keyc[0] if keyc else None
    for b in pos:
        sp = span[b]
        if sp == 0:
            cands[b] = {0}
            continue
        if div and len(pos[b]) % div:
            return None, None
        if sp == 1:
            s = set(OPS3)
            if not all(code[pc + 2] <= 11 for pc in pos[b]):
                s = {9}
            if keyb is not None and b != keyb:
                s.discard(1)        # only the key-load block can be KEY
            if lut_shape and not all(code[pc + 1] == code[pc + 2] for pc in pos[b]):
                s.discard(10)       # LUT is r_i,r_i in this generator
        else:
            s = set(OPS6)
            if b != cmpb:
                s.discard(11)
            cands[b] = s
            continue
        cands[b] = s
    # the check block and the key-load block are forced: exactly 8 CMPs and one KEY
    cands[cmpb] = {11}
    if key_shape and keyb is not None:
        cands[keyb] = {1}
    if any(not v for v in cands.values()):
        return None, None
    return cands, dict(cmpb=cmpb, keyb=keyb)


def enumerate_namings(cands):
    order = sorted(cands, key=lambda b: (len(cands[b]), -1))
    out, used, cur = [], set(), {}

    def rec(k):
        if k == len(order):
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


def solve_shard(name, lane_max=7, imm1=True, div=4, key_shape=True, lut_shape=True,
                max_bytes=None):
    sh = load(name)
    code = sh['code']
    tl, nodes = tilings(code, lane_max=lane_max, imm1=imm1)
    out = []
    for bwset, tiles in tl.items():
        pos, span = shape_of(tiles, code)
        if max_bytes is not None and len(pos) > max_bytes:
            continue
        cands, info = naming_candidates(pos, span, code, div=div, key_shape=key_shape,
                                        lut_shape=lut_shape)
        if cands is None:
            continue
        for mop in enumerate_namings(cands):
            out.append((tiles, pos, span, mop, info))
    return sh, tl, out, nodes


def targets_of(code, pos, mop):
    cmpb = [b for b, u in mop.items() if u == 11]
    return ''.join('%02x' % code[pc + 2] for pc in sorted(pos[cmpb[0]]))
