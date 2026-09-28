import struct, os

BASE = os.path.join(os.path.dirname(__file__), '..', 'files')
d = open(os.path.join(BASE, 'vmrun'), 'rb').read()
V2O = lambda v: v - 0x400000

JT = 0x486ba8
print('=== jump table at %#x (signed dword, handler = JT + off) ===' % JT)
h = {}
for op in range(14):
    off = struct.unpack_from('<i', d, V2O(JT) + op * 4)[0]
    h[op] = JT + off
    print('  op%-2d -> %#x' % (op, JT + off))

# reverse: handler address -> mnemonic guess
print('\n=== handler bodies (from the disassembly I transcribed) ===')
HANDLERS = {
    0x403608: ('XORI', 6, 'rA ^= imm32                [op][A][imm32]'),
    0x403653: ('ANDI', 6, 'rA &= imm32                [op][A][imm32]'),
    0x403665: ('CMPI', 6, 'assert rA == imm32 else FAIL'),
    0x40367d: ('TBL',  3, 'rA = (u32) sbox[ (u8) rB ]  [op][A][B]'),
    0x40369a: ('ROLR', 3, 'rA = rol32(rA, rB&31?)     [op][A][B]'),
    0x4036b0: ('ORR',  3, 'rA |= rB'),
    0x4036ca: ('ANDR', 3, 'rA &= rB'),
    0x4036e4: ('MULR', 3, 'rA = (rA * rB) & 32        [op][A][B] dest=A'),
    0x403706: ('ADDR', 3, 'rA += rB'),
    0x403720: ('XORR', 3, 'rA ^= rB'),
    0x40373a: ('MOV',  3, 'rA = rB                    [op][A][B]'),
    0x403756: ('MOVI', 6, 'rA = imm32'),
    0x40376b: ('KEY',  3, 'rA = (u32) key[ (u8) B ]   [op][A][idx]'),
}
addr2name = {a: n for a, (n, s, t) in HANDLERS.items()}
for op in range(1, 14):
    a = h[op]
    print('  op%-2d -> %#08x  %s' % (op, a, addr2name.get(a, '*** UNMAPPED ***')))

print('\n=== verdict strings ===')
for v in (0x48103a, 0x48104b):
    o = V2O(v)
    print('  %#x = %r' % (v, d[o:d[o].index(b'\0')]))
