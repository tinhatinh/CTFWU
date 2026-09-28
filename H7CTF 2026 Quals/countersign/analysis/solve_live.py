"""One-shot solver: MOT ket noi -> GET -> MINT soi chu ky -> bo nguoc -> RUN.

Image, nonce va chu ky deu sinh lai theo TUNG ket noi, nen khong duoc dung
ket qua cua ket noi kh.  Toan bo chay tren cung socket.
"""
import binascii
import os
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import back
import core
import records
import session


def probe(c, hdr):
    valid = {}
    t0 = time.time()
    for r in hdr["recs"]:
        for i, s in enumerate(r["stamps"]):
            sel = s[0]
            tgt = struct.unpack_from("<H", s, 1)[0]
            tw = struct.unpack_from("<I", s, 3)[0]
            msg = struct.pack("<HHBI", r["f0"], tgt, sel, tw)
            rep = c.mint(msg)
            ok = len(rep) >= 12 and binascii.unhexlify(rep[:12]) == s[7:13]
            valid["%d:%d" % (r["f0"], i)] = ok
    print("[*] %d link, %d hop le (%.1fs)"
          % (len(valid), sum(valid.values()), time.time() - t0))
    import json
    json.dump(dict(nonce=c.nonce, entry=hdr["entry"], valid=valid),
              open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "valid_live.json"), "w"))
    return valid


def main():
    c = session.Core()
    print("[*] banner:", c.banner)
    print("[*] nonce:", c.get_nonce())
    img = c.get_image(save="img_live.bin")
    print("[*] image %d byte entry=%d" % (len(img), records.parse(img)[0]["entry"]))
    hdr, _ = records.parse(img)
    valid = probe(c, hdr)
    t0 = time.time()
    res = back.solve(img, valid, maxdepth=200, verbose=True)
    print("[*] solve %.1fs ->" % (time.time() - t0),
          res[0].hex() if res else "KHONG CO")
    if not res:
        c.close()
        return 1
    inp, path = res
    print("[*] duong di:", " -> ".join(str(x) for x in path))
    print("[*] model forward:", core.run(img, inp, valid))
    rep = c.run(inp)
    print("[!] RUN %s -> %s" % (inp.hex(), rep))
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "flag_live.txt"),
         "a").write("%s | %s | %s\n" % (c.nonce, inp.hex(), rep))
    print("[*] thu them 2 lan nua:")
    for _ in range(2):
        print("      ", c.run(inp))
    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
