"""Precise pixel measurements: pigeon crown, planted foot, shadow root and tip."""
import cv2
import numpy as np

img = cv2.imread("../files/photo.png")
H, W = img.shape[:2]
g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)

# ---------- the pigeon: isolate it with the local colour/edge structure ----------
# the bird occupies roughly x 950..1830, y 1640..2800; find its topmost silhouette pixel
sub = g[1500:2000, 900:1350]
lp = cv2.GaussianBlur(sub, (0, 0), 60)
edge = cv2.Canny(cv2.GaussianBlur(sub.astype(np.uint8), (5, 5), 0), 40, 110)
top_rows = []
for x in range(0, sub.shape[1], 2):
    col = np.nonzero(edge[:, x])[0]
    if len(col):
        top_rows.append((x + 900, col[0] + 1500))
top_rows.sort(key=lambda t: t[1])
print("topmost silhouette samples (x, y):", top_rows[:12])
crown_y = np.median([t[1] for t in top_rows[:8]])
crown_x = np.median([t[0] for t in top_rows[:8]])
print(f"crown ~ ({crown_x:.0f}, {crown_y:.0f})")

# ---------- the shadow mask ----------
bg = cv2.GaussianBlur(g, (0, 0), 300)
ratio = g / (bg + 1e-3)
sh = (ratio < 0.80).astype(np.uint8)
sh = cv2.morphologyEx(sh, cv2.MORPH_OPEN, np.ones((15, 15), np.uint8))
sh = cv2.morphologyEx(sh, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
zone = np.zeros_like(sh)
cv2.rectangle(zone, (1300, 1450), (2700, 3000), 1, -1)
sh *= zone
n, lab, st, cent = cv2.connectedComponentsWithStats(sh, 8)
o = np.argsort(st[1:, cv2.CC_STAT_AREA])[::-1] + 1
print("\nshadow components:")
for i in o[:5]:
    x, y, w, h, a = st[i]
    print(f"   #{i} area={a:8d} bbox=({x},{y}) {w}x{h} centroid=({cent[i][0]:.0f},{cent[i][1]:.0f})")
big = o[0]
m = (lab == big)
ys, xs = np.nonzero(m)
P = np.stack([xs, ys], 1).astype(np.float64)
feet = np.array([1290.0, 2705.0])
d = np.linalg.norm(P - feet, axis=1)
tip = P[np.argmax(d)]
root = P[np.argmin(d)]
print(f"\nshadow blob: {len(P)} px")
print(f"root  = {root.round(1)}  (dist {d.min():.0f})")
print(f"tip   = {tip.round(1)}  (dist {d.max():.0f})")
v = tip - feet
print(f"shadow vector from the feet: ({v[0]:.1f}, {v[1]:.1f})  len {np.linalg.norm(v):.1f}"
      f"  image angle (y-up) {np.degrees(np.arctan2(-v[1], v[0])):.3f} deg")

# principal axis of the blob for reference
c = P.mean(0)
u, s, vt = np.linalg.svd(P - c, full_matrices=False)
print(f"blob principal axis: ({vt[0][0]:+.4f},{vt[0][1]:+.4f})  extent {s[0]/np.sqrt(len(P)):.0f}")

# ---------- the north line ----------
N = np.array([-0.92429, 0.38169])           # y-up, measured from the red stroke
S = np.array([v[0], -v[1]]) / np.linalg.norm([v[0], -v[1]])
bearing = np.degrees(np.arctan2(S[0] * N[1] - S[1] * N[0], S @ N))
print(f"\nangle from north to the shadow, clockwise in the image: {bearing:.2f} deg")
print(f"  -> sun azimuth (naive flat reading) = {(bearing + 180) % 360:.2f} deg")
h_bird = 2705.0 - crown_y
print(f"bird image height = {h_bird:.1f} px, shadow = {np.linalg.norm(v):.1f} px"
      f"  -> sun altitude (naive) = {np.degrees(np.arctan(h_bird/np.linalg.norm(v))):.2f} deg")

vis = img.copy()
cv2.circle(vis, (int(crown_x), int(crown_y)), 10, (0, 255, 0), -1)
cv2.circle(vis, tuple(feet.astype(int)), 10, (255, 0, 255), -1)
cv2.circle(vis, tuple(tip.astype(int)), 10, (0, 0, 255), -1)
cv2.line(vis, tuple(feet.astype(int)), tuple(tip.astype(int)), (0, 255, 255), 4)
cv2.line(vis, tuple(feet.astype(int)), (int(crown_x), int(crown_y)), (255, 255, 0), 4)
cv2.imwrite("meas.png", cv2.resize(vis, (W // 3, H // 3)))
np.save("meas.npy", np.array([crown_x, crown_y, feet[0], feet[1], tip[0], tip[1], root[0], root[1]]))
