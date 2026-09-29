"""Tilt-consistent affine ground model.

Ground direction at bearing b maps to the image vector (sin(b-psi), s*cos(b-psi)) with
y up, where s = sin(tau) is the ground foreshortening and tau the camera depression angle.
A vertical segment then maps with the factor cos(tau) = sqrt(1-s^2).

  north arrow  -> tan(psi)     = 2.415 s
  shadow line  -> tan(B-psi)   = 1.282 s
  shadow image extent: right 1166 px, away 909 px
  bird image height:   ~900 px
so  tan(alt) = (900/sqrt(1-s^2)) / sqrt(1166^2 + (909/s)^2)
"""
import math
from datetime import datetime, timezone
import numpy as np

# --- measured image directions (x right, y up), see measure_precise.py ---
N_IMG = np.array([-0.9239, 0.3825])
S_IMG = np.array([0.7886, 0.6149])
KN = N_IMG[0] / N_IMG[1]          # tan(psi) = KN * s
KS = S_IMG[0] / S_IMG[1]          # tan(B-psi) = KS * s
RIGHT, AWAY = 1166.0, 909.0       # shadow image extent, right / away components
BIRD = 900.0                      # pigeon image height, feet->crown
print(f"KN={KN:.4f} KS={KS:.4f}")


def solar(lat, lon, dt):
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
    alt = math.asin(math.sin(phi) * math.sin(decl) + math.cos(phi) * math.cos(decl) * math.cos(H))
    az = math.degrees(math.atan2(math.sin(H), math.cos(H) * math.sin(phi) - math.tan(decl) * math.cos(phi)))
    return (180 + az) % 360, math.degrees(alt)


CITIES = {
    "Madrid": (40.4168, -3.7038), "Barcelona": (41.3851, 2.1734), "Seville": (37.3891, -5.9845),
    "Bilbao": (43.263, -2.935), "Valencia": (39.4699, -0.3763), "Zaragoza": (41.6488, -0.9212),
    "A Coruna": (43.3623, -8.4115), "Santiago": (42.8805, -8.5457), "Lisbon": (38.7223, -9.1393),
    "Porto": (41.1579, -8.6291), "Dublin": (53.3498, -6.2603), "Cork": (51.8985, -8.4756),
    "Galway": (53.2707, -9.0568), "Belfast": (54.5973, -5.9301), "Edinburgh": (55.9533, -3.1883),
    "Glasgow": (55.8642, -4.2518), "London": (51.5074, -0.1278), "Birmingham": (52.4862, -1.8904),
    "Manchester": (53.4808, -2.2426), "Amsterdam": (52.3676, 4.9041), "Rotterdam": (51.9244, 4.4777),
    "Brussels": (50.8503, 4.3517), "Antwerp": (51.2194, 4.4025), "Paris": (48.8566, 2.3522),
    "Berlin": (52.52, 13.405), "Hamburg": (53.5511, 9.9937), "Munich": (48.1351, 11.582),
    "Frankfurt": (50.1109, 8.6821), "Cologne": (50.9375, 6.9603), "Zurich": (47.3769, 8.5417),
    "Milan": (45.4642, 9.19), "Turin": (45.0703, 7.6869), "Rome": (41.9028, 12.4964),
    "Naples": (40.8518, 14.2681), "Venice": (45.4408, 12.3155), "Vienna": (48.2082, 16.3738),
    "Prague": (50.0755, 14.4378), "Warsaw": (52.2297, 21.0122), "Krakow": (50.0647, 19.945),
    "Gdansk": (54.352, 18.6466), "Poznan": (52.4064, 16.9252), "Copenhagen": (55.6761, 12.5683),
    "Oslo": (59.9139, 10.7522), "Stockholm": (59.3293, 18.0686), "Gothenburg": (57.7089, 11.9746),
    "Bergen": (60.3913, 5.3221), "Helsinki": (60.1699, 24.9384), "Tallinn": (59.437, 24.7536),
    "Riga": (56.9496, 24.1052), "Vilnius": (54.6872, 25.2797), "Reykjavik": (64.1466, -21.9426),
    "Budapest": (47.4979, 19.0402), "Bucharest": (44.4268, 26.1025), "Belgrade": (44.7866, 20.4489),
    "Athens": (37.9838, 23.7275), "Sofia": (42.6977, 23.3219), "Zagreb": (45.815, 15.9819),
    "Lviv": (49.8397, 24.0297), "Kyiv": (50.4501, 30.5234), "Minsk": (53.9006, 27.559),
    "StPetersburg": (59.9311, 30.3609), "Moscow": (55.7558, 37.6173), "Istanbul": (41.0082, 28.9784),
    "Cairo": (30.0444, 31.2357), "Alexandria": (31.2001, 29.9187), "Tripoli": (32.8872, 13.1913),
    "Tunis": (36.8065, 10.1815), "Algiers": (36.7538, 3.0588), "Casablanca": (33.5731, -7.5898),
    "Rabat": (34.0209, -6.8416), "Marrakech": (31.6295, -7.9811), "Dakar": (14.7167, -17.4677),
    "Johannesburg": (-26.2041, 28.0473), "Windhoek": (-22.5609, 17.0658), "CapeTown": (-33.9249, 18.4241),
    "Jerusalem": (31.7683, 35.2137), "Amman": (31.9539, 35.9106), "Beirut": (33.8938, 35.5018),
    "Tehran": (35.6892, 51.389), "Baghdad": (33.3152, 44.3661), "Dubai": (25.2048, 55.2708),
    "Karachi": (24.8607, 67.0011), "Delhi": (28.6139, 77.209), "Moscow2": (55.75, 37.62),
}

OBS = datetime(2026, 6, 20, 17, 55, tzinfo=timezone.utc)


def solve_s(B):
    """Find s in (0,1) with atan(KN s) + atan(KS s) == B (mod 360), shadow pointing away."""
    grid = np.linspace(0.02, 0.999, 2000)
    f = np.array([math.degrees(math.atan(KN * s)) + math.degrees(math.atan(KS * s)) for s in grid])
    err = np.abs(((f - B + 180) % 360) - 180)
    i = err.argmin()
    return grid[i], err[i]


rows = []
for city, (la, lo) in CITIES.items():
    az, alt = solar(la, lo, OBS)
    if alt <= 0.5:
        continue
    B = (az + 180) % 360
    s, serr = solve_s(B)
    L = math.hypot(RIGHT, AWAY / s)
    h = BIRD / math.sqrt(max(1 - s * s, 1e-6))
    alt_pred = math.degrees(math.atan(h / L))
    rows.append((abs(alt_pred - alt), city, la, lo, az, alt, s, serr, alt_pred))

rows.sort()
print(f"\n{'city':13s} {'lat':>6s} {'lon':>7s} {'sunAz':>6s} {'sunAlt':>6s} {'s':>5s} {'angErr':>6s} {'altPred':>7s}  diff")
for d, city, la, lo, az, alt, s, serr, ap in rows[:18]:
    print(f"{city:13s} {la:6.1f} {lo:7.1f} {az:6.1f} {alt:6.1f} {s:5.2f} {serr:6.2f} {ap:7.1f}  {d:5.1f}")
