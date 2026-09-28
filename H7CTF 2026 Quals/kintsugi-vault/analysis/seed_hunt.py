"""Test candidate 32-byte seeds against the instance Ed25519 public key."""
import os, sys, struct, itertools, hashlib, glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vm
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding as _Enc, PublicFormat as _PF

HERE = os.path.dirname(os.path.abspath(__file__))
PUB = open(os.path.join(HERE, '..', 'files', 'pubkey.bin'), 'rb').read()
print('pubkey.bin =', PUB.hex())


def matches(seed):
    try:
        sk = Ed25519PrivateKey.from_private_bytes(seed)
        return sk.public_key().public_bytes(
            encoding=_Enc.Raw, format=_PF.Raw) == PUB
    except Exception:
        return False


def u32le(vals):
    return b''.join(struct.pack('<I', v) for v in vals)


cands = {}
regs = {}
for n in vm.ALL:
    sh = vm.load(n)
    regs[n] = sh
    seq, st, ex = vm.dismap(sh)
    tag = n[:12]
    cands[tag + '|id+nxt'] = sh['tid'] + sh['nxt']
    cands[tag + '|sbox0:32'] = sh['sbox'][0:32]
    cands[tag + '|hdr0:32'] = sh['raw'][0:32]
    cands[tag + '|hdr18:50'] = sh['raw'][0x12:0x32]
    if st == 'BADOP':
        continue
    xori = [struct.unpack_from('<I', sh['code'], p + 2)[0] for p, o in seq if o == 13]
    cmpi = [struct.unpack_from('<I', sh['code'], p + 2)[0] for p, o in seq if o == 11]
    andi = [struct.unpack_from('<I', sh['code'], p + 2)[0] for p, o in seq if o == 12]
    if len(xori) >= 8:
        cands[tag + '|xori8le'] = u32le(xori[:8])
        cands[tag + '|xori8be'] = b''.join(struct.pack('>I', v) for v in xori[:8])
    if len(xori) == 8:
        cands[tag + '|xoriALLle'] = u32le(xori)
    cands[tag + '|cmp8le'] = u32le(cmpi[:8])
    cands[tag + '|cmp_lowbyte'] = bytes(v & 0xFF for v in cmpi[:8])
    cands[tag + '|andixor'] = u32le(andi[:8]) if len(andi) >= 8 else b''
    # f6f1 style: byte-sized XORI immediates grouped by 8
    by = bytes(v & 0xFF for v in xori)
    for k in range(0, len(by) - 31, 8):
        cands['%s|xoribytes@%d' % (tag, k)] = by[k:k + 32]

# 8-byte pieces across the four readable shards, all orders
pieces = {}
for n in vm.ALL:
    if n not in regs or regs[n]['flag'] is None:
        continue
    seq, st, ex = vm.dismap(regs[n])
    if st == 'BADOP':
        continue
    cmpi = [struct.unpack_from('<I', regs[n]['code'], p + 2)[0] for p, o in seq if o == 11]
    xori = [struct.unpack_from('<I', regs[n]['code'], p + 2)[0] for p, o in seq if o == 13]
    pieces[n[:12]] = bytes(v & 0xFF for v in cmpi[:8])
    pieces[n[:12] + '_x'] = u32le(xori[:8]) if len(xori) == 8 else b'.' * 8

print('\n--- single-field candidates ---')
hit = []
for k, v in list(cands.items()):
    if len(v) == 32 and matches(v):
        print('  *** MATCH', k, v.hex())
        hit.append(k)
print('  tested', len(cands))

print('\n--- 8-byte piece permutations (cmp low bytes and xori blocks) ---')
names = [k for k in pieces if not k.endswith('_x')]
xs = [k for k in pieces if k.endswith('_x')]
sets = [(names, 'cmpbytes'), ([k + '_x' for k in names], 'xori')]
for keys, lbl in sets:
    vals = [pieces[k] for k in keys]
    if any(len(v) != 8 for v in vals):
        continue
    for perm in itertools.permutations(range(len(vals))):
        s = b''.join(vals[i] for i in perm)
        if matches(s):
            print('  *** MATCH order %s (%s): %s' % (
                [keys[i] for i in perm], lbl, s.hex()))
print('  done')
