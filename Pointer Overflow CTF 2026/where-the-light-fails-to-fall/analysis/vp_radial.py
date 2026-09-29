"""Vanishing points from radial-gradient coherence: at a VP every joint is a ray out of
that point, so the image gradient there is purely tangential."""
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
P = np.stack([xs * STEP, ys * STEP], 1).astype(np.float64)
G = np.stack([gxx[::STEP, ::STEP], gyy[::STEP, ::STEP]], -1)[ys, xs]
M2 = mag[::STEP, ::STEP][ys, xs]
w = np.clip(M2, 0, np.percentile(M2, 98)) ** 2          # emphasise real edges
ok = w > np.percentile(w, 55)
P, G, w = P[ok], G[ok], w[ok]
G = G / np.linalg.norm(G, axis=1, keepdims=True)
print("gradient samples:", len(P))

gx, gy = G[:, 0], G[:, 1]
px, py = P[:, 0], P[:, 1]


def score(vx, vy):
    rx, ry = px - vx, py - vy
    n = np.hypot(rx, ry)
    n = np.maximum(n, 1.0)
    tx, ty = -ry / n, rx / n                 # tangential unit
    c = gx * tx + gy * ty                    # |component along the tangent|
    return float((w * c * c).sum() / w.sum())


# coarse sweep over a wide field, then local refinement
best = []
xs_g = np.concatenate([np.linspace(-40000, 40000, 161)])
ys_g = np.concatenate([np.linspace(-40000, 12000, 131)])
S = np.zeros((len(ys_g), len(xs_g)))
for i, vy in enumerate(ys_g):
    S[i] = [score(vx, vy) for vx in xs_g]
print("coarse max:", S.max())

flat = np.argsort(S.ravel())[::-1]
found = []
for k in flat:
    i, j = divmod(k, S.shape[1])
    v = np.array([xs_g[j], ys_g[i]])
    if any(np.linalg.norm(v - f) < 6000 for f in found):
        continue
    found.append(v)
    if len(found) >= 6:
        break

for v0 in found:
    v = v0.copy()
    step = 2000.0
    cur = score(*v)
    while step > 1.0:
        improved = False
        for dx in (-step, 0, step):
            for dy in (-step, 0, step):
                s = score(v[0] + dx, v[1] + dy)
                if s > cur:
                    cur, nv = s, v + np.array([dx, dy])
                    improved = True
                    break
            if improved:
                break
        if improved:
            v = nv
        else:
            step *= 0.5
    print(f"VP=({v[0]:11.1f},{v[1]:11.1f})  coherence={cur:.5f}")
    np.save("vp_radial.npy", np.array([v]))
