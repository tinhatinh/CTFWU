"""Self-test of vm_isa.py against the traps in the task."""
import struct, sys
sys.path.insert(0, r"C:\Users\Administrator\Documents\Qoder\2026-09-23\1788d23b\CTF-Writeups\kintsugi-vault\analysis\agent_vm")
from vm_isa import VM, u32, rol32

DEC = bytes(range(256))                       # identity decode table: opcode == decoded value
LUT = bytes([(i * 7 + 3) & 0xFF for i in range(256)])

def mk(prog):
    b = bytearray(0x32)
    b[0:4] = b'KSHD'; b[5] = 1
    struct.pack_into('<2H', b, 8, 0x100, len(prog))   # t, proglen
    return bytes(b) + DEC + LUT + bytes(prog)         # DEC@0x32, LUT@0x132, prog@0x232

def R(v, i): return struct.unpack_from('<I', v.mem, 0x30 + 4*i)[0]
def W(v, i, x): struct.pack_into('<I', v.mem, 0x30 + 4*i, x & 0xFFFFFFFF)

n = p = 0
def chk(name, cond):
    global n, p
    n += 1; p += bool(cond)
    print(('PASS  ' if cond else 'FAIL  ') + name)

v = VM(mk([])); W(v,3,0x12345); W(v,5,0x10001)
v.prog = bytes([6,3,5]); v.step()
chk('IMUL dst = 1st operand byte, low 32 bits', R(v,3)==u32(0x12345*0x10001) and R(v,5)==0x10001)

v = VM(mk([])); v.prog = bytes([3,2,7]); W(v,7,0xdeadbeef); v.step()
chk('MOV dst = 1st operand (2nd byte is the source)', R(v,2)==0xdeadbeef and R(v,7)==0xdeadbeef)

for c, exp in ((0x21, 2), (0x20, 0x80000000 >> 31 if False else 1), (0xff, rol32(7,31))):
    pass
v = VM(mk([])); v.prog = bytes([9,1,0x21]); W(v,1,1); v.step()
chk('ROL count 0x21 behaves as rol 1 (x86 masks &31)', R(v,1)==2)
v = VM(mk([])); v.prog = bytes([9,1,0x20]); W(v,1,0x80000000); v.step()
chk('ROL count 0x20 is a no-op', R(v,1)==0x80000000)
v = VM(mk([])); v.prog = bytes([9,1,0xff]); W(v,1,1); v.step()
chk('ROL count 0xff == rol (0xff&31)=31', R(v,1)==rol32(1,31)==0x80000000)

v = VM(mk([])); v.prog = bytes([10,4,6]); W(v,4,0xAABBCCDD); W(v,6,0x11223344); v.step()
chk('LUT idx = LOW BYTE of src cell', R(v,4)==LUT[0x44])
chk('LUT result is zext8 -> upper 24 bits cleared', R(v,4) < 256)
v = VM(mk([])); v.prog = bytes([10,4,6]); W(v,6,0x000001ff); v.step()
chk('LUT idx 0x1ff wraps to 0xff (byte read, not full u32)', R(v,4)==LUT[0xff])
v = VM(mk([])); v.prog = bytes([10,4,6]); W(v,4,0xffffffff); W(v,6,1); v.step()
chk('LUT overwrites whole cell (not just low byte)', R(v,4)==LUT[1])

v = VM(mk([])); v.mem[0x58:0x60] = b'ABCDEFGH'; v.prog = bytes([1,0,9]); v.step()
chk('LDKEY idx 9 is UNMASKED -> rsp+0x61 = live decode-table byte 1', R(v,0)==v.mem[0x58+9]==bytes(v.dec)[1])
v = VM(mk([])); v.prog = bytes([1,0,0xff]); v.step()
chk('LDKEY idx 0xff reads rsp+0x157 (last decode-table byte)', R(v,0)==v.mem[0x157])

v = VM(mk([])); v.prog = bytes([2,11,0x41,0x42,0x43,0x44]); v.step()
chk('reg 11 aliases key[4:8] -> writing r11 rewrites the key', v.mem[0x5c:0x60]==bytes([0x41,0x42,0x43,0x44]))
v = VM(mk([])); v.prog = bytes([2,10,0x31,0x32,0x33,0x34]); v.step()
chk('reg 10 aliases key[0:4]', v.mem[0x58:0x5c]==bytes([0x31,0x32,0x33,0x34]))
v = VM(mk([])); v.prog = bytes([2,12,0xde,0xad,0xbe,0xef]); v.step()
chk('reg 12 aliases the decode table -> ISA is self-modifiable', bytes(v.dec[0:4])==bytes([0xde,0xad,0xbe,0xef]))
v = VM(mk([])); v.prog = bytes([2,87,1,0,0,0]); v.step()
v = VM(mk([])); v.prog = bytes([2,255,0xaa,0xbb,0xcc,0xdd]); v.step()
chk('max reg operand 255 -> writable cell at rsp+0x42c', struct.unpack_from('<I',v.mem,0x42c)[0]==0xddccbbaa)
chk('cell->offset map: 78=canary(rsp+0x168) 82=rbx 84=rbp 86=retaddr',
    [0x30+4*i for i in (78,82,84,86)]==[0x168,0x178,0x180,0x188])

v = VM(mk([])); v.prog = bytes([11,0,1,0,0,0]); W(v,0,1); chk('CMP pass -> run', v.step()=='run')
v = VM(mk([])); v.prog = bytes([11,0,1,0,0,0]); W(v,0,2); chk('CMP fail  -> fail', v.step()=='fail')
v = VM(mk([])); v.prog = bytes([5,0,1]); W(v,0,0xffffffff); W(v,1,2); v.step()
chk('ADD wraps mod 2^32', R(v,0)==1)
v = VM(mk([])); v.prog = bytes([4,0,1]); W(v,0,0x0f0f0f0f); W(v,1,0xff); v.step()
chk('XOR r,r is reg-reg (2nd operand read as full cell)', R(v,0)==0x0f0f0ff0)
print('\n%d/%d passed' % (p, n))
