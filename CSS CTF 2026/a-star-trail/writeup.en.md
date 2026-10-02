# A Star Trail - Misc/OSINT (Beginner)

**Flag:** `CSSCTF{P1JT-21.0}` · **Files:** `A_Star_Trail.png` (3780x1890, sha256 `a3584ca6…c3d33ed`)

## Challenge

The card is a star map: "POLARIS LOGISTICS STAR MAP - NO. CA-S08-R11" draws 13 celestial bodies
joined by 20 dashed routes, each labelled with a number of days. The delivery has to go from EARTH
to LANCER-RXKRD along existing routes only, in under 25 days. The flag is the first letter of each
body on the path, joined to the total number of days (one decimal place) with a dash.

## Initial Analysis

The PNG is an Inkscape export with the standard chunk layout `IHDR / pHYs / tEXt / 74xIDAT / IEND`,
no bytes after IEND and nothing suspicious inside the data, so there is no stego channel: the task
is purely to read the graph and find the shortest path.

13 nodes, 20 edges, real weights. Small enough that reading it by eye and re-checking in code is
enough.

## Exploit Chain

**Step 1 - Read all 20 edges.** The image was cut into four overlapping bands so that each dashed
line and its label fit inside one frame (the bands are stored in `files/band_*.png`). The edge table
came out with all 20 labels.

**Step 2 - Run Dijkstra.**

```python
path, cost = dijkstra(g)
# EARTH -> PALLUS-XA -> 12-PUCK-8 -> JIP-REIA -> TAYLOR-3489 -> LANCER-RXKRD
# 10.7   + 1.8         + 0.4          + 5.5         + 2.6            = 21.0 ngay
```

**Step 3 - Check the optimum is unique.** Enumerating every simple path under 25 days: five of them,
21.0 / 21.6 / 22.7 / 22.9 / 24.3. The 21.0 optimum appears once, so no further crib is needed.

**Step 4 - Verify.** Re-summing each edge of the Dijkstra path gives exactly 21.0; every edge on the
path exists in the table read from the image; the number of edges used equals the number of labels on
the map.

**Step 5 - Assemble the flag.** "each planet/oid in your path" here means the intermediate stops,
excluding the origin and the destination. The full route is
`EARTH -> PALLUS-XA -> 12-PUCK-8 -> JIP-REIA -> TAYLOR-3489 -> LANCER-RXKRD`, the four middle stops
give P (PALLUS-XA), 1 (12-PUCK-8), J (JIP-REIA), T (TAYLOR-3489) → `P1JT`, then `-21.0`.
The variant that includes both endpoints (`EP1JTL-21.0`) was submitted and rejected.

The sensitivity worth remembering: the runner-up is only 0.6 days behind, so misreading one small
weight (0.4 or 1.8) flips the flag to `EPBJTL-21.6`. The script tries those two variants and shows
the result really does change, which means the image reading is the fragile part, not the arithmetic.

## Flag

```
$ python exploit.py
1) do thi: 13 nut, 20 canh (doc tu anh)
2) Dijkstra: EARTH -> PALLUS-XA -> 12-PUCK-8 -> JIP-REIA -> TAYLOR-3489 -> LANCER-RXKRD = 21.0 ngay
3) cong lai tung canh: 21.0 - khop
4) duong duoi 25 ngay: 5, ngan nhat 21.0, thu nhi 21.6
5) dinh dang CSSCTF{<ky tu dau moi nut>-<ngay>}

FLAG: CSSCTF{P1JT-21.0}
```

## Reproduce

```bash
python exploit.py
```
