import struct
BASE = r"C:\Users\Administrator\Documents\Qoder\2026-09-23\1788d23b\CTF-Writeups\kintsugi-vault"
P = BASE + r"\analysis\agent_vm"
raw = open(BASE + r"\files\f6f11ad133cab21c96e0185e3411ddc4.shard", 'rb').read()
t, plen = struct.unpack_from('<2H', raw, 8)
DEC = raw[0x32:0x132]; LUT = raw[0x32+t:0x32+t+256]; prog = raw[0x32+t+256:0x32+t+256+plen]
H = {0:'HALT',1:'LDKEY',2:'MOVI',3:'MOV',4:'XOR',5:'ADD',6:'IMUL',7:'AND',8:'OR',
     9:'ROL',10:'LUT',11:'CMP',12:'ANDI',13:'XORI'}
S = {0:1,1:3,2:6,3:3,4:3,5:3,6:3,7:3,8:3,9:3,10:3,11:6,12:6,13:6}
pc = 0; lines = []; ops = 0; consumed = 0
while True:
    d = DEC[prog[pc]]
    assert d <= 13, (pc, d)
    s = S[d]; ops += 1; consumed += s
    a = prog[pc+1] if s > 1 else None
    if d == 0: txt = '-- halt, print "OK", return 0'
    elif d == 1: txt = 'r%d = zext8(key[%d])' % (a, prog[pc+2])
    elif d == 2: txt = 'r%d = 0x%x' % (a, struct.unpack_from('<I',prog,pc+2)[0])
    elif d == 3: txt = 'r%d = r%d' % (a, prog[pc+2])
    elif d == 4: txt = 'r%d ^= r%d' % (a, prog[pc+2])
    elif d == 5: txt = 'r%d = (r%d + r%d) mod 2^32' % (a, a, prog[pc+2])
    elif d == 6: txt = 'r%d = (r%d * r%d) mod 2^32' % (a, a, prog[pc+2])
    elif d == 7: txt = 'r%d &= r%d' % (a, prog[pc+2])
    elif d == 8: txt = 'r%d |= r%d' % (a, prog[pc+2])
    elif d == 9: txt = 'r%d = rol32(r%d, 0x%02x & 31 = %d)' % (a, a, prog[pc+2], prog[pc+2]&31)
    elif d == 10: txt = 'r%d = zext8(LUT[r%d & 0xff])' % (a, prog[pc+2])
    elif d == 11: txt = 'assert r%d == 0x%x   (else FAIL, return 1)' % (a, struct.unpack_from('<I',prog,pc+2)[0])
    elif d == 12: txt = 'r%d &= 0x%x' % (a, struct.unpack_from('<I',prog,pc+2)[0])
    elif d == 13: txt = 'r%d ^= 0x%x' % (a, struct.unpack_from('<I',prog,pc+2)[0])
    lines.append('%3d: %-5s %s' % (pc, H[d], txt))
    if d == 0: break
    pc += s
assert consumed == len(prog) == plen, (consumed, len(prog), plen)
open(P + r'\start_shard.asm', 'w').write('\n'.join(lines) + '\n')
print('\n'.join(lines))
print('# instrs=%d  bytes=%d  proglen=%d  ends_with_HALT=1' % (ops, consumed, plen))
