"""Faithful simulator + assembler for the ouroboros VM (validated against the ELF)."""
from model import gates, M

OPS = {
    "LOAD": 0x10,   # w[a] = imm mod M      pc+=1
    "MOV":  0x20,   # w[a] = w[b]           pc+=1
    "ADD":  0x30,   # w[a] += w[b]          pc+=2
    "SUB":  0x35,   # w[a] -= w[b]          pc+=2
    "XOR":  0x40,   # w[a] ^= w[b]          pc+=2
    "JMP":  0x50,   # index += (int8)imm    pc+=3
    "END":  0x7f,   # pc+=10 then verify
}
P0 = [0x10, 0x20, 0x30, 0x35, 0x40, 0x50, 0x7F, 0xFF]


def s8(v):
    v &= 0xFF
    return v - 256 if v > 127 else v


class VM:
    def __init__(self, beacon, nbytes=512):
        self.w = [0, 0, 0, 0]
        self.z = 0x5A
        self.pc = 0
        self.idx = 0
        self.P = list(P0)
        self.beacon = beacon
        self.mem = bytearray(nbytes)
        self.trail = []

    def step(self, b):
        """execute one instruction from the 4 bytes b at self.idx"""
        idx = self.idx
        si = idx
        assert si <= 508, "index guard"
        b0, b1, b2, b3 = b
        a = b1 & 3
        bb = b2 & 3
        imm = ((b2 << 8) | b3) % M
        w0low_pre = self.w[0] & 0xFF
        op = (b0 ^ self.z) & 7
        ins = self.P[op]
        self.idx = (si + 4) & 0xFFFF
        self.z = (self.z * 31 + w0low_pre) & 0xFF
        if ins == OPS["LOAD"]:
            self.w[a] = imm
            self.pc += 1
        elif ins == OPS["MOV"]:
            self.w[a] = self.w[bb]
            self.pc += 1
        elif ins == OPS["ADD"]:
            self.w[a] = (self.w[a] + self.w[bb]) % M
            self.pc += 2
        elif ins == OPS["SUB"]:
            self.w[a] = (self.w[a] - self.w[bb]) % M
            self.pc += 2
        elif ins == OPS["XOR"]:
            self.w[a] ^= self.w[bb]
            self.pc += 2
        elif ins == OPS["JMP"]:
            self.idx = (self.idx + s8(b3)) & 0xFFFF
            self.pc += 3
        elif ins == OPS["END"]:
            self.pc += 10
            self.trail.append(("END", ins))
            return False
        elif ins == 0xFF:
            raise RuntimeError("ILLEGAL INSTRUCTION")
        else:
            raise RuntimeError("bad opcode %02x" % ins)
        # self-rewriting permutation
        i = (self.w[0] & 0xFF) & 7
        j = self.w[1] & 7
        self.P[i], self.P[j] = self.P[j], self.P[i]
        assert self.pc <= 128, "cycle budget breached"
        return True


def encode(vm, want, a, imm=0, bslot=0):
    """build 4 bytes for instruction `want` given vm state; advance vm"""
    op = vm.P.index(OPS[want])
    b0 = ((vm.z & 7) ^ op) | (vm.z & 0xF8)
    b3 = imm & 0xFF
    b2 = (imm >> 8) & 0xFF
    if want in ("MOV", "ADD", "SUB", "XOR"):
        b2 = (b2 & 0xFC) | bslot        # b = b2 & 3 selects source slot
    b1 = a
    b = (b0 & 0xFF, b1 & 0xFF, b2 & 0xFF, b3 & 0xFF)
    before = list(vm.P)
    cont = vm.step(b)
    return b, cont


def build(beacon, tvec, npad=100):
    tgt = [(x + beacon) % M for x in tvec]
    vm = VM(beacon)
    prog = []
    # padding: LOAD w2 = 0 (keeps w0=w1=0 so the permutation swap is a no-op)
    for _ in range(npad):
        b, _c = encode(vm, "LOAD", 2, 0)
        prog.append(b)
    assert vm.P == P0, "permutation drifted"
    # set slots that don't perturb the swap first, then w1, then w0
    b, _ = encode(vm, "LOAD", 3, tgt[3]); prog.append(b)
    b, _ = encode(vm, "LOAD", 2, tgt[2]); prog.append(b)
    b, _ = encode(vm, "LOAD", 1, tgt[1]); prog.append(b)
    b, _ = encode(vm, "LOAD", 0, tgt[0]); prog.append(b)
    b, cont = encode(vm, "END", 0)
    prog.append(b)
    assert 112 <= vm.pc <= 128, vm.pc
    assert vm.w == tgt, (vm.w, tgt)
    return bytes(bytearray(b for row in prog for b in row)), vm
