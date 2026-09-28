import json, ssl, urllib.request, urllib.error, re, itertools, sys
from concurrent.futures import ThreadPoolExecutor

BASE = "https://web-3f25599ac74e8a91.web.h7tex.com"
CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
CL = "MeridianPay-Android/3.2.1 (attested)"

def raw(p, m="GET", b=None, t=None, h=None):
    hh = {"Content-Type": "application/json", "X-Meridian-Client": CL}
    if t: hh["Authorization"] = "Bearer " + t
    if h: hh.update(h)
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE+p, data=d, method=m, headers=hh)
    try:
        with urllib.request.urlopen(r, context=CTX, timeout=8) as f: return f.status, f.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e: return e.code, e.read().decode("utf-8","replace")
    except Exception as e: return None, repr(e)

_, t = raw("/api/v1/auth/device","POST",{"device_id":"wide"})
T = json.loads(t)["token"]

NOUN = """promo promotions internal admin accounts account receipts receipt files file export exports share shared
keystore keychain prefs preferences storage provider content provider intent intents deeplink links link open router
webview web apps app mobile client clients attestation attest attested device devices session sessions token tokens jwt
auth login logout refresh revoke introspect session_token
loyalty enroll enrolment enrollment claim redeem coupon voucher points bonus referral referrals campaign campaigns offers offer
ledger journal transactions transaction transfers transfer payments payment balance balances statement statements invoice
profile profiles users me identity kyc verify onboarding welcome seed seeds init bootstrap
config settings debug dev console wsgi env environ metrics stats health healthz ping status version info
flag flags secret secrets keys keyset master corporate executive cfo ceo staff support auditor compliance risk fraud
webhooks webhook callback notify events event feed audit logs log trail activity
cards card wallet wallets iban swift routing number account_number pdf csv xlsx report reports document documents attachment
manifest apk apk_version app_version upgrade update version_check compatibility
vault kms envelope dek kek rotation rotate master_key masterkey signing signature signed sign
jwks well-known openid swagger openapi api-docs routes url-map map sitemap robots humans favicon static assets public private
search query lookup resolve validate validation check status_check device_check session_check
phone email address country dob ssn tax_id national_id
notes note memo memos annotations tags
premium tier tiers plan plans subscription subscriptions entitlements features
sandbox staging test preview draft
""".split()
TAIL = ["", "/me", "/1", "/1001", "/1002", "/current", "/flag", "/flags", "/export", "/all", "/latest",
        "/internal", "/public", "/raw", "/full", "/summary", "/list", "/get", "/data", "/key", "/keys",
        "/secret", "/secrets", "/admin", "/debug", "/status", "/check", "/verify", "/attest", "/token",
        "/session", "/device", "/receipt", "/receipts", "/ledger", "/master", "/rotate", "/0", "-8827"]

paths = set()
STAGE = sys.argv[1] if len(sys.argv) > 1 else "1"
if STAGE == "1":
    for pre in ["/", "/api/", "/api/v1/", "/api/v1/internal/", "/api/v1/admin/", "/api/v1/auth/",
                "/api/v1/accounts/", "/api/v1/promo/", "/v1/", "/internal/", "/admin/", "/mobile/",
                "/api/v1/mobile/", "/api/v1/system/", "/api/v1/corporate/"]:
        for n in NOUN:
            paths.add(pre+n)
else:
    for pre in ["/", "/api/v1/", "/api/v1/internal/", "/api/v1/admin/", "/api/v1/accounts/",
                "/api/v1/auth/", "/api/v1/promo/", "/api/v1/ledger/"]:
        for n in NOUN:
            for tl in TAIL:
                paths.add(pre+n+tl)
paths = sorted(paths)
print("paths:", len(paths), flush=True)

hits = []
def work(p):
    c, b = raw(p, "GET", None, T)
    if c and c != 404 and "404 Not Found" not in b:
        return (p, c, b[:220])
    return None

with ThreadPoolExecutor(max_workers=18) as ex:
    for i, r in enumerate(ex.map(work, paths)):
        if r:
            print("HIT", r, flush=True); hits.append(r)
        if i % 2000 == 0: print("...progress", i, flush=True)
json.dump(hits, open("wide_hits.json","w"), indent=1)
print("TOTAL HITS", len(hits))

print("\n===== method matrix on known routes =====")
for p in ["/", "/api/v1/auth/device", "/api/v1/promo/public", "/api/v1/internal/promo",
          "/api/v1/profile", "/api/v1/admin/ledger", "/api/v1/accounts/me"]:
    for m in ["GET","POST","PUT","PATCH","DELETE","HEAD","OPTIONS","TRACE","COPY","MKCOL","PROPFIND"]:
        c, b = raw(p, m, {} if m in ("POST","PUT","PATCH") else None, T)
        if c in (405,) and "Allow" in b:
            pass
    # single OPTIONS reveals Allow
    c, b = raw(p, "OPTIONS", None, T)
    al = re.search(r"Allow: ([^\n<]*)", b)
    print(f"  {p:28s} OPTIONS={c} allow={al.group(1) if al else '?'}")
