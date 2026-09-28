"""VM + di bo + tim input 24 byte cho countersign.

Da doi chieu lai tung handler cua 0x1810 (Xem notes.md):
  * Moi lenh tu cong pc dung theo SZ[op]; KHONG có buoc nhay theo operand.
    Chi opcode > 15 di duong 0x1877 va cong 1.
  * Ops 2..6 va 12: dst = code[pc+1], src = code[pc+2] (truoc day dao chieu).
  * op13 = LOADFLAG (nap chuoi co vao buffer in), op14 = SETPRINT (dat co, chay tiep),
    op15 = RET 1.  main in khi co SETPRINT duoc dat, khong phu thuoc byte `done`.

Do chinh xac duoc kiem chung bang cach doi chieu payload cua record start: no giai ma
thanh bo dong goi 24 byte input -> 6 word u32, nen SZ va thu tu toan hang dung.
"""
import os
import random
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import records

M = 0xFFFFFFFF
SZ = {0: 1, 1: 6, 2: 3, 3: 3, 4: 3, 5: 3, 6: 3, 7: 3, 8: 3, 9: 6,
      10: 6, 11: 6, 12: 3, 13: 1, 14: 1, 15: 1}


def run(code, plen, inp, r=None, limit=5000):
    # BO THANH GHI DUNG CHUNG CA CUOC DI BO: main chi xoat mot lan TRUOC vong lap
    # (0x1519..0x154b nam ngoai nhan 0x1553), nen record start (bo dong goi input
    # -> r0..r5) de lai gia tri cho cac decision node sau doc.
    if r is None:
        r = [0] * 32
    pc = printed = loaded = 0
    steps = 0
    while pc < plen:
        steps += 1
        if steps > limit:
            return None
        op = code[pc]
        if op > 15:
            pc += 1
            continue
        d = code[pc + 1] if pc + 1 < len(code) else 0
        s = code[pc + 2] if pc + 2 < len(code) else 0
        if op == 0:
            pass
        elif op == 1:
            r[d] = struct.unpack_from("<I", code, pc + 2)[0]
        elif op == 2:
            r[d] = r[s & 31]
        elif op == 3:
            r[d] = (r[d] + r[s & 31]) & M
        elif op == 4:
            r[d] ^= r[s & 31]
        elif op == 5:
            r[d] &= r[s & 31]
        elif op == 6:
            r[d] |= r[s & 31]
        elif op == 7:
            n = s & 31
            r[d] = ((r[d] << n) | (r[d] >> (32 - n))) & M if n else r[d]
        elif op == 8:
            r[d] = 0 if s > 31 else (r[d] >> s)
        elif op == 9:
            r[d] = 0 if s > 31 else ((r[d] << s) & M)
        elif op == 10:
            r[d] = (r[d] + struct.unpack_from("<I", code, pc + 2)[0]) & M
        elif op == 11:
            r[d] &= struct.unpack_from("<I", code, pc + 2)[0]
        elif op == 12:
            r[d] = inp[s] if s < len(inp) else 0
        elif op == 13:
            loaded = 1
        elif op == 14:
            printed = 1
        elif op == 15:
            break
        pc += SZ[op]
    return (printed, loaded, r)


def edge(s):
    return (s[0], struct.unpack_from("<H", s, 1)[0])


def step(bytag, tag, inp, regs=None, valid=None):
    """Mot buoc.  regs xuyen suot ca cuoc di bo (main chi xoat TRUOC vong lap).

    valid: dict (tag, i) -> entry do stamp that; Neu khong co thi coi nhu hop le.
    """
    rec = bytag.get(tag)
    if rec is None:
        return "unknown", tag, regs
    st = run(rec["code"], rec["ln"], inp, regs)
    if st is None:
        return "loop", tag, regs
    printed, loaded, regs = st
    if printed:
        return ("FLAG" if loaded else "emptyprint"), tag, regs
    if rec["f1"] == 255:
        bpl = 255
    else:
        reg = regs[rec["f1"]] if rec["f1"] < 32 else 0
        bpl = (reg >> rec["f2"]) & 1 if rec["f2"] < 32 else 0
    for i, s in enumerate(rec["stamps"]):
        t, tgt = edge(s)
        if t == bpl and (valid is None or valid.get((tag, i))):
            return "go", tgt, regs
    return "go", rec["f3"], regs


def walk(bytag, start, inp, maxlen=500, valid=None, regs=None):
    if regs is None:
        regs = [0] * 32
    tag, seen, path = start, set(), []
    for _ in range(maxlen):
        kind, tag, regs = step(bytag, tag, inp, regs, valid)
        if kind != "go":
            return kind, tag, path
        if tag in seen:
            return "cycle", tag, path
        seen.add(tag)
        path.append(tag)
    return "long", tag, path


def load(path="imgE.bin"):
    img = open(path, "rb").read()
    hdr, _ = records.parse(img)
    bytag = {r["f0"]: r for r in hdr["recs"]}
    goal = next((r["f0"] for r in hdr["recs"]
                 if r["ln"] >= 3 and r["code"][0] == 13 and r["code"][1] == 14), None)
    return hdr, bytag, goal


def solve(bytag, start, rng, tries=400000):
    for _ in range(tries):
        inp = bytes(rng.randrange(256) for _ in range(24))
        kind, tag, seen = walk(bytag, start, inp)
        if kind == "FLAG":
            return inp, seen
    return None, None


if __name__ == "__main__":
    import collections
    for f in sys.argv[1:] or ["imgE.bin", "imgG.bin"]:
        hdr, bytag, goal = load(f)
        print("== %s entry=%d goal=%s nrec=%d" % (f, hdr["entry"], goal, len(bytag)))
        print("   input=0 ->", walk(bytag, hdr["entry"], bytes(24))[:2])
        rng = random.Random(7)
        cnt = collections.Counter()
        win = None
        for _ in range(5000):
            inp = bytes(rng.randrange(256) for _ in range(24))
            kind, tag, seen = walk(bytag, hdr["entry"], inp)
            cnt[kind] += 1
            if kind == "FLAG" and win is None:
                win = (inp, tag, seen)
        print("   5000 input ngau nhien:", dict(cnt))
        if win:
            print("   *** WIN input=%s ket=%d buoc=%d" % (win[0].hex(), win[1], len(win[2])))
