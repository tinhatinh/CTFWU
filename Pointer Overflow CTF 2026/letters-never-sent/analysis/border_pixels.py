import os
import numpy as np
from PIL import Image
from scipy import ndimage
from collections import Counter

p = os.path.join(os.path.dirname(__file__), "..", "files/letter.png")
im = np.asarray(Image.open(p).convert("RGB")).astype(int)
R, G, B = im[:, :, 0], im[:, :, 1], im[:, :, 2]
score = R - (G + B) / 2
thr = np.percentile(score, 99.5)
mask = score >= max(thr, 40)
print("score p99.5 =", round(float(thr), 1), "pixels:", int(mask.sum()))
ys, xs = np.where(mask)
cols = Counter(map(tuple, im[ys, xs]))
print("top colors:", cols.most_common(6))

lab, n = ndimage.label(ndimage.binary_closing(mask, np.ones((3, 3))))
print("components:", n)
info = []
for i in range(1, n + 1):
    yy, xx = np.where(lab == i)
    if len(yy) < 25:
        continue
    w, h = xx.max() - xx.min() + 1, yy.max() - yy.min() + 1
    info.append((xx.min(), xx.max(), yy.min(), yy.max(), round(xx.mean(), 1), round(yy.mean(), 1), w, h, len(yy)))
for t in sorted(info, key=lambda t: (t[5], t[0]))[:40]:
    x0, x1, y0, y1, cx, cy, w, h, a = t
    side = "top" if y0 < 90 else "bottom" if y1 > im.shape[0] - 90 else "left" if x0 < 90 else "right" if x1 > im.shape[1] - 90 else "body"
    print(f"{side:6s} x[{x0:4d}-{x1:4d}] y[{y0:4d}-{y1:4d}] w={w:3d} h={h:3d} area={a:5d} aspect={w/max(h,1):.2f}")
