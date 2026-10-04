"""Trich 1/2/3 bit thap cua moi kenh PNG, dong goi theo ca hai thu tu bit,
do ti le byte in duoc de phat hien payload ASCII an trong pixel.

Chay:  python analysis/lsb_scan.py files/blake.png
Can:   numpy + Pillow.
"""

import sys

import numpy as np
from PIL import Image

path = sys.argv[1] if len(sys.argv) > 1 else "files/blake.png"
a = np.asarray(Image.open(path).convert("RGB")).astype(np.uint8).reshape(-1)

for pc in (1, 2, 3):
    bits = (a & ((1 << pc) - 1)).astype(np.uint8).ravel()
    for order in ("little", "big"):
        n = (len(bits) // 8) * 8
        t = np.packbits(bits[:n], bitorder=order).tobytes()
        pr = sum(1 for x in t if 32 <= x < 127 or x in (9, 10, 13)) / len(t)
        print(pc, order, "printable=%.3f" % pr, repr(t[:48]))
