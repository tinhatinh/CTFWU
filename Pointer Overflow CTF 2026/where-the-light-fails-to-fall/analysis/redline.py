"""Measure the red true-north overlay line exactly (it is a pure graphic)."""
import numpy as np
from PIL import Image

img = np.asarray(Image.open("../files/photo.png").convert("RGB"), dtype=np.int16)
R, G, B = img[:, :, 0], img[:, :, 1], img[:, :, 2]
red = (R > 120) & (R - G > 55) & (R - B > 55)
ys, xs = np.nonzero(red)
print("red pixels:", len(xs), " bbox x", xs.min(), xs.max(), " y", ys.min(), ys.max())

# the 'N' glyph sits at one end; separate it by fitting a line to the long stroke
pts = np.stack([xs, ys], 1).astype(np.float64)
# robust line fit: total least squares, then drop outliers, twice
v = pts.mean(0)
for it in range(6):
    q = pts - v
    u, s, vt = np.linalg.svd(q, full_matrices=False)
    d = vt[0]
    nrm = np.array([-d[1], d[0]])
    t = q @ d
    perp = np.abs(q @ nrm)
    inl = perp < max(6.0, np.percentile(perp, 92))
    print(f"  it{it}: inliers={inl.sum():5d} span_t={t[inl].min():.0f}..{t[inl].max():.0f} "
          f"dir=({d[0]:+.5f},{d[1]:+.5f})")
    v = pts[inl].mean(0)
    pts_in = pts[inl]
d = vt[0]
if d[1] > 0:                 # report the direction with y-up positive component
    d = -d
t = (pts_in - v) @ d
p0 = v + t.min() * d
p1 = v + t.max() * d
print(f"\nline endpoints (x, y-down): {p0.round(1)}  ->  {p1.round(1)}")
print(f"length {np.linalg.norm(p1-p0):.1f} px")
print(f"unit dir y-down ({d[0]:+.5f},{d[1]:+.5f})   y-up ({d[0]:+.5f},{-d[1]:+.5f})")
print(f"angle from +x axis, y-up: {np.degrees(np.arctan2(-d[1], d[0])):.2f} deg")

# the arrowhead / N glyph: which end is the head? count red pixels off the line
off = pts[(np.abs((pts - v) @ np.array([-d[1], d[0]])) > 8)]
print("off-line red pixels (glyph + head):", len(off))
for end, nm in ((p0, "end0"), (p1, "end1")):
    dd = np.linalg.norm(off - end, axis=1)
    print(f"   {nm} {end.round(0)}: glyph pixels within 120px = {(dd < 120).sum()}")
