"""Backward preimage search -> a key the shard must accept, then forward
verification with the ground-truth VM model (analysis/vm.py).

The template lives in the byte domain and is almost invertible: XORI / XOR / LUT are
bijections on bytes, MOV padding is the identity, ANDI only clears a few bits (few
preimages), KEY defines key[i] = the value its lane must carry.  So the set of keys
reaching the 8 CMP targets is small and enumerable.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from produce import classify, canon_table, hard_check, load
from final_lib import tilings, HALT_PC
from solve2 import W, NM, REGPAIR
from vm import VM

M = 0xFF


def backward(code, path, sbox, targets):
    inv = [0] * 256
    for i, v in enumerate(sbox):
        inv[v] = i
    # state = 8 lane values; keyreq = dict key-index -> required byte value
    states = [tuple(targets)]
    reqs = [{} for _ in states]
    for pc, u in reversed(path):
        if u == 0:
            continue
        a = code[pc + 1]
        new, nreq = [], []
        if u == 11:                       # CMP: the requirement is already applied
            continue
        if u == 13:
            k = code[pc + 2]
            for s, rq in zip(states, reqs):
                t = list(s)
                t[a] ^= k
                new.append(tuple(t))
                nreq.append(rq)
        elif u == 12:
            k = code[pc + 2]
            free = [b for b in range(8) if not (k >> b) & 1]
            for s, rq in zip(states, reqs):
                if s[a] & ~k:
                    continue
                for m in range(1 << len(free)):
                    t = list(s)
                    v = s[a]
                    for j, bit in enumerate(free):
                        if (m >> j) & 1:
                            v |= 1 << bit
                    t[a] = v
                    new.append(tuple(t))
                    nreq.append(rq)
        elif u == 4:
            b = code[pc + 2]
            for s, rq in zip(states, reqs):
                t = list(s)
                t[a] = (s[a] ^ s[b]) & M
                new.append(tuple(t))
                nreq.append(rq)
        elif u == 10:
            b = code[pc + 2]
            if a != b:
                return None, None, 'LUT r%d,r%d not self' % (a, b)
            for s, rq in zip(states, reqs):
                t = list(s)
                t[a] = inv[s[a]]
                new.append(tuple(t))
                nreq.append(rq)
        elif u == 3:
            b = code[pc + 2]
            for s, rq in zip(states, reqs):
                t = list(s)
                t[a] = s[b]
                new.append(tuple(t))
                nreq.append(rq)
        elif u == 1:
            b = code[pc + 2]
            if b > 7:
                return None, None, 'KEY index %d' % b
            for s, rq in zip(states, reqs):
                r2 = dict(rq)
                if r2.get(b, s[a]) != s[a]:
                    return None, None, 'KEY lane %d conflict' % b
                r2[b] = s[a]
                new.append(s)
                nreq.append(r2)
        else:
            return None, None, 'op %s not invertible' % NM[u]
        dedup, seen = [], set()
        for s, rq in zip(new, nreq):
            k = (s, tuple(sorted(rq.items())))
            if k in seen:
                continue
            seen.add(k)
            dedup.append((s, rq))
        states = [s for s, _ in dedup]
        reqs = [rq for _, rq in dedup]
        if len(states) > 20000:
            return None, None, 'blow-up'
    return states, reqs, 'ok'


if __name__ == '__main__':
    names = sys.argv[1:] or ['f6f11ad133cab21c96e0185e3411ddc4',
                             '080ec62d7daef51f2e635d17f9b8e075',
                             '3e3a0fc9a5c28e964f9ba37bb499e742',
                             'cfa1fa34718c426f23e2318dfe8b330d']
    for name in names:
        sh = load(name)
        code, sbox, tbl_in = sh['code'], sh['sbox'], sh['tbl']
        tl, _ = tilings(code, lane_max=7, imm1=True)
        tiles = list(tl.values())[0]
        mop, why = classify(tiles, code)
        path, probs = hard_check(mop, tiles, code)
        tab = canon_table(mop)
        cmp_pcs = [pc for pc, u in path if u == 11]
        targets = [code[pc + 2] for pc in cmp_pcs]
        states, reqs, err = backward(code, path, sbox, targets)
        print('=' * 84)
        print('%s target=%s classify=%s probs=%s backward=%s(%s)' % (
            name[:12], ''.join('%02x' % t for t in targets), why, probs or 'none', err,
            len(states) if states else 0))
        if not states:
            continue
        found = None
        for s, rq in zip(states, reqs):
            if len(rq) != 8 or any(v is None or v > 255 for v in rq.values()):
                continue
            key = bytes(rq[i] for i in range(8))
            vm = VM(tab, bytes(sbox), code, key)
            st, pc = vm.run()
            if st == 'HALT':
                found = (key, st, pc)
                break
        if found:
            key, st, pc = found
            print('   VERIFIED KEY %s -> VM %s at pc=%d (all 8 CMPs pass)' % (key.hex(), st, pc))
            open(os.path.join(os.path.dirname(os.path.abspath(__file__)), name + '.verified_key'), 'w').write(key.hex() + '\n')
            if name.startswith('f6f1'):
                print('   self-test: real in-file table gives the same result:',
                      VM(tbl_in, bytes(sbox), code, key).run()[0] == 'HALT')
        else:
            print('   no satisfying key found in %d preimage states' % len(states))
