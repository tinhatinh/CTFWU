---
title: "Traveller-5 : Two Shapes on the Horizon"
category: "OSINT"
tags: ["dem-skyline", "terrarium-tiles", "exif-gps-bearing", "peak-identification"]
solve_date: "2026-10-09"
language: "en"
---

# Traveller-5 : Two Shapes on the Horizon

**Flag:** `OWASP{lohagad_visapur}`
**Artifact:** the photograph attached on the platform, taken from the same position already fixed in the earlier challenges (the `img_2.jpg` EXIF anchor). The shared artifact set and coordinates for the whole series are in the Analysis section.

## Challenge

```text
Challenge Description
What are those in the picture.
Points 150   Difficulty Hard   Format OWASP{FORT1_FORT2}
```

"Solves (32)". The picture shows two mountain silhouettes on the horizon. The flag format `FORT1_FORT2` demands two names, so both forts and their order have to be identified.

## Analysis

### Series context

The fifth challenge still stands at the same position the earlier ones had fixed. The Traveller series is tied together by the artifact set unpacked from `Travellers_dump.zip` and the GPS anchor in the EXIF of `img_2.jpg`:

```text
Travellers_dump.zip
  img_1.jpg          3,566,466 B
  img_2.jpg          2,130,878 B
  Traveller Note.txt   1,026 B

img_2.jpg EXIF: 18 deg 37' 55.09" N  73 deg 30' 45.13" E   altitude 762 m
                 direction 261 (ref Magnetic North)  date 2026:10:04 04:02:36Z
```

The EXIF coordinates coincide with the OpenStreetMap node `Tikona peak` within ~4 m, so the observation point is Tikona. The `GPSImgDirection` field (=261, ref Magnetic North) gives the direction the lens is pointed and is used to orient the skyline reconstruction.

### The problem

From a known position, "two shapes on the horizon" are two peaks whose projected silhouettes match the outline in the photo. The method recorded in the working notes was to compare a skyline rendered from a DEM (Terrarium elevation tiles) against the profile extracted from the image, oriented by the bearing read from the EXIF, and to see which pair of named peaks reproduces the two-shape profile.

## Solution

### Rendering the skyline from the DEM

The regional DEM was assembled from Terrarium elevation tiles and stored as `dem.npy` with its metadata:

```json
{"Z": 11, "X0": 1438, "Y0": 912, "W": 2304, "H": 2304, "N": 2048}
```

The metadata records zoom 11, top-left tile `(1438,912)`, a `2304×2304` raster and `N=2048`. `W/H` are raster dimensions, not a 2304×2304 tile grid. Separate image and DEM profiles were saved for comparison.

Positioning and enumeration of the peaks/water around the observation point rely on an Overpass query (saved as `q1.txt`):

```text
[out:json][timeout:30];
(
  node["place"~"village|hamlet|locality"](around:7000,18.63198,73.51250);
  way["place"~"village|hamlet"](around:7000,18.63198,73.51250);
  node["historic"](around:9000,18.63198,73.51250);
  way["historic"]["name"](around:9000,18.63198,73.51250);
  node["natural"="peak"](around:9000,18.63198,73.51250);
  node["waterway"="dam" ](around:9000,18.63198,73.51250);
  way["natural"="water"]["name"](around:9000,18.63198,73.51250);
);
out center tags;
```

### The matching pair of peaks

The skyline match returned the pair Lohagad and Visapur (`cands.json`, each line being `[name, OSM type, lat, lon, elevation m, recorded value]`):

```text
["Lohagad", "district", 18.7206, 73.4915, 1051, 1.15]
["Visapur", "other", 18.7218, 73.4928, 1070, 1.25]
```

The two peaks are adjacent in azimuth, so they appear as two consecutive shapes on one side of the horizon. The accepted order is Lohagad then Visapur, consistent with the recorded detail that the note "marked them 1 and 2" from left to right. Because the platform uses lowercase joined by `_` (Traveller-3 rejected `OWASP{Tikona Peth}` and accepted `OWASP{tikona_peth}`), the flag is `OWASP{lohagad_visapur}`.

## Result

```text
OWASP{lohagad_visapur}
```

The flag was accepted by the platform; the working record stores the line reporting this exact string as correct.

## Reproduce

Positioning and skyline reconstruction need network in two steps: fetching the Terrarium elevation tiles and calling Overpass; the DEM-vs-image match runs locally with numpy. exiftool reads the anchor from the artifact:

```console
$ exiftool -GPS* img_2.jpg
$ curl -s --data-urlencode data@q1.txt https://overpass.kumi.systems/api/interpreter
```

The orientation field used to rotate the skyline (from `exiftool -j`, relevant fields quoted):

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

The DEM is stored as `dem.npy` (metadata as above); the horizon outline and polar projection are stored in `horizon_*.npy` and `polar.npz`; the candidate peaks/water list is in `cands.json`. Compare the image's horizon profile against the DEM-rendered skyline along direction 261°, left-to-right, to settle the pair Lohagad–Visapur. Result: `OWASP{lohagad_visapur}`.

The DEM generation, skyline extraction and matching code are not included. Saved metadata and results alone do not reproduce the automated image match. EXIF uses magnetic north, which needs correction when compared with true-north DEM bearings.
