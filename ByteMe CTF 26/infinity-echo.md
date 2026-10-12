---
title: "Infinity Echo"
category: "Crypto"
tags: ["ecdsa", "nonce-reuse", "secp256k1", "xor-keystream"]
solve_date: "2026-10-09"
language: "vi"
---

# Infinity Echo

**Flag:** `OWASP{th3_s0ul_st0n3_r3m3mb3rs_3v3ry_n0nc3}`
**Artifacts:** `curve.txt` (114 B), `signatures.txt` (487 B), `vault.bin` (43 B). Tác giả: Pratik Jadhav.

## Đề bài

Đề (Medium, 200 điểm):

```text
The Soul Stone signing system reused an ECDSA nonce. Recover the private key and use it to unlock the encrypted vault.
```

```text
curve=secp256k1
order=115792089237316195423570985008687907852837564279074904382605163141518161494337
hash=SHA-256
```

```text
z1=67347588885445611531902820368931932972040444711827578851545284568070995729591
r1=25051988655222711058432113143458427847319390342701470934547852446846422711567
s1=52962683639686838739783902028128198551006424233866284700402805681421689936337
z2=37899425276155539946685780241020155430073356926193948616690695112278990220884
r2=25051988655222711058432113143458427847319390342701470934547852446846422711567
s2=115743676190342659491968252099211722828859636197180484755175383932038123963381
```

`vault.bin` là 43 byte không có header nhận dạng được.

## Phân tích

`r1 == r2`, còn `z1 != z2` và `s1 != s2`. Xét giả thiết dùng lại cùng nonce `k` trong quan hệ `s = k^-1 (z + r*d) mod n`, ta có hệ hai phương trình theo `k` và `d`. Việc trùng `r` riêng lẻ chưa đủ chứng minh hai nonce giống nhau:

```text
k = (z1 - z2) * (s1 - s2)^-1  mod n
d = (s1*k - z1) * r1^-1       mod n
```

Phép trừ và nghịch đảo lấy theo modulo `n`, là giá trị ở dòng `order=` của `curve.txt`.

Hằng số này đáng để đo kỹ. Giá trị trong file là `115792089237316195423570985008687907852837564279074904382605163141518161494337` = `0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141`, tức đúng **group order** `n` của secp256k1. Field prime `p` của cùng đường cong là `115792089237316195423570985008687907853269984665640564039457584007908834671663` = `0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f`. Hai số thập phân dài 78 chữ số, trùng nhau ở 38 chữ số đầu và chỉ khác từ chữ số thứ 39, nên cặp này rất dễ bị nhầm; kiểm tra lại bằng hai cách độc lập cho cùng một kết luận:

```text
order value == field prime P ? False
order value == group order N ? True
order * G is the point at infinity ? True
```

Toàn bộ `z`, `r`, `s` đều nhỏ hơn `n`. `z1` và `z2` được cho sẵn dưới dạng số nguyên, nên đề đã tính sẵn hash; dòng `hash=SHA-256` không tham gia vào bước recover nào.

Chạy phép recover:

```text
r1 == r2 ? True
k = 123456789abcdef123456789abcdef123456789abcdef123456789abcdef1234
d = 1a2b3c4d5e6f778899aabbccddeeff00112233445566778899aabbccddeeff11
sig1 residual (s*k - z - r*d) mod n = 0
sig2 residual (s*k - z - r*d) mod n = 0
```

Cả hai số đều là literal có khuynh hướng dễ đọc (`0x123456789abcdef` lặp lại, `0x1a2b3c4d5e6f...`), và cả hai phương trình chữ ký nghiệm đúng với residual bằng 0.

Tuy nhiên có một điểm phải ghi nhận như quan sát, không phải như suy luận: `r` mà đề cho **không** phải `x(k*G) mod n`. Tính độc lập trên secp256k1 với `k` vừa recover:

```text
x(k*G)      = 72588cf4bc7fb52a68d5c81b83643a96a881acfd9359d268bf675c0173b46920
r from file = 3762ec5011ac54e73768730a8b73619c69fa74f9bcf0263f37c9bf5733597d0f
x(k*G) mod n == r ? False
```

Nghĩa là bài này không tuân quan hệ ECDSA chuẩn ở vế `r`; lời giải đi trên hệ đại số `s*k = z + r*d mod n` với `r` lấy trực tiếp từ file, và chỉ nghiệm đúng theo nghĩa residual. `d*G` cho một điểm hợp lệ `(0x908f37a8..., 0xc1b1bc2c...)` nhưng không có artifact nào công bố public key để đối chiếu, nên điểm đó không phải bằng chứng.

Với `vault.bin`: sinh khoá từ `d` rồi XOR lặp theo vị trí byte:

```text
key = SHA256(b"SOUL-VAULT:" + str(d).encode())
```

Khoá XOR được tính bằng `SHA256(b"SOUL-VAULT:" + str(d).encode())`, sau đó lặp digest 32 byte trên ciphertext. Nhãn `SOUL-VAULT:` được lưu trong solver; dữ liệu hiện có không giải thích cách tìm ra nhãn này. Phép đối chiếu với crib `OWASP{` cho:

```text
keystream[:6]: d7d8bb0bb267 | vault[:6]^OWASP{: d7d8bb0bb267
re-encrypt ok: True
plaintext: OWASP{th3_s0ul_st0n3_r3m3mb3rs_3v3ry_n0nc3}
```

Vế phải của dòng đầu không dùng kết quả giải mã: nó chỉ XOR 6 byte ciphertext với `OWASP{`. Hai vế bằng nhau, và 43 byte của `vault.bin` đúng bằng độ dài chuỗi thu được, nên toàn bộ vault là cờ, không phải cờ kèm padding.

## Lời giải

Script đầy đủ, chỉ stdlib (`hashlib` và số học đường cong tự viết), đọc cả ba artifact:

```python
import hashlib

FIELD_P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
GROUP_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
GX = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
GY = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

def load(path):
    out = {}
    for line in open(path).read().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out

def add(A, B):
    if A is None:
        return B
    if B is None:
        return A
    x1, y1 = A
    x2, y2 = B
    if x1 == x2 and (y1 + y2) % FIELD_P == 0:
        return None
    if A == B:
        lam = 3 * x1 * x1 * pow(2 * y1, -1, FIELD_P) % FIELD_P
    else:
        lam = (y2 - y1) * pow(x2 - x1, -1, FIELD_P) % FIELD_P
    x3 = (lam * lam - x1 - x2) % FIELD_P
    return (x3, (lam * (x1 - x3) - y1) % FIELD_P)

def mul(k, Pt):
    R, Q = None, Pt
    while k:
        if k & 1:
            R = add(R, Q)
        Q = add(Q, Q)
        k >>= 1
    return R

curve = load("curve.txt")
sig = load("signatures.txt")
n = int(curve["order"])
print("curve.txt:", curve)
print("order value == field prime P ?", n == FIELD_P)
print("order value == group order N ?", n == GROUP_N)
print("order * G is the point at infinity ?", mul(n, (GX, GY)) is None)

z1, r1, s1 = int(sig["z1"]), int(sig["r1"]), int(sig["s1"])
z2, r2, s2 = int(sig["z2"]), int(sig["r2"]), int(sig["s2"])
print("r1 == r2 ?", r1 == r2)

k = (z1 - z2) * pow(s1 - s2, -1, n) % n
d = (s1 * k - z1) * pow(r1, -1, n) % n
print("k = %064x" % k)
print("d = %064x" % d)
for i, (z, s) in enumerate(((z1, s1), (z2, s2)), 1):
    print("sig%d residual (s*k - z - r*d) mod n = %d" % (i, (s * k - z - r1 * d) % n))

R = mul(k, (GX, GY))
print("x(k*G)      = %064x" % R[0])
print("r from file = %064x" % r1)
print("x(k*G) mod n == r ?", R[0] % n == r1)
Q = mul(d, (GX, GY))
print("d*G = (%064x, %064x)" % (Q[0], Q[1]))

vault = open("vault.bin", "rb").read()
key = hashlib.sha256(("SOUL-VAULT:%d" % d).encode("ascii")).digest()
pt = bytes(a ^ key[i % 32] for i, a in enumerate(vault))
print("keystream[:6]:", key[:6].hex(), "| vault[:6]^OWASP{:",
      bytes(a ^ b for a, b in zip(vault[:6], b"OWASP{")).hex())
print("re-encrypt ok:", bytes(a ^ key[i % 32] for i, a in enumerate(pt)) == vault)
print("plaintext:", pt.decode())
```

```text
curve.txt: {'curve': 'secp256k1', 'order': '115792089237316195423570985008687907852837564279074904382605163141518161494337', 'hash': 'SHA-256'}
order value == field prime P ? False
order value == group order N ? True
order * G is the point at infinity ? True
r1 == r2 ? True
k = 123456789abcdef123456789abcdef123456789abcdef123456789abcdef1234
d = 1a2b3c4d5e6f778899aabbccddeeff00112233445566778899aabbccddeeff11
sig1 residual (s*k - z - r*d) mod n = 0
sig2 residual (s*k - z - r*d) mod n = 0
x(k*G)      = 72588cf4bc7fb52a68d5c81b83643a96a881acfd9359d268bf675c0173b46920
r from file = 3762ec5011ac54e73768730a8b73619c69fa74f9bcf0263f37c9bf5733597d0f
x(k*G) mod n == r ? False
d*G = (908f37a80cad36ed8f161b25015574261675c74ccf1367e14c698a52c849fc53, c1b1bc2c5cbbdd8eb86da9a0e9603f58485f1ec2bba3d204575ec664daeab149)
keystream[:6]: d7d8bb0bb267 | vault[:6]^OWASP{: d7d8bb0bb267
re-encrypt ok: True
plaintext: OWASP{th3_s0ul_st0n3_r3m3mb3rs_3v3ry_n0nc3}
```

## Kết quả

```text
OWASP{th3_s0ul_st0n3_r3m3mb3rs_3v3ry_n0nc3}
```

Dữ liệu giải mã từ artifact `vault.bin` với khoá dựng từ `d` recover được; keystream khớp với crib `OWASP{` ở 6 byte đầu và phép XOR ngược trả về đúng ciphertext (`re-encrypt ok: True`). Bài không kèm dịch vụ remote. Lưu ý đã nêu ở phần Phân tích: `r` trong file không bằng `x(k*G) mod n`, nên lời giải không mô phỏng ECDSA chuẩn đầy đủ. Chưa lưu phản hồi submission.

## Tái hiện

Bản chính cần Python 3 stdlib (`hashlib`), đặt `echo_all.py` — nội dung ở phần Lời giải — cùng thư mục với `curve.txt`, `signatures.txt`, `vault.bin`:

```console
$ python echo_all.py
```

Luồng giải trên chỉ cần standard library. Các thử nghiệm tìm khoá khác không cần để tái hiện lời giải này.
