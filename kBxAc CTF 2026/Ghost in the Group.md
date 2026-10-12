---
title: "Ghost in the Group"
category: "Crypto"
tags: ["diffie-hellman", "pohlig-hellman", "discrete-logarithm", "hkdf-sha256", "aes-256-gcm"]
solve_date: "2026-10-10T16:56:00+07:00"
language: "vi"
points: 424
---

# Ghost in the Group

**Tác giả:** HexAsh  
**Flag:** `kBxAc{tHe_ghO$T_!S_oN_Th3_W@Y_7o_THE_He1l_@nD_HEaVEN_CiTy_oF_gOD}`

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `ghostgroup.zip` | 1,061 | `11a9b06aa74dc2b5e43977f556ea917d59419a3ca84bb8654c88f7fdf08c1c87` |
| `report.txt` (trong ZIP) | 1,564 | `f5a595c067128d7bb52173b90eed777c0e37aa8d5a472487406db8c0086de84d` |

## Đề bài

Một hệ thống dùng finite-field Diffie–Hellman (DH) để tạo khóa mã hóa AES-GCM. Chỉ có tham số công khai `p, g`, hai public key `A, B`, salt/info HKDF và nonce/ciphertext của AES-GCM. Mục tiêu là khôi phục private exponent, suy ra shared secret và giải mã.

## Phân tích dữ liệu

Trong `report.txt`:

```text
p = 63467945649558061108050038689766719425570161602312573669177550438400000001
g = 34952038223805443010720493058853465706314868555565705932753928511299642526
A = 32042156517052529276780975726463240054802798908955726096181227009867410282
B = 37135947831804401007053458686511576709944818927810443240150867786090625989
KDF = HKDF-SHA256, salt=bb02b73977165f5eb5e4a68fe3a20d6f
info = ghost-in-the-group/aes-gcm, output=32 bytes
AEAD = AES-256-GCM, nonce=f5d4d68f2bbe8d324a1fea1a
```

Thông thường DH yêu cầu giải logarit rời rạc `A = g^a mod p`. `p` có **246 bit**, nhưng **độ lớn không đồng nghĩa bậc nhóm khó phân tích**.

## Điểm yếu: p−1 smooth

Phân tích thành thừa số nguyên tố:

```text
p - 1 = 2^24 · 3^12 · 5^8 · 7^6 · 11^4 · 13^3 · 17^3 · 19^2 · 23^2 · 29^2 · 31^2 · 37 · 41 · 43 · 47 · 53 · 59 · 61 · 67 · 162075354975923
```

Đã kiểm tra `g` có bậc `p−1`, tức một phần tử sinh của nhóm nhân. Phần lớn bậc nhóm gồm các prime power rất nhỏ; thừa số nguyên tố lớn nhất là `162075354975923` (48 bit). Do đó thuật toán **Pohlig–Hellman** đưa logarit rời rạc gốc về các subgroup nhỏ và một subgroup 48 bit. Subgroup cuối có thể giải bằng discrete logarithm chuyên dụng (Pollard rho/BSGS; phần tốn công nhất).

Với mỗi `m = q^e` trong factorization, đặt:

```text
G_m = g^((p-1)/m) mod p
H_m = A^((p-1)/m) mod p
r_m = log_(G_m)(H_m) mod m
```

Sau đó áp dụng **Chinese Remainder Theorem (CRT)** cho các `r_m`, lấy `a mod (p−1)`.

## Khôi phục private exponent

Kết quả:

```text
a = 707872189507578477552274894304445771641188692329866348522823114155044802
```

Điều kiện bắt buộc được kiểm tra độc lập:

```text
pow(g, a, p) == A   -> True
```

Có thể tái hiện bước discrete log bằng SageMath (subgroup 48 bit có thể tốn tài nguyên):

```python
# Run with SageMath (Pohlig–Hellman + CRT).
p = ZZ(63467945649558061108050038689766719425570161602312573669177550438400000001)
g = ZZ(34952038223805443010720493058853465706314868555565705932753928511299642526)
A = ZZ(32042156517052529276780975726463240054802798908955726096181227009867410282)
order = p - 1
parts = factor(order)
residues, moduli = [], []
for ell, exponent in parts:
    m = ell ** exponent
    # Project into the subgroup of order m.
    base = Mod(power_mod(g, order // m, p), p)
    target = Mod(power_mod(A, order // m, p), p)
    # The largest prime factor (~48 bits) is the expensive step.
    r = discrete_log(target, base, ord=m, operation='*')
    residues.append(ZZ(r))
    moduli.append(ZZ(m))
a = CRT_list(residues, moduli)
assert power_mod(g, a, p) == A
print("a =", a)
print("shared =", power_mod(ZZ(37135947831804401007053458686511576709944818927810443240150867786090625989), a, p))
```

## Tạo khóa và giải mã

Shared secret `S = B^a mod p`:

```text
7371495731907457570335172938636690069572639110804625667070088674540265086
```

Quan trọng: truyền vào HKDF **giá trị nguyên S ở dạng big-endian tối thiểu (31 byte)**, không phải chuỗi ASCII của số thập phân. HKDF-SHA256 với salt/info trong report sinh khóa 32 byte:

```text
a9615ee5d4780da0830b6d5ece9d6baf2ab16996c0989922ee8e12fbca4c3125
```

Ciphertext chứa GCM authentication tag ở **16 byte cuối**. Không có associated data (AAD); khi AESGCM.decrypt thành công, nó đã đồng thời xác minh tag.

## Script kiểm chứng độc lập (Python 3)

Cần `pip install cryptography`. Script dưới dùng exponent đã khôi phục để xác minh handshake và giải mã từ đúng các tham số file đính kèm.

```python
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

p = 63467945649558061108050038689766719425570161602312573669177550438400000001
g = 34952038223805443010720493058853465706314868555565705932753928511299642526
A = 32042156517052529276780975726463240054802798908955726096181227009867410282
B = 37135947831804401007053458686511576709944818927810443240150867786090625989
a = 707872189507578477552274894304445771641188692329866348522823114155044802  # recovered discrete log (also obtainable with the Sage code above)
assert pow(g, a, p) == A
S = pow(B, a, p)
assert S == 7371495731907457570335172938636690069572639110804625667070088674540265086

# The integer must be encoded as minimal-length big-endian bytes.
ikm = S.to_bytes((S.bit_length() + 7) // 8, 'big')
key = HKDF(
    algorithm=hashes.SHA256(),
    length=32,
    salt=bytes.fromhex('bb02b73977165f5eb5e4a68fe3a20d6f'),
    info=b'ghost-in-the-group/aes-gcm',
).derive(ikm)
assert key.hex() == 'a9615ee5d4780da0830b6d5ece9d6baf2ab16996c0989922ee8e12fbca4c3125'
nonce = bytes.fromhex('f5d4d68f2bbe8d324a1fea1a')
ct_tag = bytes.fromhex(
    'b2fed82fa575a837bc583ee24799e5518d66c4e46a1fb981d4b20fa075b6fb15'
    'c1b84f3c1b6cf3d8d3cbe210b63b30df6264aed0ba08d8d93082736c9752c7714'
    'c4768676f68c9e3577aa6bd74f9562137'
)
flag = AESGCM(key).decrypt(nonce, ct_tag, None).decode('utf-8')
print('shared secret:', S)
print('AES-256 key:', key.hex())
print('flag:', flag)
```

Output:

```text
shared secret: 7371495731907457570335172938636690069572639110804625667070088674540265086
AES-256 key: a9615ee5d4780da0830b6d5ece9d6baf2ab16996c0989922ee8e12fbca4c3125
flag: kBxAc{tHe_ghO$T_!S_oN_Th3_W@Y_7o_THE_He1l_@nD_HEaVEN_CiTy_oF_gOD}
```

## Kết luận

DH bị phá không phải do modulus nhỏ, mà vì **bậc nhóm có phần lớn thừa số nhỏ**, cho phép Pohlig–Hellman khôi phục số mũ. Shared secret cho phép dẫn xuất đúng khóa HKDF và vượt qua bước xác thực AES-GCM; flag được khôi phục từ plaintext hợp lệ.
