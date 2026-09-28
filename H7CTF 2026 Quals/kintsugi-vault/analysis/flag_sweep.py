"""Exhaustive offline hunt for a flag string in the Kintsugi handout.

Sweeps every file (and every derived byte-array: recovered tables, sbox, program
regions, header fields) under many encodings, looking for the challenge prefix.
"""
import os, re, sys, base64, codecs, glob, itertools, zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vm

NEEDLES = ['H7CTF', 'h7ctf', 'FLAG', 'flag{', 'CTF{', 'SUN{', 'webverse', 'WEBVERSE']
HERE = os.path.dirname(os.path.abspath(__file__))
FILES = [f for f in sorted(glob.glob(os.path.join(HERE, '..', 'files', '*')))
         if not f.endswith('.asm') and os.path.isfile(f)]


def variants(b):
    yield 'raw', b
    yield 'utf16le', b.decode('utf-16-le', 'ignore').encode('utf-16-le')
    yield 'utf16be', b.decode('utf-16-be', 'ignore').encode('utf-16-be')
    yield 'rev', b[::-1]
    yield 'xor255', bytes(x ^ 0xFF for x in b)
    yield 'rot13', codecs.encode(b.decode('latin-1'), 'rot_13').encode('latin-1')
    hexs = b.hex().encode()
    yield 'hex', hexs
    for k in range(0, 4):
        try:
            yield 'b64@%d' % k, base64.b64encode(b[k:])
            yield 'b32@%d' % k, base64.b32encode(b[k:])
        except Exception:
            pass
    for k in range(0, 3):
        try:
            yield 'b64u@%d' % k, base64.urlsafe_b64encode(b[k:])
        except Exception:
            pass
    yield 'b64ofutf16', base64.b64encode(b.decode('latin-1').encode('utf-16-le'))
    for algo in ('zlib', 'gzip'):
        try:
            f = getattr(zlib, 'compress' if algo == 'zlib' else 'compress')
            yield algo, f(b)
        except Exception:
            pass
    # nibble swap and per-byte arithmetic families
    yield 'nibswap', bytes(((x << 4) | (x >> 4)) & 0xFF for x in b)
    for key in range(1, 8):
        yield 'xor%d' % key, bytes(x ^ key for x in b)
    for key in range(1, 4):
        yield 'add%d' % key, bytes((x + key) & 0xFF for x in b)
        yield 'sub%d' % key, bytes((x - key) & 0xFF for x in b)


blobs = {}
for f in FILES:
    d = open(f, 'rb').read()
    name = os.path.basename(f)
    if name.endswith('.shard'):
        sh = vm.load(name[:-6])
        blobs[name + '|whole'] = d
        blobs[name + '|table'] = bytes(sh['tbl'])
        blobs[name + '|sbox'] = bytes(sh['sbox'])
        blobs[name + '|code'] = bytes(sh['code'])
        blobs[name + '|hdr'] = d[:0x32]
        blobs[name + '|id+next'] = sh['tid'] + sh['nxt']
    else:
        blobs[name] = d
for t in glob.glob(os.path.join(HERE, '*.table')) + glob.glob(os.path.join(HERE, 'recovered_*.table')):
    blobs['recovered|' + os.path.basename(t)] = open(t, 'rb').read()
blobs['seed'] = bytes.fromhex(open(os.path.join(HERE, 'seed.hex')).read().split()[0])

print('[*] %d blobs x %d encodings' % (len(blobs), 30))
hits = 0
for bname, b in blobs.items():
    for enc, v in variants(b):
        low = v.lower()
        for n in NEEDLES:
            if n.lower().encode() in low:
                i = low.find(n.lower().encode())
                print('  HIT %s / %s / %s @%d : %r' % (bname, enc, n, i, v[max(0, i - 12):i + 48]))
                hits += 1
print('[%s] needle hits: %d' % ('none' if not hits else 'FOUND', hits))

# printable runs containing braces anywhere (structure check)
print('\n[*] brace-delimited runs in every blob (raw):')
pat = re.compile(rb'[A-Za-z0-9_./:+-]{2,40}\{[^}\n]{1,60}\}')
seen = set()
for bname, b in blobs.items():
    for m in pat.finditer(b):
        s = m.group()
        if s in seen:
            continue
        seen.add(s)
        print('   %-40s %s' % (bname[:40], s[:80]))
print('   (%d distinct)' % len(seen))
