import os, sys, json, urllib.request, urllib.parse, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding as E, PublicFormat as P

HOST = 'https://web-d6403eb95a65eea4.web.h7tex.com'
SEED = bytes.fromhex(open(os.path.join(HERE, 'seed.hex')).read().split()[0])
PUB = open(os.path.join(HERE, '..', 'files', 'pubkey.bin'), 'rb').read()
sk = Ed25519PrivateKey.from_private_bytes(SEED)


def req(method, path, form=None):
    url = HOST + path
    data = urllib.parse.urlencode(form).encode() if form else None
    r = urllib.request.Request(url, data=data, method=method,
                               headers={'Content-Type': 'application/x-www-form-urlencoded'}
                               if form else {})
    try:
        with urllib.request.urlopen(r, timeout=25) as f:
            return f.status, f.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except Exception as ex:
        return -1, repr(ex)


# local sanity: is our signature verifiable under the handout pubkey?
msg = bytes.fromhex('00' * 24)
s = sk.sign(msg)
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
Ed25519PublicKey.from_public_bytes(PUB).verify(s, msg)
print('[ok] self-verify under pubkey.bin works for a test message (sig len %d)' % len(s))

variants = [
    ('missing sig', {'nonce': 'aa' * 24}),
    ('missing nonce', {'sig': 'bb' * 64}),
    ('short sig', {'nonce': 'aa' * 24, 'sig': 'cc' * 32}),
    ('empty', {}),
]
for label, form in variants:
    print('  %-14s -> %s' % (label, req('POST', '/attest', form)))

for label, mode in (('raw24', 'raw'), ('hexascii48', 'ascii'),
                    ('sha512ofnonce', 'h'), ('nonce+pubkey', 'np')):
    st, nonce = req('GET', '/attest')
    nonce = nonce.strip()
    if mode == 'raw':
        m = bytes.fromhex(nonce)
    elif mode == 'ascii':
        m = nonce.encode()
    elif mode == 'h':
        import hashlib
        m = hashlib.sha512(bytes.fromhex(nonce)).digest()
    else:
        m = bytes.fromhex(nonce) + PUB
    st2, body = req('POST', '/attest', {'nonce': nonce, 'sig': sk.sign(m).hex()})
    print('  %-14s nonce=%s -> %s %r' % (label, nonce[:12], st2, body.strip()))

st, nonce = req('GET', '/attest')
nonce = nonce.strip()
sig = sk.sign(bytes.fromhex(nonce))
for enc, val in (('hex', sig.hex()), ('hex-upper', sig.hex().upper()),
                 ('base64', __import__('base64').b64encode(sig).decode())):
    st2, body = req('POST', '/attest', {'nonce': nonce, 'sig': val}) if enc != 'hex' else (400, '(already tried)')
    print('  enc %-10s -> %s %r' % (enc, st2, str(body).strip()[:60]))
