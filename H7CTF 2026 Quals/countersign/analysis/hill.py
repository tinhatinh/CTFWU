"""Tim 24 byte input dua cuoc di bo doc duong toi record LOADFLAG+SETDONE.

Duong di mong muon lay tu BFS tren do thi canh-that (canh co stamp hop le).
score(input) = do dai prefix khop duong mong muon, tinh khi xuyen bo ghi.
Tim kiem: hill-clinh + khoi dong lai, vi moi rang buoc la 1 bit cua mot word
u32 duoc nap truc tiep tu 4 byte input -> nhieu loi dan.
"""
import json
import os
import random
import struct
import sys
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import search
import walk

HERE = os.path.dirname(os.path.abspath(__file__))


def goal_path(bytag, valid, start, goal):
    adj = {}
    for t, r in bytag.items():
        adj[t] = [walk.edge(s)[1] for i, s in enumerate(r["stamps"])
                  if valid.get((t, i))]
    q = deque([(start, [start])])
    while q:
        u, p = q.popleft()
        if u == goal:
            return p
        for v in adj.get(u, []):
            if v not in p:
                q.append((v, p + [v]))
    return None


def trace(bytag, valid, start, inp, want):
    """Do dai khop cua duong di voi `want`."""
    regs = [0] * 32
    tag, seen = start, set()
    hit = 1 if (want and want[0] == start) else 0
    for _ in range(200):
        kind, tag, regs = walk.step(bytag, tag, inp, regs, valid)
        if kind != "go":
            return hit, kind, tag
        if tag in seen:
            return hit, "cycle", tag
        seen.add(tag)
        if len(want) > hit and tag == want[hit]:
            hit += 1
        else:
            return hit, "diverge", tag
    return hit, "long", tag


def main():
    S, bytag, valid = search.load_state()
    start = S["entry"]
    goal = next(t for t, r in bytag.items()
                if r["ln"] >= 2 and r["code"][0] == 13 and r["code"][1] == 14)
    want = goal_path(bytag, valid, start, goal)
    print("[*] start=%d goal=%d duong mong muon dai %d" % (start, goal, len(want or [])))
    if not want:
        print("[-] khong co duong")
        return 1
    rng = random.Random()
    best = (0, None)
    for att in range(400):
        inp = bytearray(rng.randrange(256) for _ in range(24))
        cur, _, _ = trace(bytag, valid, start, bytes(inp), want)
        improved = True
        while improved and cur < len(want):
            improved = False
            for pos in range(24):
                for v in range(256):
                    if v == inp[pos]:
                        continue
                    old = inp[pos]
                    inp[pos] = v
                    sc, _, _ = trace(bytag, valid, start, bytes(inp), want)
                    if sc > cur:
                        cur, improved = sc, True
                        break
                    inp[pos] = old
                if improved:
                    break
        if cur > best[0]:
            best = (cur, bytes(inp))
            print("   thu %3d: khop %d/%d  input=%s" % (att, cur, len(want), best[1].hex()))
        if cur >= len(want):
            break
    inp = best[1]
    if not inp:
        print("[-] khong tim duoc")
        return 1
    kind, tag, _ = trace(bytag, valid, start, inp, want)
    print("[*] ket qua tot nhat: khop=%d kind=%s tag=%d" % (best[0], kind, tag))
    if best[0] >= len(want):
        print("[+] INPUT THANG LOI:", inp.hex())
        open(os.path.join(HERE, "win.hex"), "w").write(inp.hex() + "\n")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
