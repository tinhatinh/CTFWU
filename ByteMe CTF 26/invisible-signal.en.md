---
title: "Invisible Signal"
category: "Steg"
tags: ["matplotlib", "plot-marker-recovery", "blob-detection", "axis-calibration"]
solve_date: "2026-10-09"
language: "en"
---

# Invisible Signal

**Flag:** `OWASP{Sou15_c4nt_b3_533n_bY_n0rm41_3y3s}`
**Artifact:** `soul_stone_graph.png` (414,443 B) — PNG 4475×2474 RGBA, 0 bytes after `IEND`. Author: Suyog Jadhav.

## Challenge

Medium, 200 points, shipped as a single PNG. The image is a Matplotlib-style plot: a gridded axis system, three overlaid sine curves, and a family of small markers that nearly blend into the background. The flag is not in metadata and not in the low bits of the pixels; it lives in the **data coordinates** of those markers.

## Analysis

### Ruling out bit-level stego

`IEND` ends the file with no appended data. The recorded `zsteg -a` and `strings` checks found no payload. These results motivate inspecting marker coordinates; they do not rule out every other steganographic method.

### Reading the axes

The plot carries no numeric tick labels, but its grid lines allow calibration. The horizontal pixel range 372 to 4351 maps to x = 0 to 40, and the vertical range 445 to 2036 maps to y = 40 to 120:

```text
x : pixel  372 -> 4351  map to  data x =   0 .. 40
y : pixel  445 -> 2036  map to  data y =  40 .. 120
```

With these two linear maps, any pixel cluster on the image converts back to a data coordinate pair.

### Disc-shaped marker filter

The markers are solid discs about 11 px across. Isolated pixels on a sine curve or on a grid line do not match that shape, so a score measuring how solid a cluster is (pixel count divided by its bounding area) separates three populations:

```text
disc score, solid marker   : 103 - 117
disc score, plain image    :   8
disc score, curve crossing :  40 -  60
```

Running the filter over the whole image returns **exactly 40 detections**: every one lands on an integer x in 0..39 with no duplicate and no gap, and each matching y is an integer inside the printable ASCII range. x acts as the index, y as the character code:

```text
decoded: / OWASP{Sou15_c4nt_b3_533n_bY_n0rm41_3y3s} / len 40
```

`len 40` equals the number of detected markers, so the flag is assembled from all 40 characters rather than a subset.

## Solution

The solve is offline image analysis:

1. Load the PNG as an RGB array and threshold the channel sum to drop background and grid pixels.
2. Calibrate from the grid lines: pixel 372→4351 for x = 0→40, pixel 445→2036 for y = 40→120.
3. Group connected components, compute the solidity score, keep components around 11 px whose score falls in 103–117.
4. Convert each component centre to data coordinates, round, and verify the recovered x set is exactly {0..39}.
5. `chr(y)` in x order gives the 40 flag characters.

Two independent detectors on the same image — one scanning grid cells, one measuring disc fill — agree on the same 40 points, which is the basis for treating the coordinates as real markers rather than an artefact of one threshold choice.

## Result

```text
OWASP{Sou15_c4nt_b3_533n_bY_n0rm41_3y3s}
```

The flag was decoded from the artifact itself by offline image analysis, and cross-checked by two independent detectors (grid-cell scan and disc-fill measurement) over the same 40 markers. No submission response recorded.

## Reproduce

Requires Python 3 with `numpy` + `PIL`, plus `scipy` for the connected-component step (a hand-written flood fill works too). Nothing network- or service-dependent.

```console
$ file soul_stone_graph.png
$ zsteg -a soul_stone_graph.png
$ strings soul_stone_graph.png | grep -i matplot
```

Marker detection skeleton:

```python
import numpy as np
from PIL import Image
from scipy import ndimage

img = np.asarray(Image.open("soul_stone_graph.png").convert("RGB")).astype(int)
mask = img.sum(axis=2) < 240                      # dark pixels on the plot
lab, n = ndimage.label(mask)
pts = []
for i in range(1, n + 1):
    ys, xs = np.where(lab == i)
    h = ys.max() - ys.min() + 1
    w = xs.max() - xs.min() + 1
    fill = len(ys) / (h * w)                      # filled circle ~ 1.0
    if 9 <= h <= 13 and 9 <= w <= 13 and fill > 0.85:
        pts.append((xs.mean(), ys.mean(), h, w, fill))

# grid calibration: col 372->4351 = x 0..40 ; row 445->2036 = y 40..120
def to_data(x_px, y_px):
    gx = (x_px - 372) / (4351 - 372) * 40
    gy = 40 + (y_px - 445) / (2036 - 445) * (120 - 40)
    return gx, gy

out = {}
for x_px, y_px, h, w, fill in pts:
    gx, gy = to_data(x_px, y_px)
    out[int(round(gx))] = chr(int(round(gy)))
print(len(out), "".join(out[k] for k in sorted(out)))
```

The `fill` threshold has to be tuned to the actual pixels of this image: real markers score 103–117, sine-curve crossings 40–60, empty background 8. The kept band must exclude the five false candidates listed above; if one of them survives, the recovered x set will no longer be exactly {0..39}.
