import binascii
import collections
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

V = {}
for ln in open("mint_vectors.txt", encoding="utf-8"):
    a, _, b = ln.partition(" ")
    if not a or not b.strip():
        continue
    try:
        V[binascii.unhexlify(a)] = b.strip()
    except Exception:
        pass
print("vectors:", len(V))

# 1) thuan tien: voi input 16 byte one-hot, 16 byte dau cua output phai = input dao nguoc
def tail(x):
    h = V[x]
    return binascii.unhexlify(h)

z16 = bytes(16)
print("MINT(16x00) ->", V.get(z16))
one = bytes([1]) + bytes(15)
print("MINT(01 00*15) ->", V.get(one))
if z16 in V and one in V:
    print("  prefix dao nguoc khop:",
          V[one][:32] == binascii.hexlify(one[::-1]).decode())

# 2) do phu hop giua dong lenh 1 byte va 16 byte
bad = 0
for b in range(256):
    x = bytes([b])
    if x not in V:
        continue
    o = binascii.unhexlify(V[x])
    if o[0] != b:
        bad += 1
print("len1 prefix khop:", 256 - bad, "/256")

# 3) kiem tra tinh cong theo XOR tren cac one-hot 16 byte
base = V.get(z16)
if base:
    bz = binascii.unhexlify(base)[16:]
    print("tail(0) =", bz.hex())
    rows = collections.defaultdict(dict)
    for k, v in V.items():
        if len(k) == 16 and sum(1 for c in k if c) == 1:
            p = next(i for i, c in enumerate(k) if c)
            rows[p][k[p]] = binascii.unhexlify(v)[16:]
    print("so vi tri one-hot:", len(rows), "moi bang 256:",
          all(len(r) == 256 for r in rows.values()))
    # neu cong dien ra thi tail(m) ^ tail(0) = XOR_p (tail(one-hot p,v) ^ tail(0))
    def xs(a, b):
        return bytes(x ^ y for x, y in zip(a, b))
    predict = bz
    for p in (0, 1):
        v = 0x41
        predict = xs(predict, xs(rows[p][v], bz))
    print("du doan tail(41 41 00..) =", predict.hex(), " (can MINT that to confirm)")
