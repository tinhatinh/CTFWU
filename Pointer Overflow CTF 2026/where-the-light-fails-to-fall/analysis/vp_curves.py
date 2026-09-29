"""Fit the ground vanishing points from long joint curves extracted as connected components."""
import cv2
import numpy as np
from scipy.optimize import minimize

img = cv2.imread("../files/photo.png", cv2.IMREAD_GRAYSCALE)
H, W = img.shape
f = img.astype(np.float32)
lp = cv2.GaussianBlur(f, (0, 0), 220)
hp = f - lp
loc = np.sqrt(cv2.GaussianBlur(hp * hp, (0, 0), 120)) + 1e-3
dark = (hp < -0.45 * loc).astype(np.uint8)
dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
yy, xx = np.mgrid[0:H, 0:W]
valid = np.ones((H, W), np.uint8)
valid[yy < np.maximum(0.0, 0.1818 * (xx - 780)) + 60] = 0
valid[:60, :] = 0
cv2.rectangle(valid, (760, 1280), (2640, 3060), 0, -1)
dark *= valid
cv2.imwrite("dark_comp.png", dark * 255)

n, lab, st, cent = cv2.connectedComponentsWithStats(dark, 8)
print("components:", n - 1)
lines = []
for i in range(1, n):
    x, y, w, h, a = st[i]
    if a < 1200 or w < 260:
        continue
    m = (lab == i)
    ys, xs = np.nonzero(m)
    P = np.stack([xs, ys], 1).astype(np.float64)
    # total least squares line through the component
    c = P.mean(0)
    q = P - c
    u, s, vt = np.linalg.svd(q, full_matrices=False)
    d = vt[0]
    nrm = np.array([-d[1], d[0]])
    t = q @ d
    # keep only components that are genuinely thin (a joint, not a blob)
    thick = float(np.percentile(np.abs(q @ nrm), 90))
    if thick > max(22, 0.10 * w):
        continue
    ang = np.degrees(np.arctan2(d[1], d[0])) % 180
    lines.append((c[0], c[1], ang, float(t.max() - t.min()), thick, i))

lines = np.array(lines)
print("long thin joint curves:", len(lines))
for lo, hi in ((0, 50), (50, 100), (100, 140), (140, 180)):
    m = (lines[:, 2] >= lo) & (lines[:, 2] < hi)
    if m.sum():
        print(f"   angle {lo}-{hi}: n={m.sum():3d} median span={np.median(lines[m,3]):6.0f}")
np.save("jointcurves.npy", lines)

P = lines[:, 0:2]
g = np.radians(lines[:, 2])
U = np.stack([np.cos(g), np.sin(g)], 1)
WT = lines[:, 3]
C = np.array([1500.0, 2000.0])


def obj(v, sel):
    dv = P[sel] - v
    r = np.maximum(np.linalg.norm(dv, axis=1), 1.0)
    s = np.abs(dv[:, 0] * U[sel][:, 1] - dv[:, 1] * U[sel][:, 0]) / r
    return float((WT[sel] * np.degrees(np.arcsin(np.clip(s, -1, 1))) ** 2).sum())


def fit(v0, sel):
    d = v0 - C
    z0 = [np.arctan2(d[1], d[0]), np.log(max(np.linalg.norm(d), 60))]
    best = None
    for scale in (0.1, 0.5, 2.0, 10.0):
        z = [z0[0], np.log(max(np.linalg.norm(d) * scale, 60))]
        r = minimize(lambda z: obj(C + np.exp(z[1]) * np.array([np.cos(z[0]), np.sin(z[0])]), sel),
                     z, method="Powell", options=dict(xtol=1e-7, ftol=1e-12, maxiter=60000))
        if best is None or r.fun < best.fun:
            best = r
    return C + np.exp(best.x[1]) * np.array([np.cos(best.x[0]), np.sin(best.x[0])])


# two-cluster EM on the curve directions
lab2 = (lines[:, 2] > 90).astype(int)
for it in range(8):
    V = []
    for k in (0, 1):
        sel = lab2 == k
        if sel.sum() < 6:
            V.append(np.array([1500.0, -50000.0]))
            continue
        v = fit(np.array([1500.0 if k else -30000.0, -5000.0 if k else -20000.0]), sel)
        # drop curves whose residual is in the worst 20% and refit
        dv = P[sel] - v
        r = np.maximum(np.linalg.norm(dv, axis=1), 1)
        res = np.degrees(np.arcsin(np.clip(np.abs(dv[:, 0] * U[sel][:, 1] - dv[:, 1] * U[sel][:, 0]) / r, -1, 1)))
        keep = res <= np.percentile(res, 80)
        s2 = np.zeros(len(lines), bool); s2[np.where(sel)[0]] = keep
        V.append(fit(v, s2))
    r0, r1 = obj(V[0], np.ones(len(lines), bool)), obj(V[1], np.ones(len(lines), bool))
    dv0, dv1 = P - V[0], P - V[1]
    a0 = np.degrees(np.arcsin(np.clip(np.abs(dv0[:, 0] * U[:, 1] - dv0[:, 1] * U[:, 0]) /
                                      np.maximum(np.linalg.norm(dv0, axis=1), 1), -1, 1)))
    a1 = np.degrees(np.arcsin(np.clip(np.abs(dv1[:, 0] * U[:, 1] - dv1[:, 1] * U[:, 0]) /
                                      np.maximum(np.linalg.norm(dv1, axis=1), 1), -1, 1)))
    new = (a1 < a0).astype(int)
    print(f"it{it}: A n={(new==0).sum():3d} VP=({V[0][0]:11.1f},{V[0][1]:10.1f}) med res={np.median(np.minimum(a0,a1)[new==0]):5.2f}"
          f"   B n={(new==1).sum():3d} VP=({V[1][0]:11.1f},{V[1][1]:10.1f}) med res={np.median(np.minimum(a0,a1)[new==1]):5.2f}")
    if (new == lab2).all():
        break
    lab2 = new
np.save("vp_curves.npy", np.stack(V))
np.save("vp_curves_lab.npy", lab2)
