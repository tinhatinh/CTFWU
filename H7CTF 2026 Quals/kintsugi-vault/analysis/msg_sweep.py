"""Sweep the signed-message construction now that the required field set is known:
POST /attest wants `seed` (hex) + `sig` (hex); `nonce` is optional.
"""
import os, sys, http.client, ssl, urllib.parse, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

SEED = bytes.fromhex(open(os.path.join(HERE, 'seed.hex')).read().split()[0])
PUB = open(os.path.join(HERE, '..', 'files', 'pubkey.bin'), 'rb').read()
sk = Ed25519PrivateKey.from_private_bytes(SEED)
H = 'web-d6403eb95a65eea4.web.h7tex.com'
ctx = ssl.create_default_context()


def pair():
    c = http.client.HTTPSConnection(H, context=ctx, timeout=20)
    c.request('GET', '/attest')
    n = c.getresponse().read().decode().strip()
    return c, n


def post(c, form):
    c.request('POST', '/attest', urllib.parse.urlencode(form),
              {'Content-Type': 'application/x-www-form-urlencoded'})
    r = c.getresponse()
    b = r.read().decode().strip()
    return r.status, b


def sign(msg):
    return sk.sign(msg if isinstance(msg, bytes) else str(msg).encode()).hex()


def main():
    msgs = {
        'raw': lambda n: bytes.fromhex(n),
        'ascii': lambda n: n.encode(),
        'ascii_nl': lambda n: (n + '\n').encode(),
        'raw+seed': lambda n: bytes.fromhex(n) + SEED,
        'seed+raw': lambda n: SEED + bytes.fromhex(n),
        'ascii+seed': lambda n: n.encode() + SEED,
        'seed_only': lambda n: SEED,
        'pub+raw': lambda n: PUB + bytes.fromhex(n),
        'raw+pub': lambda n: bytes.fromhex(n) + PUB,
        'sha256raw': lambda n: hashlib.sha256(bytes.fromhex(n)).digest(),
        'sha512raw': lambda n: hashlib.sha512(bytes.fromhex(n)).digest(),
        'upper': lambda n: n.upper().encode(),
        'label_raw': lambda n: b'attest' + bytes.fromhex(n),
        'kint_raw': lambda n: b'kintsugi' + bytes.fromhex(n),
    }
    for name, f in msgs.items():
        for withnonce in (True, False):
            c, n = pair()
            form = {'seed': SEED.hex(), 'sig': sign(f(n))}
            if withnonce:
                form['nonce'] = n
            st, body = post(c, form)
            c.close()
            print('%-10s nonce=%-5s -> %s %r' % (name, withnonce, st, body[:70]))
            if st == 200:
                open(os.path.join(HERE, '..', 'flag.txt'), 'w').write(body + '\n')
                print('\n[+] FLAG:', body)
                return
    print('no variant accepted')


main()
