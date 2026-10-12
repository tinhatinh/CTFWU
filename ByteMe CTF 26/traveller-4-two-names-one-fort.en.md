---
title: "Traveller-4 : Two Names, One Fort"
category: "OSINT"
tags: ["geolocation", "wikipedia", "toponym", "exif-gps"]
solve_date: "2026-10-09"
language: "en"
---

# Traveller-4 : Two Names, One Fort

**Flag:** `OWASP{vitandgad}`
**Artifact:** `Travellers_dump.zip` (the positioning anchor is the EXIF of `img_2.jpg`). The shared artifact set and coordinates for the whole series are in the Analysis section.

## Challenge

```text
Challenge Description
What is the old name of the fort traveller hiked.
Points 100   Difficulty Medium   Format OWASP{...}
```

The challenge asks for the old name of the fort the traveller hiked. The title "Two Names, One Fort" points directly at the detail to find: the same fort is known by two names.

## Analysis

### Series context

This is the fourth challenge in the Traveller series and it reuses the single location that the first three had already placed (starting station, stop, base village, then the fort). The series is tied together by the artifact set unpacked from `Travellers_dump.zip` and the GPS anchor stored in the EXIF of `img_2.jpg`:

```text
Travellers_dump.zip
  img_1.jpg          3,566,466 B
  img_2.jpg          2,130,878 B
  Traveller Note.txt   1,026 B

img_2.jpg EXIF: 18 deg 37' 55.09" N  73 deg 30' 45.13" E   altitude 762 m
                 direction 261 (ref Magnetic North)  date 2026:10:04 04:02:36Z
```

`img_1.jpg` has no EXIF GPS (its latitude/longitude fields are empty), so the positioning rests on `img_2.jpg` alone. The EXIF coordinates coincide with the OpenStreetMap node `Tikona peak` within ~4 m, so the fort of the series is Tikona. The flag-format convention learned at Traveller-3 — lowercase and underscores — means the single word `Vitandgad` only has to be lowercased here, with no space:

```text
rejected : OWASP{Tikona Peth}   (Traveller-3, has a space)
accepted : OWASP{tikona_peth}   (Traveller-3, lowercase + underscore)
```

## Solution

The answer is the alternate name of the same fort Tikona, taken directly from the opening line of the Wikipedia page about it:

```text
Tikona also known as Vitandgad,  is the dominant hill fort in Maval in western India.
```

The page `https://en.wikipedia.org/wiki/Tikona` (the copy stored in the working record) gives exactly that sentence. The spelling `Vitandgad` (one word) was cross-checked against two other independent sources present in the record — "Tikona Fort &#124; Vitandgad Monsoon Special Trek" (maharashtragadkille.com) and "Tikona Fort, also known by the pseudonym Vitandgad" (escape2explore.com) — all of which use the same form. Applying the format convention learned at Traveller-3, the one-word lowercase name becomes the flag:

```text
OWASP{vitandgad}
```

## Result

```text
OWASP{vitandgad}
```

No submission response for this exact string was preserved.

## Reproduce

The positioning runs entirely on the local artifact; verifying the name spelling needs network.

```console
$ exiftool img_1.jpg
$ exiftool img_2.jpg
$ for f in img_1.jpg img_2.jpg; do echo "########## $f GPS ##########"; exiftool -GPS* "$f"; done
```

`img_1.jpg` returns empty GPS fields; `img_2.jpg` gives the following (from `exiftool -j`, relevant fields quoted):

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

The pair `18°37'55.09"N 73°30'45.13"E` matches the OSM node `Tikona peak` within ~4 m, so the subject of the challenge is Tikona. The alternate name needs network: read the first line of `https://en.wikipedia.org/wiki/Tikona` — "Tikona also known as Vitandgad" — then cross-check a trekking page or escape2explore to fix the spelling. Result: `OWASP{vitandgad}`.
