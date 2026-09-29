"""Two-pencil EM fit over the high-pass joint segments, then full ground calibration."""
import numpy as np
from scipy.optimize import minimize

s = np.load("segs_hp.npy")
M, A, L = s[:, 0:2], np.radians(s[:, 2]), s[:, 3]
U = np.stack([np.cos(A), np.sin(A)], 1)
C = np.array([1500.0, 2000.0])
print("segments:", len(s), " total length:", int(L.sum()))


def resid(v):
    dv = M - v
    r = np.maximum(np.linalg.norm(dv, axis=1), 1.0)
    return np.degrees(np.arcsin(np.clip(np.abs(dv[:, 0] * U[:, 1] - dv[:, 1] * U[:, 0]) / r, -1, 1)))


def fit(sel, v0, w=None):
    P, Q, WW = M[sel], U[sel], (L[sel] if w is None else w)

    def f(z):
        v = C + np.exp(z[1]) * np.array([np.cos(z[0]), np.sin(z[0])])
        dv = P - v
        r = np.maximum(np.linalg.norm(dv, axis=1), 1.0)
        th = np.degrees(np.arcsin(np.clip(np.abs(dv[:, 0] * Q[:, 1] - dv[:, 1] * Q[:, 0]) / r, -1, 1)))
        return float((WW * th * th).sum())

    d = v0 - C
    best = None
    for rr in (0.3, 1.0, 3.0):
        z0 = [np.arctan2(d[1], d[0]), np.log(max(np.linalg.norm(d) * rr, 50))]
        res = minimize(f, z0, method="Powell", options=dict(xtol=1e-6, ftol=1e-10, maxiter=40000))
        if best is None or res.fun < best.fun:
            best = res
    v = C + np.exp(best.x[1]) * np.array([np.cos(best.x[0]), np.sin(best.x[0])])
    return v


V = [np.array([5250.0, -14250.0]), np.array([-16250.0, -2750.0])]
for it in range(10):
    r0, r1 = resid(V[0]), resid(V[1])
    lab = (r1 < r0).astype(int)
    for k in (0, 1):
        sel = lab == k
        if sel.sum() < 20:
            continue
        r = resid(V[k])
        w = np.exp(-(r[sel] / 3.0) ** 2) * L[sel]          # soft, robust weights
        V[k] = fit(sel, V[k], w)
    r0, r1 = resid(V[0]), resid(V[1])
    lab = (r1 < r0).astype(int)
    for k, r in ((0, r0), (1, r1)):
        sel = lab == k
        print(f"  it{it} pencil{k}: n={sel.sum():5d} len={L[sel].sum():8.0f} VP=({V[k][0]:10.1f},{V[k][1]:10.1f})"
              f" med|res|={np.median(r[sel]):.2f} w50={np.percentile(r[sel],50):.2f}")
    print()

np.save("vp_em.npy", np.stack(V))
np.save("vp_em_lab.npy", lab)
for k in (0, 1):
    sel = lab == k
    strong = sel & (L > 400)
    print(f"pencil {k}: long segments n={strong.sum()} med res={np.median(resid(V[k])[strong]):.2f} deg")
    for band in ((60, 900), (900, 1800), (1800, 2700), (2700, 3990)):
        b = strong & (M[:, 1] >= band[0]) & (M[:, 1] < band[1])
        if b.sum() > 3:
            print(f"    y {band}: n={b.sum():3d} med res={np.median(resid(V[k])[b]):.2f}")
