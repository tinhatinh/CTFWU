import os, sys, struct, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vm
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding as E, PublicFormat as P

HERE = os.path.dirname(os.path.abspath(__file__))
PUB = open(os.path.join(HERE, '..', 'files', 'pubkey.bin'), 'rb').read()

# byte-target pieces from the four "3-round" guardian programs
PC = {
 'f6f11ad1': bytes.fromhex('d13646ad8205299f'),   # table in the clear (chain start)
 '080ec62d': bytes.fromhex('71ac0250b51d4689'),   # table recovered by template transfer
 '3e3a0fc9': bytes.fromhex('42af8ab4650680fd'),   # table recovered by template transfer
 'cfa1fa34': bytes.fromhex('499c79d713c51892'),   # read directly, program shape == f6f1
}


def pub(seed):
    try:
        return Ed25519PrivateKey.from_private_bytes(seed).public_key().public_bytes(
            encoding=E.Raw, format=P.Raw)
    except Exception:
        return None


print('target pubkey:', PUB.hex())
found = []
for perm in itertools.permutations(PC):
    s = b''.join(PC[k] for k in perm)
    if pub(s) == PUB:
        print('*** MATCH order:', perm, s.hex())
        found.append((perm, s))
if not found:
    print('no plain concatenation matched; trying reversed pieces / byte order variants')
    for perm in itertools.permutations(PC):
        for rev_p in (False, True):
            for rev_s in (False, True):
                parts = [p[::-1] if rev_p else p for p in (PC[k] for k in perm)]
                s = b''.join(reversed(parts)) if rev_s else b''.join(parts)
                if pub(s) == PUB:
                    print('*** MATCH', perm, rev_p, rev_s, s.hex())
                    found.append((perm, rev_p, rev_s, s))
print('matches:', len(found))
for f in found:
    open(os.path.join(HERE, 'seed_candidate.hex'), 'w').write(f[-1].hex())
