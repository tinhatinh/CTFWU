"""Crop with a labelled grid so features can be read off by eye."""
import cv2
import numpy as np
import sys

x0, y0, x1, y1 = map(int, sys.argv[1:5])
out = sys.argv[5]
S = float(sys.argv[6]) if len(sys.argv) > 6 else 0.6
step = int(sys.argv[7]) if len(sys.argv) > 7 else 100

img = cv2.imread("../files/photo.png")
c = img[y0:y1, x0:x1].copy()
for gx in range((x0 // step + 1) * step, x1, step):
    col = (0, 255, 255) if gx % (step * 5) == 0 else (0, 140, 140)
    cv2.line(c, (gx - x0, 0), (gx - x0, c.shape[0]), col, 1)
    cv2.putText(c, str(gx), (gx - x0 + 2, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
for gy in range((y0 // step + 1) * step, y1, step):
    col = (255, 0, 255) if gy % (step * 5) == 0 else (140, 0, 140)
    cv2.line(c, (0, gy - y0), (c.shape[1], gy - y0), col, 1)
    cv2.putText(c, str(gy), (3, gy - y0 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 0, 255), 2)
c = cv2.resize(c, None, fx=S, fy=S, interpolation=cv2.INTER_AREA if S < 1 else cv2.INTER_LANCZOS4)
cv2.imwrite(out, c)
print(out, c.shape)
