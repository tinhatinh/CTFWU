"""Disassembler cho code cua record, dua tren bang opcode dich tu 0x1810 / 0x406c.

Dang instruction (theo vm_notes.md):
    0 LBI   rD,[k]     3 byte    reg[D] = k<24 ? input[k] : 0
    1 LBI   rD,[k+s]   3         reg[D] = k<24 ? input[k+reg[S]] : 0
    2 STR   [rS],rD    3         ram[reg[S] & 0x7f] = reg[D]
    3 JMP   +off       3         pc += off (i16)
    4 JZ    rS,+off    3         if reg[S]==0 jump
    5 JNZ   rS,+off    3
    6 JGE   rS,rD,+off 4         if reg[S] >= reg[D] jump
    7 JGT   rS,rD,+off 4
    8 SHR   rS,[k]     3         reg[S] >>= k (k>31 -> 0)
    9 SHL   rS,[k]     3
   10 AND   rS,[k]     6         reg[S] &= u32 imm
   11 OR    rD,[k]     6         reg[D] |= u32 imm
   12 ADD   rD,imm     6         reg[D] += u32 imm
   13 XORI  rD,imm     6         reg[D] ^= u32 imm  (can kiem tra ten)
   14 MOV   rD,rS      3         (dang 3 operand: dst = code[i+2])
   15 MOVE  rD,[k]     3
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

NAME = {0: "LBI", 1: "LBIidx", 2: "STR", 3: "JMP", 4: "JZ", 5: "JNZ",
        6: "JGE", 7: "JGT", 8: "SHR", 9: "SHL", 10: "ANDi", 11: "ORi",
        12: "ADDi", 13: "XORi", 14: "MOV", 15: "MOVc"}
SIZE = {0: 3, 1: 3, 2: 3, 3: 3, 4: 3, 5: 3, 6: 4, 7: 4, 8: 3, 9: 3,
        10: 6, 11: 6, 12: 6, 13: 6, 14: 3, 15: 3}


def disasm(code, base=0, limit=200):
    pc, out = 0, []
    while pc < len(code) and len(out) < limit:
        op = code[pc]
        if op > 15:
            out.append("%4d: HALT (op=%d)" % (pc, op))
            break
        sz = SIZE[op]
        b = code[pc + 1:pc + 1 + sz]
        args = ""
        if sz == 3:
            args = "a=%d b=%d" % (b[0], b[1])
        elif sz == 4:
            args = "a=%d b=%d off=%d" % (b[0], b[1],
                                         int.from_bytes(b[2:4], "little", signed=True))
        elif sz == 6:
            args = "a=%d b=%d imm=%d (0x%x)" % (b[0], b[1],
                                                int.from_bytes(b[2:6], "little"),
                                                int.from_bytes(b[2:6], "little"))
        raw = code[pc:pc + sz].hex()
        out.append("%4d: %-6s %-30s  [%s]" % (pc, NAME[op], args, raw))
        pc += sz - 1 if op == 3 else sz
    return out


if __name__ == "__main__":
    import records
    img = open(sys.argv[1] if len(sys.argv) > 1 else "imgC.bin", "rb").read()
    hdr, _ = records.parse(img)
    recs = hdr["recs"]
    print("== record 0 (id=%d == entry %d), code_len=%d ==" %
          (recs[0]["f0"], hdr["entry"], recs[0]["ln"]))
    for ln in disasm(recs[0]["code"], limit=40):
        print("   ", ln)
    print("\n== phan bo opcode trong toan bo 40 record ==")
    import collections
    cnt = collections.Counter()
    halt = collections.Counter()
    for r in recs:
        c = r["code"]
        i = 0
        while i < len(c):
            if c[i] > 15:
                halt[i] += 1
                break
            cnt[c[i]] += 1
            i += SIZE[c[i]]
    print("   ", sorted(cnt.items()))
    print("   so record ket thuc bang op>15 o vi tri:", sorted(halt.items())[:10])
    print("\n== ns (so stamp) va code_len tung record ==")
    print("   ", [(r["f0"], r["ln"], r["ns"]) for r in recs[:12]])
