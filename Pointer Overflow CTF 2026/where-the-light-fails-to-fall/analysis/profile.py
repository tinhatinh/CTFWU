"""Plot the row-wise darkness fraction f(y) so the sett-row spacing trend can be read off."""
import cv2
import numpy as np

img = cv2.imread("../files/photo.png", cv2.IMREAD_GRAYSCALE).astype(np.float32)
H, W = img.shape
lp = cv2.GaussianBlur(img, (0, 0), 260)
hp = img - lp
loc = np.sqrt(cv2.GaussianBlur(hp * hp, (0, 0), 140)) + 1e-3
dark = cv2.GaussianBlur((hp < -0.5 * loc).astype(np.float32), (0, 0), 3)

STRIPS = [(120, 620), (700, 1200), (2350, 2850)]
PW, PH = 1700, 620
canvas = np.full((PH * len(STRIPS) + 20 * len(STRIPS), PW, 3), 30, np.uint8)
for si, (x0, x1) in enumerate(STRIPS):
    f = dark[:, x0:x1].mean(1)
    g = np.full((PH, PW, 3), 30, np.uint8)
    ymax = f.max()
    xs = np.linspace(0, PW - 1, H).astype(int)
    ys = (PH - 1 - f / ymax * (PH - 40)).astype(int)
    for i in range(1, len(xs)):
        cv2.line(g, (xs[i - 1], ys[i - 1]), (xs[i], ys[i]), (0, 255, 120), 1)
    for y in range(0, H, 200):
        X = int(y / H * (PW - 1))
        cv2.line(g, (X, 0), (X, PH), (60, 60, 120), 1)
        cv2.putText(g, str(y), (X + 3, PH - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 255), 1)
    for v in np.linspace(0, ymax, 5):
        Y = int(PH - 1 - v / ymax * (PH - 40))
        cv2.line(g, (0, Y), (PW, Y), (60, 90, 60), 1)
    cv2.putText(g, f"strip x {x0}-{x1}  max f={ymax:.2f}", (8, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 255), 2)
    y0 = si * (PH + 20)
    canvas[y0:y0 + PH] = g
cv2.imwrite("profile.png", canvas)
print("wrote profile.png", canvas.shape)
