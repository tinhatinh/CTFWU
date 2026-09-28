"""Attest over ONE keep-alive connection (gunicorn workers may not share nonce state)."""
import os, sys, json, http.client, ssl, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

SEED = bytes.fromhex(open(os.path.join(HERE, 'seed.hex')).read().split()[0])
sk = Ed25519PrivateKey.from_private_bytes(SEED)
HOST = 'web-d6403eb95a65eea4.web.h7tex.com'
ctx = ssl.create_default_context()


def attempt(ctype, fields, msg_mode, tag):
    c = http.client.HTTPSConnection(HOST, context=ctx, timeout=25)
    c.request('GET', '/attest')
    r = c.getresponse()
    nonce = r.read().decode().strip()
    m = bytes.fromhex(nonce) if msg_mode == 'raw' else nonce.encode()
    sig = sk.sign(m).hex()
    if ctype == 'application/json':
        body = json.dumps({**fields, 'nonce': nonce, 'sig': sig})
    else:
        body = '&'.join(['nonce=' + nonce, 'sig=' + sig] +
                        ['%s=%s' % kv for kv in fields.items()])
    c.request('POST', '/attest', body=body, headers={'Content-Type': ctype})
    r2 = c.getresponse()
    out = r2.read().decode().strip()
    c.close()
    print('%-34s -> %s %r' % (tag, r2.status, out[:90]))
    return r2.status, out


for msg_mode in ('raw', 'ascii'):
    for ctype in ('application/x-www-form-urlencoded', 'application/json'):
        attempt(ctype, {}, msg_mode, 'keepalive %s %s' % (ctype.split('/')[1], msg_mode))
st, out = attempt('application/x-www-form-urlencoded', {'seed': SEED.hex()}, 'raw',
                  'extra seed field')
if 'H7' not in out:
    # same connection, several POSTs with the same nonce (worker-state probe)
    c = http.client.HTTPSConnection(HOST, context=ctx, timeout=25)
    c.request('GET', '/attest')
    nonce = c.getresponse().read().decode().strip()
    sig = sk.sign(bytes.fromhex(nonce)).hex()
    for i in range(6):
        c.request('POST', '/attest', 'nonce=%s&sig=%s' % (nonce, sig),
                  {'Content-Type': 'application/x-www-form-urlencoded'})
        r = c.getresponse()
        b = r.read().decode().strip()
        print('  retry %d -> %s %r' % (i, r.status, b[:70]))
        if r.status == 200:
            break
        time.sleep(0.4)
    c.close()
if 'H7' in out:
    open(os.path.join(HERE, 'flag.txt'), 'w').write(out + '\n')
