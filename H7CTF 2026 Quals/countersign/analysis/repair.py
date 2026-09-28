import json
import os
import random
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import hill
import walk

HERE = os.path.dirname(os.path.abspath(__file__))


def first_diverge(bytag, valid, start, inp, want):
    """Tra ve (index lech, tag dang dung, can-bit muon) hoac (len(want), None, None)."""
    regs = [0] * 32
    tag, seen = start, set()
    idx = 1
    for _ in range(300):
        if tag not in bytag:
            return idx, tag, None
        rec = bytag[tag]
        st = walk.run(rec["code"], rec["ln"], inp, regs)
        if st is None:
            return idx, tag, None
        printed, loaded, regs = st
        if printed:
            return len(want), tag, None
        if idx >= len(want):
            return idx, tag, None
        need = want[idx]
        chosen = None
        if rec["f1"] == 255:
            bpl = 255
        else:
            reg = regs[rec["f1"]] if rec["f1"] < 32 else 0
            bpl = (reg >> rec["f2"]) & 1 if rec["f2"] < 32 else 0
        for i, s in enumerate(rec["stamps"]):
            t, tgt = walk.edge(s)
            if t == bpl and valid.get((tag, i)):
                chosen = tgt
                break
        if chosen == need:
            if tag in seen:
                return idx, tag, None
            seen.add(tag)
            tag = chosen
            idx += 1
            continue
        # lech: can bit khac
        want_bit = None
        for t, tgt in [walk.edge(s) for s in rec["stamps"]]:
            if tgt == need and valid.get((tag, [walk.edge(s)[1] for s in rec["stamps"]].index(tgt))):
                want_bit = t if t <= 1 else None
                break
        return idx, tag, (rec["f1"], rec["f2"], want_bit)


def main():
    S, bytag, valid = hill.search.load_state()
    start, want = S["entry"], None
    goal = next(t for t, r in bytag.items()
                if r["ln"] >= 2 and r["code"][0] == 13 and r["code"][1] == 14)
    want = hill.goal_path(bytag, valid, start, goal)
    print("[*] duong mong muon dai %d (start=%d goal=%d)" % (len(want), start, goal))
    rng = random.Random(11)
    t0 = time.time()
    best = (0, None)
    tries = 0
    while time.time() - t0 < 500:
        inp = bytearray(rng.randrange(256) for _ in range(24))
        sc, _, _ = first_diverge(bytag, valid, start, bytes(inp), want)
        tries += 1
        improved = True
        while improved and sc < len(want):
            improved = False
            idx, tag, info = first_diverge(bytag, valid, start, bytes(inp), want)
            if info is None:
                break
            reg, bit, wb = info
            if reg == 255 or wb is None or reg > 5:
                break
            # word reg `reg` duoc nap tu input[4*reg .. 4*reg+3]: try all
            base = list(inp[4 * reg:4 * reg + 4])
            cands = []
            for pos in range(4):
                for v in range(256):
                    nb = list(base)
                    nb[pos] = v
                    cands.append((pos, v, nb))
            for pos, v, nb in cands:
                trial = bytearray(inp)
                trial[4 * reg:4 * reg + 4] = nb
                s2, _, _ = first_diverge(bytag, valid, start, bytes(trial), want)
                tries += 1
                if s2 > sc:
                    inp, sc, improved = trial, s2, True
                    break
        if sc > best[0]:
            best = (sc, bytes(inp))
            print("   khop %d/%d  (%.0fs, %d trace)  %s" %
                  (sc, len(want), time.time() - t0, tries, inp.hex()), flush=True)
        if sc >= len(want):
            break
    sc, inp = best
    if inp and sc >= len(want):
        print("[+] INPUT THANG LOI:", inp.hex())
        open(os.path.join(HERE, "win.hex"), "w").write(inp.hex() + "\n")
        return 0
    print("[-] tot nhat %d/%d sau %d trace" % (sc, len(want), tries))
    return 1


if __name__ == "__main__":
    sys.exit(main())
