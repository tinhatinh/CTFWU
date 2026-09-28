"""Emulator VM cua countersign + bieu dien bpl(record, input) nhu ham cua 24 byte.

Bang opcode da doi chieu handler body (0x1810 / 0x406c, handler = 0x406c + int32).
Regs: 32 u32, khoi dong = 0 moi vong RUN.  Chi op 12 (LBI) doc input.
Vi khong co lenh nhanh du lieu (chi co pc += operand cua op 4/5/6), ket qua
`bpl` cua mot record chi phu thuoc input, khong phu thuoc buoc di truoc.

De giai rang buoc ma khong can SAT: vi moi reg duoc tinh bang cac phep bit-wise
trong tung bit, NGOAI ADD/ADDi (co nho) va ROL/SHR/SHL (doi cho bit), ta thang
quyet dinh tung bit cua tung byte input theo thur tu dependency, va thu ca hai
gia tri khi can (quay lui nho).  Cach don gian nhat va du cho 13 rang buoc:
kiem tra xem bpl co ph thuoc input khong da - neu record khong dung LBI thi bpl
co dinh, va ta chi can chon nhanh cho phu hop.
"""
import struct
import sys

MASK = 0xFFFFFFFF
SZ = {0: 3, 1: 6, 2: 3, 3: 3, 4: 3, 5: 3, 6: 3, 7: 3,
      8: 3, 9: 6, 10: 6, 11: 6, 12: 3, 13: 1, 14: 1, 15: 1}
ADV = {4: "op3", 5: "op3", 6: "op3"}     # pc += code[i+3]


def run(code, code_len, inp, trace=None, limit=4000):
    regs = [0] * 32
    pc = 0
    flag = 0
    steps = 0
    while pc < code_len:
        steps += 1
        if steps > limit:
            break
        op = code[pc]
        if op > 15:
            pc += 1
            continue
        a = code[pc + 1] if pc + 1 < len(code) else 0
        b = code[pc + 2] if pc + 2 < len(code) else 0
        c = code[pc + 3] if pc + 3 < len(code) else 0
        imm = struct.unpack_from("<I", code, pc + 2)[0] if SZ[op] == 6 else 0
        if op == 0:
            pass
        elif op == 1:
            regs[a] = imm
        elif op == 2:
            regs[a] = regs[b]
        elif op == 3:
            regs[b] = (regs[b] + regs[a]) & MASK
        elif op == 4:
            regs[b] ^= regs[a]
        elif op == 5:
            regs[b] &= regs[a]
        elif op == 6:
            regs[a] |= regs[b]
        elif op == 7:
            n = b & 31
            regs[a] = ((regs[a] << n) | (regs[a] >> (32 - n))) & MASK if n else regs[a]
        elif op == 8:
            regs[a] = 0 if b > 31 else (regs[a] >> b)
        elif op == 9:
            regs[a] = 0 if c > 31 else ((regs[a] << c) & MASK)
        elif op == 10:
            regs[a] = (regs[a] + imm) & MASK
        elif op == 11:
            regs[a] &= imm
        elif op == 12:
            regs[a] = inp[b] if b < len(inp) else 0
        elif op == 13:
            regs[a] = (regs[a] >> imm) & 1 if imm < 32 else 0
        elif op == 14:
            regs[a] = (regs[a] << (imm & 31)) & MASK
        elif op == 15:
            regs[a] = regs[b]
        if op in ADV:
            pc = (pc + c) & MASK
        else:
            pc += SZ[op]
        if trace is not None:
            trace.append((pc, op, list(regs)))
        if pc < 0 or pc > 100000:
            break
    return regs, flag


def bpl(code, code_len, inp, regidx, bitidx):
    if regidx == 255:
        return 255
    regs, _ = run(code, code_len, inp)
    if regidx > 31 or bitidx > 31:
        return 0
    return (regs[regidx] >> bitidx) & 1


if __name__ == "__main__":
    import records
    img = open("imgE.bin", "rb").read()
    hdr, _ = records.parse(img)
    byid = {r["f0"]: r for r in hdr["recs"]}
    ent = byid[hdr["entry"]]
    print("entry id=%d regidx=%d bitidx=%d ln=%d" %
          (ent["f0"], ent["f1"], ent["f2"], ent["ln"]))
    print("code:", ent["code"][:48].hex())
    for probe in (bytes(24), bytes([0xff]) * 24, bytes(range(24))):
        regs, _ = run(ent["code"], ent["ln"], probe)
        nz = {i: v for i, v in enumerate(regs) if v}
        print("  input %s -> regs khac 0: %s" % (probe[:6].hex(), nz))
    print("\n== dem record co dung LBI (op 12) trong code ==")
    n = sum(1 for r in hdr["recs"] if 12 in r["code"][:r["ln"]])
    print("   %d/%d record co op12" % (n, len(hdr["recs"])))
