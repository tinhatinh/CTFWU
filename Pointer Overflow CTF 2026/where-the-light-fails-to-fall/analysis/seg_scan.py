"""Long joint segments, colour-coded by orientation, to identify the two lattice families."""
import cv2
import numpy as np

img = cv2.imread("../files/photo.png")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
bh = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31)))
bh = cv2.GaussianBlur(bh, (5, 5), 0)
edges = cv2.Canny(bh, 30, 90)
mask = np.zeros_like(edges)
cv2.rectangle(mask, (0, 250), (W := 3000, 4000), 255, -1)
cv2.rectangle(mask, (880, 1400), (2520, 2950), 0, -1)   # bird + shadow
edges = cv2.bitwise_and(edges, mask)

seg = cv2.HoughLinesP(edges, 1, np.pi / 900, threshold=120, minLineLength=260, maxLineGap=14)
seg = np.asarray(seg).reshape(-1, 4)
print("segments:", len(seg))
ang = (np.degrees(np.arctan2(seg[:, 3] - seg[:, 1], seg[:, 2] - seg[:, 0])) + 180) % 180
ln = seg
L = np.hypot(ln[:, 2] - ln[:, 0], ln[:, 3] - ln[:, 1])
print("length percentiles:", np.percentile(L, [10, 50, 90]).round(0))

hist, e = np.histogram(ang, bins=90, range=(0, 180), weights=L)
for i in np.argsort(hist)[::-1][:16]:
    print(f"   {0.5*(e[i]+e[i+1]):6.1f} deg   weight={hist[i]:9.0f}")

vis = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
for (x0, y0, x1, y1), a in zip(ln, ang):
    c = (int(a * 2) % 256, 80, 255 - int(a * 2) % 256)
    cv2.line(vis, (x0, y0), (x1, y1), c, 3)
cv2.imwrite("segments.png", cv2.resize(vis, (750, 1000)))
