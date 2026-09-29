import math
from datetime import datetime, timezone, timedelta

# ---- solar position (NOAA-style, good to ~0.1 deg) ----
def solar(lat, lon, dt_utc):
    jd = (dt_utc - datetime(2000, 1, 1, 12, tzinfo=timezone.utc)).total_seconds() / 86400.0 + 2451545.0
    T = (jd - 2451545.0) / 36525.0
    L0 = (280.46646 + 36000.76983 * T) % 360
    M = 357.52911 + 35999.05029 * T - 0.0001537 * T * T
    M = math.radians(M % 360)
    e = 0.016708634 - 0.000042037 * T
    C = (1.914602 - 0.004817 * T) * math.sin(M) + 0.019993 * math.sin(2 * M) + 0.000289 * math.sin(3 * M)
    true_long = L0 + C
    omega = 125.04 - 1934.136 * T
    lam = true_long - 0.00569 - 0.00478 * math.sin(math.radians(omega))
    eps0 = 23 + (26 + (21.448 - T * (46.815 + T * (0.00059 - T * 0.001813))) / 60) / 60
    eps = math.radians(eps0 + 0.00256 * math.cos(math.radians(omega)))
    decl = math.asin(math.sin(eps) * math.sin(math.radians(lam)))
    eqtime = math.degrees(math.tan(eps / 2) ** 2 * 2 * math.sin(2 * math.radians(L0))
                          - 2 * e * math.sin(M) * math.cos(eps)
                          + 4 * e * math.cos(eps) * math.sin(M) * math.cos(2 * math.radians(L0))) / 4.0
    frac = dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600
    tst = (frac * 15 + lon + eqtime) % 1440 / 60.0        # true solar time, hours
    H = math.radians((tst - 12) * 15)
    phi = math.radians(lat)
    cosz = (math.sin(phi) * math.sin(decl) + math.cos(phi) * math.cos(decl) * math.cos(H))
    cosz = max(-1, min(1, cosz))
    z = math.acos(cosz)
    alt = 90 - math.degrees(z)
    az = math.degrees(math.acos(max(-1, min(1, (math.sin(phi) * cosz - math.sin(decl)) /
                                             (math.cos(phi) * math.sin(z))))))
    if math.sin(H) > 0:
        az = 360 - az
    return az, alt


OBS = datetime(2026, 6, 20, 17, 55, tzinfo=timezone.utc)   # 19:55 UTC+02:00

CITIES = {
    "Berlin": (52.52, 13.405), "Paris": (48.8566, 2.3522), "Madrid": (40.4168, -3.7038),
    "Rome": (41.9028, 12.4964), "Vienna": (48.2082, 16.3738), "Prague": (50.0755, 14.4378),
    "Warsaw": (52.2297, 21.0122), "Amsterdam": (52.3676, 4.9041), "Brussels": (50.8503, 4.3517),
    "Copenhagen": (55.6761, 12.5683), "Stockholm": (59.3293, 18.0686), "Oslo": (59.9139, 10.7522),
    "Zurich": (47.3769, 8.5417), "Budapest": (47.4979, 19.0402), "Belgrade": (44.7866, 20.4489),
    "Zagreb": (45.815, 15.9819), "Bratislava": (48.1486, 17.1077), "Ljubljana": (46.0569, 14.5058),
    "Helsinki": (60.1699, 24.9384), "Vilnius": (54.6872, 25.2797), "Riga": (56.9496, 24.1052),
    "Tallinn": (59.437, 24.7536), "Athens": (37.9838, 23.7275), "Bucharest": (44.4268, 26.1025),
    "Sofia": (42.6977, 23.3219), "Kyiv": (50.4501, 30.5234), "Minsk": (53.9006, 27.559),
    "Cairo": (30.0444, 31.2357), "Tripoli": (32.8872, 13.1913), "Tunis": (36.8065, 10.1815),
    "Algiers": (36.7538, 3.0588), "Lagos": (6.5244, 3.3792), "Windhoek": (-22.5609, 17.0658),
    "Johannesburg": (-26.2041, 28.0473), "Pretoria": (-25.7479, 28.2293),
    "Gaborone": (-24.6544, 25.9096), "Lusaka": (-15.4141, 28.2937), "Harare": (-17.8318, 31.0453),
    "Nairobi": (-1.2921, 36.8219), "Istanbul": (41.0082, 28.9784), "Jerusalem": (31.7683, 35.2137),
    "Beirut": (33.8938, 35.5018), "Damascus": (33.5138, 36.2765), "Amman": (31.9539, 35.9106),
    "Riyadh": (24.7136, 46.6753), "Doha": (25.2854, 51.531), "Dubai": (25.2048, 55.2708),
    "Moscow": (55.7558, 37.6173), "St Petersburg": (59.9311, 30.3609),
    "Seoul": (37.5665, 126.978), "Tokyo": (35.6762, 139.6503), "Beijing": (39.9042, 116.4074),
    "Singapore": (1.3521, 103.8198), "Jakarta": (-6.2088, 106.8456), "Manila": (14.5995, 120.9842),
    "London": (51.5074, -0.1278), "Dublin": (53.3498, -6.2603), "Lisbon": (38.7223, -9.1393),
    "Reykjavik": (64.1466, -21.9426), "New York": (40.7128, -74.006), "Chicago": (41.8781, -87.6298),
    "Mexico City": (19.4326, -99.1332), "Bogota": (4.711, -74.0721), "Lima": (-12.0464, -77.0428),
    "Santiago": (-33.4489, -70.6693), "Buenos Aires": (-34.6037, -58.3816),
    "Sao Paulo": (-23.5505, -46.6333), "Cape Town": (-33.9249, 18.4241),
}

rows = []
for city, (la, lo) in CITIES.items():
    az, alt = solar(la, lo, OBS)
    rows.append((city, la, lo, az, alt))

rows.sort(key=lambda r: r[3])
print(f"{'city':16s} {'lat':>7s} {'lon':>7s} {'sunAz':>7s} {'sunAlt':>7s} {'shadowBearing':>13s}")
for city, la, lo, az, alt in rows:
    sb = (az + 180) % 360
    print(f"{city:16s} {la:7.2f} {lo:7.2f} {az:7.1f} {alt:7.1f} {sb:13.1f}")
