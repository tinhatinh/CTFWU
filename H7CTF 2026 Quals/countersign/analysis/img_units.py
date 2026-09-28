import binascii
import collections
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
img = open("imgA.bin", "rb").read()
nonce = "ff1abc43fad01dc1"
print("image", len(img), "= 26 hdr + 26 hdr2 + 24*126 ?", 26 + 26 + 24 * 126 == len(img))
h1, h2 = img[:26], img[26:52]
print("hdr1", h1.hex())
print("hdr2", h2.hex())
units = [img[52 + 126 * k: 52 + 126 * (k + 1)] for k in range(24)]
for k, u in enumerate(units[:4]):
    print("u%-2d %s" % (k, binascii.hexlify(u, 2 if False else " ") if False else
                       " ".join(u[i:i + 6].hex() for i in range(0, 126, 6))))
print("\n== cau truc tung unit: dem gia tri 0 va byte khac 0 ==")
for k, u in enumerate(units):
    nz = [i for i, b in enumerate(u) if b]
    print("u%-2d nonzero=%3d  range %s..%s  first8=%s" %
          (k, len(nz), nz[0] if nz else None, nz[-1] if nz else None, u[:8].hex()))
print("\n== tan suat byte tai cac vi tri co dinh ==")
for off in (0, 1, 2, 3, 4, 5, 10, 16, 86, 120):
    col = collections.Counter(u[off] for u in units)
    print("  off %3d: %s" % (off, col.most_common(6)))
print("\n== kiem tra 25 'one-hot' trong block 70 byte ==")
for k, u in enumerate(units[:5]):
    blk = u[16:86]
    oneh = [i for i, b in enumerate(blk) if b and (b & (b - 1)) == 0]
    print("  u%-2d onehot-ish=%d  val=%s" % (k, len(oneh), sorted(blk[i] for i in oneh)[:26]))
print("\n== cac cap 6 byte trung lap (stamp?) ==")
seen = collections.Counter()
for u in units:
    for i in range(0, 120):
        seen[u[i:i + 6]] += 1
rep = [(v.hex(), c) for v, c in seen.items() if c > 1]
print("  so chuoi 6 byte xuat hien >1 lan:", len(rep), rep[:6])
