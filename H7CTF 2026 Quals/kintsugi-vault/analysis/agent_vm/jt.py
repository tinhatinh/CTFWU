import struct
base = r"C:\Users\Administrator\Documents\Qoder\2026-09-23\1788d23b\CTF-Writeups\kintsugi-vault"
data = open(base + r"\files\vmrun", "rb").read()
TI = 0x486ba8                 # jump table vaddr
off = struct.unpack_from('<14i', data, TI - 0x400000)
for i, o in enumerate(off):
    print("decoded=%2d -> 0x%x" % (i, (TI + o) & 0xFFFFFFFF))
