"""Decisive test: is the nonce store per-worker/per-replica?

Issue ONE nonce, then submit the same (nonce, valid signature) many times.  If any
backend replica holds that nonce, that POST must behave differently (flag, or at least
a different message).  Also measures latency so a 'reached the crypto' path can be
told apart from a 'failed the lookup' path.
"""
import os, sys, time, statistics, urllib.parse, http.client, ssl

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature

SEED = bytes.fromhex(open(os.path.join(HERE, 'seed.hex')).read().split()[0])
sk = Ed25519PrivateKey.from_private_bytes(SEED)
H = os.environ.get('HOST', 'web-d6403eb95a65eea4.web.h7tex.com')
ctx = ssl.create_default_context()
N = int(os.environ.get('N', '120'))


def newconn():
    return http.client.HTTPSConnection(H, context=ctx, timeout=15)


def timed(fn):
    t0 = time.perf_counter()
    r = fn()
    return r, (time.perf_counter() - t0) * 1000


c = newconn()
c.request('GET', '/attest')
nonce = c.getresponse().read().decode().strip()
sig = sk.sign(bytes.fromhex(nonce)).hex()
print('[*] single nonce =', nonce)
print('[*] sig          =', sig[:32], '...')

codes = {}
lat = []
for i in range(N):
    def go():
        c.request('POST', '/attest', urllib.parse.urlencode({'nonce': nonce, 'sig': sig}),
                  {'Content-Type': 'application/x-www-form-urlencoded'})
        r = c.getresponse()
        return r.status, r.read().decode('utf-8', 'replace').strip()
    (st, body), ms = timed(go)
    lat.append(ms)
    key = (st, body[:40])
    if key not in codes:
        codes[key] = [0, i, ms]
    codes[key][0] += 1
    if st == 200:
        print('[+] ACCEPTED at attempt', i, body)
        open(os.path.join(HERE, '..', 'flag.txt'), 'w').write(body + '\n')
        sys.exit(0)
    if i % 20 == 19:
        time.sleep(0.2)
    if i % 30 == 29:                     # keep the connection warm but re-issue a nonce too
        pass
print('[*] distinct responses:')
for (st, body), (cnt, first, ms) in codes.items():
    print('    %s %r  x%d (first at #%d, %.1fms)' % (st, body, cnt, first, ms))
print('[*] latency ms: median %.2f  mean %.2f  min %.2f  max %.2f  stdev %.2f' % (
    statistics.median(lat), statistics.mean(lat), min(lat), max(lat), statistics.stdev(lat)))

# latency baseline: fabricated nonce (lookup must fail) vs real nonce
def sample(make, n=25):
    out = []
    for _ in range(n):
        nn = '00' * 24 if make == 'fake' else nonce
        s = sk.sign(bytes.fromhex(nn)).hex()
        (_, _), ms = timed(lambda: (c.request('POST', '/attest',
                        urllib.parse.urlencode({'nonce': nn, 'sig': s}),
                        {'Content-Type': 'application/x-www-form-urlencoded'}),
                        c.getresponse().read()))
        out.append(ms)
    return out


a = sample('real')
b = sample('fake')
print('[*] real-nonce  median %.2f ms' % statistics.median(a))
print('[*] fake-nonce  median %.2f ms' % statistics.median(b))
c.close()
