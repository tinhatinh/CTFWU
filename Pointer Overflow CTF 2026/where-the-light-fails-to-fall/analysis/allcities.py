"""Rank every Natural Earth city (pop_max >= 100k) against the photo's allowed sun band."""
import json
import math
from datetime import datetime, timezone
import numpy as np

OBS = datetime(2026, 6, 20, 17, 55, tzinfo=timezone.utc)


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
seen = set()
for f in d["features"]:
    p = f["properties"]
    try:
        pop = float(p.get("pop_max") or 0)
    except Exception:
        pop = 0
    if pop < 200000:
        continue
    lon, lat = f["geometry"]["coordinates"][0], f["geometry"]["coordinates"][1]
    nm = p.get("name") or p.get("name_en")
    ct = p.get("adm0name") or p.get("sov0name")
    if (round(lat, 2), round(lon, 2)) in seen:
        continue
    seen.add((round(lat, 2), round(lon, 2)))
    az, alt = solar(lat, lon)
    rows.append((nm, ct, lat, lon, pop, az, alt))
print("cities with pop_max >= 200k:", len(rows))

# the band the photo allows under the flat/ruler reading
print("\n=== band az 292..306, alt 24..42 (photo reading, flat model) ===")
sel = [r for r in rows if 292 <= r[5] <= 306 and 24 <= r[6] <= 42]
sel.sort(key=lambda r: -r[4])
for nm, ct, la, lo, pop, az, alt in sel:
    print(f"   {nm:22s} {ct:16s} lat{la:7.2f} lon{lo:8.2f} pop={pop/1e6:5.2f}M az={az:6.1f} alt={alt:5.1f}")

print("\n=== band az 278..300, alt 6..22 (if the author assumed a low evening sun) ===")
sel2 = [r for r in rows if 278 <= r[5] <= 300 and 6 <= r[6] <= 22]
sel2.sort(key=lambda r: -r[4])
for nm, ct, la, lo, pop, az, alt in sel2[:25]:
    print(f"   {nm:22s} {ct:16s} lat{la:7.2f} lon{lo:8.2f} pop={pop/1e6:5.2f}M az={az:6.1f} alt={alt:5.1f}")

# closest to my two concrete readings
for tag, az_t, alt_t in (("feet->tip   ", 292.1, 37.8), ("crown-proj  ", 298.2, 34.6),
                         ("mid guess   ", 296.0, 33.0)):
    rr = sorted(rows, key=lambda r: abs(((r[5] - az_t + 180) % 360) - 180) * 1.2 + abs(r[6] - alt_t))
    print(f"\n=== nearest to {tag} az={az_t} alt={alt_t} ===")
    for nm, ct, la, lo, pop, az, alt in rr[:8]:
        print(f"   {nm:22s} {ct:16s} az={az:6.1f} alt={alt:5.1f}  daz={az-az_t:+5.1f} dalt={alt-alt_t:+5.1f} pop={pop/1e6:5.2f}M")
