"""Lay khong gian linear form 'vinegar' V = span(z_17..z_32) tu W, va doi chieu
voi A2 that cua mot khoa tu sinh de biet tan cong chay den dau.

W = kernel cua anh xa phan bac 4 = span{w_1..w_16}.  Dao ham bac nhat cua cac
thanh phan bac 2 cua W sinh dung ra V (vi bac 2 cua w_i la -q_i chi chua 16 bien
z_17..z_32, va q_i khong the thoat khoi 16 bien ay).
"""

import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "files"))
from source import keygen, unpack  # noqa: E402

P, N = 17, 32


def rref(rows, ncols):
    m = [r[:] for r in rows]
    piv = []
    for col in range(ncols):
        r = next((i for i in range(len(piv), len(m)) if m[i][col]), None)
        if r is None:
            continue
        k = len(piv)
        m[k], m[r] = m[r], m[k]
        inv = pow(m[k][col], -1, P)
        m[k] = [v * inv % P for v in m[k]]
        for i in range(len(m)):
            if i != k and m[i][col]:
                f = m[i][col]
                m[i] = [(a - f * b) % P for a, b in zip(m[i], m[k])]
        piv.append(col)
    return piv


def quartic_kernel(polys):
    mons4 = sorted({mon for poly in polys for mon in poly if len(mon) == 4})
    rows = [[poly.get(mon, 0) for mon in mons4] for poly in polys]
    piv = rref(rows, len(rows[0]))
    free = [c for c in range(len(rows[0])) if c not in piv]
    basis = []
    for f in free:
        v = [0] * len(rows[0])
        v[f] = 1
        for i, pc in enumerate(piv):
            v[pc] = (-rows[i][f]) % P
        basis.append(v)
    return basis


def homogeneous(polys, lam, deg):
    out = []
    for lam_row in lam:
        d = {}
        for poly, k in zip(polys, lam_row):
            if not k:
                continue
            for mon, c in poly.items():
                if len(mon) == deg:
                    d[mon] = (d.get(mon, 0) + k * c) % P
        out.append({m: c for m, c in d.items() if c})
    return out


def derivatives(quadrics):
    """Moi dao ham rieng phan cua mot bac 2 la mot linear form theo cac bien."""
    forms = []
    for q in quadrics:
        for mon, c in q.items():
            i, j = mon
            if i == j:
                f = [0] * N
                f[i] = (2 * c) % P
                forms.append(f)
            else:
                for a, b in ((i, j), (j, i)):
                    f = [0] * N
                    f[b] = c
                    forms.append(f)
    return [f for f in forms if any(f)]


def main():
    rng = random.Random(20260930)
    public, private = keygen(p=P, n=N, m=34, t=16, s=4, rng=rng)
    polys = unpack(public["polynomials"])

    K = quartic_kernel(polys)
    print("kernel bac 4: %d vector (ky vong 16)" % len(K))
    W2 = homogeneous(polys, K, 2)
    print("bac 2 cua chung: %d da thuc, so mon: %s" % (len(W2), [len(q) for q in W2[:5]]))

    V = derivatives(W2)
    piv = rref(V[:], N)
    print("hang cua khong gian sinh boi dao ham = %d (ky vong 16)" % len(piv))

    A2 = private["A2"]
    truth = [list(row) for row in A2[16:]]
    tpiv = rref(truth, N)
    print("hang cua span(z_17..z_32) that = %d" % len(tpiv))
    same = rref([v[:] for v in V], N) == rref([t[:] for t in truth], N)
    print("V == span(z_17..z_32) that khong:", same)

    # bac 1 cua cung nhung to hop do: cho span(z_1..z_16) mod V
    W1 = homogeneous(polys, K, 1)
    L = [w for w in W1 if any(w)]
    print("hang cua cac linear form cua W (mod V) = %d" % len(rref(L, N)))


if __name__ == "__main__":
    main()
