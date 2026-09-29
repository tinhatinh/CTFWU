"""Measure the sett lattice vectors per patch after suppressing the granite grain.

Outputs the two vanishing points (pencil fits on the direction field) and the cell-area
field (whose cube root is linear in the distance from the horizon)."""
import cv2
import numpy as np

img = cv2.imread("../files/photo.png", cv2.IMREAD_GRAYSCALE).astype(np.float32)
H, W = img.shape
g = cv2.GaussianBlur(img, (0, 0), 24)                      # granite grain gone
bg = cv2.GaussianBlur(g, (0, 0), 260)
hp = g - bg
yy, xx = np.mgrid[0:H, 0:W]
valid = np.ones((H, W), bool)
valid[yy < np.maximum(0.0, 0.1818 * (xx - 780)) + 70] = False
valid[:120, :] = False
cv2.rectangle(valid, (760, 1280), (2660, 3080), False, -1)

NF = 384


def lattice(cx, cy):
    best = None
    for R in (150, 220, 320, 460, 660, 900):
        x0, y0 = cx - R, cy - R
        if x0 < 0 or y0 < 0 or x0 + 2 * R > W or y0 + 2 * R > H:
            continue
        if not valid[y0:y0 + 2 * R:30, x0:x0 + 2 * R:30].all():
            continue
        p = hp[y0:y0 + 2 * R, x0:x0 + 2 * R]
        if p.std() < 3:
            continue
        p = cv2.resize(p, (NF, NF), interpolation=cv2.INTER_AREA).astype(np.float32)
        p = (p - p.mean()) * np.hanning(NF)[:, None] * np.hanning(NF)[None, :]
        F = np.fft.fftshift(np.abs(np.fft.fft2(p)))
        scale = 2 * R / NF
        fv = (np.arange(NF) - NF // 2) / NF * scale
        fy, fx = np.meshgrid(fv, fv, indexing="ij")
        per = 1.0 / np.maximum(np.hypot(fx, fy), 1e-12)
        band = (per > 0.30 * R) & (per < 1.4 * R)
        Fm = np.where(band, F, 0.0)
        c = NF // 2
        Fm[c - 2:c + 3, c - 2:c + 3] = 0
        noise = np.median(F[band]) + 1e-9
        pk = []
        for _ in range(2):
            i, j = np.unravel_index(np.argmax(Fm), Fm.shape)
            if Fm[i, j] <= 0 or not (1 <= i < NF - 1 and 1 <= j < NF - 1):
                break
            wi = np.array([F[i - 1, j], F[i, j], F[i + 1, j]], float)
            wj = np.array([F[i, j - 1], F[i, j], F[i, j + 1]], float)
            di = (wi[2] - wi[0]) / max(wi.sum(), 1e-9) if (wi.sum() > 0) else 0.0
            dj = (wj[2] - wj[0]) / max(wj.sum(), 1e-9) if (wj.sum() > 0) else 0.0
            f_y = fv[i] + di * (fv[1] - fv[0])
            f_x = fv[j] + dj * (fv[1] - fv[0])
            pk.append((f_x, f_y, F[i, j] / noise))
            Fm[max(0, i - 9):i + 10, max(0, j - 9):j + 10] = 0
        if len(pk) < 2:
            continue
        (ax, ay, sa), (bx, by, sb) = pk
        cr = abs(ax * by - ay * bx)
        if cr <= 0:
            continue
        snr = min(sa, sb)
        if best is None or snr > best[0]:
            # the lattice directions are perpendicular to the frequency vectors
            d1 = np.degrees(np.arctan2(-ax, ay)) % 180
            d2 = np.degrees(np.arctan2(-bx, by)) % 180
            p1 = 1.0 / np.hypot(ax, ay)
            p2 = 1.0 / np.hypot(bx, by)
            best = (snr, d1, p1, d2, p2, 1.0 / cr, R)
    return best


recs = []
for cy in range(200, 3990, 110):
    for cx in range(150, 2960, 150):
        r = lattice(cx, cy)
        if r and r[0] > 6.0:
            recs.append((cx, cy) + r[1:])
recs = np.array(recs)
print("patches:", len(recs))
np.save("lattice_vecs.npy", recs)

for lo, hi in ((150, 700), (700, 1400), (1400, 2100), (2100, 2800), (2800, 3400), (3400, 3990)):
    m = (recs[:, 1] >= lo) & (recs[:, 1] < hi)
    if m.sum() < 3:
        continue
    a1, a2 = recs[m, 2], recs[m, 4]
    p1, p2 = recs[m, 3], recs[m, 5]
    ca = recs[m, 6] ** (1 / 3)
    print(f"y {lo}-{hi}: n={m.sum():3d}  dir1 med={np.median(a1):6.1f}  dir2 med={np.median(a2):6.1f}"
          f"   per1={np.median(p1):6.1f} per2={np.median(p2):6.1f}   cell^(1/3)={np.median(ca):6.1f}")
