import math
import numpy as np
from PIL import Image
from scipy import ndimage

im = Image.open("files/photo.png").convert("RGB")
a = np.asarray(im).astype(float)
H, W = a.shape[:2]
R, G, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]
lum = 0.299 * R + 0.587 * G + 0.114 * B

# ---------- 1. north arrow (red, below the bird) ----------
red = (R > 120) & (R - G > 60) & (R - B > 60)
red[:2950, :] = False
ys, xs = np.where(red)
P = np.stack([xs, ys], 1).astype(float)
d = np.linalg.svd(P - P.mean(0), full_matrices=False)[2][0]
# the "N" glyph sits at the upper-left end of the arrow
if d[0] > 0:
    d = -d
north = d / np.linalg.norm(d)
print("north (image, x right / y down):", np.round(north, 4),
      "screen angle", round(math.degrees(math.atan2(north[1], north[0])), 2))

# ---------- 2. shadow region: blurred luminance, low local brightness ----------
blur = ndimage.gaussian_filter(lum, 45)
# sunlit stones are bright and warm; shadow is cool and dark
warmth = R - B
sh = (blur < np.percentile(blur[1500:3000, :], 30)) & (warmth < np.median(warmth[1500:3000, :]))
sh[:1500, :] = False
sh[2900:, :] = False
lbl, n = ndimage.label(sh)
sizes = ndimage.sum(sh, lbl, range(1, n + 1))
big = int(np.argmax(sizes)) + 1
m = lbl == big
ys2, xs2 = np.where(m)
print("shadow blob px", int(sizes.max()), "bbox x", xs2.min(), xs2.max(), "y", ys2.min(), ys2.max())
Q = np.stack([xs2, ys2], 1).astype(float)
qm = Q.mean(0)
dq = np.linalg.svd(Q - qm, full_matrices=False)[2][0]
# shadow points away from the bird: bird body centroid is left of the shadow blob
if dq[0] < 0:
    dq = -dq
dq /= np.linalg.norm(dq)
print("shadow (image):", np.round(dq, 4), "screen angle", round(math.degrees(math.atan2(dq[1], dq[0])), 2))

ang_n = math.degrees(math.atan2(north[1], north[0]))
ang_s = math.degrees(math.atan2(dq[1], dq[0]))
# clockwise-on-screen difference from north to shadow
delta = (ang_s - ang_n) % 360
print(f"\nnaive screen angle north->shadow = {delta:.1f} deg (clockwise on screen)")
print("sun azimuth implied =", f"{(delta + 180) % 360:.1f}")

# also report the two candidate tips for a manual check
t = (Q - qm) @ dq
print("blob extremes along axis:", int(t.min()), int(t.max()), "length px", int(t.max() - t.min()))
print("centroid", np.round(qm, 1))
np.save("analysis/shadow_mask2.npy", m)
