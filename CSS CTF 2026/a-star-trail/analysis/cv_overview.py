"""Trich xuat cac net net dut tren A_Star_Trail.png bang OpenCV, khong doc bang mat.

Buoc 1 nay chi dem va phan loai connected component de biet tam dong nut, canh
va chu nam o dau.
"""

import cv2
import numpy as np

SRC = r"C:\Users\Administrator\Downloads\CTFWU\CSS CTF 2026\_wip\a-star-trail\files\A_Star_Trail.png"

img = cv2.imread(SRC, cv2.IMREAD_COLOR)
h, w = img.shape[:2]
white = cv2.inRange(img, (200, 200, 200), (255, 255, 255))
print("anh %dx%d, pixel trang %d" % (w, h, int(white.sum() / 255)))

n, lab, stats, cent = cv2.connectedComponentsWithStats(white, connectivity=8)
areas = stats[:, cv2.CC_STAT_AREA]
print("so component:", n - 1)
hist = {"nho(<400)": 0, "chu(400-2500)": 0, "net dut(2500-20000)": 0, "lon(>20000)": 0}
big = []
for i in range(1, n):
    a = int(areas[i])
    if a < 400:
        hist["nho(<400)"] += 1
    elif a < 2500:
        hist["chu(400-2500)"] += 1
    elif a < 20000:
        hist["net dut(2500-20000)"] += 1
    else:
        hist["lon(>20000)"] += 1
        x, y, bw, bh = stats[i, 0], stats[i, 1], stats[i, 2], stats[i, 3]
        big.append((a, i, (x, y, bw, bh)))
print(hist)
print("\ncomponent lon (area, id, bbox):")
for a, i, bb in sorted(big, reverse=True):
    pts = (lab == i).astype(np.uint8) * 255
    cnts, _ = cv2.findContours(pts, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    (cx, cy), r = cv2.minEnclosingCircle(max(cnts, key=cv2.contourArea))
    print("  area=%7d bbox=%-28s tam=(%4d,%4d) R=%4d" % (a, str(bb), cx, cy, r))
