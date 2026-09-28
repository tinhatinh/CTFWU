"""Two-phase decode-table reconstruction (fast + exhaustive).

Phase 1 (tiling): the 649-byte program is 216 three-byte groups + 1 final byte.
  Every instruction starts at a group boundary (widths are 3 and 6, and the only
  width-1 instruction is the final HALT), so a "tiling" is a choice, per visited
  group, of taking 1 or 2 groups, subject to:
    * the tiling covers all 216 groups exactly (then pc = 648 = the HALT byte);
    * byte -> group-span is a FUNCTION (one raw byte can never straddle two widths);
    * at most 14 distinct opcode bytes (a permutation table holds 0..13 once each);
    * the byte at pc+1 of every tile is <= 11 (every op has its destination
      register there), and the HALT byte never collides with an opcode byte.
Phase 2 (naming): assign real opcodes to the opcode bytes, injectively, within the
  width class each byte got in phase 1 (width1->{0}; width3->{1,3,4,5,6,7,8,9,10};
  width6->{2,11,12,13}), with the per-op operand constraints and exactly 8 CMPs
  whose immediates are single bytes.
"""
import os, struct, itertools, collections

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.normpath(os.path.join(HERE, '..', '..', 'files'))
W = {0: 1, 1: 3, 2: 6, 3: 3, 4: 3, 5: 3, 6: 3, 7: 3, 8: 3, 9: 3, 10: 3, 11: 6, 12: 6, 13: 6}
NM = ['HALT', 'KEY', 'MOVI', 'MOV', 'XOR', 'ADD', 'MUL', 'AND', 'OR', 'ROL',
      'LUT', 'CMP', 'ANDI', 'XORI']
REGPAIR = (1, 3, 4, 5, 6, 7, 8, 10)
OPS3 = (1, 3, 4, 5, 6, 7, 8, 9, 10)
OPS6 = (2, 11, 12, 13)
NG = 216


def load(name):
    d = open(os.path.join(BASE, name + '.shard'), 'rb').read()
    assert d[:4] == b'KSHD'
    tl, pl = struct.unpack_from('<HH', d, 8)
    assert (tl, pl) == (256, 649), (tl, pl)
    return dict(name=name, raw=d, flag=d[5], tbl=list(d[0x32:0x132]),
                sbox=d[0x132:0x232], code=d[0x232:])


def tilings(code, max_tilings=2_000_000):
    """Enumerate byte->width maps (as frozensets) plus their tile list."""
    res = {}
    bw = {}                      # opcode byte -> groups spanned (1 or 2)
    tiles = []                   # (pc, byte, span)
    halt_byte = code[648]
    nodes = [0]

    def rec(i):
        nodes[0] += 1
        if len(res) > max_tilings:
            return
        if i == NG:
            res[frozenset(bw.items())] = list(tiles)
            return
        pc = 3 * i
        b = code[pc]
        for span in (1, 2):
            if i + span > NG:
                continue
            if code[pc + 1] > 11:            # destination register byte
                continue
            if span == 2 and pc + 6 > 648:
                continue
            known = bw.get(b)
            if known is not None:
                if known != span:
                    continue
            else:
                if len(bw) >= 14:
                    continue
                if b == halt_byte:
                    continue                 # that byte must decode to HALT
                bw[b] = span
            tiles.append((pc, b, span))
            rec(i + span)
            tiles.pop()
            if known is None:
                del bw[b]

    rec(0)
    return res, nodes[0]


def name_ops(code, tiles, strict_cmp=True, ncmp_target=8):
    """Assign opcodes within width classes; yield every valid full assignment."""
    bytew = {}
    for pc, b, span in tiles:
        bytew[b] = span
    cls3 = sorted([b for b, s in bytew.items() if s == 1])
    cls6 = sorted([b for b, s in bytew.items() if s == 2])
    n3, n6 = len(cls3), len(cls6)
    if n3 > len(OPS3) or n6 > len(OPS6):
        return []
    out = []
    for p3 in itertools.permutations(OPS3, n3):
        m3 = dict(zip(cls3, p3))
        # width-3 operand check (ROL only needs pc+1; the others need pc+2 <= 11)
        ok = True
        seen6 = set()
        for pc, b, span in tiles:
            if span != 1:
                seen6.add(b)
                continue
            u = m3[b]
            if u in REGPAIR and code[pc + 2] > 11:
                ok = False
                break
        if not ok:
            continue
        for p6 in itertools.permutations(OPS6, n6):
            m6 = dict(zip(cls6, p6))
            mop = dict(m3)
            mop.update(m6)
            mop[648 and code[648]] = 0
            ncmp = 0
            good = True
            for pc, b, span in tiles:
                u = mop[b]
                if u == 11:
                    ncmp += 1
                    if strict_cmp and (code[pc + 3] or code[pc + 4] or code[pc + 5]):
                        good = False
                        break
            if not good or ncmp != ncmp_target:
                continue
            path = [(pc, mop[b]) for pc, b, span in tiles] + [(648, 0)]
            out.append((mop, path))
    return out


def solve_all(name, strict_cmp=True, verbose=False):
    sh = load(name)
    code = sh['code']
    tl, nodes = tilings(code)
    sols = []
    for bwset, tiles in tl.items():
        for mop, path in name_ops(code, tiles, strict_cmp):
            sols.append((mop, path, tiles))
    return sh, tl, sols, nodes


def cmp_list(code, path):
    return [(pc, code[pc + 1], struct.unpack_from('<I', code, pc + 2)[0])
            for pc, u in path if u == 11]


def disasm(code, path):
    lines = []
    for pc, u in path:
        if u == 0:
            lines.append('%4d  %02x  %-8s' % (pc, code[pc], 'HALT'))
        elif W[u] == 3 and u in REGPAIR:
            lines.append('%4d  %02x  %-8s r%-2d, r%-2d   [bytes %02x %02x]' % (
                pc, code[pc], NM[u], code[pc + 1], code[pc + 2], code[pc + 1], code[pc + 2]))
        elif u == 9:
            lines.append('%4d  %02x  %-8s r%-2d, %d      [bytes %02x %02x]' % (
                pc, code[pc], 'ROL', code[pc + 1], code[pc + 2], code[pc + 1], code[pc + 2]))
        else:
            imm = struct.unpack_from('<I', code, pc + 2)[0]
            lines.append('%4d  %02x  %-8s r%-2d, %s' % (
                pc, code[pc], NM[u], code[pc + 1],
                '0x%02x (byte)' % imm if imm < 256 else '0x%08x' % imm))
    return lines


def canon_table(assign):
    t = [None] * 256
    for b, u in assign.items():
        t[b] = u
    free = [b for b in range(256) if b not in assign]
    for u in range(14):
        if u not in set(assign.values()):
            t[free.pop(0)] = u
    rest = list(range(14, 256))
    for b in free:
        t[b] = rest.pop(0)
    assert sorted(t) == list(range(256))
    return t
