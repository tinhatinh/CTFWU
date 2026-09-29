"""Build a joint-only mask: blur out the granite speckle, keep the wide dark mortar bands."""
import cv2
import numpy as np

img = cv2.imread("../files/photo.png", cv2.IMREAD_GRAYSCALE).astype(np.float32)
H, W = img.shape
g = cv2.GaussianBlur(img, (0, 0), 22)                      # kills the speckle
bg = cv2.GaussianBlur(g, (0, 0), 190)                      # illumination
d = cv2.GaussianBlur(bg - g, (0, 0), 6)                    # >0 where a joint darkens the stone
sc = cv2.GaussianBlur(np.abs(bg - g), (0, 0), 190) + 1e-3
norm = d / (1.15 * sc)
mask = (norm > 0.42).astype(np.uint8)
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
yy, xx = np.mgrid[0:H, 0:W]
valid = np.ones((H, W), np.uint8)
valid[yy < np.maximum(0.0, 0.1818 * (xx - 780)) + 60] = 0
valid[:60, :] = 0
cv2.rectangle(valid, (760, 1280), (2640, 3060), 0, -1)
mask *= valid
cv2.imwrite("jointmask.png", mask * 255)
cv2.imwrite("jointmask_over.png",
            cv2.addWeighted(cv2.imread("../files/photo.png"), 1,
                            cv2.cvtColor((mask * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR), 0.35, 0))
n, lab, st, cent = cv2.connectedComponentsWithStats(mask, 8)
a = st[1:, cv2.CC_STAT_AREA]
w = st[1:, cv2.CC_STAT_WIDTH]
print(f"components {n-1}: area p50={np.median(a):.0f} p90={np.percentile(a,90):.0f} max={a.max()}")
print(f"           width p50={np.median(w):.0f} p90={np.percentile(w,90):.0f} max={w.max()}")
print("coverage:", mask.mean().round(4))
