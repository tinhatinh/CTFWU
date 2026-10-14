---
title: "Flag from the Future"
category: "Misc"
tags: ["cellular-automaton", "reverse-game-of-life", "dejavu-font", "glyph-metrics", "screenshot-parsing"]
solve_date: "2026-10-10"
language: "en"
---

# Flag from the Future

**Flag:** `FortID{R3al_L1f3_H45_N0_R3w1nd_Bu7t0n}`
**Artifact:** a single screenshot, no source file, no instancer; the byte size of the image was not recorded. Author: ipaljak.

## Challenge

The challenge ships one screenshot showing a bitmapped line of characters, and states two facts: that line was rendered from one of the DejaVu 2.37 TTF files, and every cell with intensity of 50% or more became a live cell. No service, no script, no source.

The image is an evolved Life grid, so what is visible is the *descendant*. The flag sits on the other side, in the configuration that produced it.

## Analysis

### Grid geometry

The screenshot yields a 27-row × 371-column grid with 909 live cells, each cell 6×6 px at pitch 8 px, grid origin `x = 55 + 8c`, `y = 32 + 8r`.

```python
R, C = 27, 371                      # grid extracted from the screenshot


def top_left(r, c):                 # cell origin and pitch, as recorded
    return 55 + 8 * c, 32 + 8 * r


print("grid", R, "x", C, "=", R * C, "cells")
print("live", 909, "density", round(909 / (R * C), 4))
print("last cell top-left", top_left(R - 1, C - 1))
print("raster size", 55 + 8 * (C - 1) + 6, "x", 32 + 8 * (R - 1) + 6)


def pen(i):                         # pen column after i glyphs, recorded formula
    return 1 + round(i * 617 / 64)


print([pen(i) for i in range(13)])
print("pen(38) =", pen(38), " grid width =", C, " cols/glyph =", 617 / 64)
```

```text
grid 27 x 371 = 10017 cells
live 909 density 0.0907
last cell top-left (3015, 240)
raster size 3021 x 246
[1, 11, 20, 30, 40, 49, 59, 68, 78, 88, 97, 107, 117]
pen(38) = 367  grid width = 371  cols/glyph = 9.640625
```

Live-cell density is 9.07% — low, consistent with an image many generations past a rendered line of text rather than a fresh render of one.

### The rule

Counting still lifes in the grid gives: 7 blocks, 2 beehives, 2 loaves, 2 boats. All four of these objects are fixed points of B3/S23:

```python
def step(g, rule):
    birth, survive = rule
    r, c = len(g), len(g[0])
    out = [[0] * c for _ in range(r)]
    for i in range(r):
        for j in range(c):
            n = sum(g[i + di][j + dj]
                    for di in (-1, 0, 1) for dj in (-1, 0, 1)
                    if (di, dj) != (0, 0) and 0 <= i + di < r and 0 <= j + dj < c)
            out[i][j] = 1 if (n in birth) or (g[i][j] and n in survive) else 0
    return out


BLOCK = [[1, 1], [1, 1]]
BEEHIVE = [[0, 1, 1, 0], [1, 0, 0, 1], [0, 1, 1, 0]]
LOAF = [[0, 1, 1, 0], [1, 0, 0, 1], [0, 1, 0, 1], [0, 0, 1, 0]]
BOAT = [[1, 1, 0], [1, 0, 1], [0, 1, 0]]

for name, obj in [("block", BLOCK), ("beehive", BEEHIVE), ("loaf", LOAF), ("boat", BOAT)]:
    print(name, "stable under B3/S23:", step(obj, ((3,), (2, 3))) == obj)
```

```text
block stable under B3/S23: True
beehive stable under B3/S23: True
loaf stable under B3/S23: True
boat stable under B3/S23: True
```

Block, beehive, loaf and boat are stable together under B3/S23 but not together under other rules, which makes the census a usable filter: per the record, 16 other rules were excluded on exactly these structures. The record does not state that the whole space of Life-like rules was enumerated, so the conclusion is bounded to "the rule consistent with every object counted in the grid, having eliminated 16 candidates".

### The flag is the ancestor, not the descendant

Forward Life destroys information, so the flag cannot be read out of the grid. The problem is a predecessor search: find a generation-0 configuration that, after 18 generations of B3/S23, becomes exactly the grid extracted from the screenshot. With only that constraint the space of axioms is effectively unbounded — reverse Life is an under-determined problem.

The second constraint comes from the statement itself: generation 0 must be the render of a text line using a DejaVu 2.37 TTF. The predecessor is therefore not an arbitrary configuration but the bitmap of a character string, with glyph columns placed by the pen advance. The record uses:

```text
pen(i) = 1 + round(i * 617 / 64)
```

`617/64 = 9.640625` columns per glyph; `pen(38) = 367` fits inside the 371-column grid, so this geometry admits a 38-character string — precisely the length of the flag. Two consequences: the search space collapses from configurations to character strings, and every candidate has a cheap test (render, then simulate forward).

## Solution

The search ran over candidate strings: render the string with the recorded DejaVu metrics to obtain the predecessor, evolve it forward 18 generations under B3/S23, and compare cell by cell against the extracted grid. The candidate with zero mismatches is the solution.

The final search log includes a 40-character candidate whose prefix is the flag:

```text
mism= 0 len=40 'FortID{R3al_L1f3_H45_N0_R3w1nd_Bu7t0n}83'
```

The extra `83` is outside the accepted flag. The 371-column target grid does not distinguish those trailing candidates, so `len=40` describes a matching search candidate, not the flag's length. The final check rendered the 38-character flag in DejaVuSansMono-Bold, evolved it 18 generations under B3/S23, and reported an exact match with the extracted grid: 909 live cells and zero mismatches. The recovered ancestor bitmap was also visually confirmed to read `FortID{R3al_L1f3_H45_N0_R3w1nd_Bu7t0n}`.

## Result

```text
FortID{R3al_L1f3_H45_N0_R3w1nd_Bu7t0n}
```

The saved final check confirms that rendering the 38-character flag and evolving it 18 generations under B3/S23 reproduces the extracted grid exactly. The full search program and screenshot are not included in this repository, so the search itself is not packaged for a fresh run.

## Reproduce

Inputs: the statement screenshot, the DejaVu 2.37 font files (TTFs), Python 3 with `pillow`/`numpy` for pixel sampling and glyph rendering, plus `fonttools` if the metrics are to be read from the TTFs directly.

1. Sample the grid with the recorded parameters: 27×371, cells 6×6 px at pitch 8 px, origin `x = 55 + 8c`, `y = 32 + 8r`; cell intensity ≥ 50% means live. The geometry block in the Analysis section re-runs those parameters and prints the 0.0907 density and the 3021×246 px raster size implied by them.
2. Count the still lifes to fix the rule; the `step()` block verifies that block/beehive/loaf/boat are all fixed points of B3/S23.
3. For each candidate string: render the predecessor with pen advance `pen(i) = 1 + round(i * 617 / 64)`, evolve forward 18 generations under B3/S23, count mismatching cells against the grid from step 1.
4. Stop at the candidate with `mism= 0`; the string that rendered that predecessor is the flag.

Step 3 is the expensive part and runs entirely locally. The record preserves the final exact-match check, but not the full search script or screenshot; those inputs are needed to rerun the candidate search from scratch.
