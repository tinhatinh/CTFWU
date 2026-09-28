"""Packer/parse record cua countersign, theo dung vong serialize 0x1240..0x1396.

In-memory: R stride 0x30c, p = R+0x10:
    u16 [p-0x8]   f0
    u8  [p-0x6]   f1
    u8  [p-0x5]   f2
    u16 [p-0x4]   f3
    u16 [p-0x2]   code_len
    u8  [p+0x200] n_stamp
    16-byte entries tai [p+0x20c]
Wire:  hdr 18 ("CSGN", u16 ver=2, u16 n_rec, u16 entry, u64 seed)
     + moi record: 8 byte header + code_len byte code + 1 byte n_stamp + 13*n_stamp
"""
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def u16(b, o):
    return struct.unpack_from("<H", b, o)[0]


def parse(img):
    assert img[:4] == b"CSGN", img[:4]
    ver, nrec, entry = struct.unpack_from("<HHH", img, 4)
    seed = img[0x0a:0x12]
    o = 18
    recs = []
    while o < len(img):
        f0, = struct.unpack_from("<H", img, o)
        f1 = img[o + 2]
        f2 = img[o + 3]
        f3, = struct.unpack_from("<H", img, o + 4)
        ln, = struct.unpack_from("<H", img, o + 6)
        code = img[o + 8:o + 8 + ln]
        p = o + 8 + ln
        ns = img[p]
        stamps = [img[p + 1 + 13 * i: p + 1 + 13 * (i + 1)] for i in range(ns)]
        recs.append(dict(off=o, f0=f0, f1=f1, f2=f2, f3=f3, ln=ln, code=code,
                         ns=ns, stamps=stamps))
        o = p + 1 + 13 * ns
    return dict(ver=ver, nrec=nrec, entry=entry, seed=seed, recs=recs), o


if __name__ == "__main__":
    img = open(sys.argv[1] if len(sys.argv) > 1 else "imgA.bin", "rb").read()
    hdr, end = parse(img)
    print("ver=%d nrec_field=%d entry=%d seed=%s" %
          (hdr["ver"], hdr["nrec"], hdr["entry"], hdr["seed"].hex()))
    print("records parsed: %d, consume to %d of %d  (clean=%s)"
          % (len(hdr["recs"]), end, len(img), end == len(img)))
    bad = [r for r in hdr["recs"] if r["ln"] > 600 or r["ns"] > 40]
    print("ky la:", len(bad))
    for r in hdr["recs"][:10]:
        print("  off=%5d f0=%5d f1=%3d f2=%3d f3=%5d ln=%4d ns=%2d code[:10]=%s"
              % (r["off"], r["f0"], r["f1"], r["f2"], r["f3"], r["ln"], r["ns"],
                 r["code"][:10].hex()))
        for s in r["stamps"][:3]:
            print("        stamp13 =", s.hex())
    lns = [r["ln"] for r in hdr["recs"]]
    nss = [r["ns"] for r in hdr["recs"]]
    print("ln range", min(lns), max(lns), " ns set", sorted(set(nss)))
    f0s = [r["f0"] for r in hdr["recs"]]
    print("f0 values:", f0s[:24])
    print("f3 values:", [r["f3"] for r in hdr["recs"]][:24])
