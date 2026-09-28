"""Kintsugi Vault VM ISA -- derived independently from vmrun.asm 0x403530..0x403790.

Shard layout (file offset):  'KSHD' magic@0, flag@5, u16 t@8 (=0x100), u16 proglen@0xa
  0x032 .. 0x132 : decode table (256 B) -> copied to rsp+0x60, mutable by the program
  0x132 (=0x32+t) : LUT (256 B)          -> r10, read-only to the VM
  0x232 (=0x32+t+0x100) : program (proglen bytes)

VM state = the interpreter's stack window (bytearray, index == offset from rsp):
  0x30+4*i : register cell i (u32 LE). reg operand = UNMASKED u8 -> i in 0..255
  0x58+8   : key (8 B) == cells 10,11  -> writing r10/r11 rewrites the key
  0x60+256 : decode table == cells 12..87 -> writing r12.. rewrites the ISA itself
  only cells 0..7 are zeroed at entry (`rep stos`, ecx=8); 8,9 are stack garbage.
"""
M32 = 0xFFFFFFFF
import struct
def u32(x): return x & M32
def rol32(v, c):                       # c from a byte; x86 masks 32-bit rotates by 31
    c &= 31; v &= M32
    return v if c == 0 else ((v << c) | (v >> (32 - c))) & M32

# decoded value -> (mnemonic, total bytes consumed incl. opcode)
SIZE = {0: 1, 1: 3, 2: 6, 3: 3, 4: 3, 5: 3, 6: 3, 7: 3, 8: 3, 9: 3, 10: 3, 11: 6, 12: 6, 13: 6}
NAME = {0: 'HALT', 1: 'LDKEY', 2: 'MOVI', 3: 'MOV', 4: 'XOR', 5: 'ADD', 6: 'IMUL', 7: 'AND',
        8: 'OR', 9: 'ROL', 10: 'LUT', 11: 'CMP', 12: 'ANDI', 13: 'XORI'}
# d, a, b, imm, R(get), W(set), K(i) key byte, L(i) LUT byte  -> lambda
SEM = {
    1:  lambda R, W, K, L, a, b, imm: W(a, K(b)),                        # LDKEY r[a]=zext8(key[b])
    2:  lambda R, W, K, L, a, b, imm: W(a, imm),                          # MOVI  r[a]=imm32
    3:  lambda R, W, K, L, a, b, imm: W(a, R(b)),                         # MOV   dst = 1st operand
    4:  lambda R, W, K, L, a, b, imm: W(a, R(a) ^ R(b)),                  # XOR
    5:  lambda R, W, K, L, a, b, imm: W(a, u32(R(a) + R(b))),             # ADD   mod 2^32
    6:  lambda R, W, K, L, a, b, imm: W(a, u32(R(a) * R(b))),             # IMUL  dst = 1st operand, low 32
    7:  lambda R, W, K, L, a, b, imm: W(a, R(a) & R(b)),                  # AND
    8:  lambda R, W, K, L, a, b, imm: W(a, R(a) | R(b)),                  # OR
    9:  lambda R, W, K, L, a, b, imm: W(a, rol32(R(a), b)),               # ROL   count = imm8 & 31
    10: lambda R, W, K, L, a, b, imm: W(a, L(R(b) & 0xFF)),               # LUT   idx = r[b] LOW BYTE, zext8
    11: lambda R, W, K, L, a, b, imm: ('fail' if R(a) != imm else None),  # CMP   -> FAIL / return 1
    12: lambda R, W, K, L, a, b, imm: W(a, R(a) & imm),                   # ANDI
    13: lambda R, W, K, L, a, b, imm: W(a, R(a) ^ imm),                   # XORI
}

class VM:
    def __init__(self, shard, key=b'\x00' * 8, stack=0x500):
        self.mem = bytearray(stack)
        self.t, self.proglen = struct.unpack_from('<2H', shard, 8)
        self.mem[0x60:0x160] = shard[0x32:0x132]      # decode table lives IN the stack frame
        self.dec = memoryview(self.mem)[0x60:0x160]   # live view: r12.. writes rewire the ISA
        self.lut = shard[0x32 + self.t:0x32 + self.t + 256]   # r10, file image (VM cannot write)
        self.prog = shard[0x32 + self.t + 256: 0x32 + self.t + 256 + self.proglen]
        self.mem[0x58:0x60] = key[:8]
        self.pc = 0
    def R(self, i):
        import struct; return struct.unpack_from('<I', self.mem, 0x30 + 4 * i)[0]
    def W(self, i, v):
        import struct; struct.pack_into('<I', self.mem, 0x30 + 4 * i, v & M32)
    def decode(self, raw_byte): return self.dec[raw_byte]
    def step(self):
        import struct
        if self.pc >= len(self.prog): return 'halt'
        d = self.dec[self.prog[self.pc]]
        if d == 0: return 'halt'
        if d > 13: return 'badoptc'
        s = SIZE[d]
        a = self.prog[self.pc + 1]
        b = self.prog[self.pc + 2] if s > 2 else 0
        imm = struct.unpack_from('<I', self.prog, self.pc + 2)[0] if s == 6 else 0
        r = SEM[d](self.R, self.W, lambda i: self.mem[0x58 + i],
                   lambda i: self.lut[i], a, b, imm)
        self.pc += s
        return r or 'run'
    def run(self, trace=None):
        while True:
            st = self.step()
            if trace is not None: trace.append((self.pc, st))
            if st != 'run': return st
