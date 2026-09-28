"""Naming selection + semantic verification.

Cheap shape rules (all validated on f6f11ad1, whose true table is known):
  R1 the span-1 byte whose every tile is (r0, r0) is the MOV padding run
  R2 a span-1 byte whose tiles are all self-lookups (r_i, r_i) and that is not the
     KEY/MOV byte is LUT (the generator's sbox sweeps)
  R3 a span-1 byte with cross-lane tiles keeps {XOR ADD MUL AND OR} -- decided by
     the byte-domain / reachability sampler
  R4 a span-2 byte whose immediates are all popcount-7 byte masks is ANDI; the
     other span-2 bytes keep {MOVI XORI} -- also decided by the sampler
Semantic sampler: emulate the decoded program for many random 8-byte keys and
  (a) require every compared register value to stay inside 0..255 (the generator
      works byte-wise: KEY loads a key byte, LUT stores an sbox byte, XORI/ANDI
      have byte immediates, CMP targets are bytes -- so ADD/MUL mixing would leak
      out of the byte domain),
  (b) require every CMP target to actually occur as that lane's value for some
      sampled key (an unreachable target means the naming cannot be the one the
      shard was built with).
"""
import os, sys, struct, random, collections, itertools

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from final_lib import load, tilings, shape_of, HALT_PC
from solve2 import W, NM, REGPAIR, OPS3, OPS6

M32 = 0xFFFFFFFF
WIDTH3_SELF = (1, 3, 4, 5, 6, 7, 8, 10)


def byte_domain_ok(path, code, mop, sbox, keys, targets=None):
    """Emulate; return (all_byte_values, hits) where hits = lanes whose target was seen."""
    r = [0] * 12
    seen = [set() for _ in range(12)]
    byteval = True
    for key in keys:
        for i in range(12):
            r[i] = 0
        for i in range(8):
            r[i] = key[i]
        for pc, u in path:
            if u == 0:
                break
            a = code[pc + 1]
            if W[u] == 3:
                b = code[pc + 2]
            else:
                b = code[pc + 2]           # single-byte immediate (imm1 filter)
            if u == 1:
                r[a] = key[b] if b < 8 else 0
            elif u == 2:
                r[a] = b
            elif u == 3:
                r[a] = r[b]
            elif u == 4:
                r[a] ^= r[b]
            elif u == 5:
                r[a] = (r[a] + r[b]) & M32
            elif u == 6:
                r[a] = (r[a] * r[b]) & M32
            elif u == 7:
                r[a] &= r[b]
            elif u == 8:
                r[a] |= r[b]
            elif u == 9:
                n = b & 31
                v = r[a]
                r[a] = ((v << n) | (v >> (32 - n))) & M32 if n else v
            elif u == 10:
                r[a] = sbox[r[b] & 0xFF]
            elif u == 11:
                seen[a].add(r[a])
                if r[a] > 255:
                    byteval = False
            elif u == 12:
                r[a] &= b
            elif u == 13:
                r[a] ^= b
    return byteval, seen


def popcount(x):
    return bin(x).count('1')


def select_namings(pos, span, code, div=1, verbose=False):
    """Return list of (mop, info) candidate namings after shape rules R1-R4."""
    halt = code[HALT_PC]
    cmpc = [b for b in pos if span[b] == 2 and len(pos[b]) == 8 and
            [code[pc + 1] for pc in sorted(pos[b])] == list(range(8))]
    keyc = [b for b in pos if span[b] == 1 and len(pos[b]) == 8 and
            all(code[pc + 1] == code[pc + 2] for pc in pos[b]) and
            sorted(code[pc + 1] for pc in pos[b]) == list(range(8))]
    if len(cmpc) != 1 or len(keyc) != 1:
        return None, dict(cmpc=cmpc, keyc=keyc)
    cmpb, keyb = cmpc[0], keyc[0]
    selfbytes = [b for b in pos if span[b] == 1 and all(code[pc + 1] == code[pc + 2] for pc in pos[b])]
    pad = [b for b in selfbytes if all(code[pc + 1] == 0 and code[pc + 2] == 0 for pc in pos[b])]
    padb = pad[0] if len(pad) == 1 else None
    cands = {}
    for b in pos:
        sp = span[b]
        if sp == 0:
            cands[b] = {0}
        elif b == cmpb:
            cands[b] = {11}
        elif b == keyb:
            cands[b] = {1}
        elif sp == 1:
            s = set(OPS3) - {1}
            if not all(code[pc + 2] <= 11 for pc in pos[b]):
                s = {9}
            if b == padb:
                s = {3}                       # R1
            elif b in selfbytes:
                s = {10, 7, 8}                # R2 candidates: LUT / AND / OR (self)
            else:
                s = {4, 5, 6, 7, 8}           # R3 cross-lane
            cands[b] = s
        else:
            imms = [code[pc + 2] for pc in pos[b]]
            if all(popcount(v) == 7 for v in imms) and len(set(imms)) > 1:
                cands[b] = {12}               # R4 mask run
            else:
                cands[b] = {2, 13}
    if any(not v for v in cands.values()):
        return None, dict(cands=cands)
    order = sorted(cands, key=lambda b: (len(cands[b]), -len(pos[b])))
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
    info = dict(cmpb=cmpb, keyb=keyb, padb=padb, selfbytes=selfbytes)
    return out, info


def build_path(tiles, mop, code):
    return [(pc, mop[b]) for pc, b, sp in tiles] + [(HALT_PC, 0)]


def target_bytes(code, pos, cmpb):
    return [code[pc + 2] for pc in sorted(pos[cmpb])]


def sample_keys(n, rng):
    return [tuple(rng.randrange(256) for _ in range(8)) for _ in range(n)]
