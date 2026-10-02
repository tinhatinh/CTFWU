# Lamp Drill - Warm-up (49 points)

**Flag:** `CSSCTF{css}`
**Resources:** `lampDrill.svg` (Size: 54,671 B, SHA256: `4a11f4a884aab46c...`) and its raster graphics version `lampDrill.png` (2624x1472).

## Problem Description

The challenge provides `lampDrill.svg` and `lampDrill.png` with the hint "Warm-up. No spaces.". The top row defines an operation on two bulbs, and the three rows below contain the data to decode into `CSSCTF{...}`.

## Initial Analysis

The states can be read directly from the image: a filled bulb is 1 and an empty bulb is 0. For a scripted reproduction, read the SVG `<path>` elements and their `fill` values. Grouping by diameter gives:

| Diameter | Quantity | Object Identification |
| --- | --- | --- |
| 23.0 | 60 | Light bulb |
| 101.7 | 24 | Rounded background frame (grid cell) |
| ≈7.9 | 25 | Directional arrow (▶) |

There are 60 bulbs: 12 in the rule row and 48 in the data grid of 3 rows × 8 cells × 2 bulbs. The script maps `#1c1915` to 1 and `#f7f4ee` to 0.


The top row outputs 1 only when both inputs are 1, which is the AND operation:

```text
## -> #      #. -> .      .# -> .      .. -> .
```

The matrix area below consists of 3 sequences, each comprising 8 cells sequentially linked via directional arrows. Each cell contains exactly two light bulbs (2 input bits).

## Exploitation Chain

**Step 1 - Read the bulb states.**
The script reads the bounding boxes of the `<path>` elements, keeps objects with diameters from 22 to 24, and maps their `fill` values to bits. This reproduces the states visible in the image.

**Step 2 - Read the truth table.**
In the rule row, group the bulbs by x-coordinate into input pairs and single outputs. The code below records the truth table from those groups:

```python
cells = clusters(rows[0], gap=50.0)          # Array decomposition result -> [2, 1, 2, 1, 2, 1, 2, 1]
for i in range(0, len(cells), 2):
    a, b = (int(x[2]) for x in cells[i])
    table[(a, b)] = int(cells[i + 1][0][2])
```

The resulting table is `00->0 01->0 10->0 11->1`, matching the AND operation shown in the top row.

**Step 3 - Assemble the bytes.**
Apply AND to the two bits in each cell, then read eight cells from left to right as one ASCII byte:

```text
Sequence 1: bits=01100011 -> Hex: 0x63, ASCII: 'c'
Sequence 2: bits=01110011 -> Hex: 0x73, ASCII: 's'
Sequence 3: bits=01110011 -> Hex: 0x73, ASCII: 's'
```

**Step 4 - Validate integrity (Verification).** 
Check the counts: 12 bulbs in the rule row and 48 in the data rows, with two bulbs per cell. The last two rows differ at the first cell (`.#` versus `..`), but AND produces 0 in both cases, so both decode to `s`. The three decoded bytes are `css`.

## Flag

Run the script:

```bash
python exploit.py files/lampDrill.svg
```

```text
[*] Detected 60 bulbs, divided into 4 rows
[*] Analyzed rule row: 00->0 01->0 10->0 11->1
[*] Recovered truth table: {(1, 1): 1, (1, 0): 0, (0, 1): 0, (0, 0): 0}
[*] Operation format: AND
    Sequence 1 bits=01100011 -> 0x63 'c'
    Sequence 2 bits=01110011 -> 0x73 's'
    Sequence 3 bits=01110011 -> 0x73 's'
[*] Decoded result: 'css'
[!] CSSCTF{css}
```

Result:
```text
CSSCTF{css}
```

*The flag is derived from the artifact; the current record does not include a confirmed scoreboard submission.*
