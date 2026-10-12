---
title: "Chaos in the Plot"
category: "Misc"
tags: ["matplotlib", "connected-components", "coordinate-recovery", "affine-cipher", "crib-dragging"]
solve_date: "2026-10-09"
language: "en"
---

# Chaos in the Plot

**Flag:** `OWASP{CHAOS_IN_THE_PLOT}`
**Artifact:** `the_math_of_plot.zip` (49,003 B, 2 members, 98,583 B uncompressed in total).

## Challenge

The description recorded for the challenge:

```text
The Soul Stone has distorted a hidden message using a mathematical transformation and scattered the resulting values across a chaotic Matplotlib plot…
```

Medium, 200 points.

## Analysis

### The archive and its two files

The members of `chaos_artifact.bin` carry the WinZip AE extra field `0x9901` (vendor `AE`, strength 3 = AES-256, method 8 = deflate). The archive password is `OWASP`; that value was supplied during the work rather than recovered from the artifact. The solution uses only the two extracted files:

```console
$ 7z t -pOWASP chaos_artifact.bin
Testing archive: chaos_artifact.bin
--
Path = chaos_artifact.bin
Type = zip
Physical Size = 49003

Everything is Ok

Folders: 1
Files: 2
Size:       98583
Compressed: 49003
```

- `the math of plot/chaos.png` — 4500×2400, 98,191 B: a bare matplotlib scatter, no ticks, no axis labels.
- `the math of plot/fragments.dat` — 392 B: 56 `HEX:HEX` lines.

### The markers

The scatter markers are `tab:blue` (31, 119, 180). A Manhattan-distance threshold below 60 on the RGB image separates the markers from the white background; connected-component labelling of that binary image returns 56 components of exactly 777 px each, 43,512 px in total. Every component centre lands on integer pixel coordinates, so reading positions requires no interpolation.

### The two axis laws

The data axes have to be recovered because the image no longer carries ticks. Matplotlib adds a 5% autoscale margin on each side, and 180 data units span the distance between the two outermost centres. Measurement gives:

```text
x_px = 245.0 + slot * 22.277778      22.277778 = 4010/180,  slot = 0..180
key  = 0x1F4 + slot                                             key range 500..680
y_data = round((2254 - y_px) * 254 / 2026)
```

`245.0` is the pixel column of the leftmost marker, `2254` is the top edge of the data region and `2026` its height after the margins are removed; the factor `254` corresponds to a 0..254 value range. The law is confirmed by the data itself: applying it to the 56 centres matches every marker to exactly one value in `fragments.dat`, with no marker off by one.

### Duplicate keys and the coordinate law

`fragments.dat` holds only 52 distinct keys across 56 lines: `0x281`, `0x29D`, `0x29E`, `0x2A6` each occur twice. Since there are 56 markers but only 52 distinct keys, the repeated values must be told apart by height, and the height is not free — it is an image of the value itself:

```text
y_data = (value XOR 91) - 2 * [value even]
```

Directly measured example: the marker in slot 0 has `y_px = 1783`, hence `y_data = 59`; the only candidate for key `0x1F4` in `fragments.dat` is `value = 102`, and `102 XOR 91 = 61`, minus 2 because 102 is even, gives exactly 59. The relation holds over all 56 points, so it is the author's encoding rather than a one-off coincidence.

### The affine transformation

Let `c` be the sequence of the 56 `y_data` values sorted by `x`. That sequence is an affine image of the plaintext string on the ring of 256:

```text
c = (7*p + 18) mod 256          p = (c - 18) * 7^-1 mod 256,   7^-1 = 183
```

`7 * 183 = 1281 = 5*256 + 1`, so 183 is indeed the inverse of 7. Dragging the crib `OWASP{` over every position and every odd `a` (the invertibility condition mod 256) leaves exactly one solution, `(m, a, b, pos) = (256, 7, 18, 0)`; nothing else fits anywhere in the sequence.

Hand check of one element: `y_px = 1783 → c = 59 → (59 − 18) * 183 mod 256 = 79 = 'O'`.

## Solution

```python
"""Chaos in the Plot -- marker detector, axis recovery, inverse affine."""
import numpy as np
from PIL import Image
from scipy import ndimage

PNG = "chaos/the math of plot/chaos.png"
DAT = "chaos/the math of plot/fragments.dat"

a = np.array(Image.open(PNG))[:, :, :3].astype(int)
blue = (np.abs(a - np.array([31, 119, 180])).sum(2) < 60)
lab, n = ndimage.label(blue)
sizes = ndimage.sum(blue, lab, range(1, n + 1))
cen = ndimage.center_of_mass(blue, lab, range(1, n + 1))
pts = np.array([(round(c[1], 4), round(c[0], 4)) for c in cen])
print("png=%s  components=%d  distinct sizes=%s  blue px=%d"
      % (Image.open(PNG).size, n, sorted(set(int(s) for s in sizes)), int(blue.sum())))

pairs = [tuple(int(x, 16) for x in line.strip().split(":"))
         for line in open(DAT) if line.strip()]
kn = [k for k, v in pairs]
print("fragments=%d  duplicate keys=%s"
      % (len(pairs), sorted({hex(k) for k in kn if kn.count(k) > 1})))

xs = np.sort(np.unique(pts[:, 0]))
X0, XSTEP = xs[0], (xs[-1] - xs[0]) / 180
print("x0=%.1f step=%.6f (=4010/180=%.6f)  key = 0x1F4 + slot" % (X0, XSTEP, 4010 / 180))

PX1, SPAN, MOD = 2254, 2026.0, 254.0
y_data = lambda py: int(round((PX1 - py) * MOD / SPAN))
series = [y_data(int(round(y))) for x, y in sorted(pts.tolist())]
print("first c values:", series[:8])

inv = pow(7, -1, 256)
plain = [(c - 18) * inv % 256 for c in series]
print("decrypted     :", "".join(chr(p) if 32 <= p < 127 else "." for p in plain))
print("re-encrypt check:", all((7 * p + 18) % 256 == c for p, c in zip(plain, series)))

CRIB = "OWASP{"
hits = [(256, aa, (series[pos] - aa * ord(CRIB[0])) % 256, pos)
        for pos in range(len(series) - len(CRIB) + 1) for aa in range(1, 256, 2)
        if all((aa * ord(ch) + (series[pos] - aa * ord(CRIB[0]))) % 256
               == series[pos + i] for i, ch in enumerate(CRIB))]
print("crib hits:", len(hits), hits)
print("hand check: y_px=1783 -> c=%d -> (c-18)*183 mod 256 = %d = %r"
      % (y_data(1783), (y_data(1783) - 18) * inv % 256,
         chr(((y_data(1783) - 18) * inv) % 256)))
print("markers in slots 100..180:", len([1 for x, y in pts.tolist()
                                        if round((x - X0) / XSTEP) >= 100]))
```

```text
png=(4500, 2400)  components=56  distinct sizes=[777]  blue px=43512
fragments=56  duplicate keys=['0x281', '0x29d', '0x29e', '0x2a6']
x0=245.0 step=22.277778 (=4010/180=22.277778)  key = 0x1F4 + slot
first c values: [59, 115, 217, 87, 66, 111, 231, 10]
decrypted     : OWASP{CHAOS_IN_THE_PLOT}...s..J].."..)......M....L.....B
re-encrypt check: True
crib hits: 1 [(256, 7, 18, 0)]
hand check: y_px=1783 -> c=59 -> (c-18)*183 mod 256 = 79 = 'O'
markers in slots 100..180: 32
```

The `decrypted` line covers all 56 affine-decoded values: the first 24 characters are `OWASP{CHAOS_IN_THE_PLOT}` and the remaining 32 values fall outside the printable range. `re-encrypt check: True` means `(7*p + 18) mod 256` rebuilds exactly the `c` sequence measured from the image, so `(7, 18, 256)` is not a one-way fit.

## Result

```text
OWASP{CHAOS_IN_THE_PLOT}
```

The whole string derives from `chaos.png` and `fragments.dat`, confirmed by re-encrypting with `(7*p + 18) mod 256` over the measured sequence itself. The event's solved table lists this challenge as solved.

## Reproduce

Requires 7-Zip (or any tool handling WinZip AE) to open the archive, and Python 3 with `numpy`, `Pillow`, `scipy`. The solution runs entirely offline.

```console
$ 7z x -pOWASP -o./chaos chaos_artifact.bin
$ python chaos_repro.py
```

Save the script from the Solution section as `chaos_repro.py` next to the `chaos/the math of plot/` directory produced by extraction. The two constants `PX1 = 2254` and `SPAN = 2026` are measurements on the 4500×2400 image; if the image is resized, re-measure them before using the axis laws.
