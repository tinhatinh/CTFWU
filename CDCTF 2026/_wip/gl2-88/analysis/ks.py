import itertools

P = 67
Q = 11
NB = 12  # number of symbolic coefficients: constant + 11 key chars


def mod(v):
    return v % P


# ---- exact port of the Haskell 2x2 representation: Matrix = (row1, row2) ----
def mmul(m1, m2):
    (r1, r2) = m1
    (c1, c2) = ((m2[0][0], m2[1][0]), (m2[0][1], m2[1][1]))  # transpose m2 -> columns
    return (((r1[0] * c1[0] + r1[1] * c1[1]) % P, (r1[0] * c2[0] + r1[1] * c2[1]) % P),
            ((r2[0] * c1[0] + r2[1] * c1[1]) % P, (r2[0] * c2[0] + r2[1] * c2[1]) % P))


def mpow(m, n):
    acc = ((1, 0), (0, 1))
    for _ in range(n):
        acc = mmul(m, acc)
    return acc


A = ((1, 1), (0, 1))
B = ((9, 0), (0, 1))
grp = [mmul(mpow(A, a), mpow(B, b)) for a in range(P) for b in range(Q)]
assert len(grp) == P * Q


def keymats(keyvals):
    return [((1, v % P), (0, 1)) for v in keyvals]


def keystream_indices(keyvals, need):
    """Concrete keystream matrices, only the first `need` of round^12(l)."""
    m0 = keymats(keyvals)
    # go md = concat (tail (transpose (grp // md))) ; take only what we need
    def go(md):
        out = []
        rows = []
        # transpose of [coset_j]_j : row r = [coset_j[r] for j]
        nrows = max(1, (need + len(md) + 1) // len(md) + 2)
        for r in range(1, min(len(grp), nrows + 1)):
            rows.append([mmul(grp[r], m) for m in md])
        for row in rows:
            out.extend(row)
        return out

    l = m0 + go(m0)
    assert len(l) >= need + 12
    tl = l
    for _ in range(Q + 1):  # foldr over [0.._Q] == 12 rounds
        tl = [mmul(tl[i], tl[i + 1]) for i in range(len(tl) - 1)]
    return tl[:need]


def encrypt(keyvals, text):
    ks = keystream_indices(keyvals, len(text))
    out = []
    for m, ch in zip(ks, text):
        x = ord(ch) - 60
        y = (m[0][0] * x + m[0][1] * (-1)) % P
        out.append(chr(y + 60))
    return ''.join(out)


if __name__ == '__main__':
    kv = [ord(c) - 60 for c in 'ABCDEFGHIJK']
    ks = keystream_indices(kv, 3)
    for m in ks:
        print(m)
    print(encrypt(kv, 'cdctf{TEST}'))
    # self-check: every keystream matrix must stay in the affine subgroup {(k,a),(0,1)}
    for m in keystream_indices(kv, 45):
        assert m[1] == (0, 1), m
