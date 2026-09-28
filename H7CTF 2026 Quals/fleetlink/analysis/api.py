import sys, time, hmac, hashlib, uuid, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import urllib.request

BASE = "https://web-198ec1caaeb6fd82.web.h7tex.com"
PEPPER = "fleetlink_signing_pepper_v3"
DEV = "flt-" + str(uuid.uuid4())


def call(path, params=None, method="GET", device=DEV):
    params = params or {}
    q = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    key = hashlib.sha256((PEPPER + ":" + device).encode()).digest()
    ts = str(int(time.time()))
    sts = "\n".join([method, path, q, ts])
    sig = hmac.new(key, sts.encode(), hashlib.sha256).hexdigest()
    url = BASE + path + (("?" + q) if q else "")
    req = urllib.request.Request(url, method=method, headers={
        "X-Device-Id": device, "X-Ts": ts, "X-Sig": sig,
    })
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


print("device", DEV)
if __name__ == "__main__":
    code, body = call("/api/v1/trips", {"scope": "mine"})
    print("scope=mine ->", code, body[:600])
    for s in ["fleet", "all", "dispatcher", "manifest", "admin", "driver", "others", "everything"]:
        code, body = call("/api/v1/trips", {"scope": s})
        print(f"scope={s:12s} ->", code, body[:300])
