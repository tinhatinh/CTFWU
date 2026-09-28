import os, sys, struct, itertools, glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding as E, PublicFormat as P

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = sorted(glob.glob(os.path.join(HERE, '..', 'files', '*')))
PUB = open(os.path.join(HERE, '..', 'files', 'pubkey.bin'), 'rb').read()
BASE = os.path.join(HERE, '..', 'files')


def pub(seed):
    try:
        return Ed25519PrivateKey.from_private_bytes(seed).public_key().public_bytes(
            encoding=E.Raw, format=P.Raw)
    except Exception:
        return None


def test(cand, label):
    if len(cand) != 32:
        return False
    if pub(cand) == PUB:
        print('  *** MATCH %s : %s' % (label, cand.hex()))
        open(os.path.join(HERE, 'seed_found.hex'), 'w').write(cand.hex() + '\n' + label)
        return True
    return False


print('phase 1: every 32-byte window of every handout file (+ reversed)')
n = 0
for f in FILES:
    if f.endswith('.py') or os.path.isdir(f):
        continue
    d = open(f, 'rb').read()
    if len(d) > 200000:
        continue
    for i in range(len(d) - 31):
        w = d[i:i + 32]
        n += 1
        if test(w, '%s@%d' % (os.path.basename(f), i)):
            pass
        if test(w[::-1], '%s@%d rev' % (os.path.basename(f), i)):
            pass
print('  windows tested:', n)

print('\nphase 2: ordered pairs of 16-byte fields, and 4-tuples of 8-byte fields')
import vm
F16 = {}
F8 = {}
for nm in vm.ALL:
    sh = vm.load(nm)
    F16[nm[:8] + '.id'] = sh['tid']
    F16[nm[:8] + '.nxt'] = sh['nxt']
    F8[nm[:8] + '.idhi'] = sh['tid'][:8]
    F8[nm[:8] + '.idlo'] = sh['tid'][8:]
    F8[nm[:8] + '.nexthi'] = sh['nxt'][:8]
    F8[nm[:8] + '.nextlo'] = sh['nxt'][8:]
    F8[nm[:8] + '.c4+pad'] = sh['raw'][0x1E:0x22] + b'\0' * 4
for a, b in itertools.permutations(F16, 2):
    test(F16[a] + F16[b], 'pair %s+%s' % (a, b))
    test(F16[b] + F16[a], 'pair %s+%s' % (b, a))
print('  pairs done (%d)' % (len(F16) * (len(F16) - 1)))

# byte-target pieces of the four 3-round shards, all 4! orders x per-piece reversal
pieces = {
 'f6f1': bytes.fromhex('d13646ad8205299f'),
 '080e': bytes.fromhex('71ac0250b51d4689'),
 '3e3a': bytes.fromhex('42af8ab4650680fd'),
 'cfa1': bytes.fromhex('499c79d713c51892'),
 '3df1': bytes.fromhex('460a330a492542ff'),
 '63ba': bytes.fromhex('7967d1b244919980'),
 'f14a': bytes.fromhex('e8bf880e46bddc47'),
}
print('\nphase 3: any 4 of the 7 target pieces, every order, each piece possibly reversed')
hits = 0
for combo in itertools.combinations(pieces, 4):
    for perm in itertools.permutations(combo):
        for mask in range(16):
            s = b''.join(pieces[k][::-1] if (mask >> i) & 1 else pieces[k]
                         for i, k in enumerate(perm))
            if test(s, 'pieces %s m%x' % (perm, mask)):
                hits += 1
print('  piece combos tested: %d, hits %d' % (len(list(itertools.combinations(pieces, 4))) * 24 * 16, hits))
