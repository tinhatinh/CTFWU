# Where the Light Fails to Fall - OSINT

**Points:** 400 · **Wave:** 1 · **Flag:** `POCTF{99.612.WTT7UHE5X3JIJMKQ.TO6LBQYYORFL6LLPF6Q22SRR2P}`

**Artifact:** `files/PXL_20260621_181159681.jpg` (3.940.516 B, sha256 `42b362b6…520a14a`) and the
decoded PNG `files/photo.png` (3000x4000, sha256 `2a25a576…a40339`). The image shows a pigeon standing
on a background of stone blocks, its shadow falling to the right, with a red stroke pointing to true north.

## Challenge

The author says that that summer he travelled and photographed the pigeon in "every major city". The task is
to work out which city, using only three clues: the photo, the red stroke marking true north, and the team's
observation time `2026-06-20 · 19:55 · UTC+02:00`. Submit the city name into `#city-input`; if it is
correct the server returns the flag and pours it into `#flag-input` on its own.

## Initial Analysis

Two things were done immediately and produced real results:

**Get the actual original file.** The `<img>` tag points at `/challenges/where-light-falls/photo`. This
request needs the session cookie (bare curl gets 401), so it was read through the logged-in tab using
`browser-use`. The response carries `content-disposition: inline; filename=PXL_20260621_181159681.jpg`, which is
the original file name of a Google Pixel, shot 2026-06-21 at 18:11:59 machine time. This is much better data
than the `photo.png` we were holding, and it is a server oversight: the original file is still served, there
is simply no link pointing to its name.

**Measure the red stroke.** The red stroke is pure graphics, so it separates precisely by colour
(`R > 120 && R-G > 55 && R-B > 55`), then connected components are split out to discard the bird's eye and
two pink feet, which also fall inside that red threshold:

```text
nét north : (544, 3103) -> (2386, 3864)   dài 2029 px, dày ~15 px
unit direction (x right, y up): (-0.92429, +0.38169)   góc 157,561°
label \"N\" : component at (434, 3015) 84x110, located at top-left -> arrowhead pointing up-left
bird eye : (1048, 1784)      standing foot: bbox (1207,2559) 179x146 -> lowest point y = 2705
```

The bird's shadow, measured from the point where the foot touches the ground to the tip of the shadow, is
`(910, -925)` in y-down coordinates, that is roughly 1.298 px long and tilted 45,5° from the horizontal. The
bird's erected height (head top y ≈ 1700 down to the foot y = 2705) is about 1.005 px.

The number 1.298 / 1.005 = 1,29 is exactly the point where every geometric direction collapses, as the part below explains.

## Directions ruled out

The whole log is in `notes.md`; here are the four main branches and the counter-evidence.

1. **Flat image (treat the ground as parallel to the image plane).** Then the angle between the north
   stroke and the shadow, measured directly in the image, is the solar azimuth: 157,561° − 45,5° = 112,1°
   → the sun at 292,1°, and altitude = `atan(1005/1298)` = 37,8°. Inverting the pair (292°, 38°) with the time
   17:55 UT gives a point on the northeast coast of Brazil. This branch led to exactly one cluster of cities,
   so it was submitted as a trial and rejected in full: Fortaleza, Recife, Natal, Maceió, João Pessoa,
   Olinda, Teresina, São Luís, Aracaju, Salvador, Campina Grande, Mossoró. Ruled out.
2. **Affine model with a free compression factor `s`.** With the north stroke and the shadow measured, `tan ψ = 2,4154 s` and
   `tan(B − ψ) = 1,2825 s`, so `B ≤ 119,6°` and the solar azimuth is capped above at 299,6°. To get an
   altitude in the 8-19° range (right for a summer afternoon in Europe) you would need `s ≈ 0,2`, but
   `s = 0,2` pulls the azimuth back down to ~220°. The two constraints conflict directly. Ruled out.
3. **Perspective calibration from the paving.** The most disappointing one. The stone here is hand-dressed
   blockwork, rounded units of mismatched size with winding mortar joints, so there are no two families of
   lines long enough and regular enough to catch a vanishing point. The 2D Fourier spectrum locks onto the
   granite grain at a 25-50 px period rather than onto the stone grid; once blurred at sigma 24 to kill the
   grain, the spectrum keeps no sharp peak (the two "periods" return exactly the window's own bin value
   everywhere). A "coherence" peak that looked very good at (-4482, 193) turned out to be the illumination
   gradient over the whole image, not a stone joint: it does not lie on the horizon implied by the stone
   size. Without `f` and without a horizon there is no unique solution. Ruled out.
4. **A rigorous 3D solve.** Assuming the camera direction is horizontal, sweep `f ∈ [2200, 5000]` and the
   horizon line `y_h ∈ [-4000, +200]`, reconstruct the shadow tip on the ground, then find the altitude such
   that the camera ray through the top of the head meets the sunlight ray exactly: the result slides
   continuously, `az 259..296` and `alt 17..56` depending on `(f, y_h)`, and every major city has a parameter
   set matching within 2°. That means this model can express every answer, i.e. it cannot discriminate. Ruled out.

Also ruled out with evidence: reverse image search (Bing returned exactly the species *Columba livia*, Google
Lens "Exact matches" reported no results, so the photo is not on the web), metadata (no
GPSInfo, no ExifIFD, a single EOI, 0 bytes after EOI), and stego between the PNG and the JPEG (pixels
identical).

## Exploit Chain

**Step 1 - Re-read the endpoint's behaviour.** `POST /challenges/where-light-falls/answer` only compares
strings. Probing with special values shows there is no oracle at all:

```text
""  -> 400 {"correct": false, "message": "Enter a city name."}
"*" -> 200 {"correct": false, "message": "That's not the city the light points to."}
{"city": true}  -> 500            (server gọi .strip() trên bool)
{"city": []}, {"city": {}}, {}    -> 400
```

There is no distinction between "invalid name" and "wrong city", so there is no near/far signal to probe. But
that also means the success condition is a single string match, and it **can be enumerated**.

**Step 2 - Build the list in priority order.** Download `ne_10m_populated_places_simple.geojson`
(7.342 places carrying `pop_max`), split out the `name` and `name_en` values, add unaccented variants, sort by
population descending and drop the 25 names already submitted earlier. Result: 7.711 strings, of which the
first 1.100 correspond to cities of about 1 million inhabitants or more, exactly the "major city" sense the challenge uses.

**Step 3 - Worker running inside the logged-in tab.** Keep every request inside `window.__bf` so the
session cookie never leaves the browser, stop on its own as soon as `correct` comes back, and back off
automatically when the server answers 429/5xx:

```js
while (b.q.length) {
  const c = b.q.shift();
  const r = await fetch('/challenges/where-light-falls/answer', {method:'POST',
      credentials:'same-origin', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({city:c})});
  const d = await r.json();
  if (d.correct) { b.found = c; b.flag = d.flag; return; }
  await new Promise(z => setTimeout(z, b.delay));   // initial delay 250 ms
}
```

The actual rate was about 1,7 req/s (250 ms of waiting plus server latency), no request was refused, and
the queue was abandoned at name number 480 when the answer was found.

**Step 4 - Result.** Name number 480 returned `correct: true` together with the flag:

```text
found = Amsterdam
flag  = POCTF{99.612.WTT7UHE5X3JIJMKQ.TO6LBQYYORFL6LLPF6Q22SRR2P}
```

**Step 5 - Verify with the flag endpoint itself.** The flag is not ours until the submit endpoint
accepts it:

```text
POST /challenges/where-light-falls/submit {"flag":"POCTF{99.612.…}"}
-> 200 {"correct": true, "message": "Correct."}
```

The answer is coherent on content: Amsterdam at 17:55 UT on 20-06-2026 has a solar azimuth of
286,6° and an altitude of 17,0°, that is a summer afternoon exactly as the photo describes. Our error lay in
reading the altitude from the shadow ratio (37,8° instead of 17°) because of the ground's perspective, exactly
as analysed in branches 2 and 4.

## Flag

```text
POCTF{99.612.WTT7UHE5X3JIJMKQ.TO6LBQYYORFL6LLPF6Q22SRR2P}
```

Matches the template `POCTF{<cid>.<team_id>.<nonce>.<sig26>}` with cid 99, team 612, nonce 16 characters.

## Reproduce

```bash
cd where-the-light-fails-to-fall
python exploit.py                 # in đoạn JS worker + danh sách tên cần nạp
```

All the image measurements, the city list and the log of the ruled-out branches are in `analysis/`. If you
want to redo it with geometry instead of enumeration, start from `analysis/rigorous.py` and `analysis/notes.md`
so as not to walk the four already-refuted branches again.
