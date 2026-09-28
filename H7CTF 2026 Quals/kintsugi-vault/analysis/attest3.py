"""Last HTTP-contract candidates: multipart parsing, nonce-with-newline, field aliases."""
import os, sys, uuid, http.client, ssl

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

SEED = bytes.fromhex(open(os.path.join(HERE, 'seed.hex')).read().split()[0])
sk = Ed25519PrivateKey.from_private_bytes(SEED)
H = os.environ.get('HOST', 'web-d6403eb95a65eea4.web.h7tex.com')
ctx = ssl.create_default_context()


def conn():
    return http.client.HTTPSConnection(H, context=ctx, timeout=20)


def get_raw():
    """returns the response body exactly as sent, keeping any trailing newline"""
    c = conn()
    c.request('GET', '/attest')
    b = c.getresponse().read()
    c.close()
    return b


def post(form, ctype='application/x-www-form-urlencoded'):
    import urllib.parse
    body = urllib.parse.urlencode(form).encode()
    c = conn()
    c.request('POST', '/attest', body=body, headers={'Content-Type': ctype})
    r = c.getresponse()
    out = r.read().decode('utf-8', 'replace').strip()
    c.close()
    return r.status, out


def multipart(fields):
    b = uuid.uuid4().hex
    body = b''
    for k, v in fields.items():
        body += ('--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n' % (b, k, v)).encode()
    body += ('--%s--\r\n' % b).encode()
    c = conn()
    c.request('POST', '/attest', body=body,
              headers={'Content-Type': 'multipart/form-data; boundary=' + b})
    r = c.getresponse()
    out = r.read().decode('utf-8', 'replace').strip()
    c.close()
    return r.status, out


raw = get_raw()
print('[*] raw GET body =', repr(raw))
n_stripped = raw.decode().strip()
n_with_nl = raw.decode()
for tag, nonce in (('stripped', n_stripped), ('with-newline', n_with_nl)):
    for mtag, msg in (('raw', bytes.fromhex(n_stripped)), ('ascii', nonce.encode())):
        sig = sk.sign(msg).hex()
        print('  urlencoded %-13s msg=%-6s -> %s' % (tag, mtag, post({'nonce': nonce, 'sig': sig})))
        print('  multipart  %-13s msg=%-6s -> %s' % (tag, mtag, multipart({'nonce': nonce, 'sig': sig})))

sig = sk.sign(bytes.fromhex(n_stripped)).hex()
print('  alias signature ->', post({'nonce': n_stripped, 'signature': sig, 'sig': sig}))
print('  GET then POST via same conn, no strip, json ->', end=' ')
import json
c = conn()
c.request('GET', '/attest')
n = c.getresponse().read().decode()
c.request('POST', '/attest', json.dumps({'nonce': n.strip(), 'sig': sk.sign(bytes.fromhex(n.strip())).hex()}),
          {'Content-Type': 'application/json'})
r = c.getresponse()
print(r.status, r.read().decode().strip())
c.close()
