"""Lay MOT image + bang chu ky that tu dich, luu xuong file de do sat offline."""
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import records
import session
import solve_live

HERE = os.path.dirname(os.path.abspath(__file__))

c = session.Core()
print("[*] nonce:", c.get_nonce())
img = c.get_image(save=os.path.join(HERE, "img_live.bin"))
hdr, end = records.parse(img)
print("[*] image %d byte, parse den %d (clean=%s), nrec=%d parsed=%d entry=%d"
      % (len(img), end, end == len(img), hdr["nrec"], len(hdr["recs"]), hdr["entry"]))
valid = solve_live.probe(c, hdr)
json.dump(dict(nonce=c.nonce, entry=hdr["entry"], valid=valid),
          open(os.path.join(HERE, "valid_live.json"), "w"))
c.close()
print("[*] xong")
