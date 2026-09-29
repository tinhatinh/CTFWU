"""Segment the bright sett faces into blobs, then use their centroid lattice to fit the
ground vanishing points and the horizon."""
import cv2
import numpy as np

img = cv2.imread("../files/photo.png", cv2.IMREAD_GRAYSCALE).astype(np.float32)
H, W = img.shape
g = cv2.GaussianBlur(img, (0, 0), 18)
bg = cv2.medianBlur(g.astype(np.uint8), 201).astype(np.float32)
bg = cv2.GaussianBlur(bg, (0, 0), 120)
r = g - bg
sc = cv2.GaussianBlur(np.abs(r), (0, 0), 150) + 1e-3
norm = np.clip(r / (1.05 * sc), -1, 1)
m = (norm > 0.30).astype(np.uint8)
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
yy, xx = np.mgrid[0:H, 0:W]
valid = np.ones((H, W), np.uint8)
valid[yy < np.maximum(0.0, 0.1818 * (xx - 780)) + 60] = 0
valid[:80, :] = 0
cv2.rectangle(valid, (760, 1280), (2640, 3060), 0, -1)
m *= valid
cv2.imwrite("settmask.png", m * 255)

n, lab, st, cent = cv2.connectedComponentsWithStats(m, 8)
keep = []
for i in range(1, n):
    x, y, w, h, a = st[i]
    if a < 1800 or a > 400000:
        continue
    if min(w, h) < 0.35 * max(w, h):
        continue
    if w > 1.9 * h or h > 1.9 * w:
        continue
    keep.append((cent[i][0], cent[i][1], a, w, h))
K = np.array(keep)
print("sett blobs:", len(K))
np.save("setts.npy", K)

vis = cv2.cvtColor(cv2.GaussianBlur(img.astype(np.uint8), (5, 5), 0), cv2.COLOR_GRAY2BGR)
for cx, cy, a, w, h in K:
    cv2.circle(vis, (int(cx), int(cy)), 7, (0, 0, 255), -1)
    cv2.rectangle(vis, (int(cx - np.sqrt(a) / 2), int(cy - np.sqrt(a) / 2)),
                  (int(cx + np.sqrt(a) / 2), int(cy + np.sqrt(a) / 2)), (0, 255, 0), 2)
cv2.imwrite("setts_vis.png", cv2.resize(vis, (W // 3, H // 3)))

# area vs image row -> the horizon (cell area scales as 1/dist^2)
for lo, hi in ((80, 500), (500, 1000), (1000, 1600), (1600, 2200), (2200, 2800),
               (2800, 3300), (3300, 3990)):
    s = (K[:, 1] >= lo) & (K[:, 1] < hi)
    if s.sum() > 3:
        print(f"  y {lo}-{hi}: n={s.sum():4d} sqrt(area) med={np.median(np.sqrt(K[s,2])):7.1f} "
              f"p25={np.percentile(np.sqrt(K[s,2]),25):7.1f} p75={np.percentile(np.sqrt(K[s,2]),75):7.1f}")
