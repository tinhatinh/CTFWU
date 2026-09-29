"""Horizon from the sett cell-area field.

For a ground-plane homography the image cell area scales as 1/dist(p, horizon)^2; the cell
area is 1/|b1 x b2| from the two lattice fundamentals, so no anisotropy assumption is used."""
import cv2
import numpy as np

img = cv2.imread("../files/photo.png", cv2.IMREAD_GRAYSCALE).astype(np.float32)
H, W = img.shape
yy, xx = np.mgrid[0:H, 0:W]
keep = np.ones((H, W), bool)
keep[yy < np.maximum(0.0, 0.1818 * (xx - 780)) + 60] = False
cv2.rectangle(keep, (780, 1300), (2620, 3050), False, -1)

NF = 512
LO, HI = 55.0, 1500.0
fv0 = (np.arange(NF) - NF // 2) / NF


def cell(cx, cy):
    best = None
    for R in (140, 200, 280, 400, 560, 800, 1100):
        x0, y0 = cx - R, cy - R
        if x0 < 0 or y0 < 0 or x0 + 2 * R > W or y0 + 2 * R > H:
            continue
        if not keep[y0:y0 + 2 * R:40, x0:x0 + 2 * R:40].all():
            continue
        p = img[y0:y0 + 2 * R, x0:x0 + 2 * R]
        if p.std() < 6:
            continue
        p = cv2.resize(p, (NF, NF), interpolation=cv2.INTER_AREA).astype(np.float32)
        p = (p - p.mean()) * np.hanning(NF)[:, None] * np.hanning(NF)[None, :]
        F = np.fft.fftshift(np.abs(np.fft.fft2(p)))
        scale = 2 * R / NF
        fy, fx = np.meshgrid(fv0 * scale, fv0 * scale, indexing="ij")
        per = 1.0 / np.maximum(np.hypot(fx, fy), 1e-9)
        band = (per > LO) & (per < HI) & (np.abs(fv0) * scale > 1e-9)
        if band.sum() == 0:
            continue
        Fm = np.where(band, F, 0.0)
        noise = np.median(F[band]) + 1e-9
        peaks = []
        for _ in range(2):
            i, j = np.unravel_index(np.argmax(Fm), Fm.shape)
            if Fm[i, j] <= 0 or not (1 <= i < NF - 1 and 1 <= j < NF - 1):
                break
            wi = np.array([F[i - 1, j], F[i, j], F[i + 1, j]], float)
            wj = np.array([F[i, j - 1], F[i, j], F[i, j + 1]], float)
            di = (wi[2] - wi[0]) / max(wi.sum(), 1e-9)
            dj = (wj[2] - wj[0]) / max(wj.sum(), 1e-9)
            f_y = fy[i, j] + di * (fy[1, 0] - fy[0, 0])
            f_x = fx[i, j] + dj * (fx[0, 1] - fx[0, 0])
            peaks.append((f_x, f_y, F[i, j] / noise))
            Fm[max(0, i - 14):i + 15, max(0, j - 14):j + 15] = 0
        if len(peaks) < 2:
            continue
        (ax, ay, sa), (bx, by, sb) = peaks
        cross = abs(ax * by - ay * bx)
        if cross <= 0:
            continue
        area = 1.0 / cross
        if not (30 ** 2 < area < 900 ** 2):
            continue
        snr = min(sa, sb)
        if best is None or snr > best[0]:
            best = (snr, area,
                    np.degrees(np.arctan2(-ax, ay)) % 180,
                    np.degrees(np.arctan2(-bx, by)) % 180, R)
    return best


recs = []
for cy in range(820, 3980, 130):
    for cx in range(180, 2900, 180):
        r = cell(cx, cy)
        if r:
            recs.append((cx, cy, r[1], r[2], r[3], r[0], r[4]))
recs = np.array(recs)
print("patches:", len(recs))
np.save("cellarea.npy", recs)
for lo, hi in ((800, 1300), (1300, 2000), (2000, 2700), (2700, 3400), (3400, 4000)):
    m = (recs[:, 1] >= lo) & (recs[:, 1] < hi)
    if m.sum():
        sd = np.sqrt(recs[m, 2])
        print(f"  y {lo}-{hi}: n={m.sum():3d} sqrt(area) med={np.median(sd):7.1f} "
              f"p25={np.percentile(sd,25):7.1f} p75={np.percentile(sd,75):7.1f}  "
              f"R med={np.median(recs[m,6]):6.0f} snr med={np.median(recs[m,5]):6.1f}  "
              f"ang {np.median(recs[m,3]):5.1f}/{np.median(recs[m,4]):5.1f}")

u = 1.0 / np.sqrt(recs[:, 2])
P = recs[:, 0:2]
D = np.column_stack([P[:, 0], P[:, 1], np.ones(len(P)), -u])
_, sv, Vt = np.linalg.svd(D)
a, b, c, K = Vt[-1]
nn = np.hypot(a, b)
a, b, c, K = a / nn, b / nn, c / nn, K / nn
if K < 0:
    a, b, c, K = -a, -b, -c, -K
print(f"\nhorizon: {a:+.6f}x {b:+.6f}y {c:+.6f} = 0    K={K:.5g}")
print(f"   horizon direction angle = {np.degrees(np.arctan2(-a, b)):.2f} deg (y-down)")
print(f"   at x=0 -> y={-c/b:.0f};  at x=3000 -> y={( -a*3000-c)/b:.0f};  at y=0 -> x={-c/a:.0f}")
pred = (a * P[:, 0] + b * P[:, 1] + c) / K
rel = u / np.maximum(pred, 1e-9)
print(f"   fit quality: rel resid median={np.median(np.abs(rel-1)):.3f} p90={np.percentile(np.abs(rel-1),90):.3f}"
      f"   sv ratio={sv[-2]/sv[-1]:.1f}")
np.save("horizon.npy", np.array([a, b, c, K]))
