import sys, time, hmac, hashlib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import urllib.request, urllib.error

BASE = "https://web-198ec1caaeb6fd82.web.h7tex.com"
PEPPER = "fleetlink_signing_pepper_v3"
DEV = "flt-c401c0de-0000-0000-0000-000000000000"


def raw(method="GET", path="/api/v1/trips", q="scope=mine", ts=None, sig=None, key_dev=DEV, headers=None):
    ts = ts or str(int(time.time()))
    k = hashlib.sha256((PEPPER + ":" + key_dev).encode()).digest()
    if sig is None:
        sig = hmac.new(k, "\n".join([method, path, q, ts]).encode(), hashlib.sha256).hexdigest()
    url = BASE + path + (("?" + q) if q is not None else "")
    h = {"X-Device-Id": key_dev, "X-Ts": ts, "X-Sig": sig}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return "ERR", str(e)


print("baseline      ", raw()[0], raw()[1][:150])
print("bad sig       ", raw(sig="00" * 32))
print("stale ts      ", raw(ts="1000000000"))
print("no ts header  ", raw(sig="00" * 32, headers={"X-Ts": ""}))
print("POST          ", raw(method="POST", q=""))
print("HEAD          ", raw(method="HEAD"))

words = ["trips", "manifest", "fleet", "fleets", "dispatch", "dispatcher", "admin", "flag",
         "debug", "internal", "v1", "api", "all", "drivers", "driver", "route", "routes",
         "pod", "delivery", "deliveries", "sign", "signed", "seal", "proof", "scope", "role"]
prefixes = ["/api/v1/", "/api/", "/v1/", "/", "/internal/", "/api/v2/"]
seen = {}
for pre in prefixes:
    for w in words:
        p = pre + w
        c, b = raw(path=p, q="")
        tag = "HIT" if c != 404 else "."
        if c != 404:
            print(f"{tag} {p:34s} {c} {b[:160]}")
        seen[c] = seen.get(c, 0) + 1
print("status histogram:", seen)
