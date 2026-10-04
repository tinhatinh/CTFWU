import numpy as np
from solve import build, affine_space, P, inv, LETTERS

CT = "XwFAN`aXUspHB~]bhjV>_Fmk}VJ~tx=BwsvP<hK[XOo`"
N = len(CT)
known = {i: c for i, c in enumerate('cdctf{')}
known[N - 1] = '}'
unk = [i for i in range(N) if i not in known]
kvec, avec, BET = build(N)
part, basis = affine_space(kvec, avec, BET, CT, known)
d4 = len(basis)
print('free dim', d4, 'unknown positions', len(unk))

d = np.array([(ord(CT[i]) - 60 + int(avec[i]) + int(BET[i] @ part)) % P for i in unk], dtype=np.int64)
G = np.array([[int(BET[i] @ basis[j]) % P for j in range(d4)] for i in unk], dtype=np.int64)
u = np.array([inv(int(kvec[i])) % P for i in unk], dtype=np.int64)
lt = np.zeros((len(unk), P), dtype=np.int16)
for a in range(len(unk)):
    for s in range(P):
        lt[a, s] = 1 if (int(u[a]) * s) % P in LETTERS else 0

TOT = P ** d4
CH = 200_000
lam_keep, row_keep, cnt_keep = [], [], []
for lo in range(0, TOT, CH):
    idx = np.arange(lo, min(lo + CH, TOT), dtype=np.int64)
    L = np.stack([(idx // (P ** (d4 - 1 - j))) % P for j in range(d4)], axis=1)
    S = (L @ G.T + d) % P
    X = (S * u) % P
    cnt = lt[np.arange(len(unk))[None, :], X].sum(axis=1)
    sel = cnt >= 35
    if sel.any():
        lam_keep.append(idx[sel])
        row_keep.append(X[sel].astype(np.uint8))
        cnt_keep.append(cnt[sel])
    if lo % (CH * 20) == 0:
        print(lo, 'kept so far', sum(len(a) for a in lam_keep), flush=True)
lam = np.concatenate(lam_keep)
rows = np.concatenate(row_keep)
cnts = np.concatenate(cnt_keep)
order = np.argsort(-cnts)
np.save('soft_lam.npy', lam[order])
np.save('soft_rows.npy', rows[order])
np.save('soft_cnt.npy', cnts[order])
print('total survivors (>=35 letters):', len(lam), 'max letters:', cnts.max())
