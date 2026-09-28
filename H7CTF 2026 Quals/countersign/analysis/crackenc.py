"""Tim dung cach dien message 9 byte ma emit dung de kiem countersign.

Emit (0x1dd3..0x1e3d): msg 9 byte tai rsp+0xc =
    [id_lo, id_hi, 0, nx_hi, bpl, value(4 LE)]   va mode = 0x45
MINT dung mode = 0x4d, nen KHONG the assume giong nhau.  Thu mọi bien the va
doi 4 byte dau cua ket qua voi link[+8] luu trong image.

Neu mot bien the khop -> mo hinh chain da chac chan 100%, va toan bo link
da du server ky san (khong can gia).
"""
import itertools
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import session
import records


def link_fields(s):
    """13 byte serialized link -> cac truong thu o moi doi xung."""
    return dict(sel=s[0], a16_1=struct.unpack_from("<H", s, 1)[0],
                a16_2=struct.unpack_from("<H", s, 11)[0],
                u32_3=struct.unpack_from("<I", s, 3)[0],
                u32_7=struct.unpack_from("<I", s, 7)[0])


def candidates(rid, nx, val, bit):
    idl, idh = rid & 0xFF, rid >> 8
    nxl, nxh = nx & 0xFF, nx >> 8
    vs = struct.pack("<I", val)
    vb = struct.pack(">I", val)
    out = {}
    out["asm"] = bytes([idl, idh, 0, nxh, bit]) + vs
    out["asm_be"] = bytes([idl, idh, 0, nxh, bit]) + vb
    out["nohi"] = bytes([idl, 0, idh, 0, bit]) + vs
    out["full_nx"] = bytes([idl, idh, nxl, nxh, bit]) + vs
    out["nx_first"] = bytes([nxl, nxh, idl, idh, bit]) + vs
    out["bitswap"] = bytes([idl, idh, 0, nxh, 1 - bit]) + vs
    out["bit_hi"] = bytes([idl, idh, 0, nxh, bit << 7]) + vs
    out["mode4d"] = bytes([idl, idh, 0, nxh, bit]) + vs
    return out


def main():
    c = session.Core()
    c.get_nonce()
    img = c.get_image(save="imgE.bin")
    hdr, _ = records.parse(img)
    recs = hdr["recs"]
    print("[*] %d record entry=%d" % (len(recs), hdr["entry"]))
    probed = 0
    for r in recs[:8]:
        for li, s in enumerate(r["stamps"]):
            f = link_fields(s)
            for bit in (0, 1):
                for name, msg in candidates(r["f0"], f["a16_1"], f["u32_3"], bit).items():
                    rep = c.mint(msg)
                    probed += 1
                    if len(rep) < 8:
                        continue
                    got = binascii_unhex(rep)
                    if got[:4] == struct.pack("<I", f["u32_7"]) or \
                       got[:4] == struct.pack(">I", f["u32_7"]):
                        print("  *** KHOP rec id=%d link%d mode=%s bit=%d msg=%s -> %s"
                              % (r["f0"], li, name, bit, msg.hex(), rep))
                        return
    print("[-] %d probe, khong co khop nao" % probed)
    # in mot vai mau de nhin bang tay
    r = recs[0]
    print("mau rec0 id=%d ln=%d ns=%d" % (r["f0"], r["ln"], r["ns"]))
    for s in r["stamps"]:
        print("   link13", s.hex(), link_fields(s))
    print("   mint(asm bit0)", c.mint(candidates(r["f0"], 0, 0, 0)["asm"]))
    c.close()


def binascii_unhex(h):
    import binascii
    return binascii.unhexlify(h)


if __name__ == "__main__":
    main()
