"""Model THAT cua core countersign, doc lai truc tiep tu disassembly.

exec_program @0x1810  (rdi=rec, rsi=regs8, rcx=flagbuf, rdx=input24, r8=&printflag)
  code o rec+8, paylen o rec+6 (u16).  pc < paylen moi chay.  op = code[pc] u8.
  op > 15: pc += 1.  nguoc lai tra bang nhay 0x406c + int32.
  Tra 1 khi gap op 15 (HALT-REJECT), 0 khi chay het.
  Op 14 set *printflag = 1  -> RUN IN RA flagbuf va dung.
emit @0x1d50 (rdi=rec, rsi=regs8)
  sel_reg = rec[2];  neu 0xff -> bpl = 0xff, nguoc lai bpl = (regs[sel_reg] >> (rec[3] & 31)) & 1
  count = rec[0x208];  link[j] = rec + 0x20c + 16j: sel u8@0, target u16@2, tweak u32@4,
      sig_lo u32@8, sig_hi u16@12
  tim link dau tien co sel == bpl va stamp(tag||target||sel||tweak) == (sig_lo,sig_hi)
    -> tra target.  Khong co -> tra WORD[rec+4] (dflt).
RUN @0x1496:
  input phai dung 24 byte.  regs(8 u32) + flagbuf(128) + printflag KHONG dc reset giua cac buoc.
  tag = *(u16*)0x462d4;  vong lap toi da 0x30d40 buoc:
     rec = find(tag)  (khong thay -> denied)
     ret = exec_program(...)
     if printflag: xuat flagbuf -> THANG
     if ret == 1: denied
     if linkcount == 0: denied
     tag = emit(...)
"""
import struct
import sys

import records

NREG = 8
MAXSTEP = 0x30d40

# handler = 0x406c + int32(table[0x406c + 4*op])
HALT_OK = 15   # 0x1860 -> return 1
PRINT = 14     # 0x1870 -> *printflag = 1, pc += 1
GETFLAG = 13   # 0x1898 -> strncpy(flagbuf, getenv("FLAG"), 0x7f)
LBI = 12       # 0x1910 -> regs[code[pc+1]] = input[code[pc+2]] if code[pc+2] <= 0x17 else 0
MASK = 0xFFFFFFFF


class Mem:
    """Bang nho 8 u32: regs o +0, flagbuf o +0x60 (rsp+0x80 - rsp+0x20),
    va input o +0x20 (rsp+0x40 - rsp+0x20).  Chi so register >= 8 hop le
    vi binary khong kiem tra -> phai mo phong dung nhu stack that."""

    def __init__(self, inp):
        self.b = bytearray(0x100)
        self.b[0x20:0x20 + 24] = inp[:24]

    def rd32(self, idx):
        o = idx * 4
        return struct.unpack_from("<I", self.b, o)[0] if o + 4 <= len(self.b) else 0

    def wr32(self, idx, v):
        o = idx * 4
        if o + 4 <= len(self.b):
            struct.pack_into("<I", self.b, o, v & MASK)


def exec_program(rec, m, printflag, getflag):
    """Return (ret, printflag).  ret==1 nghia la拒 (HALT-REJECT)."""
    code = rec["cbuf"]
    paylen = rec["ln"]
    if paylen == 0:
        return 0, printflag
    pc = 0
    while True:
        op = code[pc]
        if op > 15:
            pc += 1
        elif op == 0:
            pc += 1
        elif op == 1:                                   # MOVI r[dc[pc+1]] = imm32
            m.wr32(code[pc + 1], struct.unpack_from("<I", code, pc + 2)[0])
            pc += 6
        elif op == 2:                                   # MOV  dst=c[p+1] src=c[p+2]
            m.wr32(code[pc + 1], m.rd32(code[pc + 2]))
            pc += 3
        elif op == 3:                                   # ADD  dst=c[p+1] += src=c[p+2]
            m.wr32(code[pc + 1], (m.rd32(code[pc + 1]) + m.rd32(code[pc + 2])) & MASK)
            pc += 3
        elif op == 4:                                   # XOR  dst=c[p+1] ^= src=c[p+2]
            m.wr32(code[pc + 1], m.rd32(code[pc + 1]) ^ m.rd32(code[pc + 2]))
            pc += 3
        elif op == 5:                                   # AND  dst=c[p+1] &= src=c[p+2]
            m.wr32(code[pc + 1], m.rd32(code[pc + 1]) & m.rd32(code[pc + 2]))
            pc += 3
        elif op == 6:                                   # OR   dst=c[p+1] |= src=c[p+2]
            m.wr32(code[pc + 1], m.rd32(code[pc + 1]) | m.rd32(code[pc + 2]))
            pc += 3
        elif op == 7:                                   # ROL  dst=c[p+1] rot c[p+2]
            d, s = code[pc + 1], code[pc + 2]
            v = m.rd32(d)
            r = s & 31
            v = ((v << r) | (v >> (32 - r))) & MASK if r else v
            m.wr32(d, v)
            pc += 3
        elif op == 8:                                   # SHR  dst=c[p+1] >>= c[p+2] (>31 -> 0)
            d, s = code[pc + 1], code[pc + 2]
            m.wr32(d, 0 if s > 31 else m.rd32(d) >> s)
            pc += 3
        elif op == 9:                                   # ADDI r[c[p+1]] += imm32
            d = code[pc + 1]
            m.wr32(d, (m.rd32(d) + struct.unpack_from("<I", code, pc + 2)[0]) & MASK)
            pc += 6
        elif op == 10:                                  # XORI
            d = code[pc + 1]
            m.wr32(d, m.rd32(d) ^ struct.unpack_from("<I", code, pc + 2)[0])
            pc += 6
        elif op == 11:                                  # ANDI
            d = code[pc + 1]
            m.wr32(d, m.rd32(d) & struct.unpack_from("<I", code, pc + 2)[0])
            pc += 6
        elif op == LBI:
            v = 0
            if code[pc + 2] <= 0x17:
                v = m.b[0x20 + code[pc + 2]]
            m.wr32(code[pc + 1], v)
            pc += 3
        elif op == GETFLAG:
            printflag = printflag   # khong doi
            getflag[0] = True
            pc += 1
        elif op == PRINT:
            printflag = 1
            pc += 1
        elif op == HALT_OK:
            return 1, printflag
        else:
            pc += 1
        if pc >= paylen:
            return 0, printflag


def selbit(rec, m):
    r = rec["f1"]
    if r == 0xff:
        return 0xff
    return (m.rd32(r) >> (rec["f2"] & 31)) & 1


def linksof(rec, i):
    s = rec["stamps"][i]
    return dict(sel=s[0], target=struct.unpack_from("<H", s, 1)[0],
                tweak=struct.unpack_from("<I", s, 3)[0],
                sig=struct.unpack_from("<I", s, 7)[0],
                sighi=struct.unpack_from("<H", s, 11)[0])


def emit(rec, m, valid):
    """valid: dict '""tag"":idx"" -> bool' (ket qua do MINT tren cung ket noi)."""
    b = selbit(rec, m)
    for i in range(rec["ns"]):
        L = linksof(rec, i)
        if L["sel"] != b:
            continue
        if valid is None or valid.get("%d:%d" % (rec["f0"], i)):
            return L["target"], i
    return rec["f3"], -1


def run(img, inp, valid, trace=None):
    hdr, _ = records.parse(img)
    bytag = {}
    for r in hdr["recs"]:
        r["cbuf"] = bytearray(512)
        r["cbuf"][:min(r["ln"], 512)] = r["code"][:512]
        bytag[r["f0"]] = r
    recs = hdr["recs"]
    m = Mem(bytes(inp))
    tag = hdr["entry"]
    printflag = 0
    getflag = [False]
    for step in range(MAXSTEP):
        rec = bytag.get(tag)
        if rec is None:
            return "denied", "no record %d" % tag, step
        ret, printflag = exec_program(rec, m, printflag, getflag)
        if trace is not None:
            trace.append((step, tag, list(m.b[0:32]), rec["f1"], selbit(rec, m),
                          rec["ns"], rec["f3"], ret, printflag))
        if printflag:
            return "win", tag, step
        if ret == 1:
            return "denied", "halt step %d tag %d" % (step, tag), step
        if rec["ns"] == 0:
            return "denied", "nolink tag %d" % tag, step
        tag, idx = emit(rec, m, valid)
    return "denied", "budget", MAXSTEP
