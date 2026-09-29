"""Both lattice vanishing points from the radial-gradient constraint g.(p - v) = 0,
which is linear in v, followed by an angular-refinement pattern search."""
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

STEP = 6
sub = (slice(None, None, STEP), slice(None, None, STEP))
ys, xs = np.nonzero(keep[sub])
px = (xs * STEP).astype(np.float64)
py = (ys * STEP).astype(np.float64)
gx = gxx[sub][ys, xs].astype(np.float64)
gy = gyy[sub][ys, xs].astype(np.float64)
m2 = mag[sub][ys, xs].astype(np.float64)
n = np.maximum(np.hypot(gx, gy), 1e-6)
gx, gy = gx / n, gy / n
w = np.clip(m2, 0, np.percentile(m2, 98)) ** 2
ok = w > np.percentile(w, 60)
P = np.stack([px, py], 1)[ok]
G = np.stack([gx, gy], 1)[ok]
Wt = w[ok]
print("samples:", len(P))


def linear_vp(G, P, Wt, mask=None):
    m = np.ones(len(P), bool) if mask is None else mask
    g, p, q = G[m], P[m], np.sqrt(Wt[m])
    A = (g[:, :, None] * g[:, None, :]) * q[:, None, None]
    b = (g * (g * p).sum(1)[:, None]) * q[:, None]
    return np.linalg.solve(A.sum(0), b.sum(0))


def ang_res(v):
    dv = P - v
    r = np.maximum(np.linalg.norm(dv, axis=1), 1.0)
    c = np.abs(dv[:, 0] * G[:, 1] - dv[:, 1] * G[:, 0]) / r
    return np.degrees(np.arcsin(np.clip(c, -1, 1)))


def coherence(v, mask, tol=1.0):
    r = ang_res(v)
    sel = mask & (r < tol)
    return float(Wt[sel].sum() / max(Wt[mask].sum(), 1e-9)), sel.sum()


def polish(v0, mask, tol=1.0):
    v = v0.copy()
    cur, _ = coherence(v, mask, tol)
    step = max(200.0, 0.02 * np.linalg.norm(v - P.mean(0)))
    while step > 0.5:
        mv = None
        for dx in (-step, 0, step):
            for dy in (-step, 0, step):
                s, _ = coherence(v + np.array([dx, dy]), mask, tol)
                if s > cur + 1e-12:
                    cur, mv = s, v + np.array([dx, dy])
        if mv is None:
            step *= 0.5
        else:
            v = mv
    return v, cur


# ---- family A: iterate the linear fit with residual rejection ----
mask = np.ones(len(P), bool)
for it in range(6):
    v = linear_vp(G, P, Wt, mask)
    r = ang_res(v)
    keepm = r < 1.5
    print(f"A it{it}: VP=({v[0]:10.1f},{v[1]:10.1f}) inliers={keepm.sum()}")
    mask = keepm
vA, cA = polish(linear_vp(G, P, Wt, mask), mask)
print(f"VP_A = ({vA[0]:.1f}, {vA[1]:.1f})  coherence={cA:.4f}  n={(ang_res(vA)<1.0).sum()}")

# ---- family B: exclude A's radial samples, then the same ----
rA = ang_res(vA)
maskB = rA > 2.0
print("B candidates:", maskB.sum())
for it in range(6):
    v = linear_vp(G, P, Wt, maskB)
    r = ang_res(v)
    maskB = maskB & (r < 2.0)
    print(f"B it{it}: VP=({v[0]:10.1f},{v[1]:10.1f}) inliers={maskB.sum()}")
vB0 = linear_vp(G, P, Wt, maskB)
vB, cB = polish(vB0, maskB)
print(f"VP_B = ({vB[0]:.1f}, {vB[1]:.1f})  coherence={cB:.4f}  n={(ang_res(vB)<1.0).sum()}")

# joint assignment, then re-polish both
rB = ang_res(vB)
mA = (rA < rB) & (rA < 2.0)
mB = (rB < rA) & (rB < 2.0)
for it in range(6):
    vA, cA = polish(linear_vp(G, P, Wt, mA), mA)
    vB, cB = polish(linear_vp(G, P, Wt, mB), mB)
    rA, rB = ang_res(vA), ang_res(vB)
    nA = (rA < rB) & (rA < 2.0)
    nB = (rB < rA) & (rB < 2.0)
    print(f"joint it{it}: A n={nA.sum()} c={cA:.4f} VP=({vA[0]:10.1f},{vA[1]:10.1f})   "
          f"B n={nB.sum()} c={cB:.4f} VP=({vB[0]:10.1f},{vB[1]:10.1f})")
    if (nA == mA).all():
        break
    mA, mB = nA, nB
np.save("vp_final.npy", np.stack([vA, vB]))

vis = cv2.cvtColor(cv2.GaussianBlur(img, (5, 5), 0), cv2.COLOR_GRAY2BGR)
vis = cv2.resize(vis, (W // 4, H // 4))
for p, a, b in zip(P, mA, mB):
    cv2.circle(vis, (int(p[0] / 4), int(p[1] / 4)), 2, (0, 255, 0) if a else (0, 120, 255), -1)
cv2.imwrite("vp_assign.png", vis)
