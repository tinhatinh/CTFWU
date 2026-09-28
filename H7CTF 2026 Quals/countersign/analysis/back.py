"""Bo nguoc tu record in co de tim 24 byte input.

Mo hinh (da doi chieu tay voi disassembly, xem core.py):
  RUN: tag = entry;  vong lap { rec=find(tag); exec_program(rec, regs, input);
       if printflag: THANG; if halt: denied; if n_link==0: denied;
       tag = emit(rec, regs) }
  regs (8 u32) GIU NGUYEN qua moi buoc.  27146 nap input vao r0..r5 (moi word LE
  4 byte).  Record 12 byte chi dong r4,r5.  Record 30 byte dong r0..r3.
  Record muc tieu G (chua op14) thu thuong la "fold": kiem r0==C0 .. r5==C5.

Do moi chuong trinh tren duong di la nghich dao duoc (ADD/XOR/ROL/ADDI/XORI),
ta di nguoc tu G: bang state => pre state.  O moi buoc kiem rang tien tri
forward (bpl va link dau tien hop le) cung chon chinh no.
"""
import struct
import sys

import core
import records

NM = {0: "NOP", 1: "MOVI", 2: "MOV", 3: "ADD", 4: "XOR", 5: "AND", 6: "OR",
      7: "ROL", 8: "SHR", 9: "ADDI", 10: "XORI", 11: "ANDI", 12: "LBI",
      13: "GETFLAG", 14: "PRINT", 15: "HALT"}
M64 = 0xFFFFFFFF


def rol(v, r):
    r &= 31
    return ((v << r) | (v >> (32 - r))) & M64 if r else v & M64


def ops_of(code, ln):
    """Cat thanh Chuong trinh = [(op, a, b, imm)] dung theo dung buoc nhay pc."""
    out = []
    pc = 0
    while pc < ln:
        op = code[pc]
        if op > 15:
            out.append((op, None, None, None))
            pc += 1
        elif op in (1, 9, 10, 11):
            out.append((op, code[pc + 1], None,
                        struct.unpack_from("<I", code, pc + 2)[0]))
            pc += 6
        elif 2 <= op <= 8 or op == 12:
            out.append((op, code[pc + 1], code[pc + 2], None))
            pc += 3
        else:
            out.append((op, None, None, None))
            pc += 1
    return out


def invert(ops, v):
    """Ap nguoc chuong trinh (chi dung duoc khi moi lenh nghich dao duoc)."""
    v = list(v)
    for op, a, b, imm in reversed(ops):
        if op == 0 or op in (13, 14, 15):
            continue
        if op in (1, 2, 5, 6, 8, 11, 12):
            raise SystemExit("op %s (%s) khong nghich dao duoc" % (op, NM[op]))
        if op == 3:                                   # ADD rD, rS  -> rD -= rS
            v[a] = (v[a] - v[b]) & M64
        elif op == 4:                                 # XOR rD, rS
            v[a] ^= v[b]
        elif op == 7:                                 # ROL rD, imm=b
            v[a] = rol(v[a], (-b) & 31)
        elif op == 9:
            v[a] = (v[a] - imm) & M64
        elif op == 10:
            v[a] ^= imm
    return v


def goal_constraints(code, ln):
    """Tim (regIndex -> gia tri phai co) trong record fold dang
    MOV r7,rX / XORI r7,C / (MOV|OR) r6,r7."""
    ops = ops_of(code, ln)
    need = {}
    pend = None
    for op, a, b, imm in ops:
        if op == 2 and b is not None and imm is None:
            pend = b                                  # MOV r7, rX  (X = b)
        elif op == 10 and imm is not None and pend is not None:
            need[pend] = imm
            pend = None
    return need


def build(img):
    hdr, _ = records.parse(img)
    recs = {}
    for r in hdr["recs"]:
        r["cbuf"] = bytearray(512)
        r["cbuf"][:min(r["ln"], 512)] = r["code"][:512]
        r["ops"] = ops_of(r["code"], r["ln"])
        r["links"] = [core.linksof(r, i) for i in range(r["ns"])]
        recs[r["f0"]] = r
    return hdr, recs


def first_match(rec, st, valid):
    """Nhu vong lap trong emit: tra (target, idx) cua link dau tien khop bpl
    VA co chu ky hop le; neu khong -> (dflt, -1)."""
    r = rec["f1"]
    b = 0xff if r == 0xff else (st[r] >> (rec["f2"] & 31)) & 1
    for i, L in enumerate(rec["links"]):
        if L["sel"] != b:
            continue
        if valid is None or valid.get("%d:%d" % (rec["f0"], i)):
            return L["target"], i
    return rec["f3"], -1


def fold_node(recs, goal, valid):
    """Record F duy nhat co link HOP LE chi thang vao record in co.
    F la 'fold': chuong trinh 117 byte gop (r_i ^ C_i) lai va thu bit 0."""
    for rec in recs.values():
        for i, L in enumerate(rec["links"]):
            if L["target"] != goal["f0"]:
                continue
            if valid is not None and not valid.get("%d:%d" % (rec["f0"], i)):
                continue
            yield rec, i, L


def solve(img, valid, maxdepth=200, verbose=False):
    hdr, recs = build(img)
    goal = next(r for r in recs.values()
                if any(o[0] == 14 for o in r["ops"]))
    start = hdr["entry"]
    ridx = {}
    for rec in recs.values():
        for i, L in enumerate(rec["links"]):
            ridx.setdefault(L["target"], []).append((rec, i))

    roots = []
    for F, i, L in fold_node(recs, goal, valid):
        seed = goal_constraints(F["code"], F["ln"])
        base = [0] * 8
        for k, v in seed.items():
            base[k] = v
        # kiem tra F that su tra ve link i khi bat dau tu `base`
        m = core.Mem(b"\x00" * 24)
        for k in range(8):
            m.wr32(k, base[k])
        core.exec_program(F, m, 0, [False])
        t, idx = core.emit(F, m, valid)
        if verbose:
            print("[?] fold %d seed=%s -> emit idx=%s (can %s)"
                  % (F["f0"], {hex(k): hex(v) for k, v in seed.items()}, idx, i))
        if idx == i and t == goal["f0"]:
            roots.append((F["f0"], tuple(base), [F["f0"], goal["f0"]]))
    if not roots:
        return None

    stack = list(roots)
    seen = set()
    for _ in range(2000000):
        if not stack:
            return None
        node, st, path = stack.pop()
        if (node, st) in seen:
            continue
        seen.add((node, st))
        if len(path) > maxdepth:
            continue
        for rec, i in ridx.get(node, ()):
            if valid is not None and not valid.get("%d:%d" % (rec["f0"], i)):
                continue
            post = st
            t, idx = first_match(rec, post, valid)
            if idx != i:
                continue
            if rec["f0"] == start:
                inp = b"".join(struct.pack("<I", post[k]) for k in range(6))
                if core.run(img, inp, valid)[0] == "win":
                    if verbose:
                        print("[+] duoi dai %d: %s" % (len(path), path[::-1]))
                    return inp, path[::-1]
                continue
            try:
                pre = tuple(invert(rec["ops"], post))
            except SystemExit:
                continue
            if rec["f0"] != node:
                stack.append((rec["f0"], pre, path + [rec["f0"]]))
        if len(seen) > 400000:
            return None
    return None
