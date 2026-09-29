"""Fit the two lattice pencils by minimising the weighted angular residual."""
import cv2
import numpy as np
from scipy.optimize import minimize

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

seg = cv2.HoughLinesP(edges, 1, np.pi / 1800, threshold=80, minLineLength=200, maxLineGap=16)
seg = np.asarray(seg).reshape(-1, 4).astype(np.float64)
d = seg[:, 2:4] - seg[:, 0:2]
L = np.hypot(d[:, 0], d[:, 1])
M = (seg[:, 0:2] + seg[:, 2:4]) / 2
U = d / L[:, None]
A = np.degrees(np.arctan2(U[:, 1], U[:, 0])) % 180
print("segments:", len(seg))


def cost(v, sel):
    dv = v[None, :] - M[sel]
    n = np.linalg.norm(dv, axis=1)
    s = (dv[:, 0] * U[sel][:, 1] - dv[:, 1] * U[sel][:, 0]) / np.maximum(n, 1e-6)
    return float((L[sel] * np.arcsin(np.clip(s, -1, 1)) ** 2).sum())


def fit(v0, sel):
    # parameterise as an angle + radius so the optimiser can move to infinity
    def unpack(z):
        return np.array([W / 2, H / 2]) + np.array([np.cos(z[0]), np.sin(z[0])]) * np.exp(z[1])

    def f(z):
        return cost(unpack(z), sel)

    r0 = np.linalg.norm(v0 - np.array([W / 2, H / 2]))
    z0 = [np.arctan2(*(v0 - np.array([W / 2, H / 2]))[::-1]), np.log(max(r0, 10))]
    res = minimize(f, z0, method="Powell", options=dict(xtol=1e-6, ftol=1e-9, maxiter=20000))
    return unpack(res.x), res.fun


# seed families by orientation
selA = (A > 55) & (A < 125)          # steep, "up the image" joints
selB = ~selA
print("seed sizes:", selA.sum(), selB.sum())
vA = np.array([W / 2, -20000.0])
vB = np.array([-20000.0, -5000.0])
for it in range(8):
    vA, cA = fit(vA, selA)
    vB, cB = fit(vB, selB)
    # reassign: a segment belongs to the pencil whose direction it matches
    def resid(sel, v):
        dv = v[None, :] - M[sel]
        n = np.linalg.norm(dv, axis=1)
        s = (dv[:, 0] * U[sel][:, 1] - dv[:, 1] * U[sel][:, 0]) / np.maximum(n, 1e-6)
        return np.abs(np.arcsin(np.clip(s, -1, 1)))
    rA = np.full(len(seg), 9.9)
    rB = np.full(len(seg), 9.9)
    rA[np.where(selA)[0]] = resid(selA, vA)
    rB[np.where(selB)[0]] = resid(selB, vB)
    na = rA < rB
    if (na == selA).all():
        break
    selA, selB = na, ~na
    print(f"iter {it}: A={selA.sum()} B={selB.sum()}")

for nm, sel, v, c in (("A", selA, vA, cost(vA, selA)), ("B", selB, vB, cost(vB, selB))):
    rms = np.sqrt(cost(v, sel) / L[sel].sum())
    print(f"family {nm}: n={sel.sum()} len={L[sel].sum():.0f} VP=({v[0]:11.1f},{v[1]:11.1f}) rms_ang={np.degrees(rms):.3f} deg")
np.save("vp2.npy", np.stack([vA, vB]))
np.save("sel2.npy", np.stack([selA, selB]))

vis = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
for s, a, b in zip(seg, selA, selB):
    cv2.line(vis, tuple(s[:2].astype(int)), tuple(s[2:].astype(int)), (255, 60, 60) if a else (60, 60, 255), 3)
for v, col in ((vA, (0, 255, 0)), (vB, (0, 255, 255))):
    for t in np.linspace(0, 1, 40):
        p = v + (np.array([W / 2, H / 2]) - v) * t
        cv2.circle(vis, tuple(p.astype(int)), 4, col, -1)
cv2.imwrite("vp2.png", cv2.resize(vis, (750, 1000)))
