import numpy as np
from ks import keystream_indices

P = 67
inv = lambda x: pow(x, P - 2, P)
UNKlo = 6


def build(N):
    b = keystream_indices([0] * 11, N)
    kvec = np.array([m[0][0] for m in b])
    avec = np.array([m[0][1] for m in b])
    BET = np.zeros((N, 11), dtype=object)
    for t in range(11):
        e = [0] * 11
        e[t] = 1
        m = keystream_indices(e, N)
        BET[:, t] = [(m[i][0][1] - avec[i]) % P for i in range(N)]
    return kvec, avec, BET


def affine_space(kvec, avec, BET, CT, known):
    N = len(CT)
    rows, rhs = [], []
    for i, ch in known.items():
        x, y = ord(ch) - 60, ord(CT[i]) - 60
        rows.append([int(v) for v in BET[i]])
        rhs.append((int(kvec[i]) * x - y - int(avec[i])) % P)
    A = np.array(rows + [[0] * 11], dtype=object)
    A = np.concatenate([A, np.array(rhs + [0], dtype=object).reshape(-1, 1)], axis=1)
    piv, r = [], 0
    for c in range(11):
        pr = next((i for i in range(r, A.shape[0]) if int(A[i, c]) % P), None)
        if pr is None:
            continue
        A[[r, pr]] = A[[pr, r]]
        A[r] = (A[r] * inv(int(A[r, c]) % P)) % P
        for i in range(A.shape[0]):
            if i != r and int(A[i, c]) % P:
                A[i] = (A[i] - A[i, c] * A[r]) % P
        piv.append(c)
        r += 1
    part = np.zeros(11, dtype=object)
    for i, c in enumerate(piv):
        part[c] = int(A[i, 11]) % P
    basis = []
    for f in [c for c in range(11) if c not in piv]:
        v = np.zeros(11, dtype=object)
        v[f] = 1
        for i, c in enumerate(piv):
            v[c] = (-int(A[i, f])) % P
        basis.append(v)
    return part, basis


def candidates(CT, known, part, basis, allow, chunk=400_000, cap=None):
    N = len(CT)
    kvec, avec, BET = build(N)
    unk = [i for i in range(N) if i not in known]
    d = np.array([(ord(CT[i]) - 60 + int(avec[i]) + int(BET[i] @ part)) % P for i in unk])
    G = np.array([[int(BET[i] @ basis[j]) % P for j in range(len(basis))] for i in unk], dtype=object).astype(np.int64)
    u = np.array([inv(int(kvec[i])) for i in unk], dtype=np.int64)
    tab = np.zeros((len(unk), P), dtype=np.uint8)
    for a in range(len(unk)):
        for s in range(P):
            tab[a, s] = 1 if (int(u[a]) * s) % P in allow else 0
    df = np.array(d, dtype=np.int64)
    d4 = len(basis)
    total = P ** d4
    keep = []
    for lo in range(0, total, chunk):
        idx = np.arange(lo, min(lo + chunk, total), dtype=np.int64)
        L = np.stack([(idx // (P ** (d4 - 1 - j))) % P for j in range(d4)], axis=1)
        S = ((L @ G.T) + df) % P
        ok = tab[np.arange(len(unk))[None, :], S].all(axis=1)
        keep.extend(idx[ok].tolist())
        if cap and len(keep) > cap:
            break
    return unk, np.array(keep, dtype=np.int64), G, df, u, d4


def bodies(CT, keep, unk, G, df, u, d4, part, basis, known):
    out = []
    N = len(CT)
    L = np.stack([(keep // (P ** (d4 - 1 - j))) % P for j in range(d4)], axis=1)
    X = (((L @ G.T) + df) % P * u) % P
    for n, row in enumerate(X):
        s = ['?'] * N
        for i, ch in known.items():
            s[i] = ch
        for a, i in enumerate(unk):
            s[i] = chr(int(row[a]) + 60)
        out.append(''.join(s))
    return out


LETTERS = set((ord(c) - 60 for c in
               'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_'))


def decrypt_with(cvals, CT):
    from ks import encrypt
    return encrypt(cvals, CT)


def solve(CT, allow=LETTERS, last_brace=True):
    N = len(CT)
    known = {i: c for i, c in enumerate('cdctf{')}
    if last_brace:
        known[N - 1] = '}'
    kvec, avec, BET = build(N)
    part, basis = affine_space(kvec, avec, BET, CT, known)
    if not basis:
        c = [int(v) for v in part]
        return [(0, decrypt_with(c, CT))], c, 0
    unk, keep, G, df, u, d4 = candidates(CT, known, part, basis, allow)
    txt = bodies(CT, keep, unk, G, df, u, d4, part, basis, known)
    return list(zip(keep.tolist(), txt)), part, len(basis)


if __name__ == '__main__':
    import random
    from ks import encrypt
    random.seed(7)
    key = ''.join(chr(random.randrange(60, 127)) for _ in range(11))
    kv = [ord(c) - 60 for c in key]
    for body in ['FeistelIsRealCryptoAndYouKnowIt', 'PrettyPatternsHideInTheGroupOfMatrices',
                 'SymmetricAndBeautifulLikeAStreamCipher']:
        fake = ('cdctf{' + body)[:43]
        fake = fake + 'x' * (43 - len(fake)) + '}'
        assert len(fake) == 44, len(fake)
        ct = encrypt(kv, fake)
        assert all(60 <= ord(c) <= 126 for c in ct) and len(ct) == 44
        print('KEY', repr(key), '\n  PT', fake, '\n  CT', ct)
        res, part, dim = solve(ct)
        hit = [t for _, t in res if t == fake]
        print('  free dim', dim, 'survivors', len(res), '| recovered:', bool(hit))
        if not hit:
            print('  *** MISSING -> pipeline or charset problem ***')
            for _, t in res[:3]:
                print('   sample', t)

