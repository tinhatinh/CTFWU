"""Recover a shard's decode table from program self-consistency alone.

Verified facts used (see notes.md / isa.py):
  op = table[program[pc]];  op==0 -> HALT(ok);  op>13 -> "bad opcode"(fatal);
  pc >= proglen -> OK as well.
  widths: HALT=1, MOVI/CMP/ANDI/XORI=6, everything else=3.
  operand bytes address cells r0..r11; >=12 alias the live table => treat as invalid.
  the real table is a permutation, so DISTINCT raw opcode bytes must get DISTINCT ops.
"""
import os, sys, struct, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vm

W = vm.W
OPS3 = [o for o in range(14) if W[o] == 3]
OPS6 = [o for o in range(14) if W[o] == 6]
MAXOP = 11


def recover(code, allow=None, cap=200000):
    """DFS: returns list of (mapping dict, [(pc,op)...], stopinfo)."""
    sols = []
    m = {}
    used = set()

    def go(pc, seq):
        if len(sols) >= cap:
            return True
        while True:
            if pc >= len(code):
                sols.append((dict(m), list(seq), ('END', pc)))
                return len(sols) >= cap
            c = code[pc]
            if c in m:
                op = m[c]
                if op == 0:
                    sols.append((dict(m), list(seq) + [(pc, 0)], ('HALT', pc)))
                    return False
                seq.append((pc, op))
                pc += W[op]
                continue
            cand = [o for o in (allow if allow is not None else range(14)) if o not in used]
            for op in cand:
                if pc + W[op] > len(code):
                    continue
                if op in OPS3 and (code[pc + 1] > MAXOP or code[pc + 2] > MAXOP):
                    continue
                if op in OPS6 and code[pc + 1] > MAXOP:
                    continue
                m[c] = op
                used.add(op)
                seq.append((pc, op))
                if go(pc + W[op], seq):
                    seq.pop(); used.discard(op); del m[c]
                    return True
                seq.pop()
                used.discard(op)
                del m[c]
            return len(sols) >= cap
    go(0, [])
    return sols


def score(code, mapping):
    """prefer: 8 CMP with byte immediates, and full coverage of the program"""
    seq = [(p, o) for p in range(0, len(code)) for c, o in mapping.items() if c == code[p]]
    return 0


if __name__ == '__main__':
    targets = sys.argv[1:] or ['080ec62d7daef51f2e635d17f9b8e075',
                               '3e3a0fc9a5c28e964f9ba37bb499e742',
                               'cfa1fa34718c426f23e2318dfe8b330d']
    for t in targets:
        sh = vm.load(t)
        sols = recover(sh['code'])
        print('#### %s  solutions=%d' % (t[:12], len(sols)))
        # group by the (pc,op) sequence shape
        seen = {}
        for m, seq, stop in sols:
            k = tuple(o for _, o in seq)
            seen.setdefault(k, []).append((m, seq, stop))
        print('     distinct op-sequences: %d' % len(seen))
        best = sorted(seen.items(), key=lambda kv: -len(kv[1]))[:4]
        for k, group in best:
            m, seq, stop = group[0]
            cmps = [struct.unpack_from('<I', sh['code'], p + 2)[0] for p, o in seq if o == 11]
            import collections
            cnt = collections.Counter(vm.NM[o] for o in k)
            print('   seq n=%d stop=%s cmps=%d lowbytes=%s' % (
                len(k), stop[0], len(cmps), ''.join('%02x' % (c & 0xff) for c in cmps)))
            print('     ops: %s' % ' '.join('%s:%d' % x for x in sorted(cnt.items())))
            print('     map: %s' % ' '.join('%02x->%s' % (c, vm.NM[o]) for c, o in sorted(m.items())))
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   'agent_table_recovered_%s.json' % t[:8]), 'w') as f:
                json.dump({'shard': t, 'map': {str(k): v for k, v in m.items()},
                           'stop': list(stop), 'cmp': ['%08x' % c for c in cmps]}, f, indent=1)
