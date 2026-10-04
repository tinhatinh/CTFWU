# Gerry the Larry (2/2) - Web Exploitation (500 points) — OPEN

**Flag:** none yet · **Points:** 500 · **Authors:** reep236, adlee7 (CDCTF)
**Artifact:** the web app on the instance, no handout

## What has been measured

### 1. PureScript client, FastAPI backend

`index.html` loads only `/assets/index.501b4b7d.js` (152 KB). Runtime strings such as
`Failed pattern match at Control.Applicative` / `Data.Map.Internal` identify compiled PureScript.
The 422 responses from `/vote` are pydantic-shaped (`{"detail":[{"type":..,"loc":[..],..}]}`).
`/openapi.json`, `/docs`, `/redoc` all 404 behind nginx, so the schema was not available at those paths.

### 2. The "signature" has no secret — UVINs can be minted at will

```javascript
ES = function(n){ return tS(((n.number + (2*n.lon_block)) + (4*n.lat_block)) + (8*n.year)) }
SS = function(n){ return lu(4)(n.year) + lu(2)(n.lat_block) + lu(2)(n.lon_block) + lu(4)(n.number) }
```

i.e. `signature = 8·year + 4·lat_block + 2·lon_block + number` and `uvin = "%04d%02d%02d%04d"`.
The UI input wants dashes (`YYYY-LL-LL-NNNN`, `_S` splits on `'-'` and requires exactly 4 groups), but
`/vote` takes the 12-digit string. Server-side confirmation: `signature:"1"` →
`flag = "Error: Invalid UVIN!"`, while `signature:"16215"` (= 8·2026+4·1+2·1+1) is not rejected as invalid.

### 3. The ballot is 121 plain booleans, and `result` is only an echo

```text
POST /vote {"uvin":"202601010001","signature":"16215","votes":[true, ... ]}
-> 200 {"result":[<exactly the list that was sent>], "flag":"<verdict or error>"}
```

pydantic answers `"Input should be a valid boolean"` for `{"address":..,"payload":..}` objects, so the
`{address,payload}` shape the client builds internally is **not** the wire format: it is a flat list ordered
by `Ys(5)` = `lat` outer `1..11`, `lon` inner `1..11`, i.e. `index = (lat-1)*11 + (lon-1)`.
Length is unvalidated: 100, 121, 122 and empty were all accepted, each echoed at its own length.
This matches the client grid: `kS(5)` walks `1..(2·5+1)`, cells with odd lat **and** odd lon are name labels
(the 6×6 `OS` table of 36 precincts), the other 85 are checkboxes.

### 4. The scope of the "already voted" lock is unknown

Ten distinct UVINs (`number` 1..10, all with `lat_block=1, lon_block=1`) returned `Error: You have already voted!`. This does not determine whether the lock is per block, IP, session, or previously recorded UVIN; further tests are needed.

## Unverified next steps

1. Test UVINs from different blocks and record responses. Control IP, session and previous voting state; a response grid alone does not establish the lock scope.
2. Every remaining valid ballot reveals the next server rule through `flag` (a different `Error: ...`, or the
   flag itself). Once the seat rule is known, `analysis/solver.py` chooses the block set: precinct grid,
   K contiguous equal-size districts, maximise our seats.
3. Solver validated locally on four control maps:

| control | our share | theoretical ceiling | solver got |
|---|---|---|---|
| 6×6, K=4 | 18/36 | 3 | **3** ✓ |
| 10×10 two blobs, K=10 | 40/100 | 6 | **6** ✓ |
| 10×10 scattered 50/50, K=10 | 40/100 | 6 | **6** ✓ |
| 10×10 we hold 10% | 10/100 | – | **0** (negative control) ✓ |

```bash
python analysis/solver.py        # runs the four controls above
```

## Still unknown

- Whether the server scores a single ballot, aggregates across UVINs, or compares against a fixed electorate
  (the 1067 voters from part 1/2 is the leading candidate for that number).
- No message other than `Invalid UVIN!` / `You have already voted!` has been observed yet, so the block sweep
  is the gate to everything else.
