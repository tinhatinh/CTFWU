import struct, collections
BASE = r"C:\Users\Administrator\Documents\Qoder\2026-09-23\1788d23b\CTF-Writeups\kintsugi-vault"
raw = open(BASE + r"\files\f6f11ad133cab21c96e0185e3411ddc4.shard", 'rb').read()
t, plen = struct.unpack_from('<2H', raw, 8)
DEC = raw[0x32:0x132]
P = 0x32 + t + 256
prog = raw[P:P+plen]
H = {0:'HALT',1:'LDKEY',2:'MOVI',3:'MOV',4:'XOR',5:'ADD',6:'IMUL',7:'AND',8:'OR',
     9:'ROL',10:'LUT',11:'CMP',12:'ANDI',13:'XORI'}
S3 = {1,3,4,5,6,7,8,9,10}; S6 = {2,11,12,13}
pc = 0; d = collections.Counter(); s_ = collections.Counter(); k = collections.Counter()
ops = collections.Counter(); regs = collections.Counter()
while pc < len(prog):
    c = DEC[prog[pc]]
    if c == 0: break
    if c in S3:
        d[prog[pc+1]] += 1; regs[prog[pc+1]] += 1
        if c == 1: k[prog[pc+2]] += 1
        else: s_[prog[pc+2]] += 1
        pc += 3
    elif c in S6:
        d[prog[pc+1]] += 1; regs[prog[pc+1]] += 1; pc += 6
    else:
        print('BAD', pc, c); break
    ops[H[c]] += 1
print('instr counts:', dict(ops))
print('dest reg idx set:', sorted(d))
print('src  reg idx set:', sorted(s_))
print('key idx set     :', sorted(k))
print('max reg operand =', max(regs), ' (cells 0..11 are the real file)')
print('regs > 9 used:', {r: n for r, n in sorted(regs.items()) if r > 9})
