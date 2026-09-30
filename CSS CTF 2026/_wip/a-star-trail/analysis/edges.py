"""Suy cac canh cua do thi tren A_Star_Trail.png bang hinh hoc.

Toa do lay tu anh goc 3780x1890 ( nhan x1.89 tu ban hien thi 2000x1000).
Moi nhan canh (con so ngay) nam gan diem trung diem cua doan thang noi hai dau.
Thu moi cap nut, tinh khoang cach tu nhan den doan va lech khoi trung diem;
cap nao nho nhat thi duoc chon, va in ra de kiem bang mat tren anh.
"""

import math

NODES = {
    "C3810-ASQUAX-8": (454, 671),
    "BACONITE": (733, 1021),
    "BARAT-BARAT": (1172, 718),
    "JIP-REIA": (1603, 350),
    "PALLUS-XA": (1374, 1266),
    "12-PUCK-8": (1890, 822),
    "TAYLOR-3489": (2344, 431),
    "HEMENS-RAJA-2": (2079, 1427),
    "TAMMY ASTEROID": (2612, 964),
    "10-49-SLATER-4090": (2907, 1474),
    "VERGINON": (3255, 1115),
}
# Hai hanh tinh lon: dung diem neo tren ria noi cac net dan cham vao
ANCHORS = {
    "EARTH": [(747, 1458), (1180, 1560), (400, 1300)],
    "LANCER-RXKRD": [(2700, 300), (3000, 560), (3300, 700)],
}
LABELS = {
    "6.3": (826, 641), "2.1": (713, 845), "9.8": (1013, 941), "1.4a": (1334, 505),
    "1.4b": (1374, 894), "5.0": (905, 1219), "10.7": (1036, 1312), "5.5": (2009, 463),
    "0.4": (1827, 575), "1.8": (1648, 964), "2.5": (1778, 1427), "3.6": (2054, 1074),
    "2.6": (2691, 391), "3.2": (2555, 643), "3.7": (2293, 1143), "6.0": (2548, 1529),
    "10.1": (2922, 713), "2.8": (3049, 971), "8.5": (3389, 907), "7.5": (3219, 1329),
}


def pts():
    out = [(k, v) for k, v in NODES.items()]
    for k, lst in ANCHORS.items():
        for i, p in enumerate(lst):
            out.append(("%s#%d" % (k, i), p))
    return out


def seg_dist(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


P = pts()
for name, lp in sorted(LABELS.items(), key=lambda kv: kv[1][0]):
    scored = []
    for i in range(len(P)):
        for j in range(i + 1, len(P)):
            (n1, a), (n2, b) = P[i], P[j]
            if n1.split("#")[0] == n2.split("#")[0]:
                continue
            d = seg_dist(lp, a, b)
            if d > 90:
                continue
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            off = math.hypot(lp[0] - mx, lp[1] - my)
            length = math.hypot(a[0] - b[0], a[1] - b[1])
            if off > 0.45 * length:
                continue
            scored.append((d + off * 0.4, d, off, n1.split("#")[0], n2.split("#")[0]))
    scored.sort()
    top = ", ".join("%s-%s(d=%.0f,o=%.0f)" % (s[3], s[4], s[1], s[2]) for s in scored[:3])
    print("%-5s %-12s -> %s" % (name, str(lp), top or "KHONG CO CAP NAO"))
