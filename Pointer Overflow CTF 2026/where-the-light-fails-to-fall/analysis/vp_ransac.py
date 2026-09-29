"""Angular RANSAC for the lattice vanishing points."""
import cv2
import itertools
import numpy as np

img = cv2.imread("../files/photo.png")
H, W = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
bh = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31)))
bh = cv2.GaussianBlur(bh, (5, 5), 0)
edges = cv2.Canny(bh, 30, 90)

yy, xx = np.mgrid[0:H, 0:W]
keep = np.ones((H, W), bool)
keep[yy < np.maximum(0.0, 0.1818 * (xx - 780)) + 40] = False
keep[:60, :] = False
cv2.rectangle(keep, (820, 1330), (2600, 3020), False, -1)
edges[~keep] = 0

seg = cv2.HoughLinesP(edges, 1, np.pi / 1800, threshold=80, minLineLength=260, maxLineGap=14)
seg = np.asarray(seg).reshape(-1, 4).astype(np.float64)
d = seg[:, 2:4] - seg[:, 0:2]
L = np.hypot(d[:, 0], d[:, 1])
M = (seg[:, 0:2] + seg[:, 2:4]) / 2
U = d / L[:, None]
print("segments:", len(seg))


def inliers(v, tol_deg):
    dv = v[None, :] - M
    n = np.linalg.norm(dv, axis=1)
    s = np.abs(dv[:, 0] * U[:, 1] - dv[:, 1] * U[:, 0]) / np.maximum(n, 1e-9)
    return s < np.sin(np.radians(tol_deg))


def refine(v, tol_deg=1.2, iters=10):
    for _ in range(iters):
        sel = inliers(v, tol_deg)
        if sel.sum() < 8:
            return v, 0
        p, q, w = M[sel], U[sel], L[sel]
        A = np.stack([q[:, 1], -q[:, 0]], 1) * np.sqrt(w)[:, None]
        b = (q[:, 1] * p[:, 0] - q[:, 0] * p[:, 1]) * np.sqrt(w)
        v = np.linalg.lstsq(A, b, rcond=None)[0]
    return v, sel.sum()


rng = np.random.default_rng(7)
SUB = rng.choice(len(seg), size=min(700, len(seg)), replace=False)
M0, U0, L0 = M[SUB], U[SUB], L[SUB]

cands = []
for i, j in itertools.combinations(range(len(M0)), 2):
    p1, q1, p2, q2 = M0[i], U0[i], M0[j], U0[j]
    den = q1[0] * q2[1] - q1[1] * q2[0]
    if abs(den) < 0.05:
        continue
    t = ((p2[0] - p1[0]) * q2[1] - (p2[1] - p1[1]) * q2[0]) / den
    v = p1 + t * q1
    if abs(v[0]) > 80000 or abs(v[1]) > 80000:
        continue
    sel = inliers(v, 1.2)
    if sel.sum() < 6:
        continue
    cands.append((L[sel].sum(), sel.sum(), v))

cands.sort(key=lambda x: -x[0])
print("raw candidates:", len(cands))
found = []
for s, k, v in cands:
    if any(np.linalg.norm(v - w) < 4000 for _, _, w in found):
        continue
    found.append((s, k, v))
    if len(found) >= 6:
        break
out = []
for s, k, v in found:
    vr, n = refine(v.copy())
    sel = inliers(vr, 1.2)
    print(f"VP=({vr[0]:11.1f},{vr[1]:11.1f})  segs={sel.sum():4d} len={L[sel].sum():8.0f}   (raw {k})")
    out.append(vr)
np.save("vp_candidates.npy", np.array(out))
