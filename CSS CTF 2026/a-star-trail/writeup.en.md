# A Star Trail - Misc/OSINT (Beginner)

**Flag:** `CSSCTF{P1JT-21.0}`
**Attached file:** `A_Star_Trail.png` (Size: 3780x1890, SHA256: `a3584ca6...c3d33ed`)

## Challenge

The challenge provides a map titled "POLARIS LOGISTICS STAR MAP - NO. CA-S08-R11". This map depicts 13 celestial bodies connected to each other via 20 dashed lines, each line annotated with the corresponding number of travel days. The requirement is to find a travel route from the celestial body `EARTH` to the celestial body `LANCER-RXKRD`, moving along the given lines such that the total number of days does not exceed 25.
The flag structure is assembled from the first letter of each celestial body on the route (counting only intermediate stations), concatenated with the total travel days (formatted with one decimal place) using a hyphen `-`.

## Analysis

Checking the PNG file structure: The file was exported from Inkscape software, strictly adhering to the format with standard chunks (`IHDR`, `pHYs`, `tEXt`, 74 `IDAT` chunks, and `IEND`). No extraneous data was detected after the `IEND` chunk, nor were there any abnormal text strings in the data structure. Therefore, the possibility of the file using steganography techniques can be ruled out. The problem reduces to a pure form: read data from the graph and find the shortest path.

The graph consists of 13 vertices and 20 edges, with real number weights. The size of this graph is small enough that data can be manually extracted via visual reading, and then programming code can be used to automate the calculation process.

## Solution

**Step 1 - Extract all 20 edges from the map.**
Proceed to split the image into four overlapping bands, ensuring each dashed line and corresponding number label completely fits within an image frame (these bands are stored at `files/band_*.png`). From there, tabulate and confirm the collection of all 20 weight labels.

**Step 2 - Apply Dijkstra's algorithm.**
Set up the graph and run Dijkstra's algorithm to find the shortest path:

```python
path, cost = dijkstra(g)
# Route: EARTH -> PALLUS-XA -> 12-PUCK-8 -> JIP-REIA -> TAYLOR-3489 -> LANCER-RXKRD
# Cost: 10.7 + 1.8 + 0.4 + 5.5 + 2.6 = 21.0 days
```

**Step 3 - Verify the route's uniqueness.**
Use a traversal algorithm to list all simple paths with a cost under 25 days. The results show a total of 5 valid paths, with respective costs of: 21.0, 21.6, 22.7, 22.9, and 24.3 days. The route taking 21.0 days is the shortest path and appears only once, requiring no additional condition (crib) for classification.

**Step 4 - Verify data integrity.**
Perform an addition check of the weights on the obtained Dijkstra path, the total exactly equals 21.0. Every edge on the route is present in the data table extracted from the original image, and the number of utilized edges matches the number of labels on the map.

**Step 5 - Extract and assemble the Flag.**
The data point "each planet/oid in your path" is interpreted as the intermediate stop stations, excluding the starting point (`EARTH`) and the destination point (`LANCER-RXKRD`).
The full route is: `EARTH -> PALLUS-XA -> 12-PUCK-8 -> JIP-REIA -> TAYLOR-3489 -> LANCER-RXKRD`.
Taking the first letter of the four intermediate stations, we have: `P` (PALLUS-XA), `1` (12-PUCK-8), `J` (JIP-REIA), `T` (TAYLOR-3489). Assembling them yields the string `P1JT`, concatenated with the total days as `-21.0`. (The testing process showed that if both endpoints are included as `EP1JTL-21.0`, the system rejects it).

The second-shortest route costs 21.6 days, 0.6 days more than the selected route. Misreading small weights such as 0.4 or 1.8 can produce `EPBJTL-21.6`, so the labels are checked against the image before finalizing the graph.

## Result

Run the script:
```bash
$ python exploit.py
1) graph: 13 nodes, 20 edges (read from image)
2) Dijkstra: EARTH -> PALLUS-XA -> 12-PUCK-8 -> JIP-REIA -> TAYLOR-3489 -> LANCER-RXKRD = 21.0 days
3) sum each edge: 21.0 - match
4) paths under 25 days: 5, shortest 21.0, runner-up 21.6
5) format CSSCTF{<first char of each node>-<days>}

FLAG: CSSCTF{P1JT-21.0}
```

Result:
```text
CSSCTF{P1JT-21.0}
```
