"""Thu RUN voi cac cach dien 24 byte tu chinh record trong image.

Gia thuyet (tu vm_notes.md):
  RUN cat 24 byte = {u16 id, pad(4), u8 code_len<<8, pad, 4x[stampslot, sig[5]], code[..]}
  va core in FLAG neu record duoc chon chay het code AND [rec+0x208] (done) khac 0.
done khong duoc truyen tren wire, nen tim cach danh: phan chieu byte cua record
ngay vao input theo nhieu kieu dien khac nhau.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import session
import records


def variants(r):
    """Yeu cau: moi variant dung 24 byte."""
    v = {}
    head = struct.pack("<H", r["f0"]) + bytes(r["f1"]) + bytes(r["f2"]) + \
        struct.pack("<H", r["f3"]) + struct.pack("<H", r["ln"])
    v["wire head24"] = (head + r["code"])[:24]
    v["head+stamps"] = (head + b"".join(s for s in r["stamps"]))[:24]
    v["id only"] = struct.pack("<H", r["f0"]) + bytes(22)
    # kieu RUN: id, 4 pad, code_len o byte 6, roi cap (slot, sig6)
    t = bytearray(24)
    t[0:2] = struct.pack("<H", r["f0"])
    t[6] = r["ln"] >> 8
    k = 8
    for s in r["stamps"]:
        if k + 6 > 24:
            break
        t[k] = s[0]
        t[k + 1:k + 7] = s[1:7]
        k += 6
    v["run layout"] = bytes(t)
    t2 = bytearray(24)
    t2[0:2] = struct.pack("<H", r["f0"])
    t2[2:] = r["code"][:22]
    v["id+code"] = bytes(t2)
    return v


def main():
    c = session.Core()
    c.get_nonce()
    img = c.get_image(save="imgD.bin")
    hdr, _ = records.parse(img)
    recs = hdr["recs"]
    print("[*] %d record, entry=%d" % (len(recs), hdr["entry"]))
    good = []
    for r in recs:
        for name, inp in variants(r).items():
            assert len(inp) == 24, (name, len(inp))
            try:
                rep = c.run(inp)
            except Exception as e:
                print("[!] reconnect (%s)" % e)
                c.close()
                return main()
            if rep != "denied":
                good.append((r["f0"], name, rep))
                print("  !!! id=%d %-12s -> %r" % (r["f0"], name, rep))
    print("[*] xong %d record; khac denied: %d" % (len(recs), len(good)))
    if not good:
        print("[-] khong co du: done khong the danh bang phan chieu, can emulator.")
    c.close()


if __name__ == "__main__":
    main()
