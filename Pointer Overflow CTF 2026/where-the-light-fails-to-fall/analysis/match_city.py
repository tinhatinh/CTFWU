import math
import numpy as np
from PIL import Image, ImageDraw
from datetime import datetime, timezone

im = Image.open("files/photo.png").convert("RGB")
m = np.load("analysis/shadow_mask2.npy")
overlay = im.copy()
arr = np.asarray(overlay).copy()
arr[m] = (0.55 * arr[m] + 0.45 * np.array([255, 0, 0])).astype(np.uint8)
o = Image.fromarray(arr).resize((750, 1000), Image.LANCZOS)
d = ImageDraw.Draw(o)
# draw measured vectors from the shadow centroid (scaled /4 from full res)
cx, cy = 1937.4 / 4, 2226.6 / 4
for vec, col in (((-0.9228, -0.3853), (0, 200, 255)), ((0.4566, -0.8897), (0, 255, 0))):
    d.line([(cx, cy), (cx + vec[0] * 220, cy + vec[1] * 220)], fill=col, width=4)
o.save("analysis/mask_overlay.png")
print("saved analysis/mask_overlay.png")


# ---- corrected solar position ----
def solar(lat, lon, dt_utc):
    d0 = dt_utc - datetime(2000, 1, 1, 12, tzinfo=timezone.utc)
    n = d0.total_seconds() / 86400.0 + 2451545.0 - 2451545.0
    J = d0.total_seconds() / 86400.0 + 2451545.0
    T = (J - 2451545.0) / 36525.0
    L0 = (280.46646 + 36000.76983 * T) % 360
    M = math.radians((357.52911 + 35999.05029 * T) % 360)
    e = 0.016708634 - 0.000042037 * T
    C = (1.914602 - 0.004817 * T) * math.sin(M) + 0.019993 * math.sin(2 * M) + 0.000289 * math.sin(3 * M)
    lam = L0 + C - 0.00569 - 0.00478 * math.sin(math.radians(125.04 - 1934.136 * T))
    eps = math.radians(23.4392911 - 0.0130042 * T)
    decl = math.asin(math.sin(eps) * math.sin(math.radians(lam)))
    eqtime = math.degrees(math.tan(eps / 2) ** 2 * 2 * math.sin(2 * math.radians(L0))
                          - 2 * e * math.sin(M) * math.cos(eps)
                          + 4 * e * math.cos(eps) * math.sin(M) * math.cos(2 * math.radians(L0))) / 4.0
    frac = dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600
    tst = (frac * 15 + lon + eqtime) / 15.0
    H = math.radians((tst - 12) * 15)
    phi, dd = math.radians(lat), decl
    sinalt = math.sin(phi) * math.sin(dd) + math.cos(phi) * math.cos(dd) * math.cos(H)
    alt = math.degrees(math.asin(max(-1, min(1, sinalt))))
    az = math.degrees(math.atan2(math.sin(H), math.cos(H) * math.sin(phi) - math.tan(dd) * math.cos(phi)))
    az = (180 + az) % 360
    return az, alt


OBS = datetime(2026, 6, 20, 17, 55, tzinfo=timezone.utc)
CITIES = {
    "Berlin": (52.52, 13.405), "Paris": (48.8566, 2.3522), "Madrid": (40.4168, -3.7038),
    "Barcelona": (41.3851, 2.1734), "Rome": (41.9028, 12.4964), "Vienna": (48.2082, 16.3738),
    "Prague": (50.0755, 14.4378), "Warsaw": (52.2297, 21.0122), "Amsterdam": (52.3676, 4.9041),
    "Rotterdam": (51.9244, 4.4777), "Brussels": (50.8503, 4.3517), "Antwerp": (51.2194, 4.4025),
    "Copenhagen": (55.6761, 12.5683), "Stockholm": (59.3293, 18.0686), "Oslo": (59.9139, 10.7522),
    "Zurich": (47.3769, 8.5417), "Geneva": (46.2044, 6.1432), "Frankfurt": (50.1109, 8.6821),
    "Munich": (48.1351, 11.582), "Hamburg": (53.5511, 9.9937), "Milan": (45.4642, 9.19),
    "Budapest": (47.4979, 19.0402), "Belgrade": (44.7866, 20.4489), "Zagreb": (45.815, 15.9819),
    "Krakow": (50.0647, 19.945), "Gdansk": (54.352, 18.6466), "Vilnius": (54.6872, 25.2797),
    "Helsinki": (60.1699, 24.9384), "Athens": (37.9838, 23.7275), "Dublin": (53.3498, -6.2603),
    "London": (51.5074, -0.1278), "Birmingham": (52.4862, -1.8904), "Edinburgh": (55.9533, -3.1883),
    "Lisbon": (38.7223, -9.1393), "Seville": (37.3891, -5.9845), "Valencia": (39.4699, -0.3763),
    "Bilbao": (43.263, -2.935), "Porto": (41.1579, -8.6291), "Casablanca": (33.5731, -7.5898),
    "Algiers": (36.7538, 3.0588), "Tunis": (36.8065, 10.1815), "Cairo": (30.0444, 31.2357),
    "Istanbul": (41.0082, 28.9784), "Kyiv": (50.4501, 30.5234), "Minsk": (53.9006, 27.559),
    "Bucharest": (44.4268, 26.1025), "Sofia": (42.6977, 23.3219), "Riga": (56.9496, 24.1052),
    "Tallinn": (59.437, 24.7536), "Moscow": (55.7558, 37.6173), "StPetersburg": (59.9311, 30.3609),
    "Reykjavik": (64.1466, -21.9426), "Luxembourg": (49.6116, 6.1319), "Dubrovnik": (42.6507, 18.0944),
    "Sarajevo": (43.8563, 18.4131), "Skopje": (41.9973, 21.428), "Tirana": (41.3275, 19.8187),
    "Chisinau": (47.0105, 28.8638), "Valletta": (35.8988, 14.5147), "Nicosia": (35.1856, 33.3823),
}
rows = []
for city, (la, lo) in CITIES.items():
    az, alt = solar(la, lo, OBS)
    rows.append((abs(az - 274.5), city, la, lo, az, alt))
rows.sort()
print(f"\n{'city':14s} {'lat':>7s} {'lon':>7s} {'sunAz':>7s} {'sunAlt':>7s}  |d-274.5|")
for diff, city, la, lo, az, alt in rows[:18]:
    print(f"{city:14s} {la:7.2f} {lo:7.2f} {az:7.1f} {alt:7.1f}  {diff:8.1f}")
