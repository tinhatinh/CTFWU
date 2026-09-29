"""Local sett-lattice direction field, measured with an adaptive-scale 2-D spectrum.

Each patch yields the two lattice row directions; family A is matched against the known
vanishing point, and family B is then fitted as a pencil."""
import cv2
import numpy as np

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
        F = np.abs(np.fft.fft2(p))
        F = np.fft.fftshift(F)
        scale = 2 * R / NF                      # source px per resampled px
        fy = (np.arange(NF) - NF // 2) / (NF * 1.0) / scale     # cycles per source px
        fx = fy.copy()
        Fc = F.copy()
        Fc[NF // 2 - 4:NF // 2 + 5, NF // 2 - 4:NF // 2 + 5] = 0
        res = []
        for _ in range(2):
            i, j = np.unravel_index(np.argmax(Fc), Fc.shape)
            # 3x3 centroid for sub-bin frequency
            wi = np.array([F[i - 1, j], F[i, j], F[i + 1, j]], float)
            wj = np.array([F[i, j - 1], F[i, j], F[i, j + 1]], float)
            di = (wi[2] - wi[0]) / max(wi[0] + wi[1] + wi[2], 1e-9)
            dj = (wj[2] - wj[0]) / max(wj[0] + wj[1] + wj[2], 1e-9)
            f_y, f_x = fy[i] + di * (fy[1] - fy[0]), fx[j] + dj * (fx[1] - fx[0])
            wl = 1.0 / np.hypot(f_x, f_y)
            snr = F[i, j] / np.median(F[F > 0])
            if 25 < wl < 1200:
                res.append((np.degrees(np.arctan2(-f_x, f_y)) % 180, wl, snr, R))
            Fc[max(0, i - 12):i + 13, max(0, j - 12):j + 13] = 0
        if len(res) == 2:
            sc = min(r[2] for r in res)
            if best is None or sc > best[0]:
                best = (sc, res)
    return best[1] if best else None


VA = np.array([-4482.0, 193.0])
rows = []
for cy in range(300, 3900, 150):
    for cx in range(200, 2900, 200):
        if 820 < cx < 2600 and 1330 < cy < 3020:
            continue                     # bird + shadow box
        if cx > 780 and cy < 0.1818 * (cx - 780) + 60:
            continue                     # ribbed slab
        r = peaks(cx, cy)
        if r:
            rows.append((cx, cy, r))
print("patches:", len(rows))

famA, famB = [], []
for cx, cy, r in rows:
    for ang, wl, snr, R in r:
        # the lattice rows with image direction `ang` (deg, y-down): does the line through
        # (cx,cy) in that direction pass near VA?
        d = np.array([np.cos(np.radians(ang)), np.sin(np.radians(ang))])
        t = ((VA - np.array([cx, cy])) @ d)
        dist = np.linalg.norm(VA - np.array([cx, cy]) - t * d)
        (famA if dist < 900 else famB).append((cx, cy, ang, wl, snr))
print("family A samples:", len(famA), " family B:", len(famB))


def pencil(fam, name):
    from scipy.optimize import minimize
    P = np.array([(a, b) for a, b, *_ in fam], float)
    g = np.radians(np.array([f[2] for f in fam], float))
    U = np.stack([np.cos(g), np.sin(g)], 1)

    def f(v):
        dv = P - v
        r = np.maximum(np.linalg.norm(dv, axis=1), 1)
        s = np.abs(dv[:, 0] * U[:, 1] - dv[:, 1] * U[:, 0]) / r
        return float((np.degrees(np.arcsin(np.clip(s, -1, 1))) ** 2).sum())

    best = None
    for x0 in (-30000, -8000, -2000, 1500, 8000, 30000):
        for y0 in (-40000, -8000, -1000, 300):
            r = minimize(f, [x0, y0], method="Nelder-Mead",
                         options=dict(maxiter=8000, xatol=1e-4, fatol=1e-10))
            if best is None or r.fun < best.fun:
                best = r
    v = best.x
    dv = P - v
    rr = np.maximum(np.linalg.norm(dv, axis=1), 1)
    s = np.abs(dv[:, 0] * U[:, 1] - dv[:, 1] * U[:, 0]) / rr
    ang = np.degrees(np.arcsin(np.clip(s, -1, 1)))
    print(f"{name}: VP=({v[0]:10.1f},{v[1]:10.1f})  rms={np.sqrt((ang**2).mean()):.2f} deg  "
          f"med={np.median(np.abs(ang)):.2f}  n={len(P)}")
    return v, ang


vA2, angA = pencil(famA, "A")
vB2, angB = pencil(famB, "B")
np.save("lattice_vps.npy", np.stack([vA2, vB2]))
for cx, cy, r in rows[:40]:
    print((cx, cy), [(round(a, 1), round(w), round(s)) for a, w, s, R in r])
