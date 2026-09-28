"""Glue: transfer a known shard's op-sequence (template) onto a scrambled shard.

All programs come from one generator, so a readable shard's (pc, op) sequence is a
template; the scrambled shards' raw opcode bytes at those same positions must map to
the same ops.  A consistent bijection == the missing decode table.
"""
import os, sys, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vm

CLR = ['f6f11ad133cab21c96e0185e3411ddc4', '3df10ef4d0789f749d972c92c8085358',
       '63bafd7f4e981709287955968d1068c0', 'f14ad4e23f898cca82c2025614bc7a7c']
ENC = ['080ec62d7daef51f2e635d17f9b8e075', '3e3a0fc9a5c28e964f9ba37bb499e742',
       'cfa1fa34718c426f23e2318dfe8b330d']


def template(name):
    sh = vm.load(name)
    seq, st, ex = vm.dismap(sh)
    assert st in ('HALT', 'END'), (name, st)
    return [(p, o) for p, o in seq], sh


def try_template(tseq, tgt):
    """returns (mapping raw->op, conflicts list)"""
    fwd, rev = {}, {}
    bad = []
    code = tgt['code']
    for pc, op in tseq:
        if pc >= len(code):
            bad.append(('oob', pc)); break
        c = code[pc]
        if op == 0:
            continue
        if c in fwd and fwd[c] != op:
            bad.append(('op-conflict', pc, c, fwd[c], op))
        elif c in fwd:
            continue
        else:
            if op in rev and rev[op] != c:
                bad.append(('bijection', pc, c, op, rev[op]))
                continue
            fwd[c] = op
            rev[op] = c
            if vm.W[op] == 3 and (code[pc + 1] > 11 or code[pc + 2] > 11):
                bad.append(('reg>11', pc, c, op))
            if vm.W[op] == 6 and code[pc + 1] > 11:
                bad.append(('reg>11', pc, c, op))
    return fwd, bad


if __name__ == '__main__':
    T = {n: template(n) for n in CLR}
    for e in ENC:
        tgt = vm.load(e)
        print('#### %s (flag=%02d, %d distinct in-file table values)' % (
            e[:12], tgt['flag'], len(set(tgt['tbl']))))
        for n in CLR:
            tseq, _ = T[n]
            fwd, bad = try_template(tseq, tgt)
            kinds = collections.Counter(b[0] for b in bad)
            print('   template %-12s mapped=%3d conflicts=%-4d %s' % (
                n[:12], len(fwd), len(bad), dict(kinds)))
            if bad:
                print('       first: %s' % str(bad[0])[:110])
            if len(bad) == 0:
                tbl = list(tgt['tbl'])
                inv = {v: k for k, v in fwd.items()}
                # build a table: executed raws get their op, everything else unique leftovers
                free = [x for x in range(256) if x not in fwd]
                allops = [o for o in range(14) if o not in fwd.values()] + list(range(14, 256))
                out = list(range(256))
                for c, o in fwd.items():
                    out[c] = o
                used = set(fwd.values())
                pool = [x for x in range(256) if x not in used]
                k = 0
                for c in free:
                    out[c] = pool[k]; k += 1
                cmps = [struct.unpack_from('<I', tgt['code'], p + 2)[0]
                        for p, o in tseq if o == 11]
                print('       *** CLEAN. table@0x32 replacement = %s' % bytes(out).hex()[:64])
                open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  'recovered_%s.table' % e[:8]), 'wb').write(bytes(out))
                print('       CMP low bytes: %s' % ''.join('%02x' % (c & 0xff) for c in cmps))
                print('       CMP full     : %s' % ['%08x' % c for c in cmps])
