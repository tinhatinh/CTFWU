"""Invert (sun azimuth, sun altitude, instant) -> (lat, lon), and see which reading of the
photo lands on a real city.  Sweeps the assumed pigeon image height."""
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


CITIES = {
 "Tokyo":(35.68,139.69),"Seoul":(37.57,126.98),"Beijing":(39.90,116.41),"Shanghai":(31.23,121.47),
 "HongKong":(22.32,114.17),"Singapore":(1.35,103.82),"Bangkok":(13.76,100.50),"Jakarta":(-6.21,106.85),
 "Manila":(14.60,120.98),"KualaLumpur":(3.14,101.69),"HoChiMinh":(10.82,106.63),"Mumbai":(19.08,72.88),
 "Delhi":(28.61,77.21),"Kolkata":(22.57,88.36),"Karachi":(24.86,67.00),"Lahore":(31.55,74.34),
 "Kabul":(34.56,69.21),"Tashkent":(41.30,69.24),"Almaty":(43.24,76.89),"Dubai":(25.20,55.27),
 "Tehran":(35.69,51.39),"Baghdad":(33.32,44.37),"Riyadh":(24.71,46.68),"Jeddah":(21.49,39.19),
 "Jerusalem":(31.77,35.21),"Amman":(31.95,35.91),"Beirut":(33.89,35.50),"Cairo":(30.04,31.24),
 "Alexandria":(31.20,29.92),"Tripoli":(32.89,13.19),"Tunis":(36.81,10.18),"Algiers":(36.75,3.06),
 "Casablanca":(33.57,-7.59),"Rabat":(34.02,-6.84),"Marrakech":(31.63,-7.98),"Dakar":(14.72,-17.47),
 "Lagos":(6.52,3.38),"Accra":(5.60,-0.19),"Nairobi":(-1.29,36.82),"AddisAbaba":(9.03,38.74),
 "Khartoum":(15.50,32.56),"Johannesburg":(-26.20,28.05),"CapeTown":(-33.92,18.42),"Windhoek":(-22.56,17.07),
 "Kampala":(0.35,32.58),"DarEsSalaam":(-6.80,39.28),"Athens":(37.98,23.73),"Istanbul":(41.01,28.98),
 "Izmir":(38.42,27.13),"Bucharest":(44.43,26.10),"Sofia":(42.70,23.32),"Belgrade":(44.79,20.45),
 "Zagreb":(45.82,15.98),"Ljubljana":(46.06,14.51),"Sarajevo":(43.86,18.41),"Skopje":(42.00,21.43),
 "Tirana":(41.33,19.82),"Valletta":(35.90,14.45),"Budapest":(47.50,19.04),"Prague":(50.08,14.44),
 "Vienna":(48.21,16.37),"Bratislava":(48.15,17.11),"Krakow":(50.06,19.94),"Warsaw":(52.23,21.01),
 "Gdansk":(54.35,18.65),"Poznan":(52.41,16.93),"Berlin":(52.52,13.41),"Hamburg":(53.55,9.99),
 "Munich":(48.14,11.58),"Frankfurt":(50.11,8.68),"Cologne":(50.94,6.96),"Stuttgart":(48.78,9.18),
 "Zurich":(47.38,8.54),"Geneva":(46.20,6.14),"Milan":(45.46,9.19),"Turin":(45.07,7.69),
 "Venice":(45.44,12.32),"Rome":(41.90,12.50),"Naples":(40.85,14.27),"Florence":(43.77,11.26),
 "Madrid":(40.42,-3.70),"Barcelona":(41.39,2.17),"Seville":(37.39,-5.98),"Valencia":(39.47,-0.38),
 "Bilbao":(43.26,-2.93),"Zaragoza":(41.65,-0.92),"Malaga":(36.72,-4.42),"A Coruna":(43.36,-8.41),
 "Santiago":(42.88,-8.55),"Lisbon":(38.72,-9.14),"Porto":(41.16,-8.63),"Dublin":(53.35,-6.26),
 "Cork":(51.90,-8.48),"Galway":(53.27,-9.06),"Belfast":(54.60,-5.93),"London":(51.51,-0.13),
 "Birmingham":(52.49,-1.89),"Manchester":(53.48,-2.24),"Edinburgh":(55.95,-3.19),"Glasgow":(55.86,-4.25),
 "Amsterdam":(52.37,4.90),"Rotterdam":(51.92,4.48),"Utrecht":(52.09,5.12),"Brussels":(50.85,4.35),
 "Antwerp":(51.22,4.40),"Paris":(48.86,2.35),"Lyon":(45.76,4.84),"Marseille":(43.30,5.37),
 "Toulouse":(43.60,1.44),"Bordeaux":(44.84,-0.58),"Nantes":(47.22,-1.55),"Strasbourg":(48.58,7.75),
 "Copenhagen":(55.68,12.57),"Oslo":(59.91,10.75),"Stockholm":(59.33,18.07),"Gothenburg":(57.71,11.97),
 "Bergen":(60.39,5.32),"Helsinki":(60.17,24.94),"Tallinn":(59.44,24.75),"Riga":(56.95,24.11),
 "Vilnius":(54.69,25.28),"Minsk":(53.90,27.56),"Kyiv":(50.45,30.52),"Lviv":(49.84,24.03),
 "Odessa":(46.48,30.73),"StPetersburg":(59.93,30.36),"Moscow":(55.76,37.62),"Reykjavik":(64.15,-21.94),
 "Anchorage":(61.22,-149.90),"Honolulu":(21.31,-157.86),"Vancouver":(49.28,-123.12),"Seattle":(47.61,-122.33),
 "Portland":(45.52,-122.68),"SanFrancisco":(37.77,-122.42),"LosAngeles":(34.05,-118.24),"LasVegas":(36.17,-115.14),
 "Phoenix":(33.45,-112.07),"Denver":(39.74,-104.99),"Dallas":(32.78,-96.80),"Houston":(29.76,-95.37),
 "Chicago":(41.88,-87.63),"Atlanta":(33.75,-84.39),"Miami":(25.76,-80.19),"NewYork":(40.71,-74.01),
 "Boston":(42.36,-71.06),"Toronto":(43.65,-79.38),"Montreal":(45.50,-73.57),"MexicoCity":(19.43,-99.13),
 "Cancun":(21.16,-86.85),"Havana":(23.11,-82.37),"Bogota":(4.71,-74.07),"Caracas":(10.48,-66.90),
 "Lima":(-12.05,-77.04),"Santiago_Ch":(-33.45,-70.66),"BuenosAires":(-34.60,-58.38),"SaoPaulo":(-23.55,-46.63),
 "Rio":(-22.91,-43.17),"Brasilia":(-15.80,-47.87),"Montevideo":(-34.90,-56.16),"Sydney":(-33.87,151.21),
 "Melbourne":(-37.81,144.96),"Brisbane":(-27.47,153.03),"Perth":(-31.95,115.86),"Auckland":(-36.85,174.76),
 "Wellington":(-41.29,174.78),"Adelaide":(-34.93,138.60),"CapeVerde":(14.93,-23.51),"Azores":(37.74,-25.67),
 "Bermuda":(32.29,-64.78),"SanJuan":(18.47,-66.11),"Reykj":(64.15,-21.94),
}


def invert(az_t, alt_t, iters=60):
    """Newton solve for (lat, lon) matching the target azimuth and altitude."""
    lat, lon = 45.0, 0.0
    for _ in range(iters):
        az, alt = solar(lat, lon)
        e1 = ((az - az_t + 180) % 360) - 180
        e2 = alt - alt_t
        if abs(e1) < 1e-7 and abs(e2) < 1e-7:
            break
        J = np.zeros((2, 2))
        for k, d in enumerate((lat, lon)):
            p = [lat, lon]
            p[k] += 0.05
            a2, o2 = solar(p[0], p[1])
            J[0, k] = (((a2 - az_t + 180) % 360) - 180 - e1) / 0.05
            J[1, k] = (o2 - alt - e2) / 0.05
        try:
            step = np.linalg.solve(J, [-e1, -e2])
        except np.linalg.LinAlgError:
            return None
        lat += float(np.clip(step[0], -3, 3))
        lon += float(np.clip(step[1], -6, 6))
        if not (-90 <= lat <= 90):
            return None
    return lat, lon


SHADOW_PX = 1479.0
for az_t, tag in ((299.6, "flat, shadow ESE -> sun WNW"), (60.4, "flat mirrored, sun ENE")):
    print(f"\n===== {tag} =====")
    print(f"{'bird px':>8} {'alt':>6} {'lat':>8} {'lon':>9}   nearest major city (km)")
    for h in (400, 500, 600, 700, 800, 900, 1005, 1100, 1200, 1400):
        alt_t = math.degrees(math.atan(h / SHADOW_PX))
        r = invert(az_t, alt_t)
        if not r:
            print(f"{h:8d} {alt_t:6.2f}   no solution")
            continue
        la, lo = r
        best = min(CITIES.items(),
                   key=lambda kv: (kv[1][0] - la) ** 2 + ((kv[1][1] - lo) * math.cos(math.radians(la))) ** 2)
        dkm = 111.32 * math.hypot(best[1][0] - la, (best[1][1] - lo) * math.cos(math.radians(la)))
        a2, o2 = solar(best[1][0], best[1][1])
        print(f"{h:8d} {alt_t:6.2f} {la:8.2f} {lo:9.2f}   {best[0]:14s} {dkm:7.0f} km  "
              f"(its az/alt {a2:6.1f}/{o2:5.1f})")
