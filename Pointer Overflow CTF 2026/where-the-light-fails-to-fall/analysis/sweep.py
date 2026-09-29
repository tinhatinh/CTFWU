"""Sweep plausible (azimuth, altitude) readings and keep only those whose best match is a
large city with a small residual -- those are the readings an author could have used."""
import json
import math
from datetime import datetime, timezone
import numpy as np

OBS = datetime(2026, 6, 20, 17, 55, tzinfo=timezone.utc)
TRIED = {"fortaleza", "recife", "natal", "maceio", "maceió", "joao pessoa", "joão pessoa",
         "olinda", "teresina", "sao luis", "são luís", "são luís", " aracaju", "aracaju",
         "salvador", "campina grande", "mossoro"}


def solar(lat, lon, dt=OBS):
    J = dt.timestamp() / 86400.0 + 2440587.5
    T = (J - 2451545.0) / 36525.0
    L0 = (280.46646 + 36000.76983 * T) % 360
    M = math.radians((357.52911 + 35999.05029 * T) % 360)
    e = 0.016708634 - 0.000042037 * T
    C = (1.914602 - 0.004817 * T) * math.sin(M) + 0.019993 * math.sin(2 * M) + 0.000289 * math.sin(3 * M)
    lam = L0 + C - 0.00569 - 0.00478 * math.sin(math.radians(125.04 - 1934.136 * T))
    eps = math.radians(23.4392911 - 0.0130042 * T)
    decl = math.asin(math.sin(eps) * math.sin(math.radians(lam)))
    y = math.tan(eps / 2) ** 2
    eqtime = math.degrees(y * math.sin(2 * math.radians(L0)) - 2 * e * math.sin(M)
                          + 4 * e * math.cos(eps) * math.sin(M) * math.cos(2 * math.radians(L0))
                          - 0.5 * y * y * math.sin(4 * math.radians(L0))
                          - 1.25 * e * e * math.sin(M) * math.cos(2 * math.radians(L0))) * 4.0
    H = math.radians((dt.hour + dt.minute / 60 + lon / 15 + eqtime / 60 - 12) * 15)
    phi = math.radians(lat)
    alt = math.degrees(math.asin(math.sin(phi) * math.sin(decl)
                                 + math.cos(phi) * math.cos(decl) * math.cos(H)))
    az = math.degrees(math.atan2(math.sin(H), math.cos(H) * math.sin(phi) - math.tan(decl) * math.cos(phi)))
    return (180 + az) % 360, alt


d = json.load(open(r"C:\Users\Administrator\AppData\Local\Temp\ne_places.json", encoding="utf-8"))
rows = []
for f in d["features"]:
    p = f["properties"]
    pop = float(p.get("pop_max") or 0)
    if pop < 300000:
        continue
    lon, lat = f["geometry"]["coordinates"][0], f["geometry"]["coordinates"][1]
    nm = (p.get("name") or p.get("name_en") or "?").strip()
    if nm.lower() in TRIED:
        continue
    az, alt = solar(lat, lon)
    rows.append((nm, p.get("adm0name", "?"), lat, lon, pop, az, alt))
print("candidate cities (>=300k, not yet tried):", len(rows))

AZS = [58, 62, 68, 74, 100, 106, 112, 118, 122, 240, 246, 252, 270, 276, 282, 288, 292, 296, 300, 304, 310, 316, 322]
ALTS = [8, 12, 16, 20, 24, 28, 32, 34.6, 38, 42, 46, 50, 54, 58, 62, 66, 70]

hits = []
for az_t in AZS:
    for alt_t in ALTS:
        sc = []
        for nm, ct, la, lo, pop, az, alt in rows:
            daz = abs((az - az_t + 180) % 360 - 180)
            res = daz + abs(alt - alt_t)
            sc.append((res, nm, ct, pop, az, alt))
        sc.sort()
        r0 = sc[0]
        if r0[0] <= 2.2 and r0[3] >= 1.5e6:
            hits.append((az_t, alt_t, r0, sc[1]))

seen = set()
print("\nreadings whose best match is a >=1.5M city with residual <= 2.2 deg:")
for az_t, alt_t, r0, r1 in hits:
    key = r0[1].lower()
    tag = "NEW " if key not in seen else ""
    seen.add(key)
    print(f"  az={az_t:5.1f} alt={alt_t:5.1f} -> {r0[1]:20s} {r0[2]:16s} pop={r0[3]/1e6:5.2f}M "
          f"(az={r0[4]:6.1f} alt={r0[5]:5.1f}) resid={r0[0]:4.1f}   2nd={r1[1]}({r1[0]:4.1f})  {tag}")

print("\nmost frequent cities across all readings (residual-weighted):")
from collections import Counter
cnt = Counter()
for az_t in AZS:
    for alt_t in ALTS:
        sc = sorted([(abs((az - az_t + 180) % 360 - 180) + abs(alt - alt_t), nm, pop)
                     for nm, ct, la, lo, pop, az, alt in rows])
        if sc[0][0] <= 3.0:
            cnt[(sc[0][1], sc[0][2])] += 1
for (nm, pop), n in cnt.most_common(14):
    print(f"   {nm:22s} pop={pop/1e6:5.2f}M  appears as best match in {n} readings")
