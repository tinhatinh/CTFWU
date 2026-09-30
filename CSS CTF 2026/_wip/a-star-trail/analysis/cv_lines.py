"""Buoc 3: gom cac dash thanh duong thang, roi noi hai dau vao nut nao.

Loc dash nam trong vong cua mot hanh tinh (do noi long cua no rat giong dash),
loc luon sat khung anh. Gom cum theo (goc, khoang cach vuong goc, khe hop).
"""

import math
import cv2
import numpy as np

SRC = r"C:\Users\Administrator\Downloads\CTFWU\CSS CTF 2026\_wip\a-star-trail\files\A_Star_Trail.png"
img = cv2.imread(SRC, cv2.IMREAD_COLOR)
white = cv2.inRange(img, (200, 200, 200), (255, 255, 255))
n, lab, stats, _ = cv2.connectedComponentsWithStats(white, connectivity=8)

NODE = {
    "C3810-ASQUAX-8": (439, 675, 191),
    "BACONITE": (730, 1017, 76),
    "BARAT-BARAT": (1174, 722, 86),
    "PALLUS-XA": (1388, 1286, 266),
    "JIP-REIA": (1622, 372, 139),
    "12-PUCK-8": (1892, 822, 77),
    "HEMENS-RAJA-2": (2104, 1430, 137),
    "TAYLOR-3489": (2342, 426, 112),
    "TAMMY ASTEROID": (2611, 977, 213),
    "10-49-SLATER-4090": (2911, 1481, 115),
    "VERGINON": (3255, 1115, 40),
}
# Hai hanh tinh lon cat sat khung: mui trai-duoi va goc phai-tren
REGIONS = {
    "EARTH": lambda x, y: (x - 250) ** 2 + (y - 2150) ** 2 < 1250 ** 2,
    "LANCER-RXKRD": lambda x, y: (x - 3450) ** 2 + (y + 480) ** 2 < 1500 ** 2,
}

dashes = []
for i in range(1, n):
    a = int(stats[i, cv2.CC_STAT_AREA])
    if not (120 <= a <= 6000):
        continue
    pts = (lab == i).astype(np.uint8) * 255
    cnts, _ = cv2.findContours(pts, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        continue
    c = max(cnts, key=cv2.contourArea)
    (cx, cy), rr = cv2.minEnclosingCircle(c)
    rect = cv2.minAreaRect(c)
    (rw, rh) = rect[1]
    if min(rw, rh) < 1:
        continue
    elong = max(rw, rh) / min(rw, rh)
    if elong < 2.6 or max(rw, rh) > 130:
        continue
    if cx < 95 or cy < 95 or cx > img.shape[1] - 95 or cy > img.shape[0] - 95:
        continue                                   # sat khung anh
    if any((cx - px) ** 2 + (cy - py) ** 2 < (pr + 12) ** 2 for px, py, pr in NODE.values()):
        continue                                   # noi long cua hanh tinh
    ang = rect[2] % 180
    if elong and max(rw, rh) == rh:
        ang = (ang + 90) % 180
    dashes.append((cx, cy, ang, max(rw, rh), a))

print("dash sau loc:", len(dashes))

parent = list(range(len(dashes)))


def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def union(x, y):
    rx, ry = find(x), find(y)
    if rx != ry:
        parent[ry] = rx


def adiff(a, b):
    return min((a - b) % 180, (b - a) % 180)


for i in range(len(dashes)):
    for j in range(i + 1, len(dashes)):
        ax, ay, aa = dashes[i][:3]
        bx, by, ba = dashes[j][:3]
        if adiff(aa, ba) > 9:
            continue
        dx, dy = bx - ax, by - ay
        gap = math.hypot(dx, dy)
        if gap > 230:
            continue
        th = math.radians(aa)
        perp = abs(-math.sin(th) * dx + math.cos(th) * dy)
        if perp < 26:
            union(i, j)

groups = {}
for i, d in enumerate(dashes):
    groups.setdefault(find(i), []).append(d)

lines = []
for g in groups.values():
    if len(g) < 2:
        continue
    ang = np.average([d[2] for d in g], weights=[d[4] for d in g])
    th = math.radians(ang)
    ux, uy = math.cos(th), math.sin(th)
    proj = [d[0] * ux + d[1] * uy for d in g]
    a0, a1 = min(proj), max(proj)
    px0, py0 = a0 * ux + (np.average([d[1] * ux - d[0] * uy for d in g])) * (-uy), \
               a0 * uy + (np.average([d[1] * ux - d[0] * uy for d in g])) * uy
    px1, py1 = a1 * ux + (np.average([d[1] * ux - d[0] * uy for d in g])) * (-uy), \
               a1 * uy + (np.average([d[1] * ux - d[0] * uy for d in g])) * uy
    lines.append(dict(ang=round(ang), dash=len(g), length=round(a1 - a0),
                      p0=(int(px0), int(py0)), p1=(int(px1), int(py1)),
                      mid=(int((px0 + px1) / 2), int((py0 + py1) / 2))))


def near(pt):
    x, y = pt
    best, bd = None, 1e18
    for name, (nx, ny, nr) in NODE.items():
        d = max(0.0, math.hypot(x - nx, y - ny) - nr)
        if d < bd:
            best, bd = name, d
    for name, fn in REGIONS.items():
        if fn(x, y):
            return best, bd, name
    return best, bd, None


print("\n%d duong:" % len(lines))
for L in sorted(lines, key=lambda L: (L["p0"][0], L["p0"][1])):
    n0, d0, r0 = near(L["p0"])
    n1, d1, r1 = near(L["p1"])
    print("  %-5s->%-18s %-5s->%-18s dash=%2d dai=%4d goc=%3d mid=%s"
          % (n0, "(%.0f)" % d0 if not r0 else r0, n1, "(%.0f)" % d1 if not r1 else r1,
             L["dash"], L["length"], L["ang"], L["mid"]))
