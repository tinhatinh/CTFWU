"""Remove family-A radial gradients, then map the coherence for family B."""
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
ys, xs = np.nonzero(keep[sub])
P = np.stack([xs * STEP, ys * STEP], 1).astype(np.float64)
G = np.stack([gxx[sub][ys, xs], gyy[sub][ys, xs]], 1).astype(np.float64)
m2 = mag[sub][ys, xs].astype(np.float64)
G /= np.maximum(np.linalg.norm(G, axis=1, keepdims=True), 1e-6)
w = np.clip(m2, 0, np.percentile(m2, 98)) ** 2
ok = w > np.percentile(w, 60)
P, G, w = P[ok], G[ok], w[ok]
print("samples:", len(P))


def ang_res(V):
    dv = P - V
    r = np.maximum(np.linalg.norm(dv, axis=1), 1.0)
    return np.degrees(np.arcsin(np.clip(np.abs(dv[:, 0] * G[:, 1] - dv[:, 1] * G[:, 0]) / r, -1, 1)))


VA = np.array([-4361.0, 206.0])
rA = ang_res(VA)
print("family A (<1deg):", (rA < 1).sum(), " (<2deg):", (rA < 2).sum())
m = rA > 2.0
P, G, w = P[m], G[m], w[m]
wn = w / w.sum()
px, py = P[:, 0], P[:, 1]
gx, gy = G[:, 0], G[:, 1]
print("remaining samples:", len(P))


def score1(vx, vy):
    rx, ry = px - vx, py - vy
    r = np.maximum(np.hypot(rx, ry), 1.0)
    c = (gx * -ry + gy * rx) / r
    return float((wn * c * c).sum())


XG = np.linspace(-40000, 60000, 200)
YG = np.linspace(-60000, 3000, 200)
S = np.empty((len(YG), len(XG)))
CH = 300
for i, vy in enumerate(YG):
    for a in range(0, len(XG), CH):
        vx = XG[a:a + CH]
        rx = px[None, :] - vx[:, None]
        ry = py[None, :] - vy
        r = np.maximum(np.hypot(rx, ry), 1.0)
        c = (gx[None, :] * -ry + gy[None, :] * rx) / r
        S[i, a:a + CH] = (c * c * wn[None, :]).sum(1)
print("max %.5f min %.5f" % (S.max(), S.min()))
np.save("cohB.npy", S)
np.savez("cohB_axes.npz", x=XG, y=YG)

flat = np.argsort(S.ravel())[::-1]
found = []
for k in flat:
    i, j = divmod(k, S.shape[1])
    v = np.array([XG[j], YG[i]])
    if any(np.linalg.norm(v - f) < 6000 for f in found):
        continue
    found.append(v)
    print(f"   peak {len(found)}: ({v[0]:10.0f},{v[1]:10.0f}) = {S[i,j]:.5f}")
    if len(found) >= 6:
        break

for v0 in found[:3]:
    v = v0.copy()
    cur = score1(*v)
    step = 3000.0
    while step > 0.5:
        mv = None
        for dx in (-step, 0, step):
            for dy in (-step, 0, step):
                s = score1(v[0] + dx, v[1] + dy)
                if s > cur + 1e-12:
                    cur, mv = s, v + np.array([dx, dy])
        if mv is None:
            step *= 0.5
        else:
            v = mv
    dv = P - v
    r = np.maximum(np.linalg.norm(dv, axis=1), 1)
    ang = np.degrees(np.arcsin(np.clip(np.abs(dv[:, 0] * G[:, 1] - dv[:, 1] * G[:, 0]) / r, -1, 1)))
    print(f"polished VP_B=({v[0]:11.1f},{v[1]:11.1f}) coh={cur:.5f} n(<0.5deg)={(ang<0.5).sum()}")
    np.save("vp_b_est.npy", v)
