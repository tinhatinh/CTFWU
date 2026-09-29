"""Locate the shadow body, its root at the bird's feet and its tip (head's shadow)."""
import cv2
import numpy as np

img = cv2.imread("../files/photo.png")
g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
H, W = g.shape

# shadow = darker than the local illumination, measured away from the bird/shadow itself
big = cv2.medianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 151).astype(np.float32)
sh = g < 0.80 * big
sh = cv2.morphologyEx(sh.astype(np.uint8), cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
sh = cv2.morphologyEx(sh, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
n, lab, st, cent = cv2.connectedComponentsWithStats(sh, 8)
order = np.argsort(st[1:, cv2.CC_STAT_AREA])[::-1] + 1
print("largest dark components:")
for i in order[:5]:
    x, y, w, h, a = st[i]
    print(f"   #{i} area={a:8d} bbox=({x},{y}) {w}x{h}")

# the shadow is the component whose centroid sits right of the bird (x ~ 1600-2200)
cands = [i for i in order[:6] if 1100 < cent[i][0] < 2600 and 1400 < cent[i][1] < 3000]
idx = max(cands, key=lambda i: st[i, cv2.CC_STAT_AREA])
m = (lab == idx).astype(np.uint8)
ys, xs = np.nonzero(m)
P = np.stack([xs, ys], 1).astype(np.float64)
print(f"\nshadow component #{idx}: {len(P)} px, bbox x {xs.min()}..{xs.max()} y {ys.min()}..{ys.max()}")

feet = np.array([1295.0, 2663.0])          # planted foot (red component #5 centroid)
d = np.linalg.norm(P - feet, axis=1)
root = P[np.argmin(d)]
tip = P[np.argmax(d)]
print(f"root (closest to the feet) = {root.round(1)}   dist={d.min():.0f}")
print(f"tip   (farthest)           = {tip.round(1)}   dist={d.max():.0f}")
v = tip - root
print(f"axis dir y-down ({v[0]/np.linalg.norm(v):+.5f},{v[1]/np.linalg.norm(v):+.5f})  "
      f"len {np.linalg.norm(v):.1f} px")

# extremes along each axis for context
for nm, k in (("x min", np.argmin(P[:, 0])), ("x max", np.argmax(P[:, 0])),
              ("y min", np.argmin(P[:, 1])), ("y max", np.argmax(P[:, 1]))):
    print(f"   {nm}: {P[k].round(0)}")

vis = cv2.resize(img, (W // 3, H // 3))
vis[m.astype(bool)][::3, ::3] = 0
for p, c in ((root, (0, 255, 0)), (tip, (0, 0, 255)), (feet, (255, 0, 255))):
    cv2.circle(vis, tuple((p / 3).astype(int)), 8, c, -1)
cv2.line(vis, tuple((root / 3).astype(int)), tuple((tip / 3).astype(int)), (255, 255, 0), 2)
cv2.imwrite("shadow_pts.png", vis)

np.save("shadow_mask.npy", m)
print("wrote shadow_pts.png")
