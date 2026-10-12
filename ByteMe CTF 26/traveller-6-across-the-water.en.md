---
title: "Traveller-6 : Across the Water"
category: "OSINT"
tags: ["dem-skyline", "lake-constraint", "exif-gps", "osm-water"]
solve_date: "2026-10-09"
language: "en"
---

# Traveller-6 : Across the Water

**Flag:** `OWASP{tung_pawna}`
**Artifact:** the "return photograph" attached on the platform, taken from the same position already fixed in the earlier challenges (the `img_2.jpg` EXIF anchor). The shared artifact set and coordinates for the whole series are in the Analysis section.

## Challenge

```text
Challenge Description
Identify the fort across the water and the lake in the return photograph.
Points 150   Difficulty Medium   Format OWASP{FORT_LAKE}
```

"Solves (26)". The flag has two parts: a fort and a lake, with the constraint that the fort lies across the water.

## Analysis

### Series context

The sixth challenge still stands at the same position as the earlier ones and reuses the shared Traveller artifacts:

```text
Travellers_dump.zip
  img_1.jpg          3,566,466 B
  img_2.jpg          2,130,878 B
  Traveller Note.txt   1,026 B

img_2.jpg EXIF: 18 deg 37' 55.09" N  73 deg 30' 45.13" E   altitude 762 m
                 direction 261 (ref Magnetic North)  date 2026:10:04 04:02:36Z
```

The EXIF coordinates coincide with the OpenStreetMap node `Tikona peak` within ~4 m, so the observation point is Tikona. Because the format is `FORT_LAKE`, a body of water must be named alongside the fort, and the "across the water" constraint removes every pairing that still uses the camera position's own fort.

### The water constraint

The first two submissions kept the observation fort Tikona and were both rejected (the record notes `OWASP{tikona_pavana}` and `OWASP{tikona_pawna}` as wrong). The problem was not the lake but the requirement that the fort be a *different* peak, seen on the far side of the water. Because the platform uses lowercase joined by `_` (Traveller-3 rejected `OWASP{Tikona Peth}` and accepted `OWASP{tikona_peth}`), the correct flag must take the form `fort_lake`.

## Solution

The skyline-from-DEM comparison was re-run under the constraint that the target peak lies on the far side of a body of water. Two lakes were evaluated, Mulshi and Pawna (the arrays `lake_MULSHI.npy`, `lake_PAWNA.npy` and `lake_mask.npy` in the record). The pair satisfying the constraint is Pawna lake together with the fort on the opposite shore, Tung (`cands.json`, each line being `[name, OSM type, lat, lon, elevation m, recorded value]`):

```text
["Tung", "other", 18.6598, 73.4616, 972, 0.55]
["Pawna", "district", 18.6975, 73.495, 774, null]
```

Joining fort + lake in the `FORT_LAKE` format, lowercased and underscore-separated, gives the flag:

```text
OWASP{tung_pawna}
```

## Result

```text
OWASP{tung_pawna}
```

The flag was accepted by the platform; the working record stores the line reporting this exact string as correct, after the `tikona_pavana` and `tikona_pawna` submissions were rejected.

## Reproduce

Positioning and skyline reconstruction need network in two steps: fetching the Terrarium elevation tiles and calling Overpass; the DEM match and the lake-mask build run locally with numpy. exiftool reads the anchor from the artifact:

```console
$ exiftool -GPS* img_2.jpg
$ curl -s --data-urlencode data@q1.txt https://overpass.kumi.systems/api/interpreter
```

Relevant EXIF fields (from `exiftool -j`, fields quoted):

```text
GPSVersionID        : 2.2.0.0
GPSLatitudeRef      : North
GPSLongitudeRef     : East
GPSAltitudeRef      : Above Sea Level
GPSDateStamp        : 2026:10:04
GPSTimeStamp        : 04:02:36Z
GPSImgDirectionRef  : Magnetic North
GPSImgDirection     : 261
```

The `q1.txt` query lists both `natural=peak` and `natural=water`/`waterway=dam` features around the observation point; the DEM is stored as `dem.npy` (zoom-11 metadata, 2304×2304-pixel raster resampled to `N=2048`), the horizon and polar projection in `horizon_*.npy`/`polar.npz`, the lake mask in `lake_mask.npy` and `lake_MULSHI.npy`/`lake_PAWNA.npy`, and the candidate list in `cands.json`. Re-running the match under the "fort across the water" constraint picks the pair Tung (fort) + Pawna (lake). Result: `OWASP{tung_pawna}`.

The DEM generation, skyline extraction and matching code are not included. Saved metadata and results alone do not reproduce the automated image match. EXIF uses magnetic north, which needs correction when compared with true-north DEM bearings.
