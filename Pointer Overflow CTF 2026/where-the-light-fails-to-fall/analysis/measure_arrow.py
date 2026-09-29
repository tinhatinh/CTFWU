import numpy as np
from PIL import Image

im = Image.open("files/photo.png").convert("RGB")
a = np.asarray(im).astype(int)
H, W = a.shape[:2]
R, G, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]

# 1. red arrow pixels
red = (R > 120) & (R - G > 60) & (R - B > 60)
ys, xs = np.where(red)
print("red pixels:", len(xs), "bbox x", xs.min(), xs.max(), "y", ys.min(), ys.max())
# principal direction of the arrow (PCA on red pixels)
pts = np.stack([xs, ys], 1).astype(float)
pts -= pts.mean(0)
u, s, vt = np.linalg.svd(pts, full_matrices=False)
d = vt[0]
print("arrow PCA dir (x,y in image coords, y down):", np.round(d, 4), "svt:", np.round(s[:2], 1))
ang_img = np.degrees(np.arctan2(d[1], d[0]))
print("arrow angle in image (deg from +x, y down):", round(ang_img, 2), "or", round(ang_img - 180, 2))

# which end carries the N label? the label is a dense blob; find the densest 40x40 window
best, bxy = -1, None
for i in range(0, len(xs), 1):
    pass
from collections import Counter
c = Counter(zip(xs // 40, ys // 40))
top = c.most_common(6)
print("densest red 40px cells (col,row,count):", top)

# 2. shadow: dark pixels in the lower-middle region around the bird
lum = 0.299 * R + 0.587 * G + 0.114 * B
print("luminance percentiles:", [round(np.percentile(lum, p), 1) for p in (1, 5, 25, 50, 75, 95)])
np.save("analysis/lum.npy", lum.astype(np.float32))
np.save("analysis/red.npy", red)
