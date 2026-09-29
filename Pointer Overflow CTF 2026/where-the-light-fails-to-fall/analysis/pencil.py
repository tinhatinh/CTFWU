"""Overlay trial vanishing-point pencils so the fit can be checked by eye."""
import cv2
import numpy as np

img = cv2.imread("../files/photo.png")
S = 0.25
small = cv2.resize(img, None, fx=S, fy=S)
H, W = small.shape[:2]


def draw(canvas, vp, col, step_deg, n=30):
    v = np.array([vp[0] * S, vp[1] * S])
    c = np.array([W / 2, H / 2])
    base = np.degrees(np.arctan2(c[1] - v[1], c[0] - v[0]))
    for k in range(-n, n + 1):
        a = np.radians(base + step_deg * k)
        d = np.array([np.cos(a), np.sin(a)])
        ts = []
        for axis, lim in ((0, W), (1, H)):
            if abs(d[axis]) > 1e-9:
                t = (0 - v[axis]) / d[axis]
                ts.append(t)
                t = (lim - v[axis]) / d[axis]
                ts.append(t)
        pts = [v + t * d for t in ts]
        pts = [p for p in pts if -1 <= p[0] <= W + 1 and -1 <= p[1] <= H + 1]
        if len(pts) >= 2:
            p, q = min(pts, key=lambda z: z[0]), max(pts, key=lambda z: z[0])
            if np.linalg.norm(p - q) < 2:
                p, q = min(pts, key=lambda z: z[1]), max(pts, key=lambda z: z[1])
            cv2.line(canvas, tuple(np.round(p).astype(int)), tuple(np.round(q).astype(int)), col, 1)


c1 = small.copy()
draw(c1, (-4482, 193), (0, 255, 0), 1.2)
draw(c1, (982, -30229), (255, 0, 255), 1.2)
cv2.imwrite("pencil_ab.png", c1)

c2 = small.copy()
draw(c2, (-15000, -800), (0, 255, 0), 1.2)
draw(c2, (2000, -12000), (255, 0, 255), 1.2)
cv2.imwrite("pencil_cd.png", c2)
print("ok")
