"""Cluster the lattice direction field into two families, fit both pencils, report."""
import cv2
import numpy as np
from scipy.optimize import minimize

img = cv2.imread("../files/photo.png", cv2.IMREAD_GRAYSCALE).astype(np.float32)
H, W = img.shape
bh = cv2.morphologyEx(img.astype(np.uint8), cv2.MORPH_BLACKHAT,
                      cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))).astype(np.float32)
SIZES = [110, 150, 210, 300, 420, 600]
NF = 1024


def peaks(cx, cy):
    best = None
    for R in SIZES:
        x0, y0 = cx - R, cy - R
        if x0 < 0 or y0 < 0 or x0 + 2 * R > W or y0 + 2 * R > H:
            continue
        p = bh[y0:y0 + 2 * R, x0:x0 + 2 * R]
        if p.mean() < 40 or p.std() < 7:
            continue
        p = cv2.resize(p, (NF, NF), interpolation=cv2.INTER_AREA).astype(np.float32)
        p = (p - p.mean()) * np.hanning(NF)[:, None] * np.hanning(NF)[None, :]
        F = np.fft.fftshift(np.abs(np.fft.fft2(p)))
        scale = 2 * R / NF
        fv = (np.arange(NF) - NF // 2) / (NF * 1.0) / scale
        Fc = F.copy()
        c = NF // 2
        Fc[c - 4:c + 5, c - 4:c + 5] = 0
        res = []
        for _ in range(2):
            i, j = np.unravel_index(np.argmax(Fc), Fc.shape)
            wi = np.array([F[i - 1, j], F[i, j], F[i + 1, j]], float)
            wj = np.array([F[i, j - 1], F[i, j], F[i, j + 1]], float)
            di = (wi[2] - wi[0]) / max(wi.sum(), 1e-9)
            dj = (wj[2] - wj[0]) / max(wj.sum(), 1e-9)
            f_y, f_x = fv[i] + di * (fv[1] - fv[0]), fv[j] + dj * (fv[1] - fv[0])
            wl = 1.0 / np.hypot(f_x, f_y)
            snr = F[i, j] / np.median(F[F > 0])
            if 22 < wl < 1500:
                res.append((np.degrees(np.arctan2(-f_x, f_y)) % 180, wl, snr, R))
            Fc[max(0, i - 12):i + 13, max(0, j - 12):j + 13] = 0
        if len(res) == 2:
            sc = min(r[2] for r in res)
            if best is None or sc > best[0]:
                best = (sc, res)
    return best[1] if best else None


recs = []
for cy in range(280, 3960, 120):
    for cx in range(160, 2960, 160):
        if 780 < cx < 2620 and 1300 < cy < 3050:
            continue
        if cx > 700 and cy < 0.1818 * (cx - 780) + 70:
            continue
        r = peaks(cx, cy)
        if r:
            for ang, wl, snr, R in r:
                if snr > 900:
                    recs.append([cx, cy, ang, wl, snr])
recs = np.array(recs)
print("direction samples:", len(recs))
np.save("dirfield.npy", recs)

# --- two-cluster fit on angles mod 180 ---
def circ_dist(a, b):
    d = np.abs(a - b) % 180
    return np.minimum(d, 180 - d)


c0 = np.percentile(recs[:, 2], [25, 75])
for it in range(25):
    d = np.stack([circ_dist(recs[:, 2], c0[0]), circ_dist(recs[:, 2], c0[1])], 1)
    lab = d.argmin(1)
    for k in (0, 1):
        m = lab == k
        if m.sum() > 5:
            c0[k] = np.average(recs[m, 2], weights=recs[m, 4])
print("cluster centres:", np.round(c0, 2), "sizes:", np.bincount(lab))


def fit_pencil(mask):
    P = recs[mask][:, 0:2]
    g = np.radians(recs[mask][:, 2])
    U = np.stack([np.cos(g), np.sin(g)], 1)
    w = np.sqrt(recs[mask][:, 4])

    def f(v):
        dv = P - v
        r = np.maximum(np.linalg.norm(dv, axis=1), 1)
        s = np.abs(dv[:, 0] * U[:, 1] - dv[:, 1] * U[:, 0]) / r
        return float((w * np.degrees(np.arcsin(np.clip(s, -1, 1))) ** 2).sum())

    best = None
    for x0 in (-60000, -20000, -6000, -1500, 1500, 6000, 20000, 60000):
        for y0 in (-60000, -20000, -6000, -1500, 0, 1500):
            r = minimize(f, [x0, y0], method="Nelder-Mead",
                         options=dict(maxiter=20000, maxfev=20000, xatol=1e-4, fatol=1e-10))
            if best is None or r.fun < best.fun:
                best = r
    v = best.x
    dv = P - v
    rr = np.maximum(np.linalg.norm(dv, axis=1), 1)
    s = np.abs(dv[:, 0] * U[:, 1] - dv[:, 1] * U[:, 0]) / rr
    ang = np.degrees(np.arcsin(np.clip(s, -1, 1)))
    return v, ang


out = {}
for k in (0, 1):
    m = lab == k
    v, ang = fit_pencil(m)
    # robust refit dropping the worst 25%
    keep = np.abs(ang) <= np.percentile(np.abs(ang), 75)
    m2 = m.copy(); m2[m] = keep
    v2, ang2 = fit_pencil(m2)
    print(f"cluster {k}: n={m.sum()} VP=({v[0]:10.1f},{v[1]:10.1f}) rms={np.sqrt((ang**2).mean()):.2f}"
          f"   robust n={m2.sum()} VP=({v2[0]:10.1f},{v2[1]:10.1f}) rms={np.sqrt((ang2**2).mean()):.2f}")
    out[k] = (v2, m2)

np.save("vp_field.npy", np.stack([out[0][0], out[1][0]]))
np.save("vp_field_lab", np.stack([out[0][1], out[1][1]]))

vis = cv2.cvtColor(cv2.GaussianBlur(img.astype(np.uint8), (5, 5), 0), cv2.COLOR_GRAY2BGR)
vis = cv2.resize(vis, (W // 4, H // 4))
for (x, y, a, wl, snr), k in zip(recs, lab):
    u = np.array([np.cos(np.radians(a)), np.sin(np.radians(a))])
    c = (0, 255, 0) if k == 0 else (0, 120, 255)
    p = np.array([x, y]) / 4
    cv2.line(vis, tuple((p - u * 12).astype(int)), tuple((p + u * 12).astype(int)), c, 2)
cv2.imwrite("dirfield.png", vis)
