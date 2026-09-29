import math
import numpy as np
import cv2

img = cv2.imread("files/photo.png")
H, W = img.shape[:2]
g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

th = cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 151, 9)
ok = np.zeros((H, W), np.uint8)
cv2.rectangle(ok, (0, 900), (W, 3000), 255, -1)
th = cv2.bitwise_and(th, ok)
e = cv2.Canny(th, 30, 90)
L = cv2.HoughLinesP(e, 1, np.pi / 360, threshold=60, minLineLength=120, maxLineGap=20).reshape(-1, 4).astype(float)
ang = (np.degrees(np.arctan2(L[:, 3] - L[:, 1], L[:, 2] - L[:, 0])) + 180) % 180
hist, ed = np.histogram(ang, bins=72, range=(0, 180))
order = np.argsort(hist)[::-1]
a1 = ed[order[0]] + 1.25
fam = [a1, None]
for i in order[1:]:
    c = ed[i] + 1.25
    if min(abs(c - a1), 180 - abs(c - a1)) > 25 and hist[i] > hist.max() * 0.30:
        fam[1] = c
        break
print("segments", len(L), "families", [round(x, 1) for x in fam])


def cdist(x, c):
    d = np.abs(x - c)
    return np.minimum(d, 180 - d)


def vanishing(segs):
    A, b = [], []
    for x1, y1, x2, y2 in segs:
        a, bb, cc = (y2 - y1), (x1 - x2), x2 * y1 - x1 * y2
        n = math.hypot(a, bb)
        A.append([a / n, bb / n])
        b.append(-cc / n)
    sol, res, rank, sv = np.linalg.lstsq(np.array(A), np.array(b), rcond=None)
    resid = float(np.mean(np.abs(np.array(A) @ sol - np.array(b)))) if len(A) else float("inf")
    return sol, resid, len(segs)


vs = []
for f0 in fam:
    s = L[cdist(ang, f0) < 10]
    v, resid, n = vanishing(s)
    vs.append(v)
    print("family %.0f deg: %4d segs, VP rel-centre=(%9.1f,%9.1f), mean resid %.2f px"
          % (f0, n, v[0], v[1], resid))

v1 = np.array([vs[0][0], vs[0][1], 1.0])
v2 = np.array([vs[1][0], vs[1][1], 1.0])
f2 = -(v1[0] * v2[0] + v1[1] * v2[1]) / (v1[2] * v2[2])
f = math.sqrt(f2) if f2 > 0 else float("nan")
print("focal from orthogonality: %.1f px" % f)

cx, cy = W / 2, H / 2
K = np.array([[f, 0, cx], [0, f, cy], [0, 0, 1]])
Ki = np.linalg.inv(K)
d1 = Ki @ v1; d1 /= np.linalg.norm(d1)
d2 = Ki @ v2; d2 /= np.linalg.norm(d2)
n = np.cross(d1, d2); n /= np.linalg.norm(n)
R = np.stack([d1, np.cross(n, d1), n], axis=1)
Hh = K @ R
elev = math.degrees(math.asin(np.linalg.norm(n[:2])))
print("ground-plane normal (cam):", np.round(n, 3), " camera elevation above ground: %.1f deg" % elev)
np.save("analysis/calib.npy", {"H": Hh, "K": K, "R": R, "f": f, "fam": fam, "vps": [v1, v2]}, allow_pickle=True)

out = cv2.warpPerspective(img, Hh, (W, H))
cv2.imwrite("analysis/rectified_small.png", cv2.resize(out, (750, 1000)))
print("saved analysis/rectified_small.png")
