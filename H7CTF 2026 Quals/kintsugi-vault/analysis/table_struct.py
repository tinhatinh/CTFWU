import glob, os, itertools, hashlib, struct

files = sorted(glob.glob(os.path.join(os.path.dirname(__file__), '..', 'files', '*.shard')))
S = {os.path.basename(f)[:-6]: open(f, 'rb').read() for f in files}
NAMES = list(S)
tid = {n: S[n][0x0E:0x1E] for n in NAMES}
tbs = {n: S[n][0x22:0x32] for n in NAMES}
c4 = {n: S[n][0x1E:0x22] for n in NAMES}
T = {n: list(S[n][0x32:0x132]) for n in NAMES}
B = {n: list(S[n][0x132:0x232]) for n in NAMES}
CLR = [n for n in NAMES if len(set(T[n])) == 256]
ENC = [n for n in NAMES if len(set(T[n])) != 256]
print('clear-table shards :', [c[:8] for c in CLR])
print('scrambled shards   :', [c[:8] for c in ENC])

def inv(p):
    q = [0] * len(p)
    for i, v in enumerate(p):
        q[v] = i
    return q
def comp(p, q):  # (p o q)[x] = p[q[x]]
    return [p[q[x]] for x in range(len(q))]
def xorm(a, b):
    return [x ^ y for x, y in zip(a, b)]
def addm(a, b):
    return [(x + y) & 0xFF for x, y in zip(a, b)]
def subm(a, b):
    return [(x - y) & 0xFF for x, y in zip(a, b)]

print('\n=== is a clear table affine / structured on its own? ===')
for c in CLR:
    t = T[c]
    print('  %s  t[0]=%02x  diff[x]=t[x+1]^t[x] distinct=%d  t[x]^x distinct=%d' % (
        c[:8], t[0], len(set(t[i + 1] ^ t[i] for i in range(255))), len(set(t[i] ^ i for i in range(256)))))

print('\n=== invariance battery: does the same expression give an identical 256-byte result for all 4 clear shards? ===')
exprs = {
    'T': lambda n: T[n],
    'B': lambda n: B[n],
    'invT': lambda n: inv(T[n]),
    'invB': lambda n: inv(B[n]),
    'T^B': lambda n: xorm(T[n], B[n]),
    'T-B': lambda n: subm(T[n], B[n]),
    'T+B': lambda n: addm(T[n], B[n]),
    'invT^invB': lambda n: xorm(inv(T[n]), inv(B[n])),
    'T o B': lambda n: comp(T[n], B[n]),
    'B o T': lambda n: comp(B[n], T[n]),
    'invB o T': lambda n: comp(inv(B[n]), T[n]),
    'T o invB': lambda n: comp(T[n], inv(B[n])),
    'invT o B': lambda n: comp(inv(T[n]), B[n]),
    'invT o T': lambda n: comp(inv(T[n]), T[n]),
    'invT^B': lambda n: xorm(inv(T[n]), B[n]),
    'T o T': lambda n: comp(T[n], T[n]),
    'B o B': lambda n: comp(B[n], B[n]),
}
for name, fn in exprs.items():
    vals = [fn(n) for n in CLR]
    same = all(v == vals[0] for v in vals)
    eqT = vals[0] == T[CLR[0]]
    eqB = vals[0] == B[CLR[0]]
    if same or eqT or eqB:
        print('  *** %-12s identical across all clear shards=%s  ==T?%s ==B?%s' % (name, same, eqT, eqB))
print('  (only flagged lines shown)')

print('\n=== pair-invariance: T_a vs T_b expressible through B_a/B_b? ===')
for a, b in itertools.permutations(CLR, 2):
    # D such that T_b = D o T_a  (D = T_b o inv(T_a))
    D = comp(T[b], inv(T[a]))
    # E such that T_b = T_a o E  (E = inv(T_a) o T_b)
    E = comp(inv(T[a]), T[b])
    for lbl, Dv in (('D(val-map)', D), ('E(pos-map)', E)):
        for bn, bv in (('B_b', B[b]), ('invB_b', inv(B[b])), ('B_a', B[a]), ('invB_a', inv(B[a]))):
            if Dv == bv:
                print('  %s -> %s: %s == %s' % (a[:8], b[:8], lbl, bn))
        for bn, bv in (('B_b', B[b]), ('invB_b', inv(B[b]))):
            if comp(Dv, bv) == bv:
                pass
    # xor-difference
    d1 = xorm(T[a], T[b]); d2 = xorm(B[a], B[b])
    if d1 == d2:
        print('  %s,%s  T_a^T_b == B_a^B_b' % (a[:8], b[:8]))
print('  (done)')

print('\n=== how many fixed points / cycles does each clear table have (random perm signature)? ===')
for c in CLR:
    t = T[c]
    seen = [0] * 256
    cyc = []
    for i in range(256):
        if not seen[i]:
            n = 0; j = i
            while not seen[j]:
                seen[j] = 1; j = t[j]; n += 1
            cyc.append(n)
    print('  %s cycles=%d lengths=%s' % (c[:8], len(cyc), sorted(cyc)[:8]))

print('\n=== check whether the scrambled tables are permutations of the CLEAR one by value-only multiset ===')
for e in ENC:
    ms = sorted(T[e])
    for c in CLR:
        if ms == sorted(T[c]):
            print('  %s multiset == %s' % (e[:8], c[:8]))
    print('  %s value-range %d..%d  count<=13: %d' % (e[:8], min(ms), max(ms),
          sum(1 for x in T[e] if x <= 13)))

print('\n=== header field candidates as seeds: does sha256(id) or sha256(hdr) touch the table? ===')
for c in CLR:
    for src_name, src in (('id', tid[c]), ('hdr50', S[c][:0x32]), ('next', tbs[c]),
                          ('sbox', bytes(B[c])), ('id+sbox', tid[c] + bytes(B[c]))):
        h = hashlib.sha256(src).digest()
        if h[:4] == c4[c]:
            print('  %s: sha256(%s)[:4] == hdr[0x1E:0x22]' % (c[:8], src_name))
        if h[:16] == tbs[c]:
            print('  %s: sha256(%s)[:16] == hdr[0x22:0x32]' % (c[:8], src_name))
print('  (no output = no sha256 link)')
