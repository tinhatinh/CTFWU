import glob, os, itertools, hashlib

files = sorted(glob.glob(os.path.join(os.path.dirname(__file__), '..', 'files', '*.shard')))
S = {os.path.basename(f)[:-6]: open(f, 'rb').read() for f in files}
NAMES = list(S)
START = 'f6f11ad133cab21c96e0185e3411ddc4'
LAST = 'cfa1fa34718c426f23e2318dfe8b330d'

xid = {n: S[n][0x0E:0x1E] for n in NAMES}
nxt = {n: S[n][0x22:0x32] for n in NAMES}
crc = {n: S[n][0x1E:0x22] for n in NAMES}
sbox = {n: S[n][0x132:0x232] for n in NAMES}
tabl = {n: S[n][0x32:0x132] for n in NAMES}
code = {n: S[n][0x232:] for n in NAMES}
xor = lambda x, y: bytes(a ^ b for a, b in zip(x, y))

print('=== the 4-byte field at 0x1E and the 16-byte field at 0x22 ===')
for n in NAMES:
    print('%s crc=%s next=%s%s' % (n[:12], crc[n].hex(), nxt[n].hex(),
                                   '   <-- ALL ZERO' if nxt[n] == b'\0' * 16 else ''))

print('\n=== can next[A] be turned into id[B] by a simple A-local transform? ===')
def apply_sub(tbl, b):  # byte substitution through a 256-entry table
    return bytes(tbl[x] for x in b)
def apply_inv(tbl, b):
    inv = [0] * 256
    for i, v in enumerate(tbl):
        inv[v] = i
    return bytes(inv[x] for x in b)

found = []
for A in NAMES:
    for B in NAMES:
        if A == B:
            continue
        cands = {
            'xor_id': xor(nxt[A], xid[B]),
            'sub_sboxA': apply_sub(sbox[A], nxt[A]),
            'sub_tabA': apply_sub(tabl[A], nxt[A]),
            'inv_sboxA': apply_inv(sbox[A], nxt[A]),
            'sub_sboxB': apply_sub(sbox[B], nxt[A]),
            'reversed': nxt[A][::-1],
        }
        if cands['sub_sboxA'] == xid[B]:
            found.append((A, B, 'sub_sboxA'))
        if cands['sub_tabA'] == xid[B]:
            found.append((A, B, 'sub_tabA'))
        if cands['inv_sboxA'] == xid[B]:
            found.append((A, B, 'inv_sboxA'))
        if cands['sub_sboxB'] == xid[B]:
            found.append((A, B, 'sub_sboxB'))
        if cands['reversed'] == xid[B]:
            found.append((A, B, 'reversed'))
        if cands['xor_id'] == b'\0' * 16:
            found.append((A, B, 'xor_zero'))
print('  direct matches:', found or 'none')

print('\n=== is next[A] a hash of B (any region)? ===')
regions = lambda d: {
    'full': d, 'hdr': d[:0x32], 'table': d[0x32:0x132], 'sbox': d[0x132:0x232],
    'code': d[0x232:], 'tab+sbox': d[0x32:0x232], 'body': d[0x32:],
    'hdr-noid': d[:0x0E] + d[0x1E:], 'id': d[0x0E:0x1E],
}
hits = []
for A in NAMES:
    for B in NAMES:
        if A == B or nxt[A] == b'\0' * 16:
            continue
        for rn, blob in regions(S[B]).items():
            for algo in ('md5', 'sha1', 'sha256'):
                h = hashlib.new(algo, blob).digest()
                if h[:16] == nxt[A]:
                    hits.append((A[:8], B[:8], rn, algo))
                # also hash of A's own data with B's id etc later
print('  hash links:', hits or 'none')

print('\n=== distribution of next[] vs id[] as raw differences (fixed keystream?) ===')
for A in NAMES:
    if nxt[A] == b'\0' * 16:
        continue
    for B in NAMES:
        d = xor(nxt[A], xid[B])
        if min(d) < 8 and max(d) < 8:
            print('  next[%s] ^ id[%s] = small: %s' % (A[:8], B[:8], d.hex()))
print('  (none above = no near-miss)')

print('\n=== which tables are valid permutations, cross-checked with the 0x05 flag ===')
for n in NAMES:
    print('  %s flag=%02x perm_table=%s perm_sbox=%s' % (
        n[:12], S[n][5], len(set(tabl[n])) == 256, len(set(sbox[n])) == 256))

print('\n=== do the 3 invalid tables equal XOR of two valid ones, or valid[i]^const16 pattern? ===')
valid = [n for n in NAMES if len(set(tabl[n])) == 256]
invalid = [n for n in NAMES if len(set(tabl[n])) != 256]
print('  valid:', [v[:8] for v in valid], ' invalid:', [v[:8] for v in invalid])
for i in invalid:
    for a, b in itertools.combinations(valid, 2):
        if tabl[i] == xor(tabl[a], tabl[b]):
            print('  %s = %s ^ %s' % (i[:8], a[:8], b[:8]))
    # count bytes where tabl[i] agrees with any valid table
    best = max(valid, key=lambda v: sum(1 for x, y in zip(tabl[i], tabl[v]) if x == y))
    agree = sum(1 for x, y in zip(tabl[i], tabl[best]) if x == y)
    print('  %s best-agreement with %s = %d/256' % (i[:8], best[:8], agree))
