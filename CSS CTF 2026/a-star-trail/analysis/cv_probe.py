"""Kiem moi cap hanh tinh: doan noi co phai la mot net dut that khong.

Dung distance transform cua mask trang: mau moi 6 doc theo doan, dem ty le mau
nam sat vat trang (<= 12 px). Net dut that -> phu ~0.45-0.95 va xen ke run/gap;
doan khong phai canh -> phu thap, hoac chi co vung tron khi cat qua chu/net khac.
"""

import math
import cv2
import numpy as np

SRC = r"C:\Users\Administrator\Downloads\CTFWU\CSS CTF 2026\_wip\a-star-trail\files\A_Star_Trail.png"
img = cv2.imread(SRC, cv2.IMREAD_COLOR)
white = cv2.inRange(img, (200, 200, 200), (255, 255, 255))

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
HANDED = {  # 20 canh doc bang mat lan dau
    frozenset(("C3810-ASQUAX-8", "BARAT-BARAT")): 6.3,
    frozenset(("C3810-ASQUAX-8", "BACONITE")): 2.1,
    frozenset(("BACONITE", "BARAT-BARAT")): 9.8,
    frozenset(("BARAT-BARAT", "JIP-REIA")): 1.4,
    frozenset(("BARAT-BARAT", "PALLUS-XA")): 1.4,
    frozenset(("JIP-REIA", "TAYLOR-3489")): 5.5,
    frozenset(("JIP-REIA", "12-PUCK-8")): 0.4,
    frozenset(("PALLUS-XA", "12-PUCK-8")): 1.8,
    frozenset(("PALLUS-XA", "HEMENS-RAJA-2")): 2.5,
    frozenset(("12-PUCK-8", "HEMENS-RAJA-2")): 3.6,
    frozenset(("HEMENS-RAJA-2", "TAMMY ASTEROID")): 3.7,
    frozenset(("HEMENS-RAJA-2", "10-49-SLATER-4090")): 6.0,
    frozenset(("TAYLOR-3489", "TAMMY ASTEROID")): 3.2,
    frozenset(("TAMMY ASTEROID", "VERGINON")): 2.8,
    frozenset(("VERGINON", "10-49-SLATER-4090")): 7.5,
}

dist = cv2.distanceTransform(cv2.bitwise_not(white), cv2.DIST_L2, 3)
H, W = dist.shape


def runs(flags):
    out, cur, prev = [], 0, None
    for f in flags:
        if f == prev:
            cur += 1
        else:
            if prev is not None:
                out.append((prev, cur))
            prev, cur = f, 1
    if prev is not None:
        out.append((prev, cur))
    return out


def probe(a, b):
    ax, ay, ar = NODE[a]
    bx, by, br = NODE[b]
    L = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / L, (by - ay) / L
    t0, t1 = ar + 6, L - br - 6
    if t1 - t0 < 60:
        return None
    ts = np.arange(t0, t1, 6.0)
    flags = [dist[int(round(ay + t * uy)), int(round(ax + t * ux))] <= 12 for t in ts]
    cov = sum(flags) / len(flags)
    rr = [n for f, n in runs(flags) if f]
    gaps = [n for f, n in runs(flags) if not f]
    return dict(cov=round(cov, 2), nrun=len(rr), maxrun=max(rr or [0]),
                maxgap=max(gaps or [0]), length=int(t1 - t0))


print("=== 55 cap nut ===")
rows = []
for a, b in [(x, y) for i, x in enumerate(NODE) for y in list(NODE)[i + 1:]]:
    p = probe(a, b)
    if not p:
        continue
    tag = "CANH-CUA-TOI(%.1f)" % HANDED[frozenset((a, b))] if frozenset((a, b)) in HANDED else ""
    looks = bool(p["cov"] >= 0.4 and p["nrun"] >= 2 and p["maxrun"] <= 9 and p["maxgap"] <= 6)
    rows.append((looks, tag, a, b, p))
for looks, tag, a, b, p in sorted(rows, key=lambda r: (-r[0], -r[4]["cov"])):
    if looks or tag:
        print("  %-4s %-22s %-18s %-18s cov=%.2f run=%d maxrun=%d maxgap=%d len=%d"
              % ("DUNG" if looks else "SAI", tag or "(khong doc)", a, b,
                 p["cov"], p["nrun"], p["maxrun"], p["maxgap"], p["length"]))
