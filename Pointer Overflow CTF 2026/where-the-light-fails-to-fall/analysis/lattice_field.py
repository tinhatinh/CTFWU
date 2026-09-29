"""Local sett-lattice direction field from patch power spectra, then pencil fits."""
import cv2
import numpy as np
from scipy.optimize import minimize

img = cv2.imread("../files/photo.png", cv2.IMREAD_GRAYSCALE).astype(np.float64)
H, W = img.shape
bh = cv2.morphologyEx(img.astype(np.uint8), cv2.MORPH_BLACKHAT,
                      cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41)))
bh = cv2.GaussianBlur(bh.astype(np.float64), (5, 5), 0)

R = 260          # patch half-size
PS = 512         # patch resample size


def lattice(cx, cy):
    x0, x1 = int(cx - R), int(cx + R)
    y0, y1 = int(cy - R), int(cy + R)
    if x0 < 0 or y0 < 0 or x1 > W or y1 > H:
        return None
    p = bh[y0:y1, x0:x1]
    # reject the bird / shadow / slab: too dark or too smooth
    if p.mean() < 45 or p.std() < 9:
        return None
    p = cv2.resize(p, (PS, PS), interpolation=cv2.INTER_AREA).astype(np.float64)
    p = (p - p.mean()) * np.hanning(PS)[:, None] * np.hanning(PS)[None, :]
    F = np.fft.fftshift(np.abs(np.fft.rfft2(p)), axes=0)[:, :PS // 2 + 1]
    fy = np.fft.fftshift(np.fft.fftfreq(PS, 2 * R / PS))     # cycles per source px
    fx = np.fft.rfftfreq(PS, 2 * R / PS)
    F = F.copy()
    F[PS // 2 - 3:PS // 2 + 4, :8] = 0                        # kill DC / low freq
    out = []
    for _ in range(2):
        i, j = np.unravel_index(np.argmax(F), F.shape)
        wl_y, wl_x = 1 / fy[i], 1 / fx[j]
        if wl_x < 40 or wl_y < 40 or wl_x > 900 or wl_y > 900:
            break
        # the frequency vector (fx, fy) is perpendicular to the lattice row it indexes;
        # the corresponding image-space lattice direction is perpendicular to it.
        dir_ang = np.degrees(np.arctan2(-fx[j], fy[i])) % 180
        out.append((dir_ang, np.hypot(wl_x, wl_y), F[i, j] / np.median(F[F > 0])))
        F[max(0, i - 10):i + 11, max(0, j - 4):j + 5] = 0
    return out


pts = []
for cy in range(500, 3900, 300):
    for cx in range(400, 2900, 400):
        L = lattice(cx, cy)
        if L:
            pts.append((cx, cy, L))
print("usable patches:", len(pts))
for cx, cy, L in pts:
    s = "  ".join(f"{a:6.1f}deg wl={w:6.0f} snr={q:5.1f}" for a, w, q in L)
    print(f"({cx:5d},{cy:5d})  {s}")
np.save("lattice_field.npy", np.array([(cx, cy, a, w, q) for cx, cy, L in pts for a, w, q in L]))
