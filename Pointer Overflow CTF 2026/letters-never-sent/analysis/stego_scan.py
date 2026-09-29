import os
import subprocess, sys, zlib, struct, os
import numpy as np
from PIL import Image
import re

P = os.path.join(os.path.dirname(__file__), "..", "files/letter.png")
data = open(P, "rb").read()

# 1. chunk inventory + any data after IEND / duplicate chunks
i = 8
chunks = []
while i < len(data):
    ln = struct.unpack(">I", data[i:i + 4])[0]
    typ = data[i + 4:i + 8].decode("latin1")
    chunks.append((typ, ln, i))
    i += 12 + ln
print("chunks:", [(t, n) for t, n, _ in chunks][:12], "... total", len(chunks))
print("bytes after last chunk:", len(data) - i)

# 2. LSB planes, printable-string scan
im = np.asarray(Image.open(P).convert("RGB")).astype(np.uint8)
bits = np.unpackbits(im.reshape(-1, 3), axis=1)
for depth in range(8):
    packed = np.packbits(bits[:, depth].astype(np.uint8)).tobytes()
    hits = re.findall(rb"[ -~]{12,}", packed)
    if hits:
        print(f"LSB plane bit{depth}: {len(hits)} printable runs, first: {hits[0][:80]!r}")

# 3. per-channel LSB bit counts (chi-square-ish anomaly)
for ch, name in enumerate("RGB"):
    col = im[:, :, ch] & 1
    ones = int(col.sum())
    print(f"channel {name}: LSB ones={ones}/{col.size} ratio={ones/col.size:.4f}")

# 4. stegano lsb reveal
try:
    from stegano import lsb
    r = lsb.reveal(P)
    print("stegano.lsb reveal:", repr(r)[:200] if r else None)
except Exception as e:
    print("stegano failed:", type(e).__name__, e)

# 5. alpha/palette + tEXt chunks
img = Image.open(P)
print("mode:", img.mode, "info:", {k: (str(v)[:60]) for k, v in img.info.items()})

# 6. try each zlib IDAT stream separately for trailing garbage
idat = b"".join(c[0] for c in [ (data[o+8:o+8+n],) for t,n,o in chunks if t=="IDAT"])
d = zlib.decompressobj()
raw = d.decompress(idat)
print("IDAT decompressed bytes:", len(raw), "unused tail:", len(d.unused_data))
if d.unused_data:
    print("tail:", d.unused_data[:120])
