import glob, os, itertools, struct

files = sorted(glob.glob(os.path.join(os.path.dirname(__file__), '..', 'files', '*.shard')))
S = {os.path.basename(f)[:-6]: open(f, 'rb').read() for f in files}
START = 'f6f11ad133cab21c96e0185e3411ddc4'

def T(d): return d[0x32:0x132]
def B(d): return d[0x132:0x232]

def isperm(a): return len(set(a)) == 256 and max(a) == 255 and min(a) == 0
def opsdist(a):
    from collections import Counter
    c = Counter(a)
    return 'lo0..13=%d distinct=%d' % (sum(v for k, v in c.items() if k <= 13), len(c))

xor = lambda x, y: bytes(a ^ b for a, b in zip(x, y))
add = lambda x, y: bytes((a + b) & 0xFF for a, b in zip(x, y))
sub = lambda x, y: bytes((a - b) & 0xFF for a, b in zip(x, y))

print('start: isperm=%s  %s' % (isperm(T(S[START])), opsdist(T(S[START]))))
print('start sbox: isperm=%s' % isperm(B(S[START])))

names = [n for n in S if n != START]
print('\n=== battery: which transform of a NON-start in-file table yields a valid permutation? ===')
cands = {}
for n in names:
    d = S[n]
    res = {
        'raw': T(d),
        'xor_start': xor(T(d), T(S[START])),
        'xor_sbox_self': xor(T(d), B(d)),
        'xor_sbox_start': xor(T(d), B(S[START])),
        'sub_start': sub(T(d), T(S[START])),
        'add_start': add(T(d), T(S[START])),
        'xor_self_sbox_rev': xor(T(d), B(d)[::-1]),
        'rev': T(d)[::-1],
    }
    good = [k for k, v in res.items() if isperm(v)]
    print('%s  rawperm=%-5s perms_when: %s' % (n[:12], isperm(res['raw']), good or '-'))

print('\n=== pairwise chained XOR among non-start tables (enc_j ^ enc_k) perm? ===')
hit = 0
for a, b in itertools.permutations(names, 2):
    if isperm(xor(T(S[a]), T(S[b]))):
        print('  %s ^ %s -> perm' % (a[:8], b[:8])); hit += 1
print('  hits=%d of %d' % (hit, len(names) * (len(names) - 1)))

print('\n=== does enc_j ^ start_table depend on shard (i.e. keystream shared)? ===')
xs = {n: xor(T(S[n]), T(S[START])) for n in names}
for a, b in itertools.combinations(names, 2):
    same = sum(1 for x, y in zip(xs[a], xs[b]) if x == y)
    if same > 40:
        print('  %s~%s equal bytes=%d' % (a[:8], b[:8], same))
print('  (nothing above = all pairs independent)')

print('\n=== overlap of value-multisets between tables ===')
from collections import Counter
cs = {n: Counter(T(S[n])) for n in S}
c0 = cs[START]
for n in names:
    inter = sum(min(c0[k], cs[n][k]) for k in set(c0) | set(cs[n]))
    print('  %s shares %d/256 value-instances with start table' % (n[:12], inter))

print('\n=== sbox as permutation: is sbox_j == sbox_start composed with something? ===')
for n in names:
    print('  %s sbox==start:%s  sbox==T:%s' % (n[:12], B(S[n]) == B(S[START]), B(S[n]) == T(S[n])))
