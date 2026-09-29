"""Map the shadow region and find its tip; visualise so the extent can be confirmed."""
import cv2
import numpy as np

img = cv2.imread("../files/photo.png")
H, W = img.shape[:2]
g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
bg = cv2.GaussianBlur(g, (0, 0), 400)
gb = cv2.GaussianBlur(g, (0, 0), 120)          # erase the joints, keep the shadow's extent
ratio = gb / (bg + 1e-3)

yy, xx = np.mgrid[0:H, 0:W]
zone = np.zeros((H, W), bool)
cv2.rectangle(zone.astype(np.uint8), (0, 0), (0, 0), 1, -1)
zone = (xx > 1250) & (xx < 2900) & (yy > 1450) & (yy < 3050)
# exclude the bird's own body
bird = ((xx - 1350) ** 2 / 520 ** 2 + (yy - 2230) ** 2 / 480 ** 2) < 1.0
zone &= ~bird

for th in (0.82, 0.86, 0.90):
    sh = ((ratio < th) & zone).astype(np.uint8)
    sh = cv2.morphologyEx(sh, cv2.MORPH_OPEN, np.ones((13, 13), np.uint8))
    sh = cv2.morphologyEx(sh, cv2.MORPH_CLOSE, np.ones((35, 35), np.uint8))
    ys, xs = np.nonzero(sh)
    if len(xs) < 500:
        continue
    P = np.stack([xs, ys], 1).astype(np.float64)
    feet = np.array([1290.0, 2705.0])
    d = np.linalg.norm(P - feet, axis=1)
    tip = P[np.argmax(d)]
    print(f"th={th}: px={len(P):7d}  tip={tip.round(0)} dist={d.max():.0f}  "
          f"x max={P[:,0].max():.0f} y min={P[:,1].min():.0f}")
    if th == 0.86:
        ov = img.copy()
        ov[sh.astype(bool)] = (0, 0, 255)
        cv2.circle(ov, tuple(feet.astype(int)), 14, (0, 255, 0), -1)
        cv2.circle(ov, tuple(tip.astype(int)), 14, (255, 0, 255), -1)
        cv2.imwrite("shadow_ov.png", cv2.resize(ov, (W // 2, H // 2)))

sh = ((ratio < 0.86) & zone).astype(np.uint8)
sh = cv2.morphologyEx(sh, cv2.MORPH_OPEN, np.ones((13, 13), np.uint8))
sh = cv2.morphologyEx(sh, cv2.MORPH_CLOSE, np.ones((35, 35), np.uint8))
ys, xs = np.nonzero(sh)
P = np.stack([xs, ys], 1).astype(np.float64)
feet = np.array([1290.0, 2705.0])
# extreme along each candidate axis direction
for ang in np.arange(30, 55, 2.5):
    u = np.array([np.cos(np.radians(ang)), -np.sin(np.radians(ang))])
    t = (P - feet) @ u
    k = np.argmax(t)
    print(f"  axis {ang:5.1f} deg: max extent {t.max():7.1f} px at {P[k].round(0)}")
v = P[np.argmax(np.linalg.norm(P - feet, axis=1))] - feet
print(f"\nshadow vector = {v.round(1)}  len {np.linalg.norm(v):.1f}  "
      f"image angle {np.degrees(np.arctan2(-v[1], v[0])):.2f} deg")
