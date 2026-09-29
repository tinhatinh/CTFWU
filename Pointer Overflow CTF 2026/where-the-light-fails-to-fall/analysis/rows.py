"""Row crossings along vertical scan lines -> harmonic fit -> horizon.

Equally spaced ground rows image to y_k with 1/(y_k - y_h) linear in k, so three
consecutive crossings give y_h in closed form:  y_h = ((a+c)b - 2ac) / (2b - a - c)."""
import cv2
import numpy as np

img = cv2.imread("../files/photo.png", cv2.IMREAD_GRAYSCALE).astype(np.float32)
H, W = img.shape
lp = cv2.GaussianBlur(img, (0, 0), 160)
hp = img - lp
loc = np.sqrt(cv2.GaussianBlur(hp * hp, (0, 0), 90)) + 1e-3
dark = (hp < -0.55 * loc).astype(np.uint8)
dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
cv2.imwrite("darkmask.png", dark * 255 if dark.dtype == np.uint8 else dark)


def crossings(x0, ylo=40, yhi=3990, span=140):
    """Dark bands on the column x0, classified by how far the darkness extends sideways."""
    col = dark[:, x0 - 2:x0 + 3].max(1)
    ys = np.nonzero(col)[0]
    ys = ys[(ys >= ylo) & (ys <= yhi)]
    if len(ys) == 0:
        return []
    groups, cur = [], [ys[0]]
    for y in ys[1:]:
        if y - cur[-1] <= 6:
            cur.append(y)
        else:
            groups.append(cur)
            cur = [y]
    groups.append(cur)
    out = []
    for g in groups:
        yc = int(np.mean(g))
        band = dark[max(0, yc - 3):yc + 4, max(0, x0 - span):x0 + span]
        frac = band.mean()
        out.append((yc, len(g), frac))
    return out


for x0 in (250, 450, 2750, 2900):
    cs = crossings(x0)
    rows = [c for c in cs if c[2] > 0.55]          # sideways-extended -> a row joint
    print(f"\n=== x={x0}: {len(cs)} dark bands, {len(rows)} classified as rows ===")
    print("   row y:", [c[0] for c in rows])
    yh = []
    for i in range(len(rows) - 2):
        a, b, c = rows[i][0], rows[i + 1][0], rows[i + 2][0]
        den = 2 * b - a - c
        if abs(den) > 1e-6:
            yh.append(((a + c) * b - 2 * a * c) / den)
    yh = np.array(yh)
    if len(yh):
        print(f"   y_h from consecutive triples: n={len(yh)} median={np.median(yh):9.0f} "
              f"p25={np.percentile(yh,25):9.0f} p75={np.percentile(yh,75):9.0f}")
    # collinearity scan: 1/(y_k - yh) should be linear in k
    best = None
    Y = np.array([c[0] for c in rows], float)
    for k0 in range(1, 4):
        for yh0 in np.linspace(-40000, 2000, 4200):
            if np.any(Y - yh0 <= 1):
                continue
            u = 1.0 / (Y - yh0)
            idx = np.arange(len(u)) * k0
            A = np.column_stack([idx, np.ones(len(idx))])
            r = u - A @ np.linalg.lstsq(A, u, rcond=None)[0]
            ss = float((r ** 2).sum())
            if best is None or ss < best[0]:
                best = (ss, yh0, k0)
    print(f"   best collinear fit: y_h={best[1]:9.1f}  gap-index={best[2]}  ss={best[0]:.3e}")
