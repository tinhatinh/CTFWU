CT = "PXYWN{2.612.QNTOXCK6E7DKGMKC.WK4KK6MPPPRJGOFZZI66EISSED}"
POS = [i for i, ch in enumerate(CT) if ch.isalpha()]
C = [ord(CT[i]) - 65 for i in POS]
N = len(C)
KEY = "ELAPSE"
K0 = [ord(c) - 65 for c in KEY]


def show(name, P):
    out = list(CT)
    for j, i in enumerate(POS):
        out[i] = chr(P[j] + 65)
    print(f"{name:26s}: {''.join(out)}")


def bf(c, k):
    return (k - c) % 26


# 1. autokey on plaintext (Beaufort)
P = [0] * N
for i in range(N):
    k = K0[i] if i < len(K0) else P[i - len(K0)]
    P[i] = bf(C[i], k)
show("beaufort autokey-PT", P)

# 2. autokey on ciphertext
P = [bf(C[i], K0[i] if i < len(K0) else C[i - len(K0)]) for i in range(N)]
show("beaufort autokey-CT", P)

# 3. progressive beaufort: key letters increment by 1 each period
P = []
for i in range(N):
    per, off = divmod(i, len(K0))
    P.append(bf(C[i], K0[off] + per))
show("beaufort progressive+1", P)

# 4. running key = starred words spelled out
RUN = "ELDERLILYANCHORPOPPYSWANELDER"
K = [ord(c) - 65 for c in RUN]
P = [bf(C[i], K[i % len(K)]) for i in range(N)]
show("beaufort key=words", P)

# 5. key = ELAPSE repeated, but beaufort over letters+digits (digits mod 10)
ALPH = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
out = []
ki = 0
for ch in CT:
    if ch.isalpha():
        out.append(chr(bf(ord(ch) - 65, K0[ki % 6]) + 65))
        ki += 1
    elif ch.isdigit():
        out.append(str((K0[ki % 6] - int(ch)) % 10))
        ki += 1
    else:
        out.append(ch)
show("letters+digits mod10", [ord(c) - 65 if c.isalpha() else 0 for c in "".join(out)])
print("letters+digits mod10 :", "".join(out))
