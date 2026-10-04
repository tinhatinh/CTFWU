import numpy as np, re, math, sys
from solve import build, P, inv

CT = "XwFAN`aXUspHB~]bhjV>_Fmk}VJ~tx=BwsvP<hK[XOo`"
WORDS = set(w.strip().lower() for w in open('words_alpha.txt') if 3 <= len(w.strip()))
BIG = __import__('collections').Counter(); UNI = __import__('collections').Counter()


def load_model():
    if BIG:
        return
    for w in WORDS:
        if len(w) > 12:
            continue
        for a, b in zip(w, w[1:]):
            BIG[(a, b)] += 1; UNI[a] += 1
        UNI[w[-1]] += 1


L = {}


def scan(CT, known, allow, mode='fwd', min_frac=1.0, chunk=250_000, label=''):
    load_model()
    global L
    if not L:
        TOT = sum(BIG.values())
        L = {(a, b): math.log10((c + .4) / (UNI[a] + .4 * 27)) for (a, b), c in BIG.items()}
    N = len(CT)
    kvec, avec, BET = build(N)
    Y = [ord(c) - 60 for c in CT]
    eqs = {}
    for i, ch in known.items():
        x = ord(ch) - 60
        # a_i = avec_i + BET_i . c
        rhs = (int(kvec[i]) * x - Y[i] - int(avec[i])) % P if mode == 'fwd' \
              else (int(kvec[i]) * Y[i] - x - int(avec[i])) % P
        eqs[i] = rhs
    from solve import affine_space
    rows = [[int(v) % P for v in BET[i]] for i in sorted(eqs)]
    rhs = [eqs[i] for i in sorted(eqs)]
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
        piv.append(c); r += 1
    part = np.zeros(11, dtype=object)
    for i, c in enumerate(piv):
        part[c] = int(A[i, 11]) % P
    basis = []
    for f in [c for c in range(11) if c not in piv]:
        v = np.zeros(11, dtype=object); v[f] = 1
        for i, c in enumerate(piv):
            v[c] = (-int(A[i, f])) % P
        basis.append(v)
    d4 = len(basis)
    unk = [i for i in range(N) if i not in known]
    G = np.array([[int(BET[i] @ basis[j]) % P for j in range(d4)] for i in unk], dtype=np.int64)
    if mode == 'fwd':
        q = np.array([(inv(int(kvec[i])) * (Y[i] + int(avec[i]) + int(BET[i] @ part))) % P for i in unk], dtype=np.int64)
        p = np.array([inv(int(kvec[i])) % P for i in unk], dtype=np.int64)
        # x = p*(T + (Y+avec+BETpart)/p...)  -> recompute properly below
        base = np.array([(Y[i] + int(avec[i]) + int(BET[i] @ part)) % P for i in unk], dtype=np.int64)
        pk = np.array([inv(int(kvec[i])) % P for i in unk], dtype=np.int64)
    else:
        base = np.array([(int(kvec[i]) * Y[i] - int(avec[i]) - int(BET[i] @ part)) % P for i in unk], dtype=np.int64)
        pk = np.ones(len(unk), dtype=np.int64)
    # x_i = (pk_i * (T_i + b_i)) for fwd  [pk = 1/k];  x_i = (b_i - T_i) for inv
    sgn = np.ones(len(unk), dtype=np.int64) if mode == 'fwd' else np.full(len(unk), P - 1, dtype=np.int64)
    tab = np.zeros((len(unk), P), dtype=np.int16)
    for a in range(len(unk)):
        b = int(base[a])
        if mode == 'fwd':
            pp = int(pk[a])
            for t in range(P):
                tab[a, t] = 1 if (pp * ((t + b) % P)) % P in allow else 0
        else:
            for t in range(P):
                tab[a, t] = 1 if ((b - t) % P) in allow else 0
    TOT = P ** d4
    nreq = int(math.ceil(min_frac * len(unk)))
    hits = []
    for lo in range(0, TOT, chunk):
        idx = np.arange(lo, min(lo + chunk, TOT), dtype=np.int64)
        Lam = np.stack([(idx // (P ** (d4 - 1 - j))) % P for j in range(d4)], axis=1)
        T = (Lam @ G.T) % P
        good = tab[np.arange(len(unk))[None, :], T].sum(axis=1)
        sel = good >= nreq
        if sel.any():
            tt = T[sel]
            for k, ii in enumerate(idx[sel]):
                s = ['?'] * N
                for i, ch in known.items():
                    s[i] = ch
                for a, i in enumerate(unk):
                    t = int(tt[k, a])
                    v = (int(pk[a]) * ((t + int(base[a])) % P)) % P if mode == 'fwd' else (int(base[a]) - t) % P
                    s[i] = chr(v + 60)
                hits.append(''.join(s))
        if len(hits) > 4_000_000:
            print(label, 'overflow', len(hits)); break
    return hits, d4


def wscore(s):
    load_model()
    t = re.split(r'(?<=[a-z])(?=[A-Z])', re.sub(r'[^A-Za-z]', ' ', s))
    return sum(len(x) for x in [w.lower() for w in t] if x in WORDS)


def bscore(s):
    load_model()
    if not L:
        TOT = sum(BIG.values())
        L.update({(a, b): math.log10((c + .4) / (UNI[a] + .4 * 27)) for (a, b), c in BIG.items()})
    x = re.sub(r'[^a-z]', '', s.lower())
    return sum(L.get((a, b), -2.5) for a, b in zip(x, x[1:])) / max(1, len(x) - 1)


LETTERS = set(ord(c) - 60 for c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_')

if __name__ == '__main__':
    N = len(CT)
    hyps = {
        'A brace@43': ({i: c for i, c in enumerate('cdctf{')} | {N - 1: '}'}, LETTERS, 'fwd', 1.0),
        'B nl@43 brace@42': ({i: c for i, c in enumerate('cdctf{')} | {N - 2: '}'}, LETTERS, 'fwd', 1.0),
        'C CDCTF upper': ({i: c for i, c in enumerate('CDCTF{')} | {N - 1: '}'}, LETTERS, 'fwd', 1.0),
        'D inv mode': ({i: c for i, c in enumerate('cdctf{')} | {N - 1: '}'}, LETTERS, 'inv', 1.0),
        'E brace@43 soft35': ({i: c for i, c in enumerate('cdctf{')} | {N - 1: '}'}, LETTERS, 'fwd', 35.0 / 37),
    }
    for name, (known, allow, mode, mf) in hyps.items():
        hits, d4 = scan(CT, known, allow, mode, mf, label=name)
        if hits is None:
            continue
        sc = sorted(((wscore(h), bscore(h), h) for h in hits), reverse=True)
        print('%-22s dim=%d n=%d' % (name, d4, len(hits)), flush=True)
        for a, b, h in sc[:6]:
            print('     %3d %6.3f  %s' % (a, b, h), flush=True)
