"""Dual-space voting: every joint segment is a line in vanishing-point space; the
peaks of the pairwise-intersection accumulator are the vanishing points."""
import cv2
import numpy as np

seg = np.load("segs_hp.npy")           # mx, my, ang_deg, len
M = seg[:, 0:2]
g = np.radians(seg[:, 2])
U = np.stack([np.cos(g), np.sin(g)], 1)
L = seg[:, 3]
print("segments:", len(seg))

rng = np.random.default_rng(3)
idx = rng.choice(len(seg), size=2400, replace=False)
m, u, ln = M[idx], U[idx], L[idx]
n = len(m)

# pairwise intersections of the supporting lines
p1, q1 = m[:, None, :], u[:, None, :]          # (n,1,2) x (1,n,2)
p2, q2 = m[None, :, :], u[None, :, :]
den = q1[..., 0] * q2[..., 1] - q1[..., 1] * q2[..., 0]
dp = p2 - p1
t = (dp[..., 0] * q2[..., 1] - dp[..., 1] * q2[..., 0]) / np.where(np.abs(den) < 1e-9, np.nan, den)
V = p1 + t[..., None] * q1
w = ln[:, None] * ln[None, :]
ok = np.isfinite(V[..., 0]) & (np.abs(den) > 0.25) & (w > 0)
Vx, Vy, Ww = V[..., 0][ok], V[..., 1][ok], w[ok]
lim_x, lim_y = 120000, 80000
inb = (np.abs(Vx) < lim_x) & (np.abs(Vy) < lim_y)
Vx, Vy, Ww = Vx[inb], Vy[inb], Ww[inb]
print("votes:", len(Vx))

BX = np.linspace(-lim_x, lim_x, 481)
BY = np.linspace(-lim_y, lim_y, 321)
for round_no in range(2):
    Hist, _, _ = np.histogram2d(Vx, Vy, bins=[BX, BY], weights=Ww)
    Hs = cv2.GaussianBlur(Hist, (0, 0), 6)
    flat = np.argsort(Hs.ravel())[::-1]
    peaks = []
    for k in flat:
        i, j = divmod(int(k), Hs.shape[1])
        v = np.array([0.5 * (BX[i] + BX[i + 1]), 0.5 * (BY[j] + BY[j + 1])])
        if any(np.linalg.norm(v - p) < 18000 for p in peaks):
            continue
        peaks.append(v)
        if len(peaks) >= 4:
            break
    print(f"\nround {round_no} peaks:")
    keep_segs = np.ones(len(seg), bool)
    for pi, v in enumerate(peaks):
        dv = M - v
        r = np.maximum(np.linalg.norm(dv, axis=1), 1)
        ang = np.degrees(np.arcsin(np.clip(np.abs(dv[:, 0] * U[:, 1] - dv[:, 1] * U[:, 0]) / r, -1, 1)))
        sel = ang < 1.2
        print(f"   VP=({v[0]:10.1f},{v[1]:10.1f})  nseg={sel.sum():5d} len={L[sel].sum():8.0f}")
        if round_no == 1:
            np.save(f"vp_peak_{pi}.npy", v)
            np.save(f"vp_peak_{pi}_sel.npy", sel)
    # remove the strongest peak's inliers and re-vote
    dv = M - peaks[0]
    r = np.maximum(np.linalg.norm(dv, axis=1), 1)
    ang = np.degrees(np.arcsin(np.clip(np.abs(dv[:, 0] * U[:, 1] - dv[:, 1] * U[:, 0]) / r, -1, 1)))
    dead = ang < 1.2
    keep = ~dead
    print(f"   removing {dead.sum()} segments belonging to peak 0")
    selidx = np.where(keep[idx])[0]
    m, u, ln = M[selidx], U[selidx], L[selidx]
    n = len(m)
    p1, q1 = m[:, None, :], u[:, None, :]
    p2, q2 = m[None, :, :], u[None, :, :]
    den = q1[..., 0] * q2[..., 1] - q1[..., 1] * q2[..., 0]
    dp = p2 - p1
    t = (dp[..., 0] * q2[..., 1] - dp[..., 1] * q2[..., 0]) / np.where(np.abs(den) < 1e-9, np.nan, den)
    V = p1 + t[..., None] * q1
    w = ln[:, None] * ln[None, :]
    ok = np.isfinite(V[..., 0]) & (np.abs(den) > 0.25)
    Vx, Vy, Ww = V[..., 0][ok], V[..., 1][ok], w[ok]
    inb = (np.abs(Vx) < lim_x) & (np.abs(Vy) < lim_y)
    Vx, Vy, Ww = Vx[inb], Vy[inb], Ww[inb]
