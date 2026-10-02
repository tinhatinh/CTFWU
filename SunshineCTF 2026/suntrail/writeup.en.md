# Suntrail - Misc (Medium)

**Flag:** `sun{qwerty_sucks}` · **Files:** `files/suntrail.klc`, 419 byte ASCII, sha256 `abe7590751412fe5607bacd7bfc4a3131e5c108bf2eedbbe78d438e96dc8c6ff`

## Challenge

`im lost, but you can find the way!`

A single file, no remote instance, no hint to open. Author oatzs.

## Initial Analysis

The file follows the Microsoft Keyboard Layout Creator format, beginning with `KBD kbdusx "US"`, followed by `SHIFTSTATE`, `LAYOUT` and `ENDKBD`.

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

Triage confirms the keyboard-layout structure. The file ends with `ENDKBD
` and has no trailing data after that marker. The flag is assembled by following the arrows, rather than read as a contiguous string in the file.

The log of each branch is in `notes.md`.

## Exploit Chain

**Step 1 - extracting the data.** Parse the 18 `LAYOUT` lines, dropping `SPACE` (scan code `0x39`,
both states are a space so it carries nothing). Arrange the remaining 17 keys into three physical
rows by scan code: top `Q W E R T`, home `A S D F G H`, bottom `Z X C V B N`.

**Step 2 - Follow the arrows on the keys.** Use the three-row layout from step 1: move right by one column, up one row or down one row, and stop at the black square. The reproduction uses:

```
U+2192 -> one column right
U+2196 -> one row up
U+2198 -> one row down
U+25A0 -> stopping point
```

**Step 3 - Follow the path from Q.** Only `Q` has no incoming arrow. Follow the arrows from `Q` to the black square at `H`; the path visits all 17 keys once. Collect the state-1 characters in that order:

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
