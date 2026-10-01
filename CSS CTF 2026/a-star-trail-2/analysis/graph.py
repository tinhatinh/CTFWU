"""Dung do thi tu map.zip va so sanh hai cach hieu "hop ly".

Moi file map/<ID>.md gom `Coords: x, y` va danh sach [[neighbour]]. Khong trong so
ngay nhu phien 1, nen phai thu: (a) it chan nhat (BFS), (b) quang duoa ngan nhat
theo toa do (Dijkstra). Bai chi ra co khi duong tra loi duy nhat.
"""

import heapq
import math
import re
import zipfile
from collections import defaultdict, deque

ZIP = r"C:\Users\Administrator\Downloads\CTFWU\CSS CTF 2026\_wip\a-star-trail-2\files\map.zip"
SRC, DST = "S0jRxc", "yRJyDb"

LINK = re.compile(r"\[\[([^\]|#]+)\]\]")
COORD = re.compile(r"Coords:\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)")

z = zipfile.ZipFile(ZIP)
names = [n for n in z.namelist() if n.endswith(".md")]
node = {}
out = defaultdict(list)
for name in names:
    text = z.read(name).decode("utf-8", "replace")
    head = re.match(r"#\s*(\S+)", text)
    nid = head.group(1) if head else name.split("/")[-1][:-3]
    m = COORD.search(text)
    if not m:
        print("THIEU COORDS:", name)
        continue
    node[nid] = (float(m.group(1)), float(m.group(2)))
    for t in LINK.findall(text):
        out[nid].append(t.strip())

print("file md: %d | nut co toa do: %d" % (len(names), len(node)))
dangling = {b for a in out for b in out[a] if b not in node}
print("link tro toi nut khong co file:", len(dangling), sorted(dangling)[:5])

pairs = {(a, b) for a in out for b in out[a] if b in node}
directed = len(pairs)
undirected = len({frozenset(p) for p in pairs})
asym = [(a, b) for (a, b) in pairs if a not in out.get(b, [])]
print("canh chieu: %d | khong huong (hop nhat): %d | lech chieu: %d" % (directed, undirected, len(asym)))
deg = [len([b for b in out[a] if b in node]) for a in node]
print("bac: trung binh %.2f, min %d, max %d" % (sum(deg) / len(deg), min(deg), max(deg)))


def bfs_hops(adj):
    dist, prev = {SRC: 0}, {SRC: []}
    q = deque([SRC])
    while q:
        u = q.popleft()
        for v in adj.get(u, ()):
            if v not in dist:
                dist[v] = dist[u] + 1
                prev[v] = prev[u] + [v]
                q.append(v)
    return (prev.get(DST), dist.get(DST))


def dijkstra_km(adj):
    def w(a, b):
        ax, ay = node[a]
        bx, by = node[b]
        return math.hypot(ax - bx, ay - by)
    dist, prev = {SRC: 0.0}, {SRC: []}
    pq = [(0.0, SRC)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, 1e18):
            continue
        for v in adj.get(u, ()):
            nd = d + w(u, v)
            if nd < dist.get(v, 1e18) - 1e-12:
                dist[v] = nd
                prev[v] = prev[u] + [v]
                heapq.heappush(pq, (nd, v))
    return (prev.get(DST), dist.get(DST))


und = defaultdict(set)
for a, b in pairs:
    und[a].add(b)
    und[b].add(a)
diradj = {a: set(b for b in out[a] if b in node) for a in out}

for label, adj in (("BFS duoc chieu", diradj), ("BFS vo huong", und)):
    path, d = bfs_hops(adj)
    print("\n%s: %s hop=%s" % (label, "->".join(path) if path else "khong toi", d))
for label, adj in (("Dijkstra duoc chieu", diradj), ("Dijkstra vo huong", und)):
    path, d = dijkstra_km(adj)
    print("%s: %s  quang duong=%.3f" % (label, "->".join(path) if path else "khong toi", d or -1))
