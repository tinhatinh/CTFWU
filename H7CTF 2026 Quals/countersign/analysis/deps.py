"""Do dung: bit input nao dieu khien duoc tung node tren duong di.

Voi moi node u tren duong BFS toi muc tieu: lat tung trong 192 bit input (tu
base), di bo lai TU DAU, va xem (a) duong co con di toi u khong, (b) bit quyet
dinh tai u co doi khong.  Ket qua cho biet path co kha thi hay khong, thay vi
doan mo.
"""
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import search
import walk

HERE = os.path.dirname(os.path.abspath(__file__))
S, bytag, valid = search.load_state()
start = S["entry"]
goal = next(t for t, r in bytag.items()
            if r["ln"] >= 2 and r["code"][0] == 13 and r["code"][1] == 14)

adj = {t: [walk.edge(s)[1] for i, s in enumerate(r["stamps"]) if valid.get((t, i))]
       for t, r in bytag.items()}
from collections import deque
q = deque([(start, [start])])
want = None
while q:
    u, p = q.popleft()
    if u == goal:
        want = p
        break
    for v in adj.get(u, []):
        if v not in p:
            q.append((v, p + [v]))
print("duong BFS:", len(want) if want else None)

base = bytes(24)


def seq_and_bit(inp, at):
    """Di bo, tra ve (danh sach tag, gia tri bit tai node `at` hoac None)."""
    regs = [0] * 32
    tags, bits = [], {}
    tag = start
    for i in range(200):
        if tag not in bytag:
            return tags, bits, "unknown"
        rec = bytag[tag]
        st = walk.run(rec["code"], rec["ln"], inp, regs)
        if st is None:
            return tags, bits, "loop"
        printed, loaded, regs = st
        tags.append(tag)
        if printed:
            return tags, bits, "print"
        bpl = 255 if rec["f1"] == 255 else \
            ((regs[rec["f1"]] >> rec["f2"]) & 1 if rec["f1"] < 32 and rec["f2"] < 32 else 0)
        bits[tag] = bpl
        nxt = rec["f3"]
        for j, s in enumerate(rec["stamps"]):
            t, tt = walk.edge(s)
            if t == bpl and valid.get((tag, j)):
                nxt = tt
                break
        if nxt in tags:
            return tags, bits, "cycle"
        tag = nxt
    return tags, bits, "long"


t0, b0, k0 = seq_and_bit(base, None)
print("base walk: %d node, ket=%s" % (len(t0), k0))
common = sum(1 for a, b in zip(t0, want) if a == b)
print("khop voi duong BFS: %d/%d" % (common, min(len(t0), len(want))))

print("\n== bit dieu khien duoc cua tung node trong 15 node dau ==")
for idx in range(min(15, len(want))):
    u = want[idx]
    ctl = []
    for bi in range(24):
        for bj in range(8):
            inp = bytearray(base)
            inp[bi] ^= 1 << bj
            t1, b1, k1 = seq_and_bit(bytes(inp), None)
            if len(t1) > idx and t1[idx] == u and b1.get(u) != b0.get(u):
                ctl.append((bi, bj, b0.get(u), b1[u]))
    print("  node %2d %-6s bit=%s  so bit input anh huong=%d %s"
          % (idx, u, b0.get(u), len(ctl), ctl[:6]))
