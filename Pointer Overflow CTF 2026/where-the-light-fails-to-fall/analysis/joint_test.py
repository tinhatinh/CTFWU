import math
from datetime import datetime, timezone
import numpy as np

# ---- measured from the photo (see measure_precise.py) ----
# north arrow image direction (x right, y up): (-0.9239, +0.3825)
# shadow image direction (x right, y up):       (+0.7886, +0.6149)
K_N = 0.9239 / 0.3825          # = tan(psi)/s   -> tan(psi) = K_N * s
K_S = 0.7886 / 0.6149          # = tan(B-psi)/s -> tan(B-psi) = K_S * s
RHO = 1478.7 / 950.0           # shadow image length / bird image height
print("measured: K_N=%.3f K_S=%.3f rho=%.3f" % (K_N, K_S, RHO))


def solar(lat, lon, dt_utc):
    J = dt_utc.timestamp() / 86400.0 + 2440587.5
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
    frac = dt_utc.hour + dt_utc.minute / 60
    tst = frac + lon / 15.0 + eqtime / 60.0
    H = math.radians((tst - 12) * 15)
    phi = math.radians(lat)
    alt = math.asin(math.sin(phi) * math.sin(decl) + math.cos(phi) * math.cos(decl) * math.cos(H))
    az = math.degrees(math.atan2(math.sin(H), math.cos(H) * math.sin(phi) - math.tan(decl) * math.cos(phi)))
    return (180 + az) % 360, math.degrees(alt)


OBS = datetime(2026, 6, 20, 17, 55, tzinfo=timezone.utc)
CITIES = {
    "Madrid": (40.4168, -3.7038), "Barcelona": (41.3851, 2.1734), "Seville": (37.3891, -5.9845),
    "Bilbao": (43.263, -2.935), "Valencia": (39.4699, -0.3763), "A Coruna": (43.3623, -8.4115),
    "Lisbon": (38.7223, -9.1393), "Porto": (41.1579, -8.6291), "Dublin": (53.3498, -6.2603),
    "Galway": (53.2707, -9.0568), "Edinburgh": (55.9533, -3.1883), "Glasgow": (55.8642, -4.2518),
    "London": (51.5074, -0.1278), "Birmingham": (52.4862, -1.8904), "Amsterdam": (52.3676, 4.9041),
    "Rotterdam": (51.9244, 4.4777), "Brussels": (50.8503, 4.3517), "Paris": (48.8566, 2.3522),
    "Berlin": (52.52, 13.405), "Hamburg": (53.5511, 9.9937), "Munich": (48.1351, 11.582),
    "Frankfurt": (50.1109, 8.6821), "Zurich": (47.3769, 8.5417), "Milan": (45.4642, 9.19),
    "Rome": (41.9028, 12.4964), "Vienna": (48.2082, 16.3738), "Prague": (50.0755, 14.4378),
    "Warsaw": (52.2297, 21.0122), "Krakow": (50.0647, 19.945), "Copenhagen": (55.6761, 12.5683),
    "Oslo": (59.9139, 10.7522), "Stockholm": (59.3293, 18.0686), "Bergen": (60.3913, 5.3221),
    "Helsinki": (60.1699, 24.9384), "Reykjavik": (64.1466, -21.9426), "Budapest": (47.4979, 19.0402),
    "Belgrade": (44.7866, 20.4489), "Athens": (37.9838, 23.7275), "Cairo": (30.0444, 31.2357),
    "Tripoli": (32.8872, 13.1913), "Tunis": (36.8065, 10.1815), "Algiers": (36.7538, 3.0588),
    "Casablanca": (33.5731, -7.5898), "Rabat": (34.0209, -6.8416), "Dakar": (14.7167, -17.4677),
    "Johannesburg": (-26.2041, 28.0473), "Windhoek": (-22.5609, 17.0658), "StPetersburg": (59.9311, 30.3609),
    "Moscow": (55.7558, 37.6173), "Kyiv": (50.4501, 30.5234), "Minsk": (53.9006, 27.559),
}

rows = []
for city, (la, lo) in CITIES.items():
    az, alt = solar(la, lo, OBS)
    B = (az + 180) % 360
    # solve s from: psi = atan(K_N s);  B - psi = atan(K_S s)   (mod 180 ambiguity handled by search)
    best = None
    for s in np.linspace(0.05, 1.0, 191):
        psi = math.degrees(math.atan(K_N * s))
        lhs = (psi + math.degrees(math.atan(K_S * s))) % 180
        err = min(abs(lhs - B % 180), 180 - abs(lhs - B % 180))
        if best is None or err < best[0]:
            best = (err, s, psi)
    err, s, psi = best
    # predicted image ratio rho for this city/s
    rel = math.radians(B - psi)
    rho_pred = math.sqrt(math.sin(rel) ** 2 + (s * math.cos(rel)) ** 2) / math.tan(math.radians(alt))
    rows.append((abs(rho_pred - RHO), city, la, lo, az, alt, s, err, rho_pred))

rows.sort()
print(f"\n{'city':14s} {'lat':>6s} {'lon':>7s} {'sunAz':>6s} {'sunAlt':>6s} {'s':>5s} {'angErr':>6s} {'rhoPred':>7s} (measured rho=%.2f)" % RHO)
for diff, city, la, lo, az, alt, s, err, rho in rows[:14]:
    print(f"{city:14s} {la:6.1f} {lo:7.1f} {az:6.1f} {alt:6.1f} {s:5.2f} {err:6.1f} {rho:7.2f}   d={diff:.2f}")
