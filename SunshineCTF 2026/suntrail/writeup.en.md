# Suntrail — Misc (Medium)

**Flag:** `sun{qwerty_sucks}` · **Files:** `files/suntrail.klc`, 419 byte ASCII, sha256 `abe7590751412fe5607bacd7bfc4a3131e5c108bf2eedbbe78d438e96dc8c6ff`

## Challenge

`im lost, but you can find the way!`

A single file, no remote instance, no hint to open. Author oatzs.

## Initial Analysis

`.klc` is a Microsoft Keyboard Layout Creator source file, not a Kaspersky license file as the
name could mislead one to think. The file begins with `KBD kbdusx "US"`, then the `SHIFTSTATE`
block, then `ENDKBD`.

The `LAYOUT` block has 18 tab-separated lines, each line being one key:

```
10  Q  0  2192  0073  -1
```

In order: scan code, key label, shift state, the unicode character in state 0, the unicode
character in state 1, and `-1`. The two states are not symmetric:

- state 0 uses only four values: `U+2192` (right arrow, 4 keys), `U+2196` (up diagonal, 4 keys),
  `U+2198` (down diagonal, 6 keys), `U+25A0` (black square, 1 key at H);
- state 1 is only lowercase letters plus `{`, `}`, `_`; `U+007B` sits on X, `U+007D` sits on H.

The black square and the `}` both sit on H, so H is the destination. Each key therefore carries
two layers: a direction to travel and a character to collect.

## Approaches Ruled Out

1. `.klc` being a Kaspersky license key: the content is ASCII following exactly the `KBD` /
   `SHIFTSTATE` / `LAYOUT` / `ENDKBD` template. Ruled out.
2. Hidden data in leftover bytes or trailing whitespace: the file ends with `ENDKBD\n`, plain LF,
   no line has a trailing space or tab, no byte after EOF. Ruled out.
3. The flag written plainly in the file: triage reports 0 hits for flag patterns; the characters in
   the file are only lowercase letters and arrows. Ruled out.

The log of each branch is in `notes.md`.

## Exploit Chain

**Step 1 - extracting the data.** Parse the 18 `LAYOUT` lines, dropping `SPACE` (scan code `0x39`,
both states are a space so it carries nothing). Arrange the remaining 17 keys into three physical
rows by scan code: top `Q W E R T`, home `A S D F G H`, bottom `Z X C V B N`.

**Step 2 - pinning down the geometry by sweeping a small space.** A real keyboard is staggered, so
which cell a diagonal arrow maps to cannot be guessed. `analysis/search_geometry.py` sweeps all 8³
ways of assigning the three direction characters onto the eight neighboring cells, walks from every
key under each assignment, and keeps the paths that produce a string containing both `{` and `}`.
This grid does not give a single solution: `analysis/geometry_search_results.txt` stores 21 paths,
most of them truncated strings or missing the leading character. The assignment set left after step 3:

```
U+2192 -> sang phải một cột
U+2196 -> lên một hàng
U+2198 -> xuống một hàng
U+25A0 -> điểm dừng
```

**Step 3 - the start point inferred from the graph.** With the geometry from step 2, count the keys
that no arrow points into: only `Q` remains. Walking from `Q` along the arrows until the black
square, that path goes through exactly 17/17 keys, each key once, and is the only one of the 21
paths that reads out a complete string.

```
Q A Z X S W E D C V F R T G B N H
s u n { q w e r t y _ s u c k s }
```

## Flag
```bash
python exploit.py files/suntrail.klc
```

```
keys with no incoming arrow (candidate starts): ['Q']
  start=Q path=QAZXSWEDCVFRTGBNH -> 'sun{qwerty_sucks}'
start key : Q
path      : QAZXSWEDCVFRTGBNH
keys used : 17/17
flag      : sun{qwerty_sucks}
```

## Reproduce

`exploit.py` uses only the stdlib, takes the artifact path from argv, exits with code 0 when it finds
a complete walk to the destination cell, and prints the flag string. `analysis/search_geometry.py`
is the geometry probing step, its results are in `analysis/geometry_search_results.txt`.
