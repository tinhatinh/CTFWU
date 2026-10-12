---
title: "Traveller-3 : The Road Ends Here"
category: "OSINT"
tags: ["geolocation", "exif", "osm", "flag-format"]
solve_date: "2026-10-09"
language: "en"
---

# Traveller-3 : The Road Ends Here

**Flag:** `OWASP{tikona_peth}`
**Artifact:** `Travellers_dump.zip` holds `img_1.jpg` (3,566,466 B), `img_2.jpg` (2,130,878 B), `Traveller Note.txt` (1,026 B).

## Challenge

The platform page (CTF7, created 08 Oct 2026, Solves 41) records the description:

```text
Which village traveller got off the bus.
```

Points 100, Difficulty Medium. The Category field on the page is blank; the challenge is a geo-OSINT task, so it is filed under OSINT here. After alighting the train at Kamshet (Traveller-2), the traveller takes a bus to a village near the foot of the fort and walks on; this challenge asks for that village.

## Analysis

The geolocation anchor of the series is the EXIF GPS on `img_2.jpg`:

```text
GPS Latitude                    : 18 deg 37' 55.09" N
GPS Longitude                   : 73 deg 30' 45.13" E
GPS Altitude                    : 762 m Above Sea Level
GPS Img Direction               : 261
GPS Img Direction Ref           : Magnetic North
GPS Date Stamp                  : 2026:10:04
```

The decimal point `18.631969 / 73.512536` coincides with the OSM node `natural=peak` "Tikona peak" (id `974330624`, `18.6319782 / 73.5124988`) to within about 4 metres, so the fort is Tikona. The note describes the last leg in prose:

```text
From there we took a bus and got down somewhere near the base. Had to walk another 1–2 km after that.
```

"From there" = Kamshet station. A bus from Kamshet toward Tikona, alighting at a village near the base, then walking 1–2 km. Wikipedia *Tikona* names that village directly: "The village nearest to the fort is called Tikona-Peth" and "The base village of the fort is Tikona peth... the trekking path starts from the hillock south of the parking area near Tikonapeth". The "parking area" is where the road stops — exactly the sense of the title "The Road Ends Here", the rest on foot.

## Solution

Road distances (OSRM driving, OSM coordinates) between station, village and fort, compared against the numbers in the note:

```text
Kamshet (KMST) -> Tikona Fort    ~20.8 km   <- note "Maps showed 20-22 km"
Kamshet        -> Tikona Peth    ~19.5 km
Tikona Peth    -> Tikona Fort    ~1.3 km     <- note "walk another 1-2 km"
Tikona Fort    -> Pavana Lake    ~4 km thang / ~18.8 km duong  <- note "stopped beside a lake"
```

The POI "Tikona Fort" sits at `18.6319 / 73.5126`, matching the EXIF GPS point of `img_2.jpg` (Tikona summit). The OSM/Photon node "Tikona Peth" is about 1.3 km from that POI — matching the note's "walk another 1–2 km" after getting off the bus. A village search around the base via Overpass (`node["place"~"village|hamlet|locality"](around:7000,18.63198,73.51250)`) yields no other village that is simultaneously the base village, 1–2 km from the fort, and reachable by bus from Kamshet.

The place is **Tikona Peth**. The only remaining issue is the string format inside `OWASP{...}`. After the Title Case form was rejected (see below), the accepted convention was established as **lowercase, spaces replaced by `_`**:

```text
OWASP{tikona_peth}
```

## Result

```text
OWASP{tikona_peth}
```

The bus is alighted at Tikona Peth (the base village of Tikona fort, about 1.3 km from the summit per OSM/OSRM). The record explicitly logs two submissions: `OWASP{Tikona Peth}` was rejected, then `OWASP{tikona_peth}` was reported correct — so the accepted convention here (lowercase, `_` for space) has direct submission evidence, unlike Traveller-1/2.

## Reproduce

Requires `exiftool` and Python 3 stdlib; the reverse-geocode, Overpass, Wikipedia and OSRM steps **all need network access**.

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

Confirm the Tikona summit (network):

```console
$ curl -s "https://photon.komoot.io/reverse?lat=18.631969&lon=73.512536"
```

The `natural=peak` node "Tikona peak" is at `18.6319782 / 73.5124988` (id `974330624`). The ~4 m offset is checked offline:

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

Search villages around the base (network; the overpass-api.de mirror returned 406, the kumi.systems mirror returned data):

```console
$ curl -s "https://overpass.kumi.systems/api/interpreter" --data-urlencode "data=[out:json][timeout:30];node[place~\"village|hamlet|locality\"](around:7000,18.63198,73.51250);out;"
```

Confirm the base village (network):

```console
$ curl -s "https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext&titles=Tikona&format=json"
```

The extract contains "The village nearest to the fort is called Tikona-Peth". The distances in the Solution table (Kamshet→Fort ~20.8 km, Tikona Peth→Fort ~1.3 km) come from OSRM driving over the same OSM coordinates; they are measurements recorded during the solve, checked against the note's "20–22 km" and "1–2 km" bands.
