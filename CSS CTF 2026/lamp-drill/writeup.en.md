# Lamp Drill - Warm-up (49 points)

**Flag:** `CSSCTF{css}`
**Resources:** `lampDrill.svg` (Size: 54,671 B, SHA256: `4a11f4a884aab46c...`) and its raster graphics version `lampDrill.png` (2624x1472).

## Problem Description

The system provides a static image file, without any accompanying online services. The problem description states: "Warm-up. No spaces." and specifies the flag format as `CSSCTF{}`. The challenge's objective is to analyze and decode the hidden character string within this graphic image.

## Initial Analysis

Evaluating the SVG file: Based on the metadata, the file was created using the Matplotlib 3.9.2 library (`dc:date` 2026-09-30T07:31:34, setting `viewBox 0 0 1180.8 662.4`). The SVG vector structure contains objects with pristine visual properties, making the application of Optical Character Recognition (OCR) techniques on the Raster image unnecessary. The analysis process is performed directly on the vector data: each light bulb is represented by a `<path>` tag drawing a Bezier curve integrating the color property `style="fill: ..."`. Classifying objects based on dimensional parameters (diameter) yields perfectly consistent results:

| Diameter | Quantity | Object Identification |
| --- | --- | --- |
| 23.0 | 60 | Light bulb |
| 101.7 | 24 | Rounded background frame (grid cell) |
| ≈7.9 | 25 | Directional arrow (▶) |

The total of 60 light bulbs is structurally streamed into two areas: The logic definition area (top row, consisting of 12 light bulbs) and the data matrix area (a grid of 3 rows x 8 cells x 2 bulbs/cell, totaling 48 bulbs).
The light bulb state data is indicated by two color codes: `#1c1915` (on) and `#f7f4ee` (off - matching the overall background color of the graph). There are no hidden text strings, no camouflage layers, and no additional suspicious metadata.

The logic definition area outlines the truth table of the operation applied to two input states:

```text
## -> #      #. -> .      .# -> .      .. -> .
```

The matrix area below consists of 3 sequences, each comprising 8 cells sequentially linked via directional arrows. Each cell contains exactly two light bulbs (2 input bits).

## Exploitation Chain

**Step 1 - Extract the light bulb array data from the SVG structure.** 
Deploy an algorithm to iterate through all `<path>` tags containing the `fill:` attribute. The system calculates the bounding box based on the coordinate systems defined in the `d` attribute. Data will be retained for objects with a diameter dimension fluctuating within the 22-24 margin (corresponding to the light bulb structure). Correlate the `fill` value with the color code `#1c1915` to quantify it into a binary bit (on = 1, off = 0).

**Step 2 - Analyze the truth table using an automated algorithm (No Hard-coding).** 
Cluster the elements based on the x-axis coordinate system: For the logic definition row, the system groups the cells into pairs (2 bulbs acting as inputs) and singles (1 bulb acting as output), arranged alternately.

```python
cells = clusters(rows[0], gap=50.0)          # Array decomposition result -> [2, 1, 2, 1, 2, 1, 2, 1]
for i in range(0, len(cells), 2):
    a, b = (int(x[2]) for x in cells[i])
    table[(a, b)] = int(cells[i + 1][0][2])
```

Exported logic matrix: `00->0 01->0 10->0 11->1`. This is the exact specification of an AND logic gate. Automating the process helps this script operate robustly even if the organizers change the parameter to an XOR or OR gate in other versions of the problem.

**Step 3 - Synthesize Bytes from the Bit system.**
Apply the AND operation for the bit pairs in each cell, synthesizing 8 cells into a raw data byte.

```text
Sequence 1: bits=01100011 -> Hex: 0x63, ASCII: 'c'
Sequence 2: bits=01110011 -> Hex: 0x73, ASCII: 's'
Sequence 3: bits=01110011 -> Hex: 0x73, ASCII: 's'
```

**Step 4 - Validate integrity (Verification).** 
Cross-examine the quantity: The total of 60 light bulbs perfectly matches the structural breakdown (12 logic bulbs + 48 data bulbs); every cell in the matrix satisfies the condition of possessing exactly 2 light bulbs; the constructed truth table covers all 4 proposition cases; all 3 decoded bytes are valid in the ASCII code table (printable characters). Detailed analysis: Sequence 2 and sequence 3 only differ in the signal state of the first cell (`.#` vs `..`), but when passed through the AND projection, both yield a 0 bit result, leading to both decoding to the character `s`. This affirms that this is a deliberate design characteristic of a warm-up problem, not due to reading sensor deviations.

## Flag

Executing the automated script:

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

*Note: Due to the nature of not providing a network service for validation, this flag structure is classified as "Successfully decoded based on Artifact analysis", pending verification from the scoring system.*
