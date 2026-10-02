# A Star Trail 2 - Misc/Graph (Intermediate)

**Flag:** `CSSCTF{STARmaPdElAUNaYTriaNGulATioNDIjKStrAVoRonoiGrAPHSdetERmiNaNTcolineaRALGOrITHmSLeEandsCHAcHTERTANgEnTSmErGECirCuMcIrcLEcOnVEXhuLLgeOMeTRy}`
**Attached file:** `map.zip` (Size: 2,663,657 B, SHA256: `31c44f1b...a97525f9`)

## Problem Description

The system provides a database comprising 10,000 Markdown format files representing a galactic map. Each file corresponds to a planet, containing information including: ID, coordinates, and a list of neighboring planets presented in wiki link tag format (`[[wikilink]]`). The requirement is to find a route from planet `S0jRxc` to planet `yRJyDb` "in a reasonable amount of time".
Flag assembly rule: Begin by taking the 1st letter of the first stop, the 2nd letter of the second stop, continuing to increment and loop back (modulo) to the 1st letter at the 7th, 13th, 19th stops, etc. This assembly process is case-sensitive.

## Initial Analysis

Proceeding to scan all 10,000 files, the data exactly displays only three types of information fields:

```python
Counter({'wikilink': 59944, 'title': 10000, 'coords': 10000})
```

There is no data field specifying the "number of days" (time) as in the previous challenge. The sole factor usable as a quantifier (weight) is the coordinates. Graph structure analysis reveals highly integral data: 59,944 directed edges, when merged, form exactly 29,972 undirected edges. This proves all links are absolutely symmetrical, with no dangling links, and the average degree of each vertex is approximately 5.99.

## Exploitation Chain

**Step 1 - Construct the graph directly from the archive file.** 
No manual extraction is needed; a Python script uses the `zipfile` library to sequentially read each `map/<ID>.md` file, from which it extracts the coordinate fields and neighbor planet lists to form the graph.

**Step 2 - Apply Dijkstra's algorithm with Euclidean distance weights.** 
Utilize the Euclidean distance formula between two coordinates as the weight for the edges, then apply Dijkstra's algorithm:

```text
Result: 135 hops, total distance 144.9333, optimal path count = 1
The straight-line distance connecting the two endpoints is 138.6231 -> The optimal route is 4.55% longer
```

Through Dynamic Programming techniques running on the Dijkstra tree, the system confirms there is exactly 1 unique optimal path, necessitating no further secondary deductions.

**Step 3 - Cross-reference evaluation criteria.** 
The path with the fewest hops measures at 199.95, while the shortest path based on the coordinate system has a length of 144.93. If the problem demanded optimizing the hop count, these two results would have coincided. This discrepancy confirms that coordinate distance is the correct weight.

**Step 4 - Validate via hidden message.** 
Applying the letter assembly rule `id[i % 6]` (including both the starting and ending vertices `S0jRxc` and `yRJyDb`), the system obtains a result string 136 characters long. When reading this string, the content forms a clearly semantic message:

```text
STAR MAP · DELAUNAY TRIANGULATION · DIJKSTRA VORONOI · GRAPHS · DETERMINANT · COLINEAR · ALGORITHMS · … TANGENTS · MERGE · CIRCUMCIRCLE · CONVEX HULL · GEOMETRY
```

If an incorrect route were chosen, the result would be a string of meaningless random characters (noise). The fact that the character string forms a list of computational geometry algorithms is the strongest conclusive evidence that the coordinate-based Dijkstra route is exactly the author's intended design.

**Step 5 - Test the flag assembly rule.** 
The problem provides an illustrative example of the assembly rule: (ASTART, BCDEFG, hijklm, NOPQRS, tuvwxy, ZFINAL -> `ACjQxL`). This example is integrated into the exploit script (`exploit.py`) as a unit test checkpoint. If an incorrect assembly rule is applied (e.g., always extracting the first letter), the unit test will detect it and report an error immediately.

## Flag

Executing the automated script:

```bash
$ python exploit.py files/map.zip
1) graph: 10000 nodes, 59944 directed edges, 29972 undirected edges
2) Dijkstra by coordinates: 135 hops, total distance 144.9333, optimal path count = 1
3) straight line start-end node = 138.6231 -> route is 4.55% longer
4) all 135 edges are real wikilinks in map
5) 'fewest hops' interpretation: 13 hops but distance 199.9478 (shortest is 144.9333) -> mismatch
6) path (136 nodes):
   S0jRxc -> 1T5eN4 -> hmANsv -> XGnRvX -> CZqgmf -> HFtEqa -> PNHmEq -> zdQEDJ -> PqE5LH -> 7GwlrF ->
   s4clAO -> BZBIfU -> Nr4nCb -> caVoaa -> iQYvOf -> PzNTZG -> 1M0urD -> QMPisi -> amu7Wo -> iNCLPy ->
   QpG6f5 -> MR8uJc -> Bj68lj -> HETuLA -> TrGMSs -> JiPYRV -> PpowW7 -> tVsNxK -> 9luvD5 -> BwCBhI ->
   jctq4E -> BK2t5a -> aMS8lF -> 0y8tTE -> Nnb8rI -> gpo1OA -> VIJCJC -> ootqYn -> YGRffF -> oqWomB ->
   gBq3nj -> 9RXg8o -> idn8MR -> 3Ge1Ze -> wDrRGY -> KgxAJF -> Au7JPZ -> sfamMH -> SZeex7 -> 5dB0SL ->
   YHeChf -> AoHtOq -> h8A8Eq -> DcGFsR -> mNypTS -> nikTvk -> QsNinN -> fJSa8c -> UI6ZN7 -> LMdJ5T ->
   cnUGJr -> So0gII -> f9ltmH -> 7Ckib9 -> 96O7nm -> GwZvTe -> aULZyG -> dRrW9E -> AcA4vb -> KQ5LGq ->
   nyeoGv -> K77Q2O -> rM0kaj -> nI3TNd -> JoT8Lw -> 4eMHte -> iOvkmn -> YNz5nS -> LZgaSg -> BepSSx ->
   aXE4nS -> 77Nab2 -> qGHln3 -> hf47ld -> sAFynQ -> lChcQn -> 8fHQzd -> XXpAa6 -> oOyVcu -> FzP1DH ->
   TMtjsI -> HEtwSC -> QFRV2e -> LAVTJQ -> Gl2ZAI -> 0QfLJN -> gjKpSu -> PEsjS8 -> r8nrfI -> RGXT2a ->
   exrjS0 -> K3oT0m -> EGoU5L -> Yrggxs -> 25GB9o -> ssqEuY -> UelHC3 -> EISTKi -> rZhn2k -> 5CXPOK ->
   9buFn2 -> Ug9MqQ -> 4cWCct -> DlIidI -> rm6bAP -> wcxQ5o -> p7LRWQ -> qLnEKN -> ZJNscx -> gymzEO ->
   np5olu -> pVWtdw -> sTEnG2 -> Ws6XnB -> Sawmhz -> KXOShu -> LrO3VY -> PLYS2Q -> GWgqRX -> clzegJ ->
   fm4gOr -> ScLSwM -> etckNZ -> KTjmKT -> jvRMt3 -> yRJyDb

FLAG: CSSCTF{STARmaPdElAUNaYTriaNGulATioNDIjKStrAVoRonoiGrAPHSdetERmiNaNTcolineaRALGOrITHmSLeEandsCHAcHTERTANgEnTSmErGECirCuMcIrcLEcOnVEXhuLLgeOMeTRy}
```

Result:
```text
CSSCTF{STARmaPdElAUNaYTriaNGulATioNDIjKStrAVoRonoiGrAPHSdetERmiNaNTcolineaRALGOrITHmSLeEandsCHAcHTERTANgEnTSmErGECirCuMcIrcLEcOnVEXhuLLgeOMeTRy}
```
