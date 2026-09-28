"""DFS tang constraint tren duong di bo, MOI lan thu are simulate lai TU DAU.

Lo truoc day: khi thu lat byte tai node u, toi giu nguyen `regs` tich luy nen
khong that su quay lai bo dong goi o record dau -> moi try deu that bai gia.

Cach nay: giu `assign` (bit cua input), va kiem tra bang cach di bo lai toan bo
duong tu start.  Bit chua phan cong -> lay ngau nhien, thu nhieu lan.
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import search
import walk

HERE = os.path.dirname(os.path.abspath(__file__))


def render(assign, fill=None):
    b = bytearray(24)
    for (i, j), v in assign.items():
        if v:
            b[i] |= 1 << j
    if fill:
        for i in range(24):
            for j in range(8):
                if (i, j) not in assign:
                    if fill[(i, j)]:
                        b[i] |= 1 << j
    return bytes(b)


def fixed_bits(assign, filled):
    return {k: ((filled[k] if k not in assign else assign[k])) for k in assign}


def path_of(bytag, valid, start, inp, cap=200):
    """Tra ve day tag di duoc, va kind ket thuc."""
    kind, tag, p = walk.walk(bytag, start, inp, valid=valid, maxlen=cap)
    return [start] + p, kind


def main():
    S, bytag, valid = search.load_state()
    start = S["entry"]
    goal = next(t for t, r in bytag.items()
                if r["ln"] >= 2 and r["code"][0] == 13 and r["code"][1] == 14)
    print("[*] start=%d goal=%d" % (start, goal))
    rng = random.Random(2024)
    TRIALS = [0]
    best = {"depth": 0, "inp": None, "path": None}

    def satisfies(assign, want_seq, tries=4000):
        """Tim input khop `assign` va di bo khop doan dau `want_seq`."""
        for _ in range(tries):
            TRIALS[0] += 1
            fill = {(i, j): rng.randrange(2) for i in range(24) for j in range(8)}
            for k, v in assign.items():
                fill[k] = v
            inp = render({}, fill)
            seq, kind = path_of(bytag, valid, start, inp)
            n = 0
            while n < len(seq) and n < len(want_seq) and seq[n] == want_seq[n]:
                n += 1
            if n >= len(want_seq):
                return inp, seq, True
            if n > best["depth"]:
                best.update(depth=n, inp=inp, path=seq)
        return None, None, False

    def dfs(want_seq, assign, depth):
        if depth > 60:
            return False
        inp, seq, ok = satisfies(assign, want_seq, tries=1500)
        if ok:
            print("[+] INPUT THANG LOI: %s" % inp.hex())
            print("    duong (%d): %s" % (len(seq), "->".join(map(str, seq))))
            open(os.path.join(HERE, "win.hex"), "w").write(inp.hex() + "\n")
            return True
        n = best["depth"]
        return False

    # lay mot duong BFS hop le trong do thi canh-that
    from collections import deque
    adj = {t: [walk.edge(s)[1] for i, s in enumerate(r["stamps"])
               if valid.get((t, i))] for t, r in bytag.items()}
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
    if not want:
        print("[-] khong co duong")
        return 1
    print("[*] duong BFS toi muc tieu dai %d" % len(want))

    # them: cho phep tim duong khac khi bit o node i khong the dat duoc
    assign = {}
    for k in range(1, len(want) + 1):
        if dfs(want[:k], dict(assign), k):
            return 0
        # ghi rang buoc: node tiep theo phai chot duoc canh toi want[k]
        tgt = want[k] if k < len(want) else None
        if tgt is None:
            break
        u = want[k - 1]
        rec = bytag[u]
        need = None
        for i, s in enumerate(rec["stamps"]):
            t, tt = walk.edge(s)
            if tt == tgt and valid.get((u, i)):
                need = t
                break
        if need is None or need > 1:
            print("   node %d: khong co canh that toi %s -> dung" % (u, tgt))
            break
        # them rang buoc: bit tai node u phai = need
        # tim bit input anh huong: thu gan no nhu mot an so bang cach them
        # moi (byte,bit) co the anh huong regs[rec.f1]
        cand = []
        for bi in range(24):
            for bj in range(8):
                a2 = dict(assign)
                a2[(bi, bj)] = need and 1 or 0
                # chi giu neu no khong mau thuan
                if any(a2[x] != assign[x] for x in assign):
                    continue
                for val in (0, 1):
                    a3 = dict(a2)
                    a3[(bi, bj)] = val
                    inp, seq, ok = satisfies(a3, want[:k], tries=120)
                    if ok:
                        cand.append(((bi, bj), val, seq))
            if cand:
                break
        if cand:
            (bi, bj), val, _ = cand[0]
            assign[(bi, bj)] = val
            print("   node %d: ep bit input[%d] bit%d = %d" % (u, bi, bj, val))
        else:
            print("   node %d: khong tim duoc bit dieu khien -> ngung" % u)
            break
    print("[-] chưa thắng; try=%d, sau nhat %d/%d, input=%s"
          % (TRIALS[0], best["depth"], len(want),
             best["inp"].hex() if best["inp"] else None))
    return 1


if __name__ == "__main__":
    sys.exit(main())
