"""Kintsugi Vault guardian VM - verified against vmrun's jump table @0x486ba8.

op: 0=HALT 1=KEY 2=MOVI 3=MOV 4=XOR 5=ADD 6=MUL 7=AND 8=OR 9=ROL(imm8)
    10=LUT 11=CMP 12=ANDI 13=XORI
cells: r0..r11 = 12 u32 at buf 0x30; key bytes at buf 0x58 => r10 lo halfword = key[0..3],
r11 = key[4..7]; r12+ alias the live decode table (which the program can rewrite).
"""
import os, struct

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'files')
W = {0: 1, 1: 3, 2: 6, 3: 3, 4: 3, 5: 3, 6: 3, 7: 3, 8: 3, 9: 3, 10: 3, 11: 6, 12: 6, 13: 6}
NM = ['HALT', 'KEY', 'MOVI', 'MOV', 'XOR', 'ADD', 'MUL', 'AND', 'OR', 'ROL',
      'LUT', 'CMP', 'ANDI', 'XORI']
M32 = 0xFFFFFFFF


def load(name):
    d = open(os.path.join(BASE, name + '.shard'), 'rb').read()
    return dict(name=name, raw=d, flag=d[5], tbl=list(d[0x32:0x132]), sbox=d[0x132:0x232],
                code=d[0x232:], tid=d[0x0E:0x1E], nxt=d[0x22:0x32])


def rol32(v, n):
    n &= 31
    return ((v << n) | (v >> (32 - n))) & M32 if n else v & M32


def text(op, code, pc):
    if op == 0:
        return 'HALT'
    a = code[pc + 1]
    if W[op] == 3:
        return '%-4s r%d, r%d' % (NM[op], a, code[pc + 2])
    if W[op] == 6 and op in (9,):
        return 'ROL  r%d, %d' % (a, code[pc + 2])
    imm = struct.unpack_from('<I', code, pc + 2)[0]
    if op == 11:
        return 'CMP  r%d, %#x' % (a, imm)
    return '%-4s r%d, %#x' % (NM[op], a, imm)


def dismap(sh):
    """Walk with a given table; return (list of (pc,op), status, extra)."""
    t, code = sh['tbl'], sh['code']
    seq, pc = [], 0
    while pc < len(code):
        op = t[code[pc]]
        if op > 13:
            return seq, 'BADOP', (pc, code[pc], op)
        seq.append((pc, op))
        if op == 0:
            return seq, 'HALT', pc
        if pc + W[op] > len(code):
            return seq, 'RUNOFF', pc
        pc += W[op]
    return seq, 'END', pc


class VM:
    """Byte-exact model of the interpreter (12 cells + 8-byte key + rewritable table)."""

    def __init__(self, tbl, sbox, code, key):
        self.mem = bytearray(0x160)          # covers r0..r11 (0x30) and table (0x60)
        for i, v in enumerate(struct.pack('<8s', key[:8])):
            self.mem[0x58 + i] = v
        self.mem[0x60:0x160] = bytes(tbl[:0x100])
        self.sbox = bytes(sbox)
        self.code = code
        self.trace = []

    def r(self, i):
        return struct.unpack_from('<I', self.mem, 0x30 + 4 * i)[0]

    def w(self, i, v):
        struct.pack_into('<I', self.mem, 0x30 + 4 * i, v & M32)

    def run(self, maxsteps=200000, verbose=False):
        pc = 0
        code, t = self.code, self.mem[0x60:0x160]
        steps = 0
        while pc < len(code):
            steps += 1
            if steps > maxsteps:
                return 'STEPLIMIT', pc
            op = t[code[pc]]
            if op > 13:
                return 'BADOP', pc
            a = code[pc + 1] if W[op] > 1 else 0
            if op == 0:
                if verbose:
                    self.trace.append((pc, 'HALT'))
                return 'HALT', pc
            if W[op] == 3:
                b = code[pc + 2]
            elif op == 9:
                b = code[pc + 2]
            else:
                b = struct.unpack_from('<I', code, pc + 2)[0]
            if verbose:
                self.trace.append((pc, text(op, code, pc)))
            if op == 1:
                self.w(a, self.mem[0x58 + (b & 0xFF)] if b < 0x100 else 0)
            elif op == 2:
                self.w(a, b)
            elif op == 3:
                self.w(a, self.r(b))
            elif op == 4:
                self.w(a, self.r(a) ^ self.r(b))
            elif op == 5:
                self.w(a, self.r(a) + self.r(b))
            elif op == 6:
                self.w(a, self.r(a) * self.r(b))
            elif op == 7:
                self.w(a, self.r(a) & self.r(b))
            elif op == 8:
                self.w(a, self.r(a) | self.r(b))
            elif op == 9:
                self.w(a, rol32(self.r(a), b))
            elif op == 10:
                self.w(a, self.sbox[self.r(b) & 0xFF])
            elif op == 11:
                if self.r(a) != b:
                    return 'FAIL', pc
            elif op == 12:
                self.w(a, self.r(a) & b)
            elif op == 13:
                self.w(a, self.r(a) ^ b)
            pc += W[op]
        return 'END', pc


ALL = ['f6f11ad133cab21c96e0185e3411ddc4', '3df10ef4d0789f749d972c92c8085358',
       '63bafd7f4e981709287955968d1068c0', 'f14ad4e23f898cca82c2025614bc7a7c',
       '080ec62d7daef51f2e635d17f9b8e075', '3e3a0fc9a5c28e964f9ba37bb499e742',
       'cfa1fa34718c426f23e2318dfe8b330d']

if __name__ == '__main__':
    import sys, collections
    for n in ALL:
        sh = load(n)
        seq, st, extra = dismap(sh)
        cnt = collections.Counter(NM[o] for _, o in seq)
        cmps = [(p, struct.unpack_from('<I', sh['code'], p + 2)[0]) for p, o in seq if o == 11]
        tgt = ''.join('%02x' % (v & 0xFF) for _, v in cmps if v < 256)
        print('%s flag=%02x n=%-4d stop=%-6s %-22s CMP=%d %s' % (
            n[:12], sh['flag'], len(seq), st, str(extra)[:22], len(cmps), tgt))
        print('      ops: %s' % ' '.join('%s:%d' % kv for kv in sorted(cnt.items())))
