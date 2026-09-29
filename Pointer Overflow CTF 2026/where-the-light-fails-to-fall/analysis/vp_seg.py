"""Score candidate vanishing points over long joint segments with a sharp angular kernel."""
import cv2
import numpy as np

img = cv2.imread("../files/photo.png", cv2.IMREAD_GRAYSCALE)
H, W = img.shape
bh = cv2.morphologyEx(img, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31)))
bh = cv2.GaussianBlur(bh.astype(np.float32), (5, 5), 0)
edges = cv2.Canny(bh.astype(np.uint8), 30, 90)
yy, xx = np.mgrid[0:H, 0:W]
keep = np.ones((H, W), bool)
keep[yy < np.maximum(0.0, 0.1818 * (xx - 780)) + 40] = False
keep[:60, :] = False
cv2.rectangle(keep, (820, 1330), (2600, 3020), False, -1)
edges[~keep] = 0

seg = cv2.HoughLinesP(edges, 1, np.pi / 1800, threshold=70, minLineLength=170, maxLineGap=18)
seg = np.asarray(seg).reshape(-1, 4).astype(np.float64)
d = seg[:, 2:4] - seg[:, 0:2]
L = np.hypot(d[:, 0], d[:, 1])
M = (seg[:, 0:2] + seg[:, 2:4]) / 2
U = d / L[:, None]
print("segments:", len(seg), "median len", np.median(L))
mx, my, ux, uy = M[:, 0], M[:, 1], U[:, 0], U[:, 1]

SIG = 0.9          # degrees
LS = np.log(10.0)  # scale for the kernel


def score(VX, VY):
    """VX,VY broadcastable -> score array."""
    vx = np.atleast_1d(VX)[:, None]
    vy = np.atleast_1d(VY)[:, None]
    rx, ry = mx[None, :] - vx, my[None, :] - vy
    r = np.maximum(np.hypot(rx, ry), 1.0)
    s = np.abs(rx * uy[None, :] - ry * ux[None, :]) / r          # |sin(angle)|
    ang = 57.29578 * s                                           # deg, small-angle
    return ((np.exp(-(ang / SIG) ** 2) * L[None, :]).sum(1))


XG = np.linspace(-60000, 80000, 281)
YG = np.linspace(-80000, 4000, 281)
S = np.empty((len(YG), len(XG)))
for i, vy in enumerate(YG):
    S[i] = score(XG, np.array([vy]))
print("max %.1f min %.1f" % (S.max(), S.min()))
np.save("seg_coh.npy", S)

flat = np.argsort(S.ravel())[::-1]
found = []
for k in flat:
    i, j = divmod(k, S.shape[1])
    v = np.array([XG[j], YG[i]])
    if any(np.linalg.norm(v - f) < 4000 for f in found):
        continue
    found.append(v)
    print(f"   peak {len(found)}: ({v[0]:10.0f},{v[1]:10.0f}) = {S[i,j]:8.1f}")
    if len(found) >= 8:
        break

for v0 in found:
    v = v0.copy()
    cur = score(*v)[0]
    step = 2000.0
    while step > 1.0:
        mv = None
        for dx in (-step, 0, step):
            for dy in (-step, 0, step):
                s = score(np.array([v[0] + dx]), np.array([v[1] + dy]))[0]
                if s > cur + 1e-9:
                    cur, mv = s, v + np.array([dx, dy])
        if mv is None:
            step *= 0.5
        else:
            v = mv
    rx, ry = mx - v[0], my - v[1]
    r = np.maximum(np.hypot(rx, ry), 1)
    ang = np.degrees(np.arcsin(np.clip(np.abs(rx * uy - ry * ux) / r, -1, 1)))
    sel = ang < 0.9
    print(f"polished ({v[0]:11.1f},{v[1]:11.1f}) score={cur:7.1f} nseg={sel.sum():4d} len={L[sel].sum():7.0f}")
    np.save("seg_peaks.npy", np.array(found))
