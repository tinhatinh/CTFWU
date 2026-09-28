"""Diagnostics for the Trace Amounts capture: is there signal, and where?"""

import numpy as np

T = np.load("traces.npy").astype(np.float64)
P = np.load("plaintexts.npy").astype(np.uint8)
n, m = T.shape
print(f"traces {T.shape}, plaintexts {P.shape}")

Tc = T - T.mean(0)

# 1. alignment: cross-correlate each trace with the mean trace
mean = T.mean(0)
shifts = []
for i in range(n):
    cc = np.correlate(T[i] - T[i].mean(), mean - mean.mean(), "full")
    shifts.append(int(np.argmax(cc) - (m - 1)))
sh = np.array(shifts)
print(f"[1] best-shift vs mean trace: min={sh.min()} max={sh.max()} "
      f"median={int(np.median(sh))} std={sh.std():.1f}  unique={len(set(sh.tolist()))}")

# 2. per-sample SNR of the aligned mean
print(f"[2] trace std across set: mean={T.std(0).mean():.3f}; "
      f"mean-trace peak-to-peak={(mean.max()-mean.min()):.3f}")
top = np.argsort(np.abs(mean - mean.mean()))[::-1][:10]
print("    largest |mean| samples at:", sorted(top.tolist()), np.round(mean[top[:6]], 2))

# 3. does the trace correlate with anything data-dependent at all?
def hw(a):
    return np.unpackbits(np.asarray(a, dtype=np.uint8)[:, None], axis=1).sum(1)

print("[3] max |corr| of each trace-sample with simple data models:")
best = []
for i in range(16):
    for name, v in (("HW(pt)", hw(P[:, i])), ("pt", P[:, i].astype(float)),
                    ("LSB", P[:, i] & 1), ("popcount^2", hw(P[:, i]) ** 2.0)):
        v = v.astype(float)
        v = v - v.mean()
        c = (Tc * v[:, None]).mean(0) / (v.std() * Tc.std(0) + 1e-9)
        best.append((float(np.abs(c).max()), i, name, int(np.argmax(np.abs(c)))))
best.sort(reverse=True)
for s, i, name, samp in best[:8]:
    print(f"    byte {i:2d} {name:11s} sample {samp:3d}  |r|={s:.3f}")
print(f"    noise floor for this test ~ {1/np.sqrt(n):.3f} per point, "
      f"{np.sqrt(2)*np.log(16*4*m)**0.5/np.sqrt(n):.3f} after multiplicity")

# 4. pairwise: is leakage split over two halves (masking)? check HW(pt_i)+HW(pt_j)
print("[4] second-order probe: HW of XOR of two plaintext bytes (masking check)")
res = []
for i in range(16):
    for j in range(i + 1, 16):
        v = hw(P[:, i] ^ P[:, j]).astype(float)
        v -= v.mean()
        c = (Tc * v[:, None]).mean(0) / (v.std() * Tc.std(0) + 1e-9)
        res.append((float(np.abs(c).max()), i, j))
res.sort(reverse=True)
for s, i, j in res[:5]:
    print(f"    bytes {i},{j}: |r|={s:.3f}")

# 5. spectrum of one trace + variance profile (where is activity?)
var = Tc.var(0)
print("[5] variance profile peaks:", np.argsort(var)[::-1][:8].tolist(),
      "flat?", f"min/max var ratio={var.min()/var.max():.4f}")
