"""Local sett-row spacing in sliding windows -> straight-line fit of 1/spacing vs y -> horizon."""
import cv2
import numpy as np

img = cv2.imread("../files/photo.png", cv2.IMREAD_GRAYSCALE).astype(np.float32)
H, W = img.shape
lp = cv2.GaussianBlur(img, (0, 0), 260)
hp = img - lp
loc = np.sqrt(cv2.GaussianBlur(hp * hp, (0, 0), 140)) + 1e-3
dark = (hp < -0.5 * loc).astype(np.float32)
dark = cv2.GaussianBlur(dark, (0, 0), 3)

STRIPS = [(120, 620), (700, 1150), (1250, 1700), (2350, 2800), (2450, 2950)]
WIN = 900


def local_period(sig, lo=28.0, hi=420.0):
    n = len(sig)
    s = sig - np.polyval(np.polyfit(np.arange(n), sig, 3), np.arange(n))
    s *= np.hanning(n)
    P = np.abs(np.fft.rfft(s))
    f = np.fft.rfftfreq(n, 1.0)
    band = (f > 1 / hi) & (f < 1 / lo)
    if band.sum() < 3:
        return None
    k = np.where(band)[0][np.argmax(P[band])]
    # parabolic refinement, clamped
    if 1 <= k < len(P) - 1:
        a, b, c = P[k - 1], P[k], P[k + 1]
        d = 0.5 * (a - c) / max(a - 2 * b + c, 1e-12) if (a - 2 * b + c) < 0 else 0.0
        d = float(np.clip(d, -0.5, 0.5))
    else:
        d = 0.0
    fpk = (k + d) / n
    if fpk <= 0:
        return None
    snr = P[k] / (np.median(P[band]) + 1e-9)
    return 1.0 / fpk, snr


recs = []
for x0, x1 in STRIPS:
    f = dark[:, x0:x1].mean(1)
    for yc in range(200, 3900, 60):
        y0, y1 = max(0, yc - WIN // 2), min(H, yc + WIN // 2)
        r = local_period(f[y0:y1])
        if r and r[1] > 1.8:
            recs.append((yc, x0, r[0], r[1]))
recs = np.array(recs)
print("windows:", len(recs))
for lo, hi in ((200, 700), (700, 1200), (1200, 1800), (1800, 2400), (2400, 3000), (3000, 3800)):
    m = (recs[:, 0] >= lo) & (recs[:, 0] < hi)
    if m.sum():
        print(f"  y {lo}-{hi}: n={m.sum():3d}  period med={np.median(recs[m,2]):7.1f} "
              f"p25={np.percentile(recs[m,2],25):7.1f} p75={np.percentile(recs[m,2],75):7.1f} "
              f" snr med={np.median(recs[m,3]):5.1f}")

# period(y) = A / (y - yh)  ->  1/period is linear in y
u = 1.0 / recs[:, 2]
Y = recs[:, 0]
for tag, m in (("all", np.ones(len(Y), bool)),):
    p = np.polyfit(Y[m], u[m], 1)
    yh = -p[1] / p[0]
    pred = np.polyval(p, Y[m])
    print(f"\nfit {tag}: 1/period = {p[0]:.3e}*(y - {yh:.0f})   "
          f"rel-resid med={np.median(np.abs(u[m]/pred-1)):.3f}")
    for x0 in sorted(set(recs[:, 1].astype(int))):
        mm = m & (recs[:, 1] == x0)
        if mm.sum() > 6:
            q = np.polyfit(Y[mm], u[mm], 1)
            print(f"    strip x0={x0:5d} n={mm.sum():3d}  y_h={-q[1]/q[0]:9.0f}  slope={q[0]:.3e}")

# per strip, also get the horizon's y at that strip's x by the same law
np.save("periods.npy", recs)
