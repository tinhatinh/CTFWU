"""Estimate the horizon row from how the sett period shrinks with image height.

For a ground plane, the local image scale is proportional to 1/(y - y_horizon)."""
import cv2
import numpy as np
from scipy.optimize import curve_fit

img = cv2.imread("../files/photo.png")
H, W = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float64)
bh = cv2.morphologyEx(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.MORPH_BLACKHAT,
                      cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31)))
bh = cv2.GaussianBlur(bh, (3, 3), 0).astype(np.float64)

rows = []
for y in range(200, 3950, 100):
    # sunlit paving columns only (avoid the bird/shadow band and the slab)
    for x0, x1 in ((60, 900), (2450, 2950)):
        band = bh[y - 60:y + 60, x0:x1]
        if band.shape[1] < 300:
            continue
        prof = band.mean(0)
        prof = prof - prof.mean()
        n = len(prof)
        win = np.hanning(n)
        P = np.abs(np.fft.rfft(prof * win))
        f = np.fft.rfftfreq(n, 1.0)
        k = np.argmax(P[(f > 1 / 400) & (f < 1 / 25)]) + np.searchsorted(f, 1 / 400, "left")
        fk = f[k]
        if fk <= 0:
            continue
        rows.append((y + (x0 == 60) * 0, x0, 1.0 / fk, P[k] / np.abs(P[f > 0]).mean()))

rows = np.array(rows)
print(" y      x0     period   snr")
for r in rows[::3]:
    print(f"{r[0]:6.0f} {r[1]:6.0f} {r[2]:8.1f} {r[3]:6.1f}")

good = rows[(rows[3] > 2.2) & (rows[2] > 25) & (rows[2] < 600)]
print("\nusing", len(good), "of", len(rows), "samples")


def model(y, C, yh):
    return C / np.abs(y - yh)


p0 = [good[:, 2].max() * (4000 - good[:, 0].min()), -1000.0]
popt, pcov = curve_fit(model, good[:, 0], good[:, 2], p0=p0, maxfev=200000)
res = good[:, 2] - model(good[:, 0], *popt)
print(f"fit: period = {popt[0]:.0f} / (y - {popt[1]:.0f})   rms={np.sqrt((res**2).mean()):.1f} px  "
      f"rel={np.sqrt((res/good[:,2])**2).mean()*100:.1f}%")

# left- and right-hand columns separately, as a consistency check
for lo, hi, nm in ((0, 1, "left"), (1, 2, "right")):
    pass
for tag, m in (("x<900", good[:, 1] < 900), ("x>2450", good[:, 1] > 2450)):
    g = good[m]
    try:
        p = curve_fit(model, g[:, 0], g[:, 2], p0=p0, maxfev=200000)[0]
        print(f"   {tag:8s} n={len(g):3d}  yh={p[1]:8.0f}  C={p[0]:9.0f}")
    except Exception as e:
        print("   ", tag, "fail", e)
