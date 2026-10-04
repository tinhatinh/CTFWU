"""Duyet chuoi chunk cua PNG va dem byte sau IEND.

Chay:  python analysis/chunk_walk.py files/blake.png
"""

import struct
import sys

d = open(sys.argv[1] if len(sys.argv) > 1 else "files/blake.png", "rb").read()
print("size", len(d))
i = 8
while i < len(d):
    ln = struct.unpack(">I", d[i:i + 4])[0]
    typ = d[i + 4:i + 8].decode("latin1")
    print(typ, ln, "data@", i + 8, "end@", i + 8 + ln)
    if typ == "IEND":
        i = i + 12 + ln
        break
    i = i + 12 + ln
print("after IEND bytes:", len(d) - i)
