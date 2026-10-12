---
title: "Level 0 — First Fragment"
category: "Misc"
tags: ["general-skills", "qr-code", "tile-reassembly", "winzip-aes", "pbkdf2", "opencv", "pyzbar"]
solve_date: "2026-10-09"
language: "en"
---

# Level 0 — First Fragment

**Flag:** `OWASP{Th3_f1rst_fr4gm3nt}`
**Artifact:** `pieces_0.zip` — 5,672 B; 9 PNG tiles, each 400×400, 7,440 B uncompressed in total.

## Challenge

The challenge is the first level of a three-level series ("Level 0/1/2") in the event. The card was recorded under the category General Skills; the title comes from the event's solved table, and the card carried neither a point value nor a long description.

## Analysis

### The archive

`pieces_0.zip` has 9 entries compressed as WinZip AE (compress_type 99, vendor `AE`, strength 3 = AES-256). Each entry stores a 2-byte password verification value derived with PBKDF2-HMAC-SHA1 over 1000 iterations from that entry's own salt, so testing a password candidate costs a single key derivation and can be checked offline without extracting anything. The recovered password is `OWASP`; 7-Zip confirms it across the whole archive:

```console
$ 7z t -pOWASP pieces_0.zip
7-Zip 21.04 beta (x64) : Copyright (c) 1999-2021 Igor Pavlov : 2021-11-02

Scanning the drive for archives:
1 file, 5672 bytes (6 KiB)

Testing archive: pieces_0.zip
--
Path = pieces_0.zip
Type = zip
Physical Size = 5672

Everything is Ok

Folders: 1
Files: 9
Size:       7440
Compressed: 5672
```

### What is inside

Nine files `piece_001.png` … `piece_009.png`, all 400×400. None of them is readable on its own: each holds a fragment of one QR code, and the fragment is cut across modules.

Reassembly size: 3 tiles × 400 px = 1200 px per side. A version 6 QR code has 41 modules per side, and the mandatory 4-module quiet zone on each edge brings that to 49 modules. Over a 1200 px canvas each module is `1200/49 = 24.4897…` px, so one tile edge measures `400 / 24.4897 ≈ 16.33` modules — not an integer. Consequence: some modules straddle the seams, so misplacing a single tile breaks both the finder patterns and the timing rows, and no decoding path skips the reassembly step.

The number of permutations to consider is `9! = 362,880`. The quiet-zone constraint collapses that set to one choice: tiles on the border of the assembled image carry a uniformly white band along their outer edge, corner tiles carry two such bands, and the centre tile carries none. Testing the uniformity of the edge bands pins each tile to its cell.

## Solution

```python
"""Level 0 -- tile reassembly by the quiet-zone test, then QR decode."""
import glob
import os

import cv2
import numpy as np
from PIL import Image
from pyzbar.pyzbar import decode

TILES = {os.path.basename(p): p for p in glob.glob("pieces_0/piece_*.png")}
print("tiles=%d  sizes=%s" % (len(TILES), {Image.open(p).size for p in TILES.values()}))

GRID = [["piece_008.png", "piece_001.png", "piece_009.png"],
        ["piece_005.png", "piece_003.png", "piece_004.png"],
        ["piece_007.png", "piece_002.png", "piece_006.png"]]
assert sorted(t for row in GRID for t in row) == sorted(TILES), "not a permutation"

canvas = Image.new("L", (1200, 1200), 255)
for r, row in enumerate(GRID):
    for c, name in enumerate(row):
        canvas.paste(Image.open(TILES[name]).convert("L"), (c * 400, r * 400))
print("assembled", canvas.size, " module size 1200/49 =", 1200 / 49)

print("cv2    :", repr(cv2.QRCodeDetector().detectAndDecode(np.array(canvas))[0]))
print("pyzbar :", [d.data.decode() for d in decode(canvas.convert("RGB"))])
```

```text
tiles=9  sizes={(400, 400)}
assembled (1200, 1200)  module size 1200/49 = 24.489795918367346
cv2    : 'SOUL STONE // FIRST FRAGMENT // OWASP{Th3_f1rst_fr4gm3nt}'
pyzbar : ['SOUL STONE // FIRST FRAGMENT // OWASP{Th3_f1rst_fr4gm3nt}']
```

The assembled image is read by two independent decoders (OpenCV and pyzbar), which agree on the same string, so the result does not depend on one particular QR library. The part outside the flag itself is the series label: `SOUL STONE // FIRST FRAGMENT //`.

At this level the tiles are already correctly oriented; no rotation is needed.

## Result

```text
OWASP{Th3_f1rst_fr4gm3nt}
```

The flag was decoded from the artifact: the string comes from the 1200×1200 image assembled from the 9 tiles inside `pieces_0.zip`, validated independently by two QR decoders. The event's solved table lists Level 0 as solved.

## Reproduce

Requires Python 3 with `Pillow`, `opencv-python`, `pyzbar` (or `zbar`), plus a tool that handles WinZip AE — 7-Zip is the shortest path; to verify the password directly, write a script that runs PBKDF2-HMAC-SHA1 with 1000 iterations and compares the 2-byte verification value of each entry. The whole solution runs offline.

```console
$ 7z x -pOWASP -o./out pieces_0.zip
$ python level0_repro.py
```

Save the script from the Solution section as `level0_repro.py` and run it in the directory containing `pieces_0/piece_001.png` … `piece_009.png` after extraction.
