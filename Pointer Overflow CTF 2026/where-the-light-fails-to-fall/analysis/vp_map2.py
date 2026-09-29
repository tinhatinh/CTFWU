"""Vectorised radial-coherence map over a wide field; report and polish the top peaks."""
import cv2
import numpy as np

img = cv2.imread("../files/photo.png", cv2.IMREAD_GRAYSCALE)
H, W = img.shape
bh = cv2.morphologyEx(img, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31)))
bh = cv2.GaussianBlur(bh.astype(np.float32), (5, 5), 0)
gxx = cv2.Sobel(bh, cv2.CV_32F, 1, 0, ksize=3)
gyy = cv2.Sobel(bh, cv2.CV_32F, 0, 1, ksize=3)
mag = np.hypot(gxx, gyy)
yy, xx = np.mgrid[0:H, 0:W]
keep = np.ones((H, W), bool)
keep[yy < np.maximum(0.0, 0.1818 * (xx - 780)) + 40] = False
keep[:60, :] = False
cv2.rectangle(keep, (820, 1330), (2600, 3020), False, -1)

STEP = 10
sub = (slice(None, None, STEP), slice(None, None, STEP))
ys, xs = np.nonzero(keep[sub])
P = np.stack([xs * STEP, ys * STEP], 1).astype(np.float64)
g = np.stack([gxx[sub][ys, xs], gyy[sub][ys, xs]], 1).astype(np.float64)
m2 = mag[sub][ys, xs].astype(np.float64)
g /= np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-6)
w = np.clip(m2, 0, np.percentile(m2, 98)) ** 2
ok = w > np.percentile(w, 60)
P, g, w = P[ok], g[ok], w[ok]
wn = w / w.sum()
px, py = P[:, 0], P[:, 1]
gx, gy = g[:, 0], g[:, 1]
print("samples:", len(P))


def map_scores(VX, VY):
    """VX: (nx,) candidate x; VY: (ny,) -> (ny,nx) coherence."""
    out = np.empty((len(VY), len(VX)))
    CH = 400
    for i, vy in enumerate(VY):
        for a in range(0, len(VX), CH):
            vx = VX[a:a + CH]
            rx = px[None, :] - vx[:, None]
            ry = py[None, :] - vy
            r = np.maximum(np.hypot(rx, ry), 1.0)
            c = (gx[None, :] * -ry + gy[None, :] * rx) / r
            out[i, a:a + CH] = (c * c * wn[None, :]).sum(1)
    return out


XG = np.concatenate([np.linspace(-300000, -20000, 100), np.linspace(-18000, 18000, 120),
                     np.linspace(20000, 300000, 100)])
YG = np.concatenate([np.linspace(-300000, -20000, 100), np.linspace(-18000, 6000, 120)])
S = map_scores(XG, YG)
np.save("coh2.npy", S)
np.savez("coh2_axes.npz", x=XG, y=YG)
print("max %.5f min %.5f" % (S.max(), S.min()))


def score1(v):
    rx, ry = px - v[0], py - v[1]
    r = np.maximum(np.hypot(rx, ry), 1.0)
    c = (gx * -ry + gy * rx) / r
    return float((c * c * wn).sum())


flat = np.argsort(S.ravel())[::-1]
found = []
for k in flat:
    i, j = divmod(k, S.shape[1])
    v = np.array([XG[j], YG[i]], float)
    if any(np.linalg.norm(v - f) < 25000 for f in found):
        continue
    found.append(v)
    print(f"   peak {len(found)}: ({v[0]:10.0f},{v[1]:10.0f}) = {S[i,j]:.5f}")
    if len(found) >= 5:
        break

for v0 in found:
    v = v0.copy()
    cur = score1(v)
    step = 20000.0
    while step > 0.5:
        mv = None
        for dx in (-step, 0, step):
            for dy in (-step, 0, step):
                s = score1(v + np.array([dx, dy]))
                if s > cur + 1e-12:
                    cur, mv = s, v + np.array([dx, dy])
        if mv is None:
            step *= 0.5
        else:
            v = mv
    dv = np.stack([px - v[0], py - v[1]], 1)
    r = np.maximum(np.linalg.norm(dv, axis=1), 1)
    ang = np.degrees(np.arcsin(np.clip(np.abs(dv[:, 0] * gy - dv[:, 1] * gx) / r, -1, 1)))
    n1 = (ang < 0.6).sum()
    print(f"polished ({v[0]:11.1f},{v[1]:11.1f}) coh={cur:.5f} n(<0.6deg)={n1}")
    np.save("peaks2.npy", np.array(found))
