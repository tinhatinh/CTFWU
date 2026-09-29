import math
import numpy as np
import cv2
from scipy import ndimage

img = cv2.imread("files/photo.png")
H, W = img.shape[:2]
R = img[:, :, 2].astype(float)      # BGR
G = img[:, :, 1].astype(float)
B = img[:, :, 0].astype(float)

# ---------- arrow: longest red component, fit a line ----------
red = ((R > 120) & (R - G > 60) & (R - B > 60)).astype(np.uint8)
red[:2950, :] = 0
lab, n = ndimage.label(red)
sizes = ndimage.sum(red, lab, range(1, n + 1))
big = int(np.argmax(sizes)) + 1
ys, xs = np.where(lab == big)
pts = np.stack([xs, ys], 1).astype(np.float32)
vx, vy, x0, y0 = cv2.fitLine(pts, cv2.DIST_L2, 0, 0.01, 0.01).ravel()
print("arrow component px", len(xs), "bbox x", xs.min(), xs.max(), "y", ys.min(), ys.max())
print("arrow unit dir (x, y-down):", round(float(vx), 4), round(float(vy), 4),
      "angle from +x:", round(math.degrees(math.atan2(float(vy), float(vx))), 2))
# orient toward the N label: the label is the dense blob near (480,3080)
if x0 > 1500:
    vx, vy = -vx, -vy
north = np.array([vx, -vy])            # convert to y-up
north /= np.linalg.norm(north)
print("north (x, y-up):", np.round(north, 4))

# ---------- bird feet (pink) -> ground contact ----------
pink = ((R > 140) & (R - G > 55) & (R - B > 45) & (G < 130)).astype(np.uint8)
pink[:1800, :] = 0
pink[3000:, :] = 0
pf = np.argwhere(pink)
print("pink px:", len(pf))
if len(pf):
    contact = pf.mean(0)[::-1].astype(float)          # (x, y)
    print("contact point (x,y):", np.round(contact, 1))
else:
    contact = np.array([1400.0, 2600.0])

# ---------- shadow tip ----------
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
blur = cv2.GaussianBlur(gray, (0, 0), 45)
warm = R - B
sh = (blur < np.percentile(blur[1500:3000, :], 30)) & (warm < np.median(warm[1500:3000, :]))
sh[:1500] = False; sh[2900:] = False; sh[:, :1200] = False
lab2, n2 = ndimage.label(sh)
s2 = ndimage.sum(sh, lab2, range(1, n2 + 1))
m = lab2 == (int(np.argmax(s2)) + 1)
ys2, xs2 = np.where(m)
Q = np.stack([xs2, ys2], 1).astype(float)
# tip = farthest point from the contact
d = ((Q - contact) ** 2).sum(1)
tip = Q[np.argmax(d)]
shadow = tip - contact
shadow_up = np.array([shadow[0], -shadow[1]])
shadow_up /= np.linalg.norm(shadow_up)
print("shadow tip:", np.round(tip, 1), "length px", round(float(np.hypot(*shadow)), 1))
print("shadow dir (x, y-up):", np.round(shadow_up, 4),
      "angle from +x:", round(math.degrees(math.atan2(shadow_up[1], shadow_up[0])), 2))

# ---------- bearings ----------
def bearing(v):
    return math.degrees(math.atan2(v[0], v[1])) % 360      # from +y-up (screen 'up'), clockwise


bn, bs = bearing(north), bearing(shadow_up)
print("\nnorth bearing in image frame: %.1f, shadow bearing: %.1f" % (bn, bs))
rel = (bs - bn) % 360
print("shadow is %.1f deg clockwise from north (naive, image plane)" % rel)
print("=> sun azimuth (naive) = %.1f" % ((rel + 180) % 360))

# foreshortening-corrected family: assume ground compression s along image-up
print("\ns-units corrected sun azimuth:")
for s in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
    # recover camera heading psi from the arrow:  tan(screen angle from up) = sin(-psi)/(s cos(-psi))
    ax, ay = north[0], north[1]
    psi = math.atan2(-ax, -ay * s)              # camera forward bearing
    sx, sy = shadow_up[0], shadow_up[1]
    ang = math.atan2(sx, sy * s)
    b = (psi + math.degrees(ang)) % 360
    print("   s=%.1f -> shadow bearing %.1f, sun azimuth %.1f" % (s, b, (b + 180) % 360))
