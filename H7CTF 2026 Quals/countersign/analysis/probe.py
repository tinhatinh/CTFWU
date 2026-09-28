"""Luu (image, bang entry that) vao file de phan tich offline, khoi doi MINT lai.

Dung:  python probe.py            -> ghi state.json
       python reach.py            -> phan tich duoc tiep + do nhay theo tung byte
"""
import binascii
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import session
import records
import walk

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    c = session.Core()
    nonce = c.get_nonce()
    img = c.get_image(save="imgP.bin")
    hdr, _ = records.parse(img)
    bytag = {r["f0"]: r for r in hdr["recs"]}
    val = {}
    for rid, rec in bytag.items():
        for i, s in enumerate(rec["stamps"]):
            t, tgt = walk.edge(s)
            x = struct.unpack_from("<I", s, 3)[0]
            msg = struct.pack("<HHBI", rid, tgt, t & 0xFF, x)[:9]
            rep = c.mint(msg)
            ok = len(rep) >= 12 and binascii.unhexlify(rep[:12]) == s[7:13]
            val["%d:%d" % (rid, i)] = ok
    out = dict(nonce=nonce, entry=hdr["entry"],
               recs={str(k): dict(f1=v["f1"], f2=v["f2"], f3=v["f3"], ln=v["ln"],
                                  code=v["code"][:v["ln"]].hex(),
                                  edges=[list(walk.edge(s)) + [s[7:13].hex()]
                                         for s in v["stamps"]])
                    for k, v in bytag.items()},
               val=val)
    json.dump(out, open(os.path.join(HERE, "state.json"), "w"))
    print("[*] luu state.json: %d record, %d entry that/%d, start=%d"
          % (len(bytag), sum(val.values()), len(val), hdr["entry"]))
    c.close()


if __name__ == "__main__":
    main()
