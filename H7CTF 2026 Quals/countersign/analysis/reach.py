import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import walk

S = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")))
recs = {int(k): v for k, v in S["recs"].items()}
start = S["entry"]

goal = [t for t, r in recs.items()
        if r["ln"] >= 2 and bytes.fromhex(r["code"])[0] == 13
        and bytes.fromhex(r["code"])[1] == 14]
print("start=%d goal=%s records=%d" % (start, goal, len(recs)))

# do thi chi dung entry THAT
adj = {}
for t, r in recs.items():
    es = []
    for i, e in enumerate(r["edges"]):
        if S["val"].get("%d:%d" % (t, i)):
            es.append(tuple(e[:2]))
    adj[t] = es
print("tong canh that:", sum(len(v) for v in adj.values()))

seen, stack = {start}, [start]
while stack:
    u = stack.pop()
    for _, v in adj.get(u, []):
        if v not in seen:
            seen.add(v)
            stack.append(v)
print("duoc tiep (bo qua rang buoc bit): %d/%d" % (len(seen), len(recs)))
print("goal dat duoc khong:", [g in seen for g in goal])

# duong di ngan nhat toi goal
from collections import deque
for g in goal:
    q = deque([(start, [start])])
    hit = None
    while q:
        u, p = q.popleft()
        if u == g:
            hit = p
            break
        for _, v in adj.get(u, []):
            if v not in p:
                q.append((v, p + [v]))
    print("  toi %s: %s" % (g, "->".join(map(str, hit)) if hit else "khong co duong"))

# cac canh di vao goal
for g in goal:
    inc = [(t, b) for t, r in recs.items() for (b, v) in adj.get(t, []) if v == g]
    print("  canh vao %s: %s" % (g, inc))

# do nhay: bit cua moi record co phu thuoc input khong
print("\n== moi record: bit co doi theo input? ==")
for t, r in sorted(recs.items()):
    if r["f1"] == 255:
        continue
    code = bytes.fromhex(r["code"])
    vals = set()
    for probe in (bytes(24), b"\xff" * 24, b"\x55" * 24):
        st = walk.run(code, r["ln"], probe)
        if st:
            vals.add((st[2][r["f1"]] >> (r["f2"] & 31)) & 1)
    if len(vals) > 1:
        print("   %d (reg=%d bit=%d) DOI, canh that=%s" %
              (t, r["f1"], r["f2"], adj.get(t)))
