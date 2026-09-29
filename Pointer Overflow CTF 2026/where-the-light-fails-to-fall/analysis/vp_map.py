"""Radial-gradient coherence map: report the strongest vanishing-point peaks."""
import cv2
import numpy as np

img = cv2.imread("../files/photo.png")
H, W = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
bh = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31)))
bh = cv2.GaussianBlur(bh, (5, 5), 0)
gxx = cv2.Sobel(bh, cv2.CV_32F, 1, 0, ksize=3)
gyy = cv2.Sobel(bh, cv2.CV_32F, 0, 1, ksize=3)
mag = np.hypot(gxx, gyy)

yy, xx = np.mgrid[0:H, 0:W]
keep = np.ones((H, W), bool)
keep[yy < np.maximum(0.0, 0.1818 * (xx - 780)) + 40] = False
keep[:60, :] = False
cv2.rectangle(keep, (820, 1330), (2600, 3020), False, -1)

STEP = 10
sel = keep[::STEP, ::STEP]
ys, xs = np.nonzero(sel)
px = (xs * STEP).astype(np.float64)
py = (ys * STEP).astype(np.float64)
gx = gxx[::STEP, ::STEP][ys, xs]
gy = gyy[::STEP, ::STEP][ys, xs]
m2 = mag[::STEP, ::STEP][ys, xs]
n = np.maximum(np.hypot(gx, gy), 1e-6)
gx, gy = gx / n, gy / n
w = np.clip(m2, 0, np.percentile(m2, 98)) ** 2
ok = w > np.percentile(w, 55)
px, py, gx, gy, w = px[ok], py[ok], gx[ok], gy[ok], w[ok]
wn = w / w.sum()
print("samples:", len(px))


def score(vx, vy):
    rx, ry = px - vx, py - vy
    r = np.maximum(np.hypot(rx, ry), 1.0)
    t = (-ry / r, rx / r)
    c = gx * t[0] + gy * t[1]
    return float((wn * c * c).sum())


XG = np.concatenate([np.linspace(-120000, -8000, 120), np.linspace(-6000, 6000, 60),
                     np.linspace(8000, 120000, 120)])
YG = np.linspace(-40000, 8000, 160)
S = np.array([[score(vx, vy) for vx in XG] for vy in YG])
np.save("coh_map.npy", S)
np.save("coh_axes.npy", np.array([S.shape], dtype=float))
np.save("coh_xg.npy", XG)
np.save("coh_yg.npy", YG)
print("map max", S.max(), "min", S.min())

flat = np.argsort(S.ravel())[::-1]
found = []
for k in flat:
    i, j = divmod(k, S.shape[1])
    v = np.array([XG[j], YG[i]])
    if any(np.hypot(v[0] - f[0], v[1] - f[1]) < 15000 for f in found):
        continue
    found.append(v)
    print(f"   peak {len(found)}: ({v[0]:10.0f},{v[1]:10.0f}) coherence={S[i,j]:.5f}")
    if len(found) >= 6:
        break

# refine each peak locally
for v0 in found:
    v = v0.copy()
    step = 4000.0
    cur = score(*v)
    while step > 2.0:
        best = (cur, v)
        for dx in (-step, 0, step):
            for dy in (-step, 0, step):
                s = score(v[0] + dx, v[1] + dy)
                if s > best[0]:
                    best = (s, v + np.array([dx, dy]))
        if best[1] is v or np.linalg.norm(best[1] - v) == 0:
            step *= 0.5
        cur, v = best
    print(f"refined VP=({v[0]:11.1f},{v[1]:11.1f}) coherence={cur:.5f}")
