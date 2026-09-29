"""Stack thin horizontal strips from several image heights so the sett width can be counted."""
import cv2
import numpy as np

img = cv2.imread("../files/photo.png")
H, W = img.shape[:2]
SC = 0.5
BANDS = [(250, 450), (900, 1100), (1700, 1900), (2500, 2700), (3300, 3500), (3750, 3950)]
rows = []
for y0, y1 in BANDS:
    c = img[y0:y1, 0:W].copy()
    for x in range(0, W, 200):
        cv2.line(c, (x, 0), (x, c.shape[0]), (0, 200, 255), 1)
    c = cv2.resize(c, None, fx=SC, fy=SC, interpolation=cv2.INTER_AREA)
    cv2.putText(c, f"y {y0}-{y1}", (6, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    rows.append(c)
out = np.vstack([np.vstack([r, np.full((14, r.shape[1], 3), 40, np.uint8)]) for r in rows])
cv2.imwrite("strips.png", out)
print("wrote strips.png", out.shape, " scale:", SC, " grid every", int(200 * SC), "px")
