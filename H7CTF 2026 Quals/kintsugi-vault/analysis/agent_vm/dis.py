import struct, sys
BASE = r"C:\Users\Administrator\Documents\Qoder\2026-09-23\1788d23b\CTF-Writeups\kintsugi-vault"
SH = BASE + r"\files\f6f11ad133cab21c96e0185e3411ddc4.shard"
raw = open(SH, 'rb').read()
t, plen = struct.unpack_from('<2H', raw, 8)
DEC = raw[0x32:0x132]
LUT = raw[0x32+t:0x32+t+256]
P = 0x32+t+256
prog = raw[P:P+plen]

H = {0:'HALT',1:'LDKEY',2:'MOVI',3:'MOV',4:'XOR',5:'ADD',6:'IMUL',7:'AND',8:'OR',
     9:'ROL',10:'LUT',11:'CMP',12:'ANDI',13:'XORI'}
SIZE = {0:1,1:3,2:6,3:3,4:3,5:3,6:3,7:3,8:3,9:3,10:3,11:6,12:6,13:6}
M3 = {1:'%s, kb[%d]', 3:'%s %s, %s', 4:'%s %s, %s', 5:'%s %s, %s', 6:'%s %s, %s',
      7:'%s %s, %s', 8:'%s %s, %s', 9:'%s %s, imm8 0x%02x (&31=%d)', 10:'%s %s, LUT[%s.lo]',
      11:'%s %s, imm32', 2:'%s %s, imm32', 12:'%s %s, imm32', 13:'%s %s, imm32'}

pc = 0; out = []; err = []
L = []
while pc < len(prog):
    d = DEC[prog[pc]]
    if d > 13:
        err.append((pc, prog[pc], d)); break
    s = SIZE[d]
    if pc + s > len(prog):
        err.append((pc, 'truncated', d)); break
    b1 = prog[pc+1] if s > 1 else None
    if s == 3:
        b2 = prog[pc+2]
        if d == 1: txt = 'r%d = zext8(key[%d])' % (b1, b2)
        elif d == 9: txt = 'r%d = rol32(r%d, 0x%02x)' % (b1, b1, b2)
        elif d == 10: txt = 'r%d = zext8(LUT[r%d & 0xff])' % (b1, b2)
        elif d == 3: txt = 'r%d = r%d' % (b1, b2)
        elif d == 6: txt = 'r%d = (r%d * r%d) mod 2^32' % (b1, b1, b2)
        elif d == 4: txt = 'r%d ^= r%d' % (b1, b2)
        elif d == 5: txt = 'r%d = (r%d + r%d) mod 2^32' % (b1, b1, b2)
        elif d == 7: txt = 'r%d &= r%d' % (b1, b2)
        elif d == 8: txt = 'r%d |= r%d' % (b1, b2)
    elif s == 6:
        imm = struct.unpack_from('<I', prog, pc+2)[0]
        if d == 11: txt = 'assert r%d == 0x%08x' % (b1, imm)
        elif d == 2: txt = 'r%d = 0x%08x' % (b1, imm)
        elif d == 12: txt = 'r%d &= 0x%08x' % (b1, imm)
        elif d == 13: txt = 'r%d ^= 0x%08x' % (b1, imm)
    else:
        txt = 'halt (returns 0); pc>=len also halts'
    L.append('%4d: %-5s %s' % (pc, H[d], txt))
    out.append('%4d(0x%03x): %3d %-5s %02x %s | %s' % (pc, pc, d, H[d], prog[pc],
                 prog[pc+1:pc+s].hex(' '), txt))
    if d == 0: break
    pc += s
print('\n'.join(out))
print('consumed', pc + (1 if out and out[-1].endswith('HALT  00 ') else 0), 'of', len(prog))
print('last pc', pc, 'errors', err)
