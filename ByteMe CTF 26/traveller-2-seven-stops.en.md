---
title: "Traveller-2 : Seven Stops"
category: "OSINT"
tags: ["geolocation", "exif", "osm", "railway"]
solve_date: "2026-10-09"
language: "en"
---

# Traveller-2 : Seven Stops

**Flag:** `OWASP{Kamshet}`
**Artifact:** `Travellers_dump.zip` holds `img_1.jpg` (3,566,466 B), `img_2.jpg` (2,130,878 B), `Traveller Note.txt` (1,026 B).

## Challenge

The platform page (CTF7, created 08 Oct 2026, Solves 44) records the description:

```text
Which station traveller got off the train.
```

Points 75, Difficulty Easy. The Category field on the page is blank; the challenge is a geo-OSINT task, so it is filed under OSINT here. This one asks for the **alighting station** — the 7th station in "After 6 stops our destination was on the 7th station", the other end of the journey from Traveller-1.

## Analysis

The geolocation anchor of the whole series is `img_2.jpg`; its EXIF GPS is

```text
GPS Latitude                    : 18 deg 37' 55.09" N
GPS Longitude                   : 73 deg 30' 45.13" E
GPS Altitude                    : 762 m Above Sea Level
GPS Img Direction               : 261
GPS Img Direction Ref           : Magnetic North
GPS Date Stamp                  : 2026:10:04
```

The decimal point `18.631969 / 73.512536` coincides with the OSM node `natural=peak` "Tikona peak" (id `974330624`, `18.6319782 / 73.5124988`) to within about 4 metres. So the fort in the note is Tikona, and the nearest station on the line whose local trains stop there is Kamshet — which makes Kamshet the candidate "7th station".

The note gives two independent checks on the same station:

```text
I live in Nigdi, Pradhikaran, so I walked to the station and took a local from there.

After 6 stops our destination was on the 7th station.

Got off there. The fort wasn't exactly near the station — Maps showed something around 20–22 km away.
```

- **Station-to-fort distance**: Kamshet → Tikona is about 20 km by road, inside the note's "20–22 km" band. Wikipedia *Tikona* also records the fort "located near Kamshet".
- **Station count**: boarding at Akurdi (Traveller-1), followed by six intermediate stations and the seventh stop at Kamshet.

## Solution

The Pune Jn → Lonavala station order (Pune Suburban Railway) recorded in the solve, counted from the starting station Akurdi:

```text
Akurdi -> Dehu Road -> Begdewadi -> Ghorawadi -> Talegaon -> Vadgaon -> Kanhe -> Kamshet
   (1)        2            3            4             5          6         7   <- 6 stops, 7th station
```

Board at Akurdi, pass 6 stations (Dehu Road, Begdewadi, Ghorawadi, Talegaon, Vadgaon, Kanhe), alight at the 7th = Kamshet. This satisfies both constraints: it is exactly "the 7th station", and Kamshet sits about 20 km from Tikona summit as the note says.

Wikipedia *Kamshet railway station* confirms the line's Pune Jn–Lonavala local trains stop here, matching the detail "took a local". The alighting station is:

```text
OWASP{Kamshet}
```

The sequence includes Akurdi, six intermediate stations and Kamshet: eight stations including the boarding point. Here “7th station” means the seventh after leaving Akurdi, not the seventh when Akurdi is counted as station 1.

## Result

```text
OWASP{Kamshet}
```

The value is a derivation in the player's work: the 7th station counted from Akurdi on the Pune Jn → Lonavala line, which is also the station nearest the Tikona summit (the EXIF anchor) with a distance matching "20–22 km". No per-submission acceptance line was recorded for this challenge in the notes; the challenge is listed as solved in the event scoreboard, and that scoreboard is the acceptance record.

## Reproduce

Requires `exiftool` and Python 3 stdlib; the geolocation/lookup steps **need network access**.

```console
$ exiftool -GPS* img_2.jpg
```

```text
GPS Latitude                    : 18 deg 37' 55.09" N
GPS Longitude                   : 73 deg 30' 45.13" E
GPS Altitude                    : 762 m Above Sea Level
GPS Img Direction               : 261
GPS Img Direction Ref           : Magnetic North
GPS Date Stamp                  : 2026:10:04
```

Confirm the Tikona summit with reverse-geocoding (network):

```console
$ curl -s "https://photon.komoot.io/reverse?lat=18.631969&lon=73.512536"
```

The `natural=peak` node "Tikona peak" is at `18.6319782 / 73.5124988` (id `974330624`). The ~4 m offset is checked with a haversine, run offline:

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

Verify Kamshet and the local-train stop pattern (network):

```console
$ curl -s "https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext&exintro&titles=Kamshet%20railway%20station&format=json"
```

The Pune Jn → Lonavala station order in the count table in the Solution section is data recorded during the solve, cross-checked against the positions of the stations on the same line.
