"""Find the two cobblestone-lattice vanishing points with a Hough transform."""
import cv2
import numpy as np
import sys

img = cv2.imread("../files/photo.png")
H, W = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# joints are dark, thin, and surrounded by bright stone -> black-hat brings them out
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))
bh = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)
edges = cv2.Canny(bh, 40, 110)

# keep only the paving: drop the bird + its shadow box, and the slab band at the top
mask = np.ones_like(edges) * 255
mask[:, :] = 255
cv2.rectangle(mask, (900, 1450), (2500, 2900), 0, -1)   # bird + shadow
mask[:250, :] = 0                                        # top slab band
edges = cv2.bitwise_and(edges, mask)
cv2.imwrite("edges.png", edges)

lines = cv2.HoughLines(edges, 1, np.pi / 720, threshold=220)
print("hough lines:", 0 if lines is None else len(lines))
if lines is None:
    sys.exit(1)
ln = lines[:, 0]                      # (rho, theta)
theta = ln[:, 1] % np.pi              # fold to [0, pi)
rho = np.where(ln[:, 1] > np.pi, -ln[:, 0], ln[:, 0])

hist, edgesb = np.histogram(theta, bins=180, range=(0, np.pi))
order = np.argsort(hist)[::-1]
print("theta peaks (deg from +y axis of the normal, count):")
used = []
for i in order:
    if hist[i] < 25:
        break
    c = (edgesb[i] + edgesb[i + 1]) / 2 * 180 / np.pi
    if any(abs(c - u) < 12 for u in used):
        continue
    used.append(c)
    print(f"   {c:6.1f} deg   n={hist[i]}")
