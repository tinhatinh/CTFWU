"""Rank major world cities by how well their sun position at the observation instant
matches candidate readings of the photo."""
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
    alt = math.asin(math.sin(phi) * math.sin(decl) + math.cos(phi) * math.cos(decl) * math.cos(H))
    az = math.degrees(math.atan2(math.sin(H), math.cos(H) * math.sin(phi) - math.tan(decl) * math.cos(phi)))
    return (180 + az) % 360, math.degrees(alt)


exec(open("cities.py").read()) if False else None
CITIES = {
 "Tokyo":(35.68,139.69),"Seoul":(37.57,126.98),"Beijing":(39.90,116.41),"Shanghai":(31.23,121.47),
 "HongKong":(22.32,114.17),"Singapore":(1.35,103.82),"Bangkok":(13.76,100.50),"Jakarta":(-6.21,106.85),
 "Manila":(14.60,120.98),"KualaLumpur":(3.14,101.69),"HoChiMinh":(10.82,106.63),"Mumbai":(19.08,72.88),
 "Delhi":(28.61,77.21),"Kolkata":(22.57,88.36),"Karachi":(24.86,67.00),"Lahore":(31.55,74.34),
 "Dubai":(25.20,55.27),"Tehran":(35.69,51.39),"Baghdad":(33.32,44.37),"Riyadh":(24.71,46.68),
 "Jerusalem":(31.77,35.21),"Cairo":(30.04,31.24),"Alexandria":(31.20,29.92),"Tripoli":(32.89,13.19),
 "Tunis":(36.81,10.18),"Algiers":(36.75,3.06),"Casablanca":(33.57,-7.59),"Rabat":(34.02,-6.84),
 "Marrakech":(31.63,-7.98),"Dakar":(14.72,-17.47),"Lagos":(6.52,3.38),"Accra":(5.60,-0.19),
 "Nairobi":(-1.29,36.82),"AddisAbaba":(9.03,38.74),"Johannesburg":(-26.20,28.05),"CapeTown":(-33.92,18.42),
 "Athens":(37.98,23.73),"Istanbul":(41.01,28.98),"Bucharest":(44.43,26.10),"Sofia":(42.70,23.32),
 "Belgrade":(44.79,20.45),"Budapest":(47.50,19.04),"Prague":(50.08,14.44),"Vienna":(48.21,16.37),
 "Krakow":(50.06,19.94),"Warsaw":(52.23,21.01),"Gdansk":(54.35,18.65),"Berlin":(52.52,13.41),
 "Hamburg":(53.55,9.99),"Munich":(48.14,11.58),"Frankfurt":(50.11,8.68),"Cologne":(50.94,6.96),
 "Zurich":(47.38,8.54),"Milan":(45.46,9.19),"Rome":(41.90,12.50),"Naples":(40.85,14.27),
 "Venice":(45.44,12.32),"Madrid":(40.42,-3.70),"Barcelona":(41.39,2.17),"Seville":(37.39,-5.98),
 "Valencia":(39.47,-0.38),"Bilbao":(43.26,-2.93),"Malaga":(36.72,-4.42),"A Coruna":(43.36,-8.41),
 "Santiago":(42.88,-8.55),"Lisbon":(38.72,-9.14),"Porto":(41.16,-8.63),"Dublin":(53.35,-6.26),
 "Cork":(51.90,-8.48),"Galway":(53.27,-9.06),"Belfast":(54.60,-5.93),"London":(51.51,-0.13),
 "Birmingham":(52.49,-1.89),"Manchester":(53.48,-2.24),"Edinburgh":(55.95,-3.19),"Glasgow":(55.86,-4.25),
 "Amsterdam":(52.37,4.90),"Rotterdam":(51.92,4.48),"Brussels":(50.85,4.35),"Antwerp":(51.22,4.40),
 "Paris":(48.86,2.35),"Lyon":(45.76,4.84),"Marseille":(43.30,5.37),"Bordeaux":(44.84,-0.58),
 "Nantes":(47.22,-1.55),"Strasbourg":(48.58,7.75),"Copenhagen":(55.68,12.57),"Oslo":(59.91,10.75),
 "Stockholm":(59.33,18.07),"Gothenburg":(57.71,11.97),"Bergen":(60.39,5.32),"Helsinki":(60.17,24.94),
 "Tallinn":(59.44,24.75),"Riga":(56.95,24.11),"Vilnius":(54.69,25.28),"Minsk":(53.90,27.56),
 "Kyiv":(50.45,30.52),"Lviv":(49.84,24.03),"Odessa":(46.48,30.73),"StPetersburg":(59.93,30.36),
 "Moscow":(55.76,37.62),"Reykjavik":(64.15,-21.94),"Anchorage":(61.22,-149.90),"Honolulu":(21.31,-157.86),
 "Vancouver":(49.28,-123.12),"Seattle":(47.61,-122.33),"Portland":(45.52,-122.68),
 "SanFrancisco":(37.77,-122.42),"LosAngeles":(34.05,-118.24),"LasVegas":(36.17,-115.14),
 "Phoenix":(33.45,-112.07),"Denver":(39.74,-104.99),"Dallas":(32.78,-96.80),"Houston":(29.76,-95.37),
 "Chicago":(41.88,-87.63),"Atlanta":(33.75,-84.39),"Miami":(25.76,-80.19),"NewYork":(40.71,-74.01),
 "Boston":(42.36,-71.06),"Washington":(38.91,-77.04),"Toronto":(43.65,-79.38),"Montreal":(45.50,-73.57),
 "MexicoCity":(19.43,-99.13),"Cancun":(21.16,-86.85),"Havana":(23.11,-82.37),"Bogota":(4.71,-74.07),
 "Caracas":(10.48,-66.90),"Lima":(-12.05,-77.04),"SantiagoCh":(-33.45,-70.66),
 "BuenosAires":(-34.60,-58.38),"SaoPaulo":(-23.55,-46.63),"Rio":(-22.91,-43.17),
 "Brasilia":(-15.80,-47.87),"Montevideo":(-34.90,-56.16),"Sydney":(-33.87,151.21),
 "Melbourne":(-37.81,144.96),"Brisbane":(-27.47,153.03),"Perth":(-31.95,115.86),
 "Auckland":(-36.85,174.76),"Azores":(37.74,-25.67),"Bermuda":(32.29,-64.78),"SanJuan":(18.47,-66.11),
 "Halifax":(44.65,-63.58),"StJohns":(47.56,-52.71),"Reyk":(64.15,-21.94),"Nuuk":(64.18,-51.69),
 "Iqaluit":(63.75,-68.52),"Yellowknife":(62.45,-114.37),"Fairbanks":(64.84,-147.72),
}

# candidate readings of the photo
SHADOW_IMG = 1455.0
BIRD_IMG = 960.0
READINGS = [
    ("flat  naive ratio", 299.6, math.degrees(math.atan(BIRD_IMG / SHADOW_IMG))),
    ("flat  mirrored az ", 60.4, math.degrees(math.atan(BIRD_IMG / SHADOW_IMG))),
    ("flat  inv ratio   ", 299.6, math.degrees(math.atan(SHADOW_IMG / BIRD_IMG))),
    ("persp s=0.9       ", 294.0, 49.0),
    ("persp s=0.75      ", 285.0, 42.0),
    ("low sun, alt 12   ", 296.0, 12.0),
    ("low sun, alt 18   ", 285.0, 18.0),
]

for nm, az_t, alt_t in READINGS:
    rows = []
    for city, (la, lo) in CITIES.items():
        az, alt = solar(la, lo)
        daz = ((az - az_t + 180) % 360) - 180
        rows.append((abs(daz) + abs(alt - alt_t), city, az, alt, daz))
    rows.sort()
    print(f"\n=== {nm}: target az={az_t:.1f} alt={alt_t:.1f} ===")
    for r, city, az, alt, daz in rows[:6]:
        print(f"   {city:14s} az={az:6.1f} alt={alt:6.1f}   daz={daz:+6.1f} dalt={alt-alt_t:+6.1f}")
