"""Vectorised solar model + world grid inverse: which (lat, lon) produces the photo's
sun azimuth/altitude at the observation instant."""
import math
from datetime import datetime, timezone
import numpy as np

OBS = datetime(2026, 6, 20, 17, 55, tzinfo=timezone.utc)


def solar_vec(lat, lon, dt=OBS):
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
    H = np.radians((dt.hour + dt.minute / 60 + lon / 15 + eqtime / 60 - 12) * 15)
    phi = np.radians(lat)
    s = np.sin(phi) * math.sin(decl) + np.cos(phi) * math.cos(decl) * np.cos(H)
    alt = np.degrees(np.arcsin(np.clip(s, -1, 1)))
    az = np.degrees(np.arctan2(np.sin(H), np.cos(H) * np.sin(phi) - math.tan(decl) * np.cos(phi)))
    return (180 + az) % 360, alt


DECL_OK = None
LA = np.arange(-60.0, 78.0, 0.10)
LO = np.arange(-180.0, 180.0, 0.10)
LAgrid, LOgrid = np.meshgrid(LA, LO, indexing="ij")
AZ, ALT = solar_vec(LAgrid, LOgrid)
print("grid", AZ.shape)

SHADOW = 1455.0
BIRD = 960.0
CITY = {
 "Recife":(-8.05,-34.87),"Salvador":(-12.97,-38.50),"Fortaleza":(-3.72,-38.52),"Belem":(-1.46,-48.50),
 "SaoPaulo":(-23.55,-46.63),"Rio":(-22.91,-43.17),"Brasilia":(-15.79,-47.88),"Fernando":(-3.85,-32.44),
 "Cayenne":(4.94,-52.33),"Georgetown":(6.82,-58.16),"Paramaribo":(5.85,-55.20),"Codajas":(-3.83,-62.06),
 "Manaus":(-3.10,-60.02),"BoaVista":(2.82,-60.67),"Caracas":(10.49,-66.88),"PuertoLaCruz":(10.66,-64.61),
 "Georgetown2":(6.80,-58.16),"Natal":(-5.79,-35.21),"Maceio":(-9.62,-36.62),"JoaoPessoa":(-7.12,-34.86),
 "Aracaju":(-10.91,-37.08),"Vitoria":(-20.32,-40.34),"BeloHorizonte":(-19.87,-43.95),
 "Dakar":(14.72,-17.47),"Thies":(14.79,-16.66),"Banjul":(13.45,-16.58),"Bissau":(11.86,-15.59),
 "Conakry":(9.64,-13.58),"Freetown":(8.48,-13.23),"Monrovia":(6.31,-10.80),"Abidjan":(5.36,-4.03),
 "Accra":(5.60,-0.19),"Lome":(6.13,1.22),"Cotonou":(6.37,2.39),"Lagos":(6.52,3.38),
 "Douala":(4.05,9.70),"Libreville":(0.39,9.45),"SaoTome":(0.33,6.73),"Luanda":(-8.84,13.23),
 "Windhoek":(-22.56,17.07),"CapeTown":(-33.92,18.42),"Johannesburg":(-26.20,28.05),
 "Nairobi":(-1.29,36.82),"Mogadishu":(2.05,45.34),"AddisAbaba":(9.03,38.74),"Khartoum":(15.50,32.56),
 "Cairo":(30.04,31.24),"Alexandria":(31.20,29.92),"Tripoli":(32.89,13.19),"Tunis":(36.81,10.18),
 "Algiers":(36.75,3.06),"Casablanca":(33.57,-7.59),"Rabat":(34.02,-6.84),"Marrakech":(31.63,-7.98),
 "Agadir":(30.42,-9.60),"ElAaiun":(27.15,-13.20),"Nouakchott":(18.09,-15.98),
 "Honolulu":(21.31,-157.86),"Anchorage":(61.22,-149.90),"Vancouver":(49.28,-123.12),
 "Seattle":(47.61,-122.33),"SanFrancisco":(37.77,-122.42),"LosAngeles":(34.05,-118.24),
 "MexicoCity":(19.43,-99.13),"Cancun":(21.16,-86.85),"Havana":(23.11,-82.37),"Miami":(25.76,-80.19),
 "NewYork":(40.71,-74.01),"Toronto":(43.65,-79.38),"Halifax":(44.65,-63.58),"StJohns":(47.56,-52.71),
 "Nuuk":(64.18,-51.69),"Reykjavik":(64.15,-21.94),"Lisbon":(38.72,-9.14),"Madrid":(40.42,-3.70),
 "London":(51.51,-0.13),"Paris":(48.86,2.35),"Berlin":(52.52,13.41),"Stockholm":(59.33,18.07),
 "Helsinki":(60.17,24.94),"Athens":(37.98,23.73),"Istanbul":(41.01,28.98),"Moscow":(55.76,37.62),
 "Dublin":(53.35,-6.26),"Galway":(53.27,-9.06),"Edinburgh":(55.95,-3.19),"Bergen":(60.39,5.32),
 "Oslo":(59.91,10.75),"Copenhagen":(55.68,12.57),"Amsterdam":(52.37,4.90),"Rome":(41.90,12.50),
 "Bucharest":(44.43,26.10),"Kyiv":(50.45,30.52),"StPetersburg":(59.93,30.36),"Tallinn":(59.44,24.75),
 "Tokyo":(35.68,139.69),"Sydney":(-33.87,151.21),"Singapore":(1.35,103.82),"Delhi":(28.61,77.21),
 "Dubai":(25.20,55.27),"CapeVerde":(16.60,-22.94),"Azores":(37.74,-25.67),"Bermuda":(32.29,-64.78),
}


def inverse(az_t, alt_t, topk=6):
    daz = np.abs((AZ - az_t + 180) % 360 - 180)
    dal = np.abs(ALT - alt_t)
    cost = daz + dal
    out = []
    C = cost.copy()
    for _ in range(topk):
        i, j = np.unravel_index(np.argmin(C), C.shape)
        la, lo = LA[i], LO[j]
        out.append((float(cost[i, j]), la, lo))
        C[max(0, i - 25):i + 26, max(0, j - 25):j + 26] = 1e9
    return out


for alt_t in (28.0, 30.0, 32.0, 33.4, 35.0, 37.0):
    for az_t in (297.0, 299.6, 302.0):
        best = inverse(az_t, alt_t, 3)[0]
        la, lo = best[1], best[2]
        near = min(CITY.items(), key=lambda kv: (kv[1][0] - la) ** 2 + ((kv[1][1] - lo) * math.cos(math.radians(la))) ** 2)
        dkm = 111.32 * math.hypot(near[1][0] - la, (near[1][1] - lo) * math.cos(math.radians(la)))
        a2, o2 = solar_vec(near[1][0], near[1][1])
        print(f"target az={az_t:6.1f} alt={alt_t:5.1f} -> best ({la:6.2f},{lo:8.2f}) cost={best[0]:5.2f}   "
              f"nearest {near[0]:14s} {dkm:6.0f} km  (its az={float(a2):6.1f} alt={float(o2):5.1f})")
