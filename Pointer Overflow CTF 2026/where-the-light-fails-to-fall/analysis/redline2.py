"""Isolate the red overlay components and fit the north stroke exactly."""
import cv2
import numpy as np

img = cv2.imread("../files/photo.png")
R, G, B = img[:, :, 2].astype(np.int16), img[:, :, 1].astype(np.int16), img[:, :, 0].astype(np.int16)
red = ((R > 120) & (R - G > 55) & (R - B > 55)).astype(np.uint8) * 255
n, lab, st, cent = cv2.connectedComponentsWithStats(red, 8)
print("components:", n - 1)
order = np.argsort(st[1:, cv2.CC_STAT_AREA])[::-1]
for r in order[:8]:
    i = r + 1
    x, y, w, h, a = st[i]
    print(f"  #{i}: area={a:7d} bbox=({x},{y}) {w}x{h} centroid=({cent[i][0]:.0f},{cent[i][1]:.0f})")

big = order[0] + 1
m = (lab == big)
ys, xs = np.nonzero(m)
P = np.stack([xs, ys], 1).astype(np.float64)
print("\nlargest component pixels:", len(P))
v = P.mean(0)
for it in range(8):
    q = P - v
    u, s, vt = np.linalg.svd(q, full_matrices=False)
    d = vt[0]
    nrm = np.array([-d[1], d[0]])
    perp = np.abs(q @ nrm)
    inl = perp < max(4.0, np.percentile(perp, 90))
    v = P[inl].mean(0)
    t = (P[inl] - v) @ d
    print(f"  it{it}: inl={inl.sum():6d} dir=({d[0]:+.5f},{d[1]:+.5f}) "
          f"ends=({(v+t.min()*d)[0]:7.1f},{(v+t.min()*d)[1]:7.1f})->({(v+t.max()*d)[0]:7.1f},{(v+t.max()*d)[1]:7.1f})")
    resid = np.abs((P[inl] - v) @ np.array([-d[1], d[0]]))
q = P - v
d = vt[0]
if d[1] > 0:
    d = -d
print(f"\nnorth stroke unit dir  y-down = ({d[0]:+.5f},{d[1]:+.5f})   y-up = ({d[0]:+.5f},{-d[1]:+.5f})")
print(f"image angle of the arrow (pointing end = smaller y): {np.degrees(np.arctan2(-d[1], d[0])):.3f} deg from +x")
print(f"thickness: 90th pct perpendicular spread = {np.percentile(np.abs(q @ np.array([-d[1], d[0]])), 90):.1f} px")

vis = np.zeros_like(img)
vis[m] = (0, 0, 255)
cv2.imwrite("red_only.png", cv2.resize(vis, (750, 1000)))
