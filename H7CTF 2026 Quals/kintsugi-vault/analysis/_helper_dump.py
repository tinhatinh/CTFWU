import struct, glob, os

base = r"C:\Users\Administrator\Documents\Qoder\2026-09-23\1788d23b\CTF-Writeups\kintsugi-vault"
files = r"C:\Users\Administrator\Documents\Qoder\2026-09-23\1788d23b\CTF-Writeups\kintsugi-vault\files"

for p in sorted(glob.glob(os.path.join(files, "*.shard"))):
    b = open(p,"rb").read()
    name=os.path.basename(p)
    magic=b[0:4]
    b4=b[4]; b5=b[5]
    w8=struct.unpack_from("<H",b,8)[0]
    wa=struct.unpack_from("<H",b,0xa)[0]
    field16=b[0x0e:0x0e+16].hex()
    hdr1e=b[0x1e:0x32].hex()
    print(name, "size",len(b), "magic",magic, "off4=%02x off5=%02x"% (b4,b5),
          "w8=%#x"%w8, "wa=%#x"%wa, "16B@0e",field16, "==name:", field16==name[:32].lower().replace('.shard','') or field16==name.split('.')[0],
          "0x1e..0x31",hdr1e)

print("--- file size sum check: 0x132+w8+wa", hex(0x132))
# dump SSE constants (vaddr -> file off = vaddr-0x400000)
exe=os.path.join(files,"vmrun")
data=open(exe,"rb").read()
for v in [0x486ba8,0x486be0,0x486be8,0x486bf0,0x486bf8,0x486c40,0x481010,0x4831e8,0x483218,0x481013,0x48101e,0x48102f,0x48103a,0x48104b,0x48103f]:
    off=v-0x400000
    chunk=data[off:off+32]
    print(hex(v), chunk.hex())
    try:
        print("   ascii:", chunk.split(b'\x00')[0].decode('latin1'))
    except: pass
