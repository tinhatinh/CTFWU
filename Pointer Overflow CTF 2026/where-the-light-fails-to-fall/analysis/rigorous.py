"""Rigorous single-view solve: ground plane from horizon+f, shadow direction from its VP,
sun altitude from the crown and its shadow tip.  Sweeps plausible (horizon, focal)."""
import math
import json
from datetime import datetime, timezone
import numpy as np
from scipy.optimize import least_squares

OBS = datetime(2026, 6, 20, 17, 55, tzinfo=timezone.utc)

FEET = np.array([1290.0, 2705.0])
TIP = np.array([2200.0, 1780.0])
CROWN = np.array([1075.0, 1700.0])
NL1, NL2 = np.array([544.0, 3103.0]), np.array([2386.0, 3864.0])
CX, CY = 1500.0, 2000.0


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


def line_to_horizon(p1, p2, yh):
    d = p2 - p1
    t = (yh - p1[1]) / d[1]
    return p1 + t * d


def solve(f, yh):
    tau = math.atan2(CY - yh, f)                       # depression angle
    ct, st = math.cos(tau), math.sin(tau)
    # camera axes in world (X east-ish, Y north-ish, Z up); forward = +Y
    Xc = np.array([1.0, 0, 0])
    Yc = np.array([0, -st, -ct])
    Zc = np.array([0, ct, -st])
    hc = 1.0                                            # arbitrary ground unit
    C = np.array([0.0, 0, hc])

    def ground(img):
        v = img[1]
        if v <= yh:
            return None
        zc = f * hc / ((v - yh) * ct)
        xc = (img[0] - CX) / f * zc
        Y = (zc - hc * st) / ct
        return np.array([xc, Y, 0.0])

    def raydir(img):
        u = (img[0] - CX) / f
        v = (img[1] - CY) / f
        return u * Xc + v * Yc + Zc

    T3 = ground(TIP)
    if T3 is None:
        return None
    VS = line_to_horizon(FEET, TIP, yh)
    s_cam = np.array([(VS[0] - CX) / f, (VS[1] - CY) / f, 1.0])
    s_w = s_cam[0] * Xc + s_cam[1] * Yc + s_cam[2] * Zc
    s_w[2] = 0.0
    n = np.linalg.norm(s_w)
    if n == 0:
        return None
    shat = s_w / n

    VN = line_to_horizon(NL1, NL2, yh)
    nc = np.array([(VN[0] - CX) / f, (VN[1] - CY) / f, 1.0])
    nw = nc[0] * Xc + nc[1] * Yc + nc[2] * Zc
    nw[2] = 0.0
    nn = np.linalg.norm(nw)
    if nn == 0:
        return None
    nhat = nw / nn
    ehat = np.array([nhat[1], -nhat[0], 0.0])

    r = raydir(CROWN)
    up = np.array([0.0, 0, 1.0])

    def res(x):
        mu, alt_r, t = x[0], x[1], x[2]
        crown = T3 + mu * (-math.cos(alt_r) * shat + math.sin(alt_r) * up)
        return crown - (C + t * r)

    best = None
    for mu0 in (0.2, 0.6, 1.5, 4.0):
        for a0 in (0.2, 0.5, 0.9):
            try:
                s = least_squares(res, [mu0, a0, 2.0], method="lm", max_nfev=4000)
                if best is None or s.cost < best.cost:
                    best = s
            except Exception:
                pass
    mu, alt_r, t = best.x
    alt = math.degrees(alt_r)
    bearing = math.degrees(math.atan2(shat @ ehat, shat @ nhat)) % 360
    az = (bearing + 180) % 360
    return az, alt, math.degrees(math.atan2((shat @ ehat), (shat @ nhat))) % 360, best.cost


d = json.load(open(r"C:\Users\Administrator\AppData\Local\Temp\ne_places.json", encoding="utf-8"))
CITY = []
for fo in d["features"]:
    p = fo["properties"]
    pop = float(p.get("pop_max") or 0)
    if pop < 800000:
        continue
    lon, lat = fo["geometry"]["coordinates"][0], fo["geometry"]["coordinates"][1]
    CITY.append(((p.get("name") or "?").strip(), p.get("adm0name", "?"), lat, lon, pop, *solar(lat, lon)))
print("cities >= 800k:", len(CITY))

print(f"{'f':>6} {'yh':>7} {'tau':>6} | {'az':>7} {'alt':>6} | best matching city (resid)")
for f in (2200, 2600, 2900, 3400, 4000, 5000):
    for yh in (-4000, -2500, -1500, -800, -300, 0, 200):
        if CY - yh <= 0:
            continue
        out = solve(f, yh)
        if not out:
            continue
        az, alt, brg, cost = out
        if cost > 1e-4 or not (0 < alt < 89):
            continue
        sc = sorted(CITY, key=lambda c: abs((c[5] - az + 180) % 360 - 180) + abs(c[6] - alt))
        b = sc[0]
        r0 = abs((b[5] - az + 180) % 360 - 180) + abs(b[6] - alt)
        tau = math.degrees(math.atan2(CY - yh, f))
        print(f"{f:6d} {yh:7d} {tau:6.1f} | {az:7.1f} {alt:6.1f} | {b[0]:18s} {b[1]:14s} "
              f"az={b[5]:6.1f} alt={b[6]:5.1f} resid={r0:5.1f} pop={b[4]/1e6:4.1f}M  2nd={sc[1][0]}({abs((sc[1][5]-az+180)%360-180)+abs(sc[1][6]-alt):5.1f})")
