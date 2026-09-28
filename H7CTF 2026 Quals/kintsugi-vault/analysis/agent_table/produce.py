"""Produce the final tables / dissemblies / targets, with verification.

Region classifier (derived from f6f11ad1's fully known template):
  tiles[0:8]              -> KEY   (r_i,r_i self sweep over the 8 lanes)
  head region (span 2)    -> alternating XORI, ANDI pairs on a lane subset
  each of 3 rounds        -> LUT self sweep (8) + XOR cross-lane round (16) + XORI sweep (8)
  padding run (self r0,r0)-> MOV
  last 8 span-2 tiles     -> CMP r0..r7
  final byte              -> HALT
Every classification is then re-checked for byte consistency (one raw byte = one op),
injectivity, operand validity, and sampling satisfiability.
"""
import sys, os, struct, collections, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from final_lib import load, tilings, shape_of, HALT_PC
from semantics import byte_domain_ok, sample_keys
from solve2 import W, NM, REGPAIR

OUT = os.path.dirname(os.path.abspath(__file__))
REF = 'f6f11ad133cab21c96e0185e3411ddc4'
BAD = ['080ec62d7daef51f2e635d17f9b8e075', '3e3a0fc9a5c28e964f9ba37bb499e742',
       'cfa1fa34718c426f23e2318dfe8b330d']
ALL7 = [REF] + BAD


def classify(tiles, code):
    """tile index -> op, using the template regions; returns dict or None."""
    n = len(tiles)
    lab = [None] * n
    # KEY head
    for i in range(8):
        pc, b, sp = tiles[i]
        if sp != 1 or code[pc + 1] != code[pc + 2] or code[pc + 1] != i:
            return None, 'key-block'
        lab[i] = 1
    # CMP tail
    for i in range(n - 8, n):
        pc, b, sp = tiles[i]
        j = i - (n - 8)
        if sp != 2 or code[pc + 1] != j or code[pc + 3] or code[pc + 4] or code[pc + 5]:
            return None, 'cmp-block'
        lab[i] = 11
    # MOV padding: maximal suffix run (before CMP) of self tiles with lane 0
    i = n - 9
    pad = 0
    while i >= 8 and tiles[i][2] == 1 and code[tiles[i][0] + 1] == 0 and code[tiles[i][0] + 2] == 0:
        pad += 1
        lab[i] = 3
        i -= 1
    # remaining middle region: head alternation + 3 rounds
    mid = list(range(8, n - 8 - pad))
    k = 0
    # head: alternating span-2 tiles whose lanes are a strict subset (<8 distinct)
    head = []
    while k < len(mid) and tiles[mid[k]][2] == 2:
        head.append(mid[k])
        k += 1
    lanes_head = set(code[tiles[j][0] + 1] for j in head)
    if len(lanes_head) >= 8 or len(head) % 2:
        return None, 'head-region'
    for t, j in enumerate(head):
        lab[j] = 13 if t % 2 == 0 else 12        # XORI, ANDI, XORI, ANDI ...
    rounds = 0
    while k < len(mid):
        # LUT sweep (8 self tiles, lanes 0..7)
        blk = mid[k:k + 8]
        if len(blk) != 8 or any(tiles[j][2] != 1 or code[tiles[j][0] + 1] != code[tiles[j][0] + 2]
                               or code[tiles[j][0] + 1] != t for t, j in enumerate(blk)):
            return None, 'lut-sweep@%d' % k
        for j in blk:
            lab[j] = 10
        k += 8
        # XOR round (16 cross-lane tiles)
        blk = mid[k:k + 16]
        if len(blk) != 16 or any(tiles[j][2] != 1 or code[tiles[j][0] + 1] == code[tiles[j][0] + 2]
                                 or code[tiles[j][0] + 1] > 7 or code[tiles[j][0] + 2] > 7 for j in blk):
            return None, 'xor-round@%d' % k
        for j in blk:
            lab[j] = 4
        k += 16
        # XORI sweep (8 span-2 tiles, lanes 0..7)
        blk = mid[k:k + 8]
        if len(blk) != 8 or any(tiles[j][2] != 2 or code[tiles[j][0] + 1] != t for t, j in enumerate(blk)):
            return None, 'xori-sweep@%d' % k
        for j in blk:
            lab[j] = 13
        k += 8
        rounds += 1
    if rounds != 3:
        return None, 'rounds=%d' % rounds
    mop = {}
    for idx, (pc, b, sp) in enumerate(tiles):
        if mop.setdefault(b, lab[idx]) != lab[idx]:
            return None, 'byte %02x needs two ops' % b
    mop[code[HALT_PC]] = 0
    return mop, 'ok(pad=%d,head=%d)' % (pad, len(head))


def hard_check(mop, tiles, code):
    path = [(pc, mop[b]) for pc, b, sp in tiles] + [(HALT_PC, 0)]
    if len(set(mop.values())) != len(mop):
        return path, ['op reuse (not a permutation)']
    probs = []
    for pc, u in path:
        if u > 13:
            probs.append('op>13@%d' % pc)
        if u and code[pc + 1] > 11:
            probs.append('reg>11@%d' % pc)
        if u in REGPAIR and code[pc + 2] > 11:
            probs.append('reg>11@%d' % pc)
    if sum(1 for _, u in path if u == 11) != 8:
        probs.append('cmp count')
    if path[-1] != (HALT_PC, 0):
        probs.append('halt not last')
    s = 0
    for pc, u in path:
        s += W[u]
    if s != 649:
        probs.append('width sum %d' % s)
    return path, probs


def canon_table(assign):
    t = [None] * 256
    for b, u in assign.items():
        if t[b] is not None and t[b] != u:
            raise AssertionError('conflict')
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


def disasm(code, path, tbl_assign):
    L = ['; Kintsugi Vault shard %s program, disassembled under the reconstructed decode table' % NAMECUR,
         '; program @0x232, 649 bytes, %d instructions, walk covers 0..648 and stops at HALT' % len(path),
         '; opcode bytes: ' + ' '.join('%02x=%s' % (b, NM[u]) for b, u in sorted(tbl_assign.items())), '']
    for pc, u in path:
        if u == 0:
            L.append('%4d:  %02x        HALT' % (pc, code[pc]))
        elif W[u] == 3 and u in REGPAIR:
            L.append('%4d:  %02x %02x %02x  %-4s r%d, r%d' % (pc, code[pc], code[pc + 1], code[pc + 2], NM[u], code[pc + 1], code[pc + 2]))
        elif u == 9:
            L.append('%4d:  %02x %02x %02x  ROL  r%d, %d' % (pc, code[pc], code[pc + 1], code[pc + 2], code[pc + 1], code[pc + 2]))
        else:
            imm = struct.unpack_from('<I', code, pc + 2)[0]
            L.append('%4d:  %02x %02x %02x %02x %02x %02x  %-4s r%d, 0x%02x' % (
                pc, code[pc], code[pc + 1], code[pc + 2], code[pc + 3], code[pc + 4], code[pc + 5],
                NM[u], code[pc + 1], imm))
    return L


rng = random.Random(20260927)
KEYS = sample_keys(4000, rng)
NAMECUR = ''
report = {}


def run_all():
  global NAMECUR
  for name in ALL7:
    sh = load(name)
    code, tbl, sbox = sh['code'], sh['tbl'], sh['sbox']
    NAMECUR = name
    tl, _ = tilings(code, lane_max=7, imm1=True)
    if not tl:
        print('=' * 90)
        print('%s  tilings=0 (template mismatch: this shard uses the other generator shape)' % name[:12])
        continue
    tiles = list(tl.values())[0]
    pos, span = shape_of(tiles, code)
    mop, why = classify(tiles, code)
    print('=' * 90)
    print('%s  tilings=%d  classify -> %s' % (name[:12], len(tl), why))
    if mop is None:
        continue
    path, probs = hard_check(mop, tiles, code)
    tgt = ''.join('%02x' % code[pc + 2] for pc, u in path if u == 11)
    byteval, seen = byte_domain_ok(path, code, mop, sbox, KEYS)
    hits = sum(1 for i in range(8) if code[[pc for pc, u in path if u == 11][i] + 2] in seen[i])
    matchreal = (name == REF and all(tbl[b] == u for b, u in mop.items()))
    print('  hard-check problems: %s | target=%s | byte-domain=%s | reachable=%d/8%s' % (
        probs or 'none', tgt, byteval, hits, ('  [RECONSTRUCTED == REAL TABLE: %s]' % matchreal) if name == REF else ''))
    report[name] = dict(mop=mop, path=path, tgt=tgt, tiles=tiles, pos=pos)
    if name == REF:
        continue                                   # self-test only, no output files
    tab = canon_table(mop)
    raw = bytes(tab)
    open(os.path.join(OUT, name + '.table'), 'wb').write(raw)
    open(os.path.join(OUT, name + '.table.hex'), 'w').write(raw.hex() + '\n')
    lines = disasm(code, path, mop)
    cmpi = [(pc, code[pc + 1], code[pc + 2]) for pc, u in path if u == 11]
    lines += ['', '; 8 CMP target check (the shard-defined 8-byte target): %s' % tgt]
    for pc, r, v in cmpi:
        lines.append(';   pc=%d  CMP r%d, 0x%02x' % (pc, r, v))
    lines.append('; opcode bytes decoded by the walk: %d; ops never used (%s) are parked in the' % (
        len(mop), ','.join(NM[u] for u in range(14) if u not in set(mop.values()))))
    lines.append('; table at raw bytes never decoded by this program, so the table is a permutation.')
    open(os.path.join(OUT, name + '.asm.txt'), 'w').write('\n'.join(lines) + '\n')
    print('  wrote %s.table (%d bytes, permutation=%s) .table.hex (%d hex chars) .asm.txt (%d lines)' % (
        name[:12], len(raw), sorted(tab) == list(range(256)), len(raw.hex()), len(lines)))
  return report


if __name__ == '__main__':
    import json
    run_all()
    print(json.dumps({k[:12]: v['tgt'] for k, v in report.items()}, indent=1))

