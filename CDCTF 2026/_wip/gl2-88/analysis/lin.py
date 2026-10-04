import numpy as np
from ks import keystream_indices

P = 67
CT = "XwFAN`aXUspHB~]bhjV>_Fmk}VJ~tx=BwsvP<hK[XOo`"
N = len(CT)
assert len(CT) == N

kv0 = [0] * 11
base = keystream_indices(kv0, N)
kvec = np.array([m[0][0] for m in base])          # key-independent multiplier
avec = np.array([m[0][1] for m in base])          # a_i at zero key
Bcol = []
for t in range(11):
    e = [0] * 11
    e[t] = 1
    m = keystream_indices(e, N)
    Bcol.append([(m[i][0][1] - avec[i]) % P for i in range(N)])
BET = np.array(Bcol).T          # (N,11): a_i = avec_i + BET_i . c


def inv(x):
    return pow(x, P - 2, P)


# ---- known plaintext: flag format ----
known = {}
for i, ch in enumerate('cdctf{'):
    known[i] = ch
known[N - 1] = '}'

rows, rhs = [], []
for i in sorted(known):
    x = ord(known[i]) - 60
    y = ord(CT[i]) - 60
    target = (int(kvec[i]) * x - y - int(avec[i])) % P     # BET_i . c == target
    rows.append(BET[i].tolist())
    rhs.append(target)
Mk = np.array(rows)
bv = np.array(rhs)

# ---- GF(67) solve: particular + nullspace ----
n = 11
A = np.concatenate([Mk, bv.reshape(-1, 1)], axis=1).astype(object)
pivots = []
r = 0
for c in range(n):
    pr = next((i for i in range(r, A.shape[0]) if A[i, c] % P), None)
    if pr is None:
        continue
    A[[r, pr]] = A[[pr, r]]
    f = inv(int(A[r, c]) % P)
    A[r] = (A[r] * f) % P
    for i in range(A.shape[0]):
        if i != r and A[i, c] % P:
            A[i] = (A[i] - A[i, c] * A[r]) % P
    pivots.append(c)
    r += 1
rank = len(pivots)
consistent = all(int(A[i, n]) % P == 0 for i in range(r, A.shape[0]))
part = np.zeros(n, dtype=int)
for i, c in enumerate(pivots):
    part[c] = int(A[i, n]) % P
free = [c for c in range(n) if c not in pivots]
basis = []
for f in free:
    v = np.zeros(n, dtype=int)
    v[f] = 1
    for i, c in enumerate(pivots):
        v[c] = (-int(A[i, f])) % P
    basis.append(v)

print('rank', rank, 'consistent', consistent, 'free dims', len(free))
print('part', part.tolist())
print('basis', [b.tolist() for b in basis])
np.save('kvec.npy', kvec); np.save('avec.npy', avec); np.save('bet.npy', BET)
np.save('part.npy', part); np.save('basis.npy', np.array(basis))
