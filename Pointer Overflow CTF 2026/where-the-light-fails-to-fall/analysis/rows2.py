"""Row-joint positions from the row-wise darkness fraction, then harmonic fit for the horizon."""
import cv2
import numpy as np
from scipy.signal import find_peaks

img = cv2.imread("../files/photo.png", cv2.IMREAD_GRAYSCALE).astype(np.float32)
H, W = img.shape
lp = cv2.GaussianBlur(img, (0, 0), 200)
hp = img - lp
loc = np.sqrt(cv2.GaussianBlur(hp * hp, (0, 0), 100)) + 1e-3
dark = (hp < -0.5 * loc).astype(np.float32)

STRIPS = [(120, 620, "left"), (2400, 2900, "right"), (700, 1200, "mid-left")]
res = {}
for x0, x1, nm in STRIPS:
    f = dark[:, x0:x1].mean(1)
    f = np.convolve(f, np.ones(5) / 5, mode="same")
    # adaptive minimum distance: rows get farther apart lower down
    ys = []
    order = np.argsort(f)[::-1]
    taken = []
    for i in order:
        if f[i] < 0.16:
            break
        y = int(i)
        # local spacing estimate from the already-accepted neighbours
        near = [t for t in taken if abs(t - y) < 600]
        need = 40 if not near else max(30, min(abs(y - t) for t in near) * 0.72)
        if all(abs(y - t) >= need for t in taken):
            taken.append(y)
    taken.sort()
    res[nm] = taken
    print(f"\n=== strip {nm} (x {x0}-{x1}): {len(taken)} row joints ===")
    print("   y:", taken)
    d = np.diff(taken)
    print("   spacing:", [int(v) for v in d])

for nm, Y in res.items():
    Y = np.array(Y, float)
    if len(Y) < 5:
        continue
    print(f"\n--- {nm}: harmonic fits ---")
    yh = []
    for i in range(len(Y) - 2):
        a, b, c = Y[i], Y[i + 1], Y[i + 2]
        den = 2 * b - a - c
        if abs(den) > 0.5:
            yh.append(((a + c) * b - 2 * a * c) / den)
    yh = np.array(yh)
    print(f"   triple y_h: n={len(yh)} median={np.median(yh):9.0f} "
          f"p25={np.percentile(yh,25):9.0f} p75={np.percentile(yh,75):9.0f} min={yh.min():9.0f} max={yh.max():9.0f}")
    # collinearity of 1/(y_k - yh) vs k, allowing a constant index gap
    best = []
    for gap in (1, 2):
        for y0 in np.linspace(-60000, 4000, 6400):
            v = Y - y0
            if v.min() <= 1:
                continue
            u = 1.0 / v
            k = np.arange(len(u)) * gap
            r = u - np.polyval(np.polyfit(k, u, 1), k)
            best.append((float((r ** 2).sum()) / (u.var() + 1e-30), y0, gap))
    best.sort()
    for ss, y0, gap in best[:4]:
        print(f"   norm-ss={ss:.2e}  y_h={y0:10.1f}  gap={gap}")
np.save("rowjoints.npy", np.array([0]))
import json
json.dump({k: [int(v) for v in Y] for k, Y in res.items()}, open("rowjoints.json", "w"))
