import glob, hashlib, os, struct

shards = {}
for f in sorted(glob.glob(os.path.join(os.path.dirname(__file__), '..', 'files', '*.shard'))):
    d = open(f, 'rb').read()
    shards[os.path.basename(f)[:-6]] = d

print('layout: 50 hdr + 256 table + 256 sbox + %d code = %d' % (
    len(next(iter(shards.values()))) - 50 - 512, len(next(iter(shards.values())))))

for name, d in shards.items():
    hdr = d[:0x32]
    ver, flg, b6, klen = hdr[4], hdr[5], hdr[6], hdr[7]
    tblen, codelen = struct.unpack_from('<HI', hdr, 8)
    ident = hdr[0x0E:0x1E]
    tail = hdr[0x1E:0x32]
    print('%s ver=%d flg=%02x b6=%02x klen=%d tblen=%#x codelen=%#x id=%s' % (
        name[:12], ver, flg, b6, klen, tblen, codelen, ident.hex()))
    print('    hdr[0x1E:0x32] = %s' % tail.hex(' '))
    # candidate digests over various regions
    regions = {
        'full': d,
        'skip_id': d[:0x0E] + d[0x1E:],
        'body': d[0x32:],
        'table+code': d[0x32:0x132] + d[0x232:],
        'code': d[0x232:],
        'hdr+tables+code': d[:0x32] + d[0x132:],
    }
    hits = []
    for rn, blob in regions.items():
        for algo in ('sha1', 'sha256', 'md5'):
            h = hashlib.new(algo, blob).digest()
            for L in (16, 20, 32):
                if h[:L] == ident:
                    hits.append('%s/%s[:%d]==id' % (rn, algo, L))
                if h[:L] == tail:
                    hits.append('%s/%s[:%d]==tail' % (rn, algo, L))
    print('    digest hits:', hits or 'none')

# link analysis: does any shard's tail contain another shard's id (or a transform)?
ids = {n: d[0x0E:0x1E] for n, d in shards.items()}
tails = {n: d[0x1E:0x32] for n, d in shards.items()}
print('\n--- cross references (tail bytes appearing in other headers/tables) ---')
for n, t in tails.items():
    for k in range(0, len(t) - 15):
        chunk = t[k:k + 16]
        for m, i in ids.items():
            if m != n and chunk == i:
                print('  %s tail[%d:%d] == id of %s' % (n, k, k + 16, m))
print('  (no output above means ids are not stored verbatim in tails)')

# are the 256-byte decode tables identical across shards?
print('\n--- table/sbox comparison vs start shard ---')
s = shards['f6f11ad133cab21c96e0185e3411ddc4']
t0, s0 = s[0x32:0x132], s[0x132:0x232]
print('start decode table  first16 %s' % t0[:16].hex(' '))
print('start decode table  is perm of 0..13? distinct=%d max=%d' % (len(set(t0)), max(t0)))
print('start sbox          first16 %s  distinct=%d' % (s0[:16].hex(' '), len(set(s0))))
for n, d in shards.items():
    t, b = d[0x32:0x132], d[0x132:0x232]
    print('%s tbl_same=%s sbox_same=%s  tbl distinct=%d  sbox distinct=%d' % (
        n[:12], t == t0, b == s0, len(set(t)), len(set(b))))
