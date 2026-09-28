"""Model VUNG NHO PHANG cua countersign (dong loi main).

Tai RUN, main sap xep stack nhu sau (offset so voi rsp):
   0x1c  printed_flag : u32
   0x20  regfile      : u32[8]   (chi co 8 word duoc khoi tao 0)
   0x40  input        : 24 byte  (do hex parse ghi vao)
   0x80  print buffer : 128 byte (noi op 13 strcpy getenv("FLAG"))

LBI (op 12) ghi `regfile[dst]` voi dst doc tu code, KHONG bi gioi han 0..7.
Voi dst >= 8, ghi do RƠI SANG vung input (va xa hon la vung in), tuc la
chinh chuong trinh VM co the SUA DOI input ma cac buoc sau doc lai.
Emulator truoc day tach doi hai vung nen sai.  O day dung MOT mang byte.
"""
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

M = 0xFFFFFFFF
SZ = {0: 1, 1: 6, 2: 3, 3: 3, 4: 3, 5: 3, 6: 3, 7: 3, 8: 3, 9: 6,
      10: 6, 11: 6, 12: 3, 13: 1, 14: 1, 15: 1}
O_FLAG, O_REG, O_IN, O_OUT = 0x1c, 0x20, 0x40, 0x80
SPAN = 0x100


def newmem(inp):
    m = bytearray(SPAN)
    m[O_IN:O_IN + len(inp)] = inp
    return m


def rd32(m, o):
    return struct.unpack_from("<I", m, o)[0] if o + 4 <= len(m) else 0


def wr32(m, o, v):
    if o + 4 <= len(m):
        m[o:o + 4] = struct.pack("<I", v & M)


def run(code, plen, m, limit=5000):
    """Thuc thi payload.  Tra (printed, loaded, mem)."""
    pc = printed = loaded = 0
    steps = 0
    while pc < plen:
        steps += 1
        if steps > limit:
            return None
        op = code[pc]
        if op > 15:
            pc += 1
            continue
        d = code[pc + 1] if pc + 1 < len(code) else 0
        s = code[pc + 2] if pc + 2 < len(code) else 0
        o = O_REG + 4 * d
        r = rd32(m, o)
        if op == 0:
            pass
        elif op == 1:
            r = struct.unpack_from("<I", code, pc + 2)[0]
        elif op == 2:
            r = rd32(m, O_REG + 4 * (s & 63))
        elif op == 3:
            r = (r + rd32(m, O_REG + 4 * (s & 63))) & M
        elif op == 4:
            r ^= rd32(m, O_REG + 4 * (s & 63))
        elif op == 5:
            r &= rd32(m, O_REG + 4 * (s & 63))
        elif op == 6:
            r |= rd32(m, O_REG + 4 * (s & 63))
        elif op == 7:
            n = s & 31
            r = ((r << n) | (r >> (32 - n))) & M if n else r
        elif op == 8:
            r = 0 if s > 31 else (r >> s)
        elif op == 9:
            r = 0 if s > 31 else ((r << s) & M)
        elif op == 10:
            r = (r + struct.unpack_from("<I", code, pc + 2)[0]) & M
        elif op == 11:
            r &= struct.unpack_from("<I", code, pc + 2)[0]
        elif op == 12:
            r = m[O_IN + s] if s < 24 else 0
        elif op == 13:
            loaded = 1
        elif op == 14:
            printed = 1
        elif op == 15:
            wr32(m, o, r)
            break
        wr32(m, o, r)
        pc += SZ[op]
    return printed, loaded, m
