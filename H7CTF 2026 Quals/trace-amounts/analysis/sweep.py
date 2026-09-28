"""Model sweep per 40-sample slot: which byte-operation leaks, and under which model?

The capture shows 16 evenly spaced activity peaks (sample 30 + 40*i), i.e. one slot per
AES state byte. For each slot we test several leakage models against every key guess.
"""

import numpy as np

T = np.load("traces.npy").astype(np.float64)
P = np.load("plaintexts.npy").astype(np.uint8)
n, m = T.shape
Tv = T - T.mean(0)
Tsd = Tv.std(0) + 1e-12


def sbox_table():
    def gmul(a, b):
        r = 0
        for _ in range(8):
            if b & 1:
                r ^= a
            hi = a & 0x80
            a = (a << 1) & 0xFF
            if hi:
                a ^= 0x1B
            b >>= 1
        return r
    inv = [0] * 256
    for i in range(1, 256):
        for j in range(1, 256):
            if gmul(i, j) == 1:
                inv[i] = j
                break
    out = []
    for i in range(256):
        x = inv[i] if i else 0x63
        s = t = x
        for _ in range(4):
            t = ((t << 1) | (t >> 7)) & 0xFF
            s ^= t
        out.append(s ^ 0x63)
    return np.array(out, dtype=np.uint8)


SB = sbox_table()
HW = np.unpackbits(np.arange(256, dtype=np.uint8)[:, None], axis=1).sum(1).astype(float)

models = {
    "HW(xor)": lambda pt, k: HW[pt ^ k],
    "HW(S[xor])": lambda pt, k: HW[SB[pt ^ k]],
    "S[xor]": lambda pt, k: SB[pt ^ k].astype(float),
    "xor": lambda pt, k: (pt ^ k).astype(float),
    "LSB(xor)": lambda pt, k: (pt ^ k) & 1,
    "HW(S[xor]^pt)": lambda pt, k: HW[SB[pt ^ k] ^ pt],
}

print(f"[*] {n} traces, {m} samples; slot width 40, peaks at 30+40*i")
results = []
for i in range(16):
    pt = P[:, i].astype(np.uint8)
    lo, hi = max(0, i * 40 - 8), min(m, i * 40 + 48)
    for mname, fn in models.items():
        V = np.stack([fn(pt, k) for k in range(256)])            # (256, n)
        Vc = V - V.mean(1, keepdims=True)
        num = Vc @ Tv[:, lo:hi]
        den = np.sqrt((Vc ** 2).sum(1)[:, None] * (Tv[:, lo:hi] ** 2).sum(0)[None, :]) + 1e-9
        c = np.abs(num / den)
        k = int(np.argmax(c.max(1)))
        results.append((float(c[k].max()), i, mname, k, lo + int(np.argmax(c[k]))))

results.sort(reverse=True)
print("\ntop 20 (slot model, best key guess, best sample):")
for s, i, mname, k, samp in results[:20]:
    print(f"  byte {i:2d}  {mname:14s} k=0x{k:02x}  sample {samp:3d}  |r|={s:.3f}")
print(f"\nnoise floor ~0.21 after multiplicity; anything clearly above that is real.")

# also: full-width sweep for the two most likely models (in case slots are shifted)
print("\nfull-trace sweep, HW(xor) and HW(S[xor]):")
for mname in ("HW(xor)", "HW(S[xor])"):
    fn = models[mname]
    for i in range(16):
        pt = P[:, i].astype(np.uint8)
        V = np.stack([fn(pt, k) for k in range(256)])
        Vc = V - V.mean(1, keepdims=True)
        num = Vc @ Tv
        den = np.sqrt((Vc ** 2).sum(1)[:, None] * (Tv ** 2).sum(0)[None, :]) + 1e-9
        c = np.abs(num / den)
        k = int(np.argmax(c.max(1)))
        print(f"  byte {i:2d} {mname:12s} k=0x{k:02x} max|r|={c[k].max():.3f} @sample {int(np.argmax(c[k]))}")
