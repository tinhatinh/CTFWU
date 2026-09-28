import json
import os
import sys
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import mem as M
import records
import struct


def edge(s):
    return (s[0], struct.unpack_from("<H", s, 1)[0])


def load_state(name="state.json", imgname="imgP.bin"):
    S = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), name)))
    img = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), imgname), "rb").read()
    hdr, _ = records.parse(img)
    bytag = {r["f0"]: r for r in hdr["recs"]}
    valid = {}
    for k, v in S["val"].items():
        t, i = k.split(":")
        valid[(int(t), int(i))] = bool(v)
    return S, bytag, valid


def step(bytag, tag, m, valid):
    rec = bytag.get(tag)
    if rec is None:
        return "unknown", tag, m
    st = M.run(rec["code"], rec["ln"], m)
    if st is None:
        return "loop", tag, m
    printed, loaded, m = st
    if printed:
        return ("FLAG" if loaded else "emptyprint"), tag, m
    if rec["f1"] == 255:
        bpl = 255
    else:
        reg = M.rd32(m, M.O_REG + 4 * rec["f1"])
        bpl = (reg >> rec["f2"]) & 1 if rec["f2"] < 32 else 0
    for i, s in enumerate(rec["stamps"]):
        t, tgt = edge(s)
        if t == bpl and valid.get((tag, i)):
            return "go", tgt, m
    return "go", rec["f3"], m


def walk(bytag, start, inp, valid=None, maxlen=300):
    m = M.newmem(inp)
    tag, seen, path = start, set(), []
    for _ in range(maxlen):
        kind, tag, m = step(bytag, tag, m, valid)
        if kind != "go":
            return kind, tag, path
        if tag in seen:
            return "cycle", tag, path
        seen.add(tag)
        path.append(tag)
    return "long", tag, path


if __name__ == "__main__":
    S, bytag, valid = load_state()
    start = S["entry"]
    goal = next(t for t, r in bytag.items()
                if r["ln"] >= 2 and r["code"][0] == 13 and r["code"][1] == 14)
    print("[*] model vung nho phang: start=%d goal=%d" % (start, goal))
    for nm, inp in (("all-zero", bytes(24)), ("all-ff", b"\xff" * 24),
                    ("dist1", bytes.fromhex("edbf88465f03aded29ab14c256e7d85056791a384320c434"))):
        kind, tag, p = walk(bytag, start, inp, valid=valid)
        print("   %-8s -> %-11s cuoi=%-6s buoc=%d  goal trong duong=%s"
              % (nm, kind, tag, len(p), goal in [start] + p))
