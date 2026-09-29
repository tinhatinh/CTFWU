import numpy as np
from PIL import Image

im = Image.open("files/photo.png").convert("RGB")
a = np.asarray(im).astype(int)
H, W = a.shape[:2]
R, G, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]
lum = 0.299 * R + 0.587 * G + 0.114 * B

# ---- arrow: red pixels below the bird only
red = (R > 120) & (R - G > 60) & (R - B > 60)
red[:2950, :] = False
ys, xs = np.where(red)
print("arrow red px:", len(xs), "x", xs.min(), xs.max(), "y", ys.min(), ys.max())
P = np.stack([xs, ys], 1).astype(float)
mean = P.mean(0)
u, s, vt = np.linalg.svd(P - mean, full_matrices=False)
d = vt[0]
if d[0] < 0:
    d = -d
print("arrow dir (unit, +x right, +y down):", np.round(d, 4),
      "angle from +x:", round(np.degrees(np.arctan2(d[1], d[0])), 2))
print("   -> the drawn N points the opposite way:",
      round(np.degrees(np.arctan2(-d[1], -d[0])), 2), "deg from +x")

# ---- bird: find it via saturated pink feet + grey body; use the shadow instead.
# Shadow = dark ground pixels. Threshold below the 25th pct of the ground area.
ground = lum[2000:3900, :]
thr = np.percentile(ground, 18)
sh = (lum < thr)
sh[:1800, :] = False
sh[3000:, :] = False          # keep the band where the bird shadow lies
sh[:, :600] = False
lbl = None
try:
    from scipy import ndimage
    lbl, n = ndimage.label(sh)
    sizes = ndimage.sum(sh, lbl, range(1, n + 1))
    big = int(np.argmax(sizes)) + 1
    m = lbl == big
    ys2, xs2 = np.where(m)
    print("largest dark blob px:", int(sizes.max()), "bbox x", xs2.min(), xs2.max(), "y", ys2.min(), ys2.max())
    Q = np.stack([xs2, ys2], 1).astype(float)
    qm = Q.mean(0)
    uq, sq, vtq = np.linalg.svd(Q - qm, full_matrices=False)
    dq = vtq[0]
    # direction away from the bird (bird is to the LEFT of its shadow)
    if dq[0] < 0:
        dq = -dq
    print("shadow principal dir:", np.round(dq, 4), "angle from +x:",
          round(np.degrees(np.arctan2(dq[1], dq[0])), 2))
    # tip = extreme point along that direction; base = extreme opposite
    t = (Q - qm) @ dq
    print("shadow extent along axis (px):", round(t.max() - t.min(), 1))
    np.save("analysis/shadow_mask.npy", m)
except Exception as e:
    print("scipy path failed:", e)
