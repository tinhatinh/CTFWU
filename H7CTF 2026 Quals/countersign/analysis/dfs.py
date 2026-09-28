"""DFS tren do thi record, gan bit input theo rang buoc tung node.

Record start la bo dong goi: r_g = OR (in[4g+k] << 8k) -> bit j cua r_g TRUNG
voi bit j cua input byte (4g + j//8).  Nen moi node quyet dinh la mot rang buoc
tren DUNG MOT bit input -> DFS gán bit, not random search.

Neu chinh record do ghi de thanh ghi duoc doc (ADD/XOR/MOV...) thi bit khong con
dieu khien duoc -> nhan (prune).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import search
import walk


def render(assign, n=24):
    b = bytearray(n)
    for (i, j), v in assign.items():
        if v:
            b[i] |= 1 << j
        else:
            b[i] &= ~(1 << j)
    return bytes(b)


def main():
    S, bytag, valid = search.load_state()
    start = S["entry"]
    goal = next(t for t, r in bytag.items()
                if r["ln"] >= 2 and r["code"][0] == 13 and r["code"][1] == 14)
    print("[*] start=%d goal=%d" % (start, goal))
    stats = {"nodes": 0, "prune_const": 0, "prune_conflict": 0, "maxdepth": 0}
    seen_solutions = []

    def step_bit(rec, inp, regs):
        st = walk.run(rec["code"], rec["ln"], inp, regs)
        if st is None:
            return None, None
        printed, loaded, regs = st
        if rec["f1"] == 255:
            return regs, 255
        return regs, ((st[2][rec["f1"]] >> rec["f2"]) & 1) if st[0] == 0 else None

    def dfs(tag, assign, regs, path, visited):
        stats["nodes"] += 1
        stats["maxdepth"] = max(stats["maxdepth"], len(path))
        if len(path) > 400 or stats["nodes"] > 400000:
            return
        if tag == goal:
            inp = render(assign)
            k, t, p = walk.walk(bytag, start, inp)
            if k in ("FLAG", "emptyprint"):
                seen_solutions.append(inp)
                print("[+] INPUT: %s  duong %d buoc kind=%s" % (inp.hex(), len(p), k))
            return
        rec = bytag.get(tag)
        if rec is None:
            return
        inp = render(assign)
        st = walk.run(rec["code"], rec["ln"], inp, list(regs))
        if st is None:
            return
        printed, loaded, regs_new = st
        if printed:
            if tag == goal:
                seen_solutions.append(inp)
                print("[+] INPUT: %s (in tai %d)" % (inp.hex(), tag))
            return
        for i, s in enumerate(rec["stamps"]):
            t, tgt = walk.edge(s)
            if not valid.get((tag, i)) or tgt in visited or tgt == tag:
                continue
            if t == 255:
                need = 255
            elif t <= 1:
                need = t
            else:
                continue
            got = (regs_new[rec["f1"]] >> (rec["f2"] & 31)) & 1 \
                if rec["f1"] != 255 else 255
            if got == need:
                dfs(tgt, dict(assign), regs_new, path + [tgt], visited | {tgt})
                continue
            # can dao bit dieu khien: thu MOI byte, moi gia tri
            if rec["f1"] == 255 or rec["f1"] >= 32:
                stats["prune_const"] += 1
                continue
            fixed = None
            for bi in range(24):
                for v in range(256):
                    trial = dict(assign)
                    trial[(bi, 0)] = 0            # marker de render() duoc dung
                    cur = bytearray(render(trial))
                    cur[:] = render(assign)
                    cur[bi] = v
                    # ghi lai tung bit de DFS giu duoc lenh
                    st2 = walk.run(rec["code"], rec["ln"], bytes(cur), list(regs))
                    if st2 is None:
                        continue
                    g2 = (st2[2][rec["f1"]] >> (rec["f2"] & 31)) & 1
                    if g2 == need:
                        fixed = (bytes(cur), st2[2])
                        break
                if fixed:
                    break
            if fixed is None:
                stats["prune_const"] += 1
                continue
            nassign = {}
            for i, byte in enumerate(fixed[0]):
                for j in range(8):
                    nassign[(i, j)] = (byte >> j) & 1
            dfs(tgt, nassign, fixed[1], path + [tgt], visited | {tgt})

    dfs(start, {}, [0] * 32, [start], {start})
    print("[*] stats", stats)
    if seen_solutions:
        open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "win.hex"), "w") \
            .write(seen_solutions[0].hex() + "\n")
        print("[+] luu win.hex =", seen_solutions[0].hex())
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
