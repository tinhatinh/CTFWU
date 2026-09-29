import math
import numpy as np
from PIL import Image

img = np.asarray(Image.open("../files/photo.png").convert("RGB"), dtype=np.float64)
lum = img.mean(axis=2)
H, W = lum.shape
print("image", W, H)


def analyse(name, x0, y0, x1, y1):
    """Strongest 2-D lattice harmonics: spatial period + orientation of the joint set."""
    p = lum[y0:y1, x0:x1]
    p = p - p.mean()
    win = np.hanning(p.shape[0])[:, None] * np.hanning(p.shape[1])[None, :]
    F = np.abs(np.fft.rfft2(p * win))
    fy = np.fft.fftfreq(p.shape[0], 1.0)
    fx = np.fft.rfftfreq(p.shape[1], 1.0)
    F = F.copy()
    F[:4, :4] = 0  # drop DC
    peaks = []
    for _ in range(4):
        i = np.unravel_index(np.argmax(F), F.shape)
        vx, vy = fx[i[1]], fy[i[0]]
        if vx == 0 and vy == 0:
            break
        ang = math.degrees(math.atan2(vy, vx)) % 180  # direction of the brightness gradient
        wl = 1.0 / math.hypot(vx, vy)
        peaks.append((round(wl, 1), round(90 - ang, 1)))  # report joint-line direction
        # suppress this peak's neighbourhood
        F[max(0, i[0] - 6): i[0] + 7, max(0, i[1] - 6): i[1] + 7] = 0
    # energy of the strongest joint orientations
    gy, gx = np.gradient(lum[y0:y1, x0:x1])
    mag = np.hypot(gx, gy)
    ang = (np.degrees(np.arctan2(gy, gx)) + 180) % 180
    hist, edges = np.histogram(ang, bins=36, range=(0, 180), weights=mag)
    order = np.argsort(hist)[::-1][:4]
    top = [(int(edges[i] + 2.5), round(float(hist[i] / hist.sum() * 100), 1)) for i in order]
    print(f"{name:10s} lattice (wavelength px, joint-line deg from +x): {peaks}")
    print(f"{'':10s} gradient-angle histogram top (deg, %): {top}")


# sunlit paving patches, chosen away from the shadow band and the bird
analyse("paving-A", 2150, 1950, 2750, 2450)
analyse("paving-B", 2400, 2450, 2990, 2990)
analyse("paving-C", 30, 2600, 600, 3200)
analyse("paving-D", 1500, 2900, 2200, 3400)
analyse("paving-E", 2600, 1700, 2999, 2100)
