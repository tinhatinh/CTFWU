"""Enumerate every candidate city whose sun position at the instant falls in the band the
photo allows, so the remaining option space is explicit."""
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


# name: (lat, lon, metro population in millions)  -- broad world list
C = {
 "Recife": (-8.05, -34.87, 4.1), "Natal": (-5.79, -35.21, 1.6), "JoaoPessoa": (-7.12, -34.86, 1.5),
 "Fortaleza": (-3.72, -38.52, 4.0), "Maceio": (-9.62, -36.62, 1.4), "Salvador": (-12.97, -38.50, 4.2),
 "Belem": (-1.46, -48.50, 2.4), "Macap": (0.04, -51.07, 1.1), "Manaus": (-3.10, -60.02, 2.8),
 "SaoLuis": (-2.53, -44.30, 1.6), "Teresina": (-5.09, -42.80, 1.3), "Cuiaba": (-15.60, -56.10, 1.0),
 "Goiania": (-16.68, -49.25, 2.5), "Brasilia": (-15.79, -47.88, 4.3), "BeloHorizonte": (-19.87, -43.95, 6.0),
 "SaoPaulo": (-23.55, -46.63, 22.0), "Rio": (-22.91, -43.17, 13.5), "Curitiba": (-25.43, -49.27, 3.7),
 "PortoAlegre": (-30.03, -51.23, 4.3), "Cayenne": (4.94, -52.33, 0.19), "Paramaribo": (5.85, -55.20, 0.55),
 "Georgetown": (6.82, -58.16, 0.4), "PuertoLaCruz": (10.66, -64.61, 1.5), "Caracas": (10.49, -66.88, 3.0),
 "Maracaibo": (10.64, -71.64, 2.0), "Bogota": (4.71, -74.07, 10.7), "Medellin": (6.24, -75.58, 4.0),
 "Quito": (-0.18, -78.47, 2.8), "Lima": (-12.05, -77.04, 10.0), "SantiagoCh": (-33.45, -70.66, 6.8),
 "BuenosAires": (-34.60, -58.38, 15.0), "CordobaAR": (-31.42, -64.18, 1.5), "Montevideo": (-34.90, -56.16, 1.9),
 "Asuncion": (-25.26, -57.57, 2.2), "SantaCruz": (-17.78, -63.18, 3.1), "LaPaz": (-16.50, -68.15, 2.7),
 "Panama": (8.98, -79.52, 1.9), "SanJose": (9.93, -84.08, 1.4), "Guatemala": (14.63, -90.51, 2.9),
 "MexicoCity": (19.43, -99.13, 21.8), "Monterrey": (25.69, -100.32, 4.5), "Guadalajara": (20.67, -103.35, 4.4),
 "Cancun": (21.16, -86.85, 0.9), "Merida": (20.97, -89.62, 1.1), "Havana": (23.11, -82.37, 2.1),
 "SantoDomingo": (18.49, -69.93, 3.0), "SanJuan": (18.47, -66.11, 2.5), "Kingston": (17.97, -76.79, 0.9),
 "PortAuPrince": (18.54, -72.34, 2.7), "Miami": (25.76, -80.19, 6.1), "Atlanta": (33.75, -84.39, 6.1),
 "Houston": (29.76, -95.37, 7.0), "Dallas": (32.78, -96.80, 7.9), "Chicago": (41.88, -87.63, 8.9),
 "NewOrleans": (29.95, -90.07, 1.3), "Washington": (38.91, -77.04, 6.3), "NewYork": (40.71, -74.01, 19.8),
 "Boston": (42.36, -71.06, 4.9), "Toronto": (43.65, -79.38, 6.2), "Montreal": (45.50, -73.57, 4.2),
 "Halifax": (44.65, -63.58, 0.4), "StJohns": (47.56, -52.71, 0.2), "Nuuk": (64.18, -51.69, 0.02),
 "Winnipeg": (49.90, -97.14, 0.8), "Regina": (50.45, -104.62, 0.29), "Edmonton": (53.55, -113.49, 1.4),
 "Calgary": (51.04, -114.07, 1.5), "Vancouver": (49.28, -123.12, 2.6), "Seattle": (47.61, -122.33, 4.0),
 "Portland": (45.52, -122.68, 2.5), "SanFrancisco": (37.77, -122.42, 8.7), "LosAngeles": (34.05, -118.24, 12.5),
 "LasVegas": (36.17, -115.14, 2.3), "Phoenix": (33.45, -112.07, 4.9), "Denver": (39.74, -104.99, 2.9),
 "Anchorage": (61.22, -149.90, 0.4), "Fairbanks": (64.84, -147.72, 0.1), "Honolulu": (21.31, -157.86, 1.0),
 "Dakar": (14.72, -17.47, 3.7), "Thies": (14.79, -16.66, 1.2), "Banjul": (13.45, -16.58, 0.4),
 "Bissau": (11.86, -15.59, 0.6), "Conakry": (9.64, -13.58, 1.9), "Freetown": (8.48, -13.23, 1.2),
 "Monrovia": (6.31, -10.80, 1.2), "Abidjan": (5.36, -4.03, 5.6), "Accra": (5.60, -0.19, 4.0),
 "Lome": (6.13, 1.22, 1.8), "Cotonou": (6.37, 2.39, 1.4), "Lagos": (6.52, 3.38, 15.4),
 "Douala": (4.05, 9.70, 3.0), "Libreville": (0.39, 9.45, 0.8), "Luanda": (-8.84, 13.23, 3.6),
 "Windhoek": (-22.56, 17.07, 0.5), "CapeTown": (-33.92, 18.42, 4.8), "Johannesburg": (-26.20, 28.05, 6.0),
 "Nairobi": (-1.29, 36.82, 4.4), "Mogadishu": (2.05, 45.34, 2.6), "AddisAbaba": (9.03, 38.74, 5.0),
 "Khartoum": (15.50, 32.56, 6.0), "Cairo": (30.04, 31.24, 21.0), "Alexandria": (31.20, 29.92, 5.3),
 "Tripoli": (32.89, 13.19, 2.4), "Tunis": (36.81, 10.18, 2.7), "Algiers": (36.75, 3.06, 3.4),
 "Casablanca": (33.57, -7.59, 3.7), "Rabat": (34.02, -6.84, 2.1), "Marrakech": (31.63, -7.98, 1.0),
 "Agadir": (30.42, -9.60, 0.6), "ElAaiun": (27.15, -13.20, 0.2), "Nouakchott": (18.09, -15.98, 1.0),
 "Praia": (14.93, -23.51, 0.2), "PontaDelgada": (37.74, -25.67, 0.1), "Hamilton": (32.29, -64.78, 0.06),
 "Madrid": (40.42, -3.70, 6.6), "Lisbon": (38.72, -9.14, 3.0), "London": (51.51, -0.13, 9.5),
 "Dublin": (53.35, -6.26, 1.4), "Galway": (53.27, -9.06, 0.2), "Paris": (48.86, 2.35, 11.0),
 "Berlin": (52.52, 13.41, 3.7), "Amsterdam": (52.37, 4.90, 2.5), "Brussels": (50.85, 4.35, 1.2),
 "Copenhagen": (55.68, 12.57, 1.4), "Oslo": (59.91, 10.75, 1.0), "Stockholm": (59.33, 18.07, 1.6),
 "Helsinki": (60.17, 24.94, 1.3), "Reykjavik": (64.15, -21.94, 0.2), "Rome": (41.90, 12.50, 4.3),
 "Athens": (37.98, 23.73, 3.2), "Istanbul": (41.01, 28.98, 15.5), "Moscow": (55.76, 37.62, 12.5),
 "Kyiv": (50.45, 30.52, 2.9), "Warsaw": (52.23, 21.01, 1.8), "Vienna": (48.21, 16.37, 1.9),
 "Prague": (50.08, 14.44, 1.3), "Budapest": (47.50, 19.04, 1.7), "Bucharest": (44.43, 26.10, 1.9),
 "Belgrade": (44.79, 20.45, 1.4), "Sofia": (42.70, 23.32, 1.3), "Jerusalem": (31.77, 35.21, 1.1),
 "Dubai": (25.20, 55.27, 3.5), "Tehran": (35.69, 51.39, 9.0), "Karachi": (24.86, 67.00, 16.0),
 "Delhi": (28.61, 77.21, 32.0), "Mumbai": (19.08, 72.88, 21.0), "Bangkok": (13.76, 100.50, 10.5),
 "Singapore": (1.35, 103.82, 5.9), "Jakarta": (-6.21, 106.85, 10.6), "Manila": (14.60, 120.98, 13.9),
 "Tokyo": (35.68, 139.69, 37.0), "Seoul": (37.57, 126.98, 9.9), "Beijing": (39.90, 116.41, 21.0),
 "Sydney": (-33.87, 151.21, 5.3), "Melbourne": (-37.81, 144.96, 5.0), "Perth": (-31.95, 115.86, 2.1),
 "Auckland": (-36.85, 174.76, 1.7),
}

rows = []
for nm, (la, lo, pop) in C.items():
    az, alt = solar(la, lo)
    rows.append((nm, la, lo, pop, az, alt))

print("cities with the sun above the horizon and azimuth in the WNW quarter at 17:55 UT:")
sel = [r for r in rows if 270 <= r[4] <= 320 and r[5] > 5]
sel.sort(key=lambda r: -r[3])
print(f"{'city':14s} {'lat':>7s} {'lon':>8s} {'pop(M)':>7s} {'az':>7s} {'alt':>6s}")
for nm, la, lo, pop, az, alt in sel:
    print(f"{nm:14s} {la:7.2f} {lo:8.2f} {pop:7.1f} {az:7.1f} {alt:6.1f}")

print("\nband that matches the photo (az 292..304, alt 26..40):")
for nm, la, lo, pop, az, alt in sel:
    if 292 <= az <= 304 and 26 <= alt <= 40:
        print(f"   {nm:14s} pop={pop:5.1f}M  az={az:6.1f}  alt={alt:5.1f}")
