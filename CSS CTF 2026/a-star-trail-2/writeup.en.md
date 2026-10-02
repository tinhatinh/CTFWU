# A Star Trail 2 - Misc/Graph (Intermediate)

**Flag:** `CSSCTF{STARmaPdElAUNaYTriaNGulATioNDIjKStrAVoRonoiGrAPHSdetERmiNaNTcolineaRALGOrITHmSLeEandsCHAcHTERTANgEnTSmErGECirCuMcIrcLEcOnVEXhuLLgeOMeTRy}` · **Files:** `map.zip` (2663657 B, sha256 `31c44f1b…a97525f9`)

## Challenge

This time the galactic map is not an image but a database of 10000 Markdown files, one file per
planet: an ID, coordinates, and a list of neighbours as `[[wikilink]]`. The flight goes from
`S0jRxc` to `yRJyDb` "in a reasonable time". The flag is built by taking the first letter of the
first stop, the second letter of the second stop, and so on, wrapping back to the first letter at
the 7th, 13th, 19th stop; case sensitive.

## Initial Analysis

Scanning all 10000 files, each one contains exactly three kinds of line:

```
Counter({'wikilink': 59944, 'title': 10000, 'coords': 10000})
```

There is no days-per-route field like in the first version, so the only measurable quantity is the
coordinates. The graph is also clean: 59944 directed edges collapse to exactly 29972 undirected ones
(linking is perfectly symmetric), no dangling links, average degree 5.99.

## Exploit Chain

**Step 1 - Build the graph from the zip** without extracting it: read each `map/<ID>.md` through
`zipfile`, taking the coordinates and the neighbour set.

**Step 2 - Dijkstra with the weight set to the Euclidean distance between two coordinates.**

```
135 chan, tong quang duong 144.9333, so duong toi uu = 1
duong thang noi hai dau 138.6231 -> lo trinh dai hon 4.55%
```

Counting optimal paths with DP over the Dijkstra tree gives exactly 1, so nothing has to be guessed.

**Step 3 - Compare the two readings of the brief.** The fewest-hops path is 199.95 long while the
shortest coordinate path is 144.93; if the author had meant hops, the two would have agreed.

**Step 4 - Verify with the hidden message.** Joining letters with the rule `id[i % 6]` (counting both
`S0jRxc` and `yRJyDb`) turns the 136-character string into:

```
STAR MAP · DELAUNAY TRIANGULATION · DIJKSTRA VORONOI · GRAPHS · DETERMINANT ·
COLINEAR · ALGORITHMS · … TANGENTS · MERGE · CIRCUMCIRCLE · CONVEX HULL · GEOMETRY
```

A string taken from a wrong path would be letter noise; it cannot read as a list of geometry
algorithms by accident. This is the strongest evidence that the chosen path is the intended one.

**Step 5 - Check the flag-assembly rule.** The example on the card (ASTART, BCDEFG, hijklm, NOPQRS,
tuvwxy, ZFINAL → `ACjQxL`) is used as a lock test inside `exploit.py`; trying the wrong rule (always
take the first letter) is caught immediately.

## Flag

```
$ python exploit.py files/map.zip
1) do thi: 10000 nut, 59944 canh chieu, 29972 canh vo huong
2) Dijkstra theo toa do: 135 chan, tong quang duong 144.9333, so duong toi uu = 1
3) duong thang lien nut dau-cuoi = 138.6231 -> lo trinh 4.55% dai hon
4) all 135 edges are actual wikilinks in the map
5) cach hieu 'it chan nhat': 13 chan nhung dai 199.9478 (ngan nhat la 144.9333) -> khong trung
6) duong di (136 nut):
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

## Reproduce

```bash
python exploit.py files/map.zip
```
