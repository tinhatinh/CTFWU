"""One-shot Kintsugi Vault solver.

  python solve.py [dir-with-shards]

Finds the byte-target guardians, rebuilds each one's missing decode table by
enumerating the few remaining raw->op assignments (validated by running the
recovered program), inverts each program to its 8-byte key, then searches piece
orderings until the Ed25519 public key derived from the assembled seed matches
pubkey.bin.  Writes seed.hex next to the shards.
"""
import os, sys, struct, itertools, glob

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vm, invert
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding as E, PublicFormat as P

REST = [3, 4, 10, 12, 13]           # MOV XOR LUT ANDI XORI - the ambiguous family members


def pub(seed):
    try:
        return Ed25519PrivateKey.from_private_bytes(seed).public_key().public_bytes(
            encoding=E.Raw, format=P.Raw)
    except Exception:
        return None


def complete(fwd):
    if len(set(fwd.values())) != len(fwd):
        return None
    out = [None] * 256
    for c, o in fwd.items():
        if not (0 <= c < 256 and 0 <= o < 256):
            return None
        out[c] = o
    holes = sum(1 for x in out if x is None)
    pool = [x for x in range(256) if x not in set(fwd.values())]
    if len(pool) != holes:
        return None
    k = 0
    for c in range(256):
        if out[c] is None:
            out[c] = pool[k]
            k += 1
    return out


def raws_of(sh):
    """pin KEY / CMP / HALT from the program's shape, return (fixed dict, rest raws)"""
    code = sh['code']
    key_raw = code[0]
    assert all(code[3 * i] == key_raw and code[3 * i + 1] == code[3 * i + 2] == i
               for i in range(8)), 'not a byte-target guardian'
    # tail: 8 six-byte CMP on r0..r7 then one byte
    cmp_raw = code[600]
    assert all(code[600 + 6 * i] == cmp_raw and code[601 + 6 * i] == i
               and struct.unpack_from('<I', code, 602 + 6 * i)[0] < 256 for i in range(8)), 'bad tail'
    halt_raw = code[648]
    seen = {code[p] for p in range(0, 648, 1) if True}
    fixed = {key_raw: 1, cmp_raw: 11, halt_raw: 0}
    # opcode slots of the 3-byte ops live at p%3==0; rank bytes by how often they
    # appear there, keeping only plausible op carriers
    from collections import Counter
    cnt = Counter(code[p] for p in range(24, 600) if p % 3 == 0)
    rest = [c for c, n in cnt.most_common() if c not in fixed and n >= 3][:8]
    return fixed, rest, code


def solve_guardian(sh):
    """yield every (table, [accepted keys]) consistent with the guardian shape"""
    fixed, rest, code = raws_of(sh)
    for chosen in itertools.permutations(rest, min(5, len(rest))):
        fwd = dict(fixed)
        fwd.update(dict(zip(chosen, REST)))
        tbl = complete(fwd)
        if tbl is None:
            continue
        trial = dict(sh)
        trial['tbl'] = tbl
        seq, st, ex = vm.dismap(trial)
        if st != 'HALT' or ex != len(sh['code']) - 1:
            continue
        ncmp = sum(1 for _, o in seq if o == 11)
        if ncmp != 8:
            continue
        try:
            know, keyreq, free, pend = invert.backwards(trial, seq)
        except Exception:
            continue
        if pend or len(keyreq) != 8:
            continue
        base = bytes(keyreq.get(i, 0) for i in range(8))
        bits = {}
        for reg, b in free:
            bits.setdefault(reg, set()).add(b)
        spots = sorted(bits)
        sets = [sorted(bits[s]) for s in spots]
        n = sum(len(x) for x in sets)
        keys = set()
        for mask in range(1 << min(n, 12)):
            k = bytearray(base)
            m = mask
            for si, s in enumerate(spots):
                for b in sets[si]:
                    bit = m & 1
                    m >>= 1
                    k[s] = (k[s] & ~(1 << b)) | (bit << b)
            c = bytes(k)
            v = vm.VM(tbl, sh['sbox'], sh['code'], c)
            if v.run()[0] == 'HALT':
                keys.add(c)
        if keys:
            yield tbl, sorted(keys)


def main(d):
    d = os.path.abspath(d)
    vm.BASE = d                       # make vm.load() read this instance's shards
    shards = sorted(glob.glob(os.path.join(d, '*.shard')))
    pub_bin = open(os.path.join(d, 'pubkey.bin'), 'rb').read()
    print('[*] %d shards, pubkey %s' % (len(shards), pub_bin.hex()))
    good = {}
    for f in shards:
        sh = vm.load(os.path.basename(f)[:-6])
        try:
            sol = list(solve_guardian(sh))
        except AssertionError as e:
            print('    %-14s skip (%s)' % (sh['tid'].hex()[:12], e))
            continue
        if not sol:
            print('    %-14s not a byte-target guardian' % sh['tid'].hex()[:12])
            continue
        seen = []
        for tbl, keys in sol:
            seen += keys
        good[sh['tid'].hex()] = sorted(set(seen))
        print('    %-34s %d candidate keys, e.g. %s' % (sh['tid'].hex(), len(seen), seen[0].hex()))
    names = list(good)
    if len(names) != 4:
        print('[!] expected 4 guardians, got %d - stop' % len(names))
        return None
    ncombo = 1
    for n in names:
        ncombo *= len(good[n])
    print('[*] assembling: %d orders x %d variants' % (
        len(names) * (len(names) - 1) * (len(names) - 2), ncombo))
    for perm in itertools.permutations(names):
        for combo in itertools.product(*[good[n] for n in perm]):
            s = b''.join(combo)
            if pub(s) == pub_bin:
                print('[+] SEED', s.hex())
                print('    order', [p[:12] for p in perm])
                open(os.path.join(d, 'seed.hex'), 'w').write(s.hex() + '\n')
                return s
    print('[-] no assembly matched the pubkey')
    return None


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'files'))
