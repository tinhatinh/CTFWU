import sys, time, hmac, hashlib, urllib.request, urllib.error
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://web-198ec1caaeb6fd82.web.h7tex.com"
PEPPER = "fleetlink_signing_pepper_v3"


def sign(method, path, q, ts, device):
    k = hashlib.sha256((PEPPER + ":" + device).encode()).digest()
    return hmac.new(k, "\n".join([method, path, q, ts]).encode(), hashlib.sha256).hexdigest()


def go(headers, path="/api/v1/trips", q=""):
    r = urllib.request.Request(BASE + path + (("?" + q) if q else ""), method="GET", headers=headers)
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return "ERR", str(e)[:120]


def hdr(device, ts=None, sig=None, q="", path="/api/v1/trips"):
    ts = ts or str(int(time.time()))
    h = {"X-Device-Id": device, "X-Ts": ts}
    h["X-Sig"] = sig if sig is not None else sign("GET", path, q, ts, device)
    return h


DEV = "flt-11111111-2222-3333-4444-555555555555"
print("== registry oracle: BAD signature, different device ids")
for d in [DEV, "flt-dispatcher", "dispatcher", "unknown-device", "", "flt-" + "0" * 32]:
    print(f"  {d!r:45s} badsig -> {go(hdr(d, sig='aa' * 32))}")
    time.sleep(0.12)

print("== header presence / format")
print("  no device     ->", go({"X-Ts": str(int(time.time())), "X-Sig": "aa" * 32}))
print("  good sig, wrong key-dev? device duplicated ->", go(hdr(DEV, sig=None, q="")))
print("  two X-Device-Id (list) ->", go({"X-Device-Id": [DEV, "flt-dispatcher"], "X-Ts": str(int(time.time())), "X-Sig": "aa" * 32}))
time.sleep(0.1)
print("  empty query path only ->", go(hdr(DEV, q=""), path="/api/v1/trips", q=""))
print("  ?scope= (empty) ->", go(hdr(DEV, q="scope="), q="scope="))
for q in ["scope=mine", "scope=fleet", "scope=all", "scope=dispatcher", "scope=manifest", "scope=*",
          "scope=__all__", "scope=fleet_manifest", "scope=dispatch", "scope=everyone", "scope=flag"]:
    print(f"  {q:22s} -> ", go(hdr(DEV, q=q), q=q))
    time.sleep(0.1)
