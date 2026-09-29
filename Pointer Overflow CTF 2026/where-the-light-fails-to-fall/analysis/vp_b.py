"""Second vanishing point: remove family-A gradient samples, then re-run the coherence map."""
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

STEP = 8
sub = (slice(None, None, STEP), slice(None, None, STEP))
sel = keep[sub]
ys, xs = np.nonzero(sel)
px = (xs * STEP).astype(np.float64)
py = (ys * STEP).astype(np.float64)
gx = gxx[sub][ys, xs].astype(np.float64)
gy = gyy[sub][ys, xs].astype(np.float64)
m2 = mag[sub][ys, xs].astype(np.float64)
n = np.maximum(np.hypot(gx, gy), 1e-6)
gx, gy = gx / n, gy / n
w = np.clip(m2, 0, np.percentile(m2, 98)) ** 2
ok = w > np.percentile(w, 50)
px, py, gx, gy, w = px[ok], py[ok], gx[ok], gy[ok], w[ok]
print("samples:", len(px))

VA = np.array([-4482.0, 193.0])
# family-A membership: gradient perpendicular to (p - VA)
rx, ry = px - VA[0], py - VA[1]
rn = np.maximum(np.hypot(rx, ry), 1)
tax, tay = -ry / rn, rx / rn          # tangent of the ray from VA
align = np.abs(gx * tax + gy * tay)   # ~1 when the edge is radial from VA
isA = align > 0.93
print("family-A samples removed:", isA.sum())
px, py, gx, gy, w = px[~isA], py[~isA], gx[~isA], gy[~isA], w[~isA]
wn = w / w.sum()


def score(vx, vy):
    rx, ry = px - vx, py - vy
    r = np.maximum(np.hypot(rx, ry), 1.0)
    c = gx * (-ry / r) + gy * (rx / r)
    return float((wn * c * c).sum())


XG = np.concatenate([np.linspace(-160000, -20000, 90), np.linspace(-15000, 15000, 120),
                     np.linspace(20000, 160000, 90)])
YG = np.linspace(-60000, 6000, 150)
S = np.array([[score(vx, vy) for vx in XG] for vy in YG])
print("map max %.5f min %.5f" % (S.max(), S.min()))
flat = np.argsort(S.ravel())[::-1]
found = []
for k in flat:
    i, j = divmod(k, S.shape[1])
    v = np.array([XG[j], YG[i]])
    if any(np.hypot(v[0] - f[0], v[1] - f[1]) < 20000 for f in found):
        continue
    found.append(v)
    print(f"   peak {len(found)}: ({v[0]:10.0f},{v[1]:10.0f}) coherence={S[i,j]:.5f}")
    if len(found) >= 5:
        break

for v0 in found[:3]:
    v = v0.copy()
    cur = score(*v)
    step = 6000.0
    while step > 1.0:
        mv = None
        for dx in (-step, 0, step):
            for dy in (-step, 0, step):
                s = score(v[0] + dx, v[1] + dy)
                if s > cur:
                    cur, mv = s, v + np.array([dx, dy])
        if mv is None:
            step *= 0.5
        else:
            v = mv
    print(f"refined VP_B=({v[0]:11.1f},{v[1]:11.1f}) coherence={cur:.5f}")
    np.save("vp_b.npy", v)
