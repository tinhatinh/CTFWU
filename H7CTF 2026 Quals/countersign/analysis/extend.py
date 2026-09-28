"""Mo rong dan buoc prefix: tai node bi ket, thu lat dong thoi toi da 3 bit input.

Ly do: cac bieu thuc bit co nho (ADD) nen mot bit it khi thay duoc ket qua,
nhung 2-3 bit thi du.  Moi lan thuare simulate lai toan bo duong (walk.walk),
nên khong the "dao" o ngoai le.
"""
import itertools
import json
import os
import random
import sys
import time

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


def bfs_path(src, dst):
    q = deque([(src, [src])])
    while q:
        u, p = q.popleft()
        if u == dst:
            return p
        for v in adj.get(u, []):
            if v not in p:
                q.append((v, p + [v]))
    return None


def prefix_match(inp, want):
    seq, kind, _ = walk.walk(bytag, start, inp, valid=valid)
    seq = [start] + seq
    n = 0
    while n < len(seq) and n < len(want) and seq[n] == want[n]:
        n += 1
    return n


def main():
    want = bfs_path(start, goal)
    print("[*] duong dinh huong dai %d" % len(want))
    rng = random.Random(int(time.time()) & 0xFFFF)
    bits = [(i, j) for i in range(24) for j in range(8)]
    best = None
    for att in range(40):
        inp = bytearray(rng.randrange(256) for _ in range(24))
        cur = prefix_match(bytes(inp), want)
        improved = True
        while improved and cur < len(want):
            improved = False
            for k in (1, 2, 3):
                for combo in itertools.combinations(bits, k):
                    trial = bytearray(inp)
                    for i, j in combo:
                        trial[i] ^= 1 << j
                    sc = prefix_match(bytes(trial), want)
                    if sc > cur:
                        inp, cur, improved = trial, sc, True
                        break
                if improved:
                    break
        if best is None or cur > best[0]:
            best = (cur, bytes(inp))
            print("   thu %2d: khop %d/%d  %s" % (att, cur, len(want), best[1].hex()),
                  flush=True)
        if cur >= len(want):
            break
    cur, inp = best
    if cur >= len(want):
        seq, kind, _ = walk.walk(bytag, start, inp, valid=valid)
        print("[+] THANG LOI model: %s  kind=%s" % (inp.hex(), kind))
        open(os.path.join(HERE, "win.hex"), "w").write(inp.hex() + "\n")
        c = search.session.Core()
        c.get_nonce()
        rep = c.run(inp)
        print("[*] RUN that ->", repr(rep)[:300])
        c.close()
        return 0
    print("[-] sau nhat %d/%d" % (cur, len(want)))
    return 1


if __name__ == "__main__":
    sys.exit(main())
