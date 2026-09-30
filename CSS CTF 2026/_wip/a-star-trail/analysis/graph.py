"""Do thi A_Star_Trail.png -> duong EARTH den LANCER-RXKRD ngan nhat.

Canh doc truc tiep tren anh (moi nhan gan nam giua doan), danh sach o EDGE.
"""

import heapq
import itertools

EDGE = [
    ("C3810-ASQUAX-8", "BARAT-BARAT", 6.3),
    ("C3810-ASQUAX-8", "BACONITE", 2.1),
    ("BACONITE", "BARAT-BARAT", 9.8),
    ("BACONITE", "EARTH", 5.0),
    ("EARTH", "PALLUS-XA", 10.7),
    ("BARAT-BARAT", "JIP-REIA", 1.4),
    ("BARAT-BARAT", "PALLUS-XA", 1.4),
    ("JIP-REIA", "TAYLOR-3489", 5.5),
    ("JIP-REIA", "12-PUCK-8", 0.4),
    ("PALLUS-XA", "12-PUCK-8", 1.8),
    ("PALLUS-XA", "HEMENS-RAJA-2", 2.5),
    ("12-PUCK-8", "HEMENS-RAJA-2", 3.6),
    ("HEMENS-RAJA-2", "TAMMY ASTEROID", 3.7),
    ("HEMENS-RAJA-2", "10-49-SLATER-4090", 6.0),
    ("TAYLOR-3489", "TAMMY ASTEROID", 3.2),
    ("TAYLOR-3489", "LANCER-RXKRD", 2.6),
    ("TAMMY ASTEROID", "LANCER-RXKRD", 10.1),
    ("TAMMY ASTEROID", "VERGINON", 2.8),
    ("VERGINON", "LANCER-RXKRD", 8.5),
    ("VERGINON", "10-49-SLATER-4090", 7.5),
]
SRC, DST = "EARTH", "LANCER-RXKRD"
LIMIT = 25.0

g = {}
for a, b, w in EDGE:
    g.setdefault(a, []).append((b, w))
    g.setdefault(b, []).append((a, w))

print("nut: %d  canh: %d" % (len(g), len(EDGE)))
for n, adj in sorted(g.items()):
    print("  %-20s bac %d" % (n, len(adj)))

dist = {SRC: 0.0}
prev = {}
pq = [(0.0, SRC)]
while pq:
    d, u = heapq.heappop(pq)
    if d > dist.get(u, 1e18):
        continue
    for v, w in g.get(u, []):
        if d + w < dist.get(v, 1e18) - 1e-9:
            dist[v] = d + w
            prev[v] = u
            heapq.heappush(pq, (d + w, v))

path, n = [], DST
while n:
    path.append(n)
    n = prev.get(n)
path.reverse()
total = round(dist[DST], 1)
print("\nDijkstra: %s = %.1f ngay" % (" -> ".join(path), total))

# Liet ke moi duong don gian duoi 25 ngay de biet co duy nhat khong
found = []


def walk(node, seen, cost, acc):
    if cost > LIMIT:
        return
    if node == DST:
        found.append((round(cost, 1), list(acc)))
        return
    for v, w in g.get(node, []):
        if v in seen:
            continue
        walk(v, seen | {v}, round(cost + w, 4), acc + [v])


walk(SRC, {SRC}, 0.0, [SRC])
found.sort()
print("\ncac duong < %.0f ngay (%d duong):" % (LIMIT, len(found)))
for c, p in found:
    mark = " <== NGAN NHAT" if c == total and p == path else ""
    print("  %5.1f  %s%s" % (c, " -> ".join(p), mark))

flag = "CSSCTF{%s-%.1f}" % ("".join(p[0] for p in path), total)
print("\nFLAG: %s" % flag)
