---
title: "Traveller-1 : The First Stop"
category: "OSINT"
tags: ["geolocation", "exif", "osm", "railway"]
solve_date: "2026-10-09"
language: "en"
---

# Traveller-1 : The First Stop

**Flag:** `OWASP{Akurdi}`
**Artifact:** `Travellers_dump.zip` holds `img_1.jpg` (3,566,466 B), `img_2.jpg` (2,130,878 B), `Traveller Note.txt` (1,026 B).

## Challenge

The platform page (CTF7, created 08 Oct 2026, Solves 43) records the description:

```text
Determine the railway station from which the traveller started.
```

Points 75, Difficulty Easy. The Category field on the page is blank; the challenge is a geo-OSINT task, so it is filed under OSINT here. Traveller-1/2/3 share one set of artifacts and one journey; this one asks for the starting station.

## Analysis

The whole series turns on a single geolocation anchor: `img_2.jpg` carries EXIF GPS while `img_1.jpg` does not. The GPS block read from the image:

```text
GPS Latitude                    : 18 deg 37' 55.09" N
GPS Longitude                   : 73 deg 30' 45.13" E
GPS Altitude                    : 762 m Above Sea Level
GPS Img Direction               : 261
GPS Img Direction Ref           : Magnetic North
GPS Date Stamp                  : 2026:10:04
```

Converted to decimal: `18 + 37/60 + 55.09/3600 = 18.631969`, `73 + 30/60 + 45.13/3600 = 73.512536`. Reverse-geocoding this point returns exactly the OSM node `natural=peak` "Tikona peak" (id `974330624`, `18.6319782 / 73.5124988`), about 4 metres from the GPS fix. The photo was taken from the summit of Tikona fort, and that anchor is what makes the series solvable.

`Traveller Note.txt` describes the journey in prose:

```text
I live in Nigdi, Pradhikaran, so I walked to the station and took a local from there.

After 6 stops our destination was on the 7th station.

Got off there. The fort wasn't exactly near the station — Maps showed something around 20–22 km away.

The fort was around 3,500 ft high. It looked almost like a pyramid from a distance.
```

Two details match Tikona: Wikipedia *Tikona* states "The 3500 foot high hill is pyramidal in shape" and "located near Kamshet". A 3,500 ft pyramidal fort, a lake on the way back (Pawna/Pavana), and views of other forts (Tung, Lohagad, Visapur) — exactly as the note says.

This challenge asks for the **starting station**, not the destination. The note says the traveller "lives in Nigdi, Pradhikaran, so walked to the station". The inner-city station of Nigdi Pradhikaran is Akurdi; Wikipedia *Akurdi railway station* places it at "Sector-26, Nigdi Pradhikaran, Pune" — the address string coincides with the home in the note, so it is independent corroboration of the boarding station.

## Solution

Two independent routes reach the same station, and they agree:

1. **From the home location**: Nigdi Pradhikaran → Akurdi station (code AKRD), confirmed by the string "Sector-26, Nigdi Pradhikaran".
2. **Counting 7 stations back**: the destination station (where the traveller alighted, the Traveller-2 answer) is Kamshet — the station nearest Tikona, about 20 km by road from the fort, matching "Maps showed 20–22 km". On the Pune Jn → Lonavala line (Pune Suburban Railway), the station order recorded in the solve is:

```text
Akurdi -> Dehu Road -> Begdewadi -> Ghorawadi -> Talegaon -> Vadgaon -> Kanhe -> Kamshet
   (1)        2            3            4             5          6         7   <- 6 stops, 7th station
```

Board at Akurdi, pass six intermediate stations, then alight at Kamshet. This is the seventh stop after leaving Akurdi; the boarding point is not one of those seven stops. The result also agrees with the Nigdi Pradhikaran residence clue.

The Traveller-1 answer is the starting station:

```text
OWASP{Akurdi}
```

The sequence includes Akurdi, six intermediate stations and Kamshet: eight stations including the boarding point. Here “7th station” means the seventh after leaving Akurdi, not the seventh when Akurdi is counted as station 1.

## Result

```text
OWASP{Akurdi}
```

The value is a derivation in the player's work (home at Nigdi Pradhikaran → Akurdi station, and 7 stations counted back from Kamshet), corroborated by the address string "Sector-26, Nigdi Pradhikaran". No per-submission acceptance line was recorded for this challenge in the notes; the challenge is listed as solved in the event scoreboard, and that scoreboard is the acceptance record.

## Reproduce

Requires `exiftool` for the GPS block and Python 3 stdlib for the distance check; the geolocation/lookup steps **need network access**.

```console
$ exiftool -GPS* img_2.jpg
$ exiftool -GPS* img_1.jpg
```

Convert DMS to decimal and cross-check the OSM node "Tikona peak" (network):

```console
$ curl -s "https://photon.komoot.io/reverse?lat=18.631969&lon=73.512536"
```

The `natural=peak` node returned is at `18.6319782 / 73.5124988` (id `974330624`). Verify the offset with a haversine, run offline:

```python
from math import radians, sin, cos, asin, sqrt
def hav(a, b, c, d):
    a, b, c, d = map(radians, (a, b, c, d))
    return 2 * 6371000 * asin(sqrt(sin((c-a)/2)**2 + cos(a)*cos(c)*sin((d-b)/2)**2))
print(round(hav(18.631969, 73.512536, 18.6319782, 73.5124988), 1), "m")
```

```text
4.1 m
```

Confirm the starting station via Wikipedia (network):

```console
$ curl -s "https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext&exintro&titles=Akurdi%20railway%20station&format=json"
```

The extract contains "Sector-26, Nigdi Pradhikaran". The Pune Jn → Lonavala station order and the fact that this line's local trains stop at Kamshet come from Wikipedia *Kamshet railway station*; the station-count table in the Solution section is data recorded during the solve.
