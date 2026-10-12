---
title: "nebula_obscura"
category: "Crypto"
tags: ["aes-cbc", "prng-vigenere", "rsa", "pollard-p-minus-1", "multi-layer"]
solve_date: "2026-10-10T12:54:00+07:00"
language: "vi"
points: 450
---

# nebula_obscura

**Flag:** `GLUG{T4K3_F1L3N4M3_53R10U5LY}`  
**File đề:** `nebula_obscura_0xB4D455.enc`

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `nebula_obscura_0xB4D455.enc` | 1,296 | `f7059d6c3615ded00adc4ccb8314749629397e546a882bbe8aec109a41658fa8` |

## Đề bài

> You've intercepted a single encrypted file: nebula_obscura_0xB4D455.enc All we know:
>
> It was encrypted with AES-128-CBC. The key and IV are not provided separately — derive them from the file's own name. Whatever you decrypt will tell you how to proceed.

Thử thách cung cấp một tệp mã hóa duy nhất `nebula_obscura_0xB4D455.enc`.

## Phân tích

Đây là một thử thách mật mã đa tầng (multi-layer challenge) kết hợp mã hóa khối đối xứng, PRNG, mật mã cổ điển và phá mã khóa công khai RSA.

### Lớp 1 — AES-128-CBC từ tên tệp

Theo mô tả đề bài, khóa và IV được dẫn xuất trực tiếp từ tên tệp `nebula_obscura_0xB4D455.enc`:
$$\text{hash} = \text{SHA-256}(\text{b"nebula\_obscura\_0xB4D455.enc"})$$
- Khóa AES (16 byte): `hash[:16]`
- Vector khởi tạo IV (16 byte): `hash[16:32]`

Giải mã AES-128-CBC thu được một đối tượng JSON chứa câu đố:
> *"I am the exact number of seconds in half of an ordinary day. Take my value, hash it with SHA-256, and use the resulting hex digest as the seed string for Python's random module."*

Số giây trong nửa ngày thường là:
$$12 \text{ giờ} = 12 \times 3.600 = 43.200 \text{ giây}$$
Seed là chuỗi hex `hashlib.sha256(b"43200").hexdigest()`, được truyền trực tiếp vào `random.seed`.

### Lớp 2 — Giải lớp XOR dùng PRNG và Vigenère

1. Khởi tạo bộ sinh ngẫu nhiên của Python:
   $$\text{random.seed}(\text{SHA-256}(\text{"43200"}))$$
2. Sinh dãy byte ngẫu nhiên để thực hiện phép XOR giải mã khối dữ liệu lớp 2 (`layer2_blob`).
3. Khối giải mã chứa một bản mã Vigenère. Khóa Vigenère được tạo từ 10 ký tự đầu của $\text{SHA-1}(\text{seed})$: `D9E8C73617`.
4. Giải mã Vigenère để lấy chuỗi Base64 chứa các tham số RSA: mô-đun $n$, số mũ công khai $e$, và bản mã $c$.

### Lớp 3 — Phân tích nhân tử RSA bằng Thuật toán Pollard's $p-1$

Mô-đun $n$ là một số nguyên 60 chữ số:
$$n = 165570081295982859187310065091722881855644781429813583648713$$

Kiểm tra thấy $p - 1$ là một số trơn (smooth), cho phép thuật toán **Pollard's $p-1$** phân tích nhân tử bằng cấu trúc này:
- $p = 1385691648282952313843858787803$
- $q = n / p = 1194855075677028975344337227411$

Tính $\phi(n) = (p - 1)(q - 1)$ và số mũ giải mã $d \equiv e^{-1} \pmod{\phi(n)}$, ta tính được $m = c^d \pmod n$ cho ra flag hoàn chỉnh.

## Lời giải

1. Tính SHA-256 của tên file để giải mã tầng AES-128-CBC.
2. Giải câu đố (43200 giây), seed bộ sinh PRNG của Python và giải mã XOR kèm Vigenère.
3. Chạy thuật toán Pollard's $p-1$ để phân tích mô-đun $n$ thành hai thừa số nguyên tố $p, q$.
4. Tính $d$ và giải mã RSA để thu về flag.

## Kết quả

```text
GLUG{T4K3_F1L3N4M3_53R10U5LY}
```

## Tái hiện

Chạy script Python độc lập dưới đây:

```python
import hashlib
import json
import base64
import random
from math import gcd
from Crypto.Cipher import AES
from pathlib import Path

# 1. Giải mã Layer 1 (AES-128-CBC)
filename = "nebula_obscura_0xB4D455.enc"
enc_data = Path(filename).read_bytes()

h = hashlib.sha256(filename.encode()).digest()
key, iv = h[:16], h[16:]
cipher = AES.new(key, AES.MODE_CBC, iv)
pt = cipher.decrypt(enc_data)
pad_len = pt[-1]
layer1_json = json.loads(pt[:-pad_len].decode())

# 2. Giải mã Layer 2 (PRNG & Vigenère)
# Nửa ngày = 12 giờ = 43200 giây
seconds = "43200"
seed_str = hashlib.sha256(seconds.encode()).hexdigest()

random.seed(seed_str)
layer2_blob = bytes.fromhex(layer1_json["layer2_blob"])
ks = bytes([random.randint(0, 255) for _ in range(len(layer2_blob))])
vigenere_ct = bytes([c ^ k for c, k in zip(layer2_blob, ks)]).decode("latin-1")

vigenere_key = hashlib.sha1(seed_str.encode()).hexdigest()[:10].upper()

# Giải mã Vigenère
def vigenere_decrypt(ciphertext, key):
    res = []
    ki = 0
    for ch in ciphertext:
        if ch.isalpha():
            base = ord('A') if ch.isupper() else ord('a')
            k_shift = ord(key[ki % len(key)].upper()) - ord('A')
            res.append(chr((ord(ch) - base - k_shift) % 26 + base))
            ki += 1
        elif ch.isdigit():
            k_shift = int(key[ki % len(key)], 16) % 10
            res.append(chr((ord(ch) - ord('0') - k_shift) % 10 + ord('0')))
            ki += 1
        else:
            res.append(ch)
    return "".join(res)

b64_data = vigenere_decrypt(vigenere_ct, vigenere_key)
rsa_params = json.loads(base64.b64decode(b64_data).decode())

n = int(rsa_params["n"])
e = int(rsa_params["e"])
c = int(rsa_params["c"])

# 3. Phân tích nhân tử Pollard's p - 1
a = 2
B = 1000000
for i in range(2, B):
    a = pow(a, i, n)
    d_cand = gcd(a - 1, n)
    if 1 < d_cand < n:
        p = d_cand
        break

q = n // p
phi = (p - 1) * (q - 1)
d = pow(e, -1, phi)
m = pow(c, d, n)
flag = m.to_bytes((m.bit_length() + 7) // 8, "big").decode()
print(f"[+] Flag: {flag}")
```
