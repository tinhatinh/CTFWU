"""High-pass the image so the lighting ramp cannot masquerade as an edge orientation,
then map how each joint family's direction varies with position."""
import cv2
import numpy as np

img = cv2.imread("../files/photo.png", cv2.IMREAD_GRAYSCALE).astype(np.float32)
H, W = img.shape

# remove the illumination ramp: subtract a very large-scale smooth version
lp = cv2.GaussianBlur(img, (0, 0), 180)
hp = img - lp
# equalise contrast so bright foreground and dark shadow contribute equally
loc = np.sqrt(cv2.GaussianBlur(hp * hp, (0, 0), 120)) + 1e-3
norm = np.clip(hp / (2.5 * loc), -1, 1)
dark = cv2.normalize((-norm * 255).astype(np.int16), None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
edges = cv2.Canny(cv2.GaussianBlur(dark, (5, 5), 0), 45, 120)

yy, xx = np.mgrid[0:H, 0:W]
keep = np.ones((H, W), bool)
keep[yy < np.maximum(0.0, 0.1818 * (xx - 780)) + 40] = False
keep[:60, :] = False
cv2.rectangle(keep, (780, 1300), (2620, 3050), False, -1)
edges[~keep] = 0
cv2.imwrite("edges_hp.png", cv2.resize(edges, (750, 1000)))

seg = cv2.HoughLinesP(edges, 1, np.pi / 1800, threshold=60, minLineLength=150, maxLineGap=12)
seg = np.asarray(seg).reshape(-1, 4).astype(np.float64)
d = seg[:, 2:4] - seg[:, 0:2]
L = np.hypot(*d.T)
M = (seg[:, 0:2] + seg[:, 2:4]) / 2
A = (np.degrees(np.arctan2(d[:, 1], d[:, 0])) + 180) % 180
print("segments:", len(seg), " len p50/p90:", np.percentile(L, [50, 90]).round(0))
np.save("segs_hp.npy", np.column_stack([M, A, L]))

print("\ndirection distribution by band (deg, y-down), weighted by length:")
for lo, hi in ((60, 700), (700, 1400), (1400, 2100), (2100, 2800), (2800, 3400), (3400, 3990)):
    m = (M[:, 1] >= lo) & (M[:, 1] < hi) & (L > 150)
    if m.sum() < 5:
        continue
    h, e = np.histogram(A[m], bins=36, range=(0, 180), weights=L[m])
    top = np.argsort(h)[::-1][:4]
    s = "  ".join(f"{0.5*(e[i]+e[i+1]):5.1f}:{h[i]/h.sum()*100:4.1f}%" for i in top)
    print(f"  y {lo:4d}-{hi:4d}  n={m.sum():4d}   {s}")

print("\ndirection distribution by column band:")
for lo, hi in ((60, 700), (700, 1400), (1400, 2100), (2100, 2800), (2800, 3400), (3400, 3990)):
    for xl, xh in ((60, 800), (2200, 2960)):
        m = (M[:, 1] >= lo) & (M[:, 1] < hi) & (M[:, 0] >= xl) & (M[:, 0] < xh) & (L > 150)
        if m.sum() < 5:
            continue
        h, e = np.histogram(A[m], bins=36, range=(0, 180), weights=L[m])
        i = np.argmax(h)
        print(f"  y {lo:4d}-{hi:4d} x {xl:4d}-{xh:4d}  n={m.sum():4d}  dominant {0.5*(e[i]+e[i+1]):5.1f} deg")
