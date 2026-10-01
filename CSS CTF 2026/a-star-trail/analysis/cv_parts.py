"""Buoc 2: tach tam nut (vong tron da giac) va mot dash cua net dut.

Dash: component keo dai (ti so minAreaRect > 2.5), dien tich nho.
Nut: component gom vong tron + noi long, dien tich lon hon nhieu.
"""

import cv2
import numpy as np

SRC = r"C:\Users\Administrator\Downloads\CTFWU\CSS CTF 2026\_wip\a-star-trail\files\A_Star_Trail.png"
img = cv2.imread(SRC, cv2.IMREAD_COLOR)
white = cv2.inRange(img, (200, 200, 200), (255, 255, 255))
n, lab, stats, cent = cv2.connectedComponentsWithStats(white, connectivity=8)

dashes, nodes, glyphs = [], [], []
for i in range(1, n):
    a = int(stats[i, cv2.CC_STAT_AREA])
    if a < 120:
        continue
    pts = (lab == i).astype(np.uint8) * 255
    cnts, _ = cv2.findContours(pts, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        continue
    c = max(cnts, key=cv2.contourArea)
    (cx, cy), rr = cv2.minEnclosingCircle(c)
    x, y, bw, bh = cv2.boundingRect(c)
    rect = cv2.minAreaRect(c)
    (rw, rh) = rect[1]
    if rw < 1 or rh < 1:
        continue
    elong = max(rw, rh) / min(rw, rh)
    fill = a / (np.pi * rr * rr + 1e-9)          # vong tron thi fill thap
    span = max(bw, bh)
    if a >= 4000 and span >= 90 and elong < 3.2:
        nodes.append(dict(id=i, area=a, cx=int(cx), cy=int(cy), r=int(rr),
                          elong=round(elong, 2), fill=round(fill, 2), span=span))
    elif elong >= 2.6 and span < 120 and a < 6000:
        dashes.append(dict(id=i, area=a, cx=int(cx), cy=int(cy), span=span, ang=int(rect[2])))
    elif a < 2600:
        glyphs.append((i, a, int(cx), int(cy)))

print("nut %d | dash %d | chu %d" % (len(nodes), len(dashes), len(glyphs)))
print("\nTAM NUT (sap theo x):")
for d in sorted(nodes, key=lambda d: d["cx"]):
    print("  (%4d,%4d) R=%3d area=%6d fill=%.2f elong=%.2f"
          % (d["cx"], d["cy"], d["r"], d["area"], d["fill"], d["elong"]))

np.save(r"C:\Users\Administrator\AppData\Local\Temp\dashes.npy",
        np.array([[d["cx"], d["cy"], d["span"], d["ang"], d["area"]] for d in dashes]))
print("\nda luu %d dash ra file tam" % len(dashes))
