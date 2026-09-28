"""Reconstruct each shard's decode table from program self-consistency.

Constraints used (all derived from the vmrun interpreter, see notes.md):
  * the dispatch dies if a decoded op > 13            -> executed raws must map into 0..13
  * the working table is a permutation of 0..255       -> distinct raws get DISTINCT ops (<=14 raws)
  * register cells only exist for R0..R13 (0x30..0x5f) -> operand bytes >= 14 read stack junk
  * op0 halts, otherwise the walk must cover the code  -> termination at 649 or at a 0
"""
import os, sys, struct, itertools

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'files')
W = {0: 1, 1: 3, 2: 3, 3: 3, 4: 6, 5: 6, 6: 3, 7: 3, 8: 3, 9: 6, 10: 3, 11: 3, 12: 3, 13: 6}
NM = ['HALT', 'TBL', 'MULR', 'KEY', 'MOVI', 'XORI', 'ANDR', 'ORR', 'ADDR', 'CMPI',
      'MOV', 'XORR', 'ROLR', 'ANDI']
# ops that are harmless given the operands we see (skip ones that read out-of-window regs)
MAXREG = 13


def load(name):
    d = open(os.path.join(BASE, name + '.shard'), 'rb').read()
    return dict(name=name, raw=d, flag=d[5], tbl=list(d[0x32:0x132]), sbox=d[0x132:0x232],
                code=d[0x232:])


def fmt(op, code, pc):
    a = code[pc + 1] if W[op] >= 3 else None
    b = code[pc + 2] if W[op] == 3 else None
    if op == 0:
        return 'HALT'
    if W[op] == 3:
        return '%-5s r%d, r%d' % (NM[op], a, b)
    imm = struct.unpack_from('<I', code, pc + 2)[0]
    if op == 9:
        return 'CMPI  r%d, %#x' % (a, imm)
    return '%-5s r%d, %#x' % (NM[op], a, imm)


def search(code, limit=40, seed_map=None, allow_ops=None):
    """DFS over (raw -> op). yields (list_of_(pc,op), stop_pc, why)."""
    results = []
    used_ops = set()
    m = {}
    if seed_map:
        m.update(seed_map)
        used_ops.update(m.values())

    def walk(pc, seq):
        if len(results) >= limit:
            return
        while True:
            if pc >= len(code):
                results.append((list(seq), pc, 'end'))
                return
            if pc + 1 > len(code):
                return
            c = code[pc]
            if c in m:
                op = m[c]
            else:
                cand = [o for o in (allow_ops if allow_ops else range(14))
                        if o not in used_ops and W[o] <= len(code) - pc]
                for op in cand:
                    # operand sanity for 3-byte reg-reg forms: both operands in window
                    if W[op] == 3 and (code[pc + 1] > MAXREG or code[pc + 2] > MAXREG):
                        continue
                    if W[op] == 6 and code[pc + 1] > MAXREG:
                        continue
                    if op == 0:
                        m[c] = op
                        seq.append((pc, op))
                        results.append((list(seq), pc, 'halt'))
                        seq.pop()
                        del m[c]
                        continue
                    m[c] = op
                    used_ops.add(op)
                    seq.append((pc, op))
                    walk(pc + W[op], seq)
                    seq.pop()
                    del m[c]
                    used_ops.discard(op)
                    if len(results) >= limit:
                        return
                return   # undecided -> handled by recursion above
            if op == 0:
                seq.append((pc, op))
                results.append((list(seq), pc, 'halt'))
                return
            seq.append((pc, op))
            pc += W[op]
    walk(0, [])
    return results


def key(sh):
    return tuple(op for _, op in sh)


if __name__ == '__main__':
    names = ['f6f11ad133cab21c96e0185e3411ddc4', '3df10ef4d0789f749d972c92c8085358',
             '63bafd7f4e981709287955968d1068c0', 'f14ad4e23f898cca82c2025614bc7a7c',
             '080ec62d7daef51f2e635d17f9b8e075', '3e3a0fc9a5c28e964f9ba37bb499e742',
             'cfa1fa34718c426f23e2318dfe8b330d']
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for n in names:
        if only and not n.startswith(only):
            continue
        sh = load(n)
        R = search(sh['code'], limit=6)
        print('#### %s flag=%02x  candidates=%d' % (n[:12], sh['flag'], len(R)))
        for seq, stop, why in R[:3]:
            ops = [o for _, o in seq]
            cnt = {}
            for o in ops:
                cnt[NM[o]] = cnt.get(NM[o], 0) + 1
            print('   stop=%d(%s) instrs=%d distinct_raws=%d  %s' % (
                stop, why, len(seq), len(set(sh['code'][p] for p, _ in seq)),
                ' '.join('%s:%d' % kv for kv in sorted(cnt.items()))))
