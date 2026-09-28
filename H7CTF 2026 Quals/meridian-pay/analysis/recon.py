import base64, hashlib, hmac, itertools, json, sys, urllib.request, urllib.error, ssl, threading, queue

BASE = "https://web-3f25599ac74e8a91.web.h7tex.com"
CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
CLIENT = "MeridianPay-Android/3.2.1 (attested)"

def req(path, method="GET", body=None, hdrs=None):
    h = {"X-Meridian-Client": CLIENT, "Content-Type": "application/json"}
    if hdrs: h.update(hdrs)
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE+path, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(r, context=CTX, timeout=8) as f:
            return f.status, f.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8","replace")
    except Exception as e:
        return None, str(e)

code, tok = req("/api/v1/auth/device","POST",{"device_id":"and-recon"})
print("auth:", code, tok[:200])
tok = json.loads(tok)["token"]
print("token sub:", json.loads(base64.urlsafe_b64decode(tok.split(".")[1]+"==")))
AUTH = {"Authorization": "Bearer "+tok}

NAMES = """admin administrator dashboard management owner staff internal private debug dev test staging
flag flags secret secrets key keys token tokens session sessions auth authenticate login logout
user users account accounts profile customer member members customer_id
transfer transfers transaction transactions payment payments money balance balances statement statements
receipt receipts invoice invoices document documents file files export download upload attachment
promo promotions offer offers loyalty enroll enrollment campaign referral referrals
device devices attestation attest verify validation validate signature sign
search query report reports analytics stats status health ping version info metrics
webhook webhooks callback notify notification events event feed journal ledger audit
settings config configuration prefs preferences
card cards wallet wallets iban swift iban_lookup
support ticket tickets chat message messages inbox
v1 v2 v3 v4 obj objective objectives level levels stage stages part parts""".split()

PREFIXES = ["/api/v1/", "/api/", "/internal/", "/", "/api/v1/internal/", "/api/v1/admin/", "/v1/"]
found = []
lock = threading.Lock()
q = queue.Queue()
for p in PREFIXES:
    for n in NAMES:
        q.put(p+n)

def worker():
    while True:
        try: path = q.get_nowait()
        except queue.Empty: return
        for m in ("GET","POST"):
            code, body = req(path, m, {} if m=="POST" else None, AUTH)
            if code and code not in (404,):
                with lock:
                    found.append((m, path, code, body[:200]))
                    print(m, path, code, body[:180].replace("\n"," "))
            if m=="GET" and code in (405,): pass
        q.task_done()

ts=[threading.Thread(target=worker,daemon=True) for _ in range(12)]
[t.start() for t in ts]
q.join()
print("\nTOTAL", len(found))
