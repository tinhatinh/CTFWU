"""Bounded sweep of remaining plausible 'sig' constructions for POST /attest."""
import os, sys, hmac, hashlib, json, time, urllib.parse, http.client, ssl

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

SEED = bytes.fromhex(open(os.path.join(HERE, 'seed.hex')).read().split()[0])
PUB = open(os.path.join(HERE, '..', 'files', 'pubkey.bin'), 'rb').read()
sk = Ed25519PrivateKey.from_private_bytes(SEED)
H = os.environ.get('HOST', 'web-d6403eb95a65eea4.web.h7tex.com')
ctx = ssl.create_default_context()


def msgs(n):
    nb = bytes.fromhex(n)
    na = n.encode()
    d = {
        'raw': nb, 'ascii': na, 'ascii_nl': na + b'\n', 'raw_nl': nb + b'\n',
        'json': json.dumps({'nonce': n}).encode(),
        'json2': json.dumps({'nonce': n}, separators=(',', ':')).encode(),
        'lbl_attest': b'attest:' + na, 'lbl_kint': b'kintsugi:' + na,
        'lbl_space': b'kintsugi vault ' + na,
        'double': nb + nb, 'pub_raw': PUB + nb, 'raw_pub': nb + PUB,
        'sha256raw': hashlib.sha256(nb).digest(),
        'sha512raw32': hashlib.sha512(nb).digest()[:32],
        'sha256ascii': hashlib.sha256(na).digest(),
        'seed_raw': SEED + nb, 'raw_seed': nb + SEED,
        'nonce_upper': n.upper().encode(),
        'rev': nb[::-1],
    }
    return d


def sign_modes(n):
    """(label, hex-sig) pairs"""
    out = []
    for lbl, m in msgs(n).items():
        out.append(('ed25519/' + lbl, sk.sign(m).hex()))
    out.append(('hmac-sha256-seed/nonce', hmac.new(SEED, bytes.fromhex(n), hashlib.sha256).hexdigest()))
    out.append(('hmac-sha256-pub/nonce', hmac.new(PUB, bytes.fromhex(n), hashlib.sha256).hexdigest()))
    out.append(('sha256(seed+nonce)', hashlib.sha256(SEED + bytes.fromhex(n)).hexdigest()))
    out.append(('sha256(nonce+seed)', hashlib.sha256(bytes.fromhex(n) + SEED).hexdigest()))
    return out


def one(c, n, sig):
    c.request('POST', '/attest', urllib.parse.urlencode({'nonce': n, 'sig': sig}),
              {'Content-Type': 'application/x-www-form-urlencoded'})
    r = c.getresponse()
    return r.status, r.read().decode('utf-8', 'replace').strip()


seen = set()
c = http.client.HTTPSConnection(H, context=ctx, timeout=20)
for rnd in range(3):
    c.request('GET', '/attest')
    n = c.getresponse().read().decode().strip()
    for lbl, sig in sign_modes(n):
        st, body = one(c, n, sig)
        if body not in seen:
            print('  NEW RESPONSE %-24s -> %s %r' % (lbl, st, body[:70]))
            seen.add(body)
        if st == 200:
            print('[+] ACCEPTED', lbl, body)
            open(os.path.join(HERE, '..', 'flag.txt'), 'w').write(body + '\n')
            sys.exit(0)
    time.sleep(0.3)
c.close()
print('[*] %d constructions x 3 rounds, all identical: %r' % (len(sign_modes('00' * 24)), seen))
