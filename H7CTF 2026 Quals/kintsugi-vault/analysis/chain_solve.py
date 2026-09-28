"""Full chain solve: rebuild each chain shard's decode table, recover its 8-byte key,
then test every assembly of the four keys against the instance public key."""
import os, sys, struct, itertools

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vm, invert, glue
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding as E, PublicFormat as P

HERE = os.path.dirname(os.path.abspath(__file__))
PUB = open(os.path.join(HERE, '..', 'files', 'pubkey.bin'), 'rb').read()
CHAIN = ['f6f11ad133cab21c96e0185e3411ddc4', '080ec62d7daef51f2e635d17f9b8e075',
         '3e3a0fc9a5c28e964f9ba37bb499e742', 'cfa1fa34718c426f23e2318dfe8b330d']
REF = CHAIN[0]                       # its table is in the clear (flag bit0)
FAMILY = {0: 'HALT', 1: 'KEY', 3: 'MOV', 4: 'XOR', 10: 'LUT', 11: 'CMP', 12: 'ANDI', 13: 'XORI'}


def table_from_map(fwd, halt_raw, base_tbl):
    """fwd: raw->op for executed raws; complete it into a permutation."""
    out = [None] * 256
    used = set()
    for c, o in list(fwd.items()) + ([(halt_raw, 0)] if halt_raw is not None else []):
        out[c] = o
        used.add(o)
    pool = [x for x in range(256) if x not in used]
    k = 0
    for c in range(256):
        if out[c] is None:
            out[c] = pool[k]
            k += 1
    return out


EXPLICIT = {'cfa1fa34718c426f23e2318dfe8b330d': ({0xf7: 1, 0x79: 13, 0x4e: 12, 0xd6: 10,
                                                  0x4c: 4, 0xc1: 3, 0xbc: 11}, 0x44)}


def build(shname):
    """returns (table, info) for a chain shard: template transfer, else explicit map"""
    if shname in EXPLICIT:
        fwd, hraw = EXPLICIT[shname]
        return table_from_map(fwd, hraw, None), 'explicit'
    ref = vm.load(REF)
    rseq, st, ex = vm.dismap(ref)
    assert st == 'HALT', st
    tgt = vm.load(shname)
    fwd, bad = glue.try_template(rseq, tgt)
    halts = [pc for pc, o in rseq if o == 0]
    hraw = tgt['code'][halts[0]] if halts else None
    if bad:
        return None, bad
    # sanity: every executed raw must be one of the 8 family raws
    return table_from_map(fwd, hraw, tgt['tbl']), (fwd, hraw)


def keys_for(shname, table):
    sh = vm.load(shname)
    sh['tbl'] = list(table)
    seq, st, ex = vm.dismap(sh)
    if st == 'BADOP':
        return None, 'badop'
    know, keyreq, free, pend = invert.backwards(sh, seq)
    if pend:
        return None, 'pend=%d' % len(pend)
    base = bytes(keyreq.get(i, 0) for i in range(8))
    bits = {}
    for reg, i in free:
        bits.setdefault(reg, set()).add(i)
    spots = sorted(bits)
    sets = [sorted(bits[s]) for s in spots]
    n = sum(len(x) for x in sets)
    out = set()
    for mask in range(1 << n):
        k = bytearray(base)
        m = mask
        for si, s in enumerate(spots):
            for b in sets[si]:
                bit = m & 1
                m >>= 1
                k[s] = (k[s] & ~(1 << b)) | (bit << b)   # force both 0 and 1
        cand = bytes(k)
        v = vm.VM(sh['tbl'], sh['sbox'], sh['code'], cand)
        if v.run()[0] == 'HALT':
            out.add(cand)
    return out, 'free=%d' % n


if __name__ == '__main__':
    tables = {}
    for n in CHAIN:
        t, info = build(n)
        if t is None:
            print('%s  BUILD FAILED %s' % (n[:12], str(info)[:200]))
            continue
        ks, note = keys_for(n, t)
        print('%s  table ok  keys=%s (%s)' % (n[:12], len(ks) if ks else None, note))
        if ks:
            for k in sorted(ks)[:3]:
                print('     ', k.hex())
            tables[n] = (t, sorted(ks))
            open(os.path.join(HERE, 'chain_%s.table' % n[:8]), 'wb').write(bytes(t))

    if len(tables) == 4:
        print('\n=== assembling the 32-byte seed ===')
        names = list(tables)
        print('   candidate counts:', {n[:8]: len(tables[n][1]) for n in names})
        start, end = CHAIN[0], CHAIN[-1]           # MANIFEST start, nxt==0 shard is last
        mids = [n for n in names if n not in (start, end)]
        orders = [tuple([start] + list(p) + [end]) for p in itertools.permutations(mids)]
        allorders = list(itertools.permutations(names))
        tried = 0
        hit = []
        for tag, olist in (('chain', orders), ('all', allorders)):
            for perm in olist:
                for combo in itertools.product(*[tables[n][1] for n in perm]):
                    s = b''.join(combo)
                    tried += 1
                    try:
                        pk = Ed25519PrivateKey.from_private_bytes(s).public_key().public_bytes(
                            encoding=E.Raw, format=P.Raw)
                    except Exception:
                        continue
                    if pk == PUB:
                        print('*** SEED FOUND (%s) order' % tag, [n[:8] for n in perm], s.hex())
                        hit.append((perm, s))
                        open(os.path.join(HERE, 'seed.hex'), 'w').write(s.hex() + '\n')
            print('  phase %s done, tried %d, hits %d' % (tag, tried, len(hit)))
            if hit:
                break
