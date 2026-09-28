"""Live instance solve: 4 byte-target guardians -> 32-byte seed -> verify vs pubkey.bin."""
import os, sys, struct, itertools, glob

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vm, invert, solve

D = os.path.abspath(sys.argv[1])
vm.BASE = D
PUB = open(os.path.join(D, 'pubkey.bin'), 'rb').read()


def keys_from(sh, tbl):
    trial = dict(sh)
    trial['tbl'] = list(tbl)
    seq, st, ex = vm.dismap(trial)
    if st != 'HALT' and st != 'END':
        return None, 'walk=%s' % st
    if ex != len(sh['code']) - 1:
        return None, 'stop=%s' % ex
    ncmp = sum(1 for _, o in seq if o == 11)
    if ncmp != 8:
        return None, 'ncmp=%d' % ncmp
    try:
        know, keyreq, free, pend = invert.backwards(trial, seq)
    except Exception as e:
        return None, 'inv=%s' % e
    if pend or len(keyreq) != 8:
        return None, 'pend=%d keyreq=%d' % (len(pend), len(keyreq))
    base = bytes(keyreq.get(i, 0) for i in range(8))
    bits = {}
    for reg, b in free:
        bits.setdefault(reg, set()).add(b)
    spots = sorted(bits)
    sets = [sorted(bits[s]) for s in spots]
    n = sum(len(x) for x in sets)
    out = set()
    for mask in range(1 << min(n, 8)):
        k = bytearray(base)
        m = mask
        for si, s in enumerate(spots):
            for b in sets[si]:
                bit = m & 1
                m >>= 1
                k[s] = (k[s] & ~(1 << b)) | (bit << b)
        c = bytes(k)
        v = vm.VM(list(tbl), sh['sbox'], sh['code'], c)
        if v.run()[0] == 'HALT':
            out.add(c)
    return sorted(out), 'free=%d' % n


def template_table(sh, ref_seq, ref_code):
    """map ref's (pc,op) onto sh's bytes; returns table or None"""
    fwd, rev = {}, {}
    for pc, op in ref_seq:
        if op == 0:
            c = sh['code'][pc] if pc < len(sh['code']) else None
            fwd.setdefault(c, 0)
            continue
        c = sh['code'][pc]
        if c in fwd and fwd[c] != op:
            return None
        if op in rev and rev[op] != c:
            return None
        fwd[c] = op
        rev[op] = c
    if len(set(fwd.values())) != len(fwd):
        return None
    return solve.complete(fwd)


def main():
    good = {}
    refs = []
    for f in sorted(glob.glob(os.path.join(D, '*.shard'))):
        name = os.path.basename(f)[:-6]
        sh = vm.load(name)
        seq_own, st_own, ex_own = vm.dismap(sh)
        cands = []
        # 1) its own table (chain start keeps it in the clear)
        if st_own == 'HALT':
            ks, note = keys_from(sh, sh['tbl'])
            if ks:
                cands.append(('own', sh['tbl'], ks))
            else:
                refs.append((name, sh, seq_own))
        # 2) search over raw->op assignments
        if not cands:
            try:
                for tbl, keys in solve.solve_guardian(sh):
                    cands.append(('search', tbl, keys))
            except AssertionError:
                pass
        # 3) template transfer from an already-solved shard
        if not cands:
            for rn, rsh, rseq in refs:
                t = template_table(sh, rseq, rsh['code'])
                if t:
                    ks, note = keys_from(sh, t)
                    if ks:
                        cands.append(('tmpl:' + rn[:8], t, ks))
                        break
        if not cands:
            print('  %-34s SKIP (selfwalk %s@%s)' % (name, st_own, ex_own))
            continue
        allk = sorted({k for _, _, ks in cands for k in ks})
        print('  %-34s %-14s keys=%d  e.g. %s' % (name, cands[0][0], len(allk), allk[0].hex()))
        good[name] = allk
        refs.append((name, sh, vm.dismap(dict(sh, tbl=list(cands[0][1])))[0]))
    names = list(good)
    print('[*] guardians with byte targets: %d' % len(names))
    if len(names) != 4:
        print('[!] need 4 pieces'); return
    tried = 0
    for perm in itertools.permutations(names):
        for combo in itertools.product(*[good[n] for n in perm]):
            s = b''.join(combo)
            tried += 1
            if solve.pub(s) == PUB:
                print('[+] SEED', s.hex())
                print('    order', [p[:12] for p in perm])
                open(os.path.join(D, 'seed.hex'), 'w').write(s.hex() + '\n')
                return s
    print('[-] no match, tried', tried)


main()
