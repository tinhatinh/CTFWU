---
title: "smooth_orbit"
category: "Crypto"
tags: ["ecc", "ecdlp", "pohlig-hellman", "smooth-order", "crt"]
solve_date: "2026-10-10T12:55:00+07:00"
language: "vi"
points: 500
---

# smooth_orbit

**Flag:** `foobarctf{p0hl1g_h3llm4n_sh4tt3rs_sm00th_curv3s_7a9c8e}`  
**File đề:** `curve.py`, `challenge.txt`

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `curve.py` | 2,057 | `374919361f0aa2221acda5d005efade4c1cf75f3379b047b94c11ee2844420b8` |
| `challenge.txt` | 940 | `808c5f8853ba1bf2482189f2a8cb06dfaf2b7ee68f824a2ea9e31ca04ddcbd62` |

## Đề bài

> An aerospace defence contractor designed a secure satellite uplink system. Suspicious of standard NIST curves and Curve25519 due to fears of "hidden backdoors", their chief security architect generated a custom elliptic curve.
>
> We intercepted the public curve parameters, the base station's public key Q, and an encrypted emergency telecommand payload. Can you recover the master private key and decrypt the payload to retrieve the flag?

Thử thách cung cấp tệp định nghĩa đường cong elliptic `curve.py` và tệp chứa tham số công khai kèm bản mã `challenge.txt`.

## Phân tích

Hệ thống sử dụng đường cong elliptic dạng Weierstrass ngắn:
$$y^2 \equiv x^3 + 3x \pmod p$$
với trường hữu hạn $\mathbb{F}_p$ ($p$ dài 216 bit), điểm sinh $G = (1, 2)$, và khóa công khai $Q = d \cdot G$.

Trong instance này, cấu trúc thừa số của bậc nhóm $\text{ORDER}$ cho phép giải ECDLP bằng Pohlig–Hellman. Phân tích thừa số nguyên tố của $\text{ORDER}$:

$$\text{ORDER} = 29 \times 41 \times 197 \times 257^2 \times 293 \times 421^2 \times 433 \times 449 \times 521 \times 593 \times 601 \times 617 \times 653 \times 661 \times 709 \times 829^2 \times 929 \times 941 \times 997^3$$

Toàn bộ các ước nguyên tố của $\text{ORDER}$ đều nhỏ hơn hoặc bằng **997** ($\text{ORDER}$ là một số trơn / B-smooth với $B = 997$).

Do đó, có thể giải ECDLP bằng **Thuật toán Pohlig-Hellman**:
1. Chiếu bài toán về từng nhóm con cấp lũy thừa nguyên tố $p_i^{e_i}$:
   $$Q_i = \left(\frac{N}{p_i^{e_i}}\right) Q, \quad G_i = \left(\frac{N}{p_i^{e_i}}\right) G$$
2. Do $p_i \le 997$, ta có thể giải logarit rời rạc trên từng nhóm con bằng phép vét cạn (brute-force) hoặc Baby-step Giant-step trong từng nhóm con để tìm $d \pmod{p_i^{e_i}}$.
3. Dùng **Định lý số dư Trung Hoa (CRT)** kết hợp các nghiệm cục bộ để tái tạo chính xác số vô hướng bí mật $d \pmod{\text{ORDER}}$.
4. Khóa AES đối xứng được suy dẫn từ $\text{SHA-256}(\text{str}(d))$ để giải mã bản mã truyền tin.

## Lời giải

1. Phân tích $\text{ORDER}$ thành tích các lũy thừa số nguyên tố nhỏ.
2. Triển khai thuật toán Pohlig-Hellman trên đường cong elliptic để tính từng thặng dư $d \pmod{p_i^{e_i}}$.
3. Áp dụng CRT tìm được khóa bí mật:
   $$d = 1966488246008519752703905121425384383816541038606442439760348604$$
4. Khởi tạo khóa AES từ SHA-256 của $d$ dạng chuỗi và giải mã bản mã AES-CBC.

## Kết quả

```text
foobarctf{p0hl1g_h3llm4n_sh4tt3rs_sm00th_curv3s_7a9c8e}
```

## Tái hiện

Chạy script Python độc lập dưới đây:

```python
import hashlib
from Crypto.Cipher import AES

p = 6521134753142873614843836235135002751093729570227995101024124417
a = 3
b = 0
G = (1, 2)
ORDER = 3260567376571436807421918117567548534157612337640795802440412833
Q = (2061573427100208603111671551304919028221649525354526770430156907, 6475257220252032604850487547502845101501630027536396815374309622)
Ciphertext = bytes.fromhex("a7d70d5eeb4e785225a542d003b29d1b1fe74c4cd270a5c42f940f108ebd9d27e5a910bd110e2cd5eba7eb6fd8ef3c64a5e46fe92717b7")

def point_add(P, Q):
    if P is None: return Q
    if Q is None: return P
    x1, y1 = P
    x2, y2 = Q
    if x1 == x2 and (y1 + y2) % p == 0: return None
    if x1 == x2:
        m = (3 * x1 * x1 + a) * pow(2 * y1, -1, p) % p
    else:
        m = (y2 - y1) * pow(x2 - x1, -1, p) % p
    x3 = (m * m - x1 - x2) % p
    y3 = (m * (x1 - x3) - y1) % p
    return (x3, y3)

def scalar_mult(k, P):
    R = None
    T = P
    while k > 0:
        if k & 1:
            R = point_add(R, T)
        T = point_add(T, T)
        k >>= 1
    return R

def dlp_brute(P, Q, order):
    curr = None
    for d in range(order):
        if curr == Q:
            return d
        curr = point_add(curr, P)
    raise ValueError("DLP failed")

def pohlig_hellman_prime_power(P, Q, p_factor, e, N):
    gamma = scalar_mult(N // p_factor, P)
    x = 0
    for k in range(e):
        scalar = N // (p_factor ** (k + 1))
        Q_sub = point_add(Q, scalar_mult((-x) % N, P))
        H = scalar_mult(scalar, Q_sub)
        d_k = dlp_brute(gamma, H, p_factor)
        x += d_k * (p_factor ** k)
    return x

factors = [
    (29, 1), (41, 1), (197, 1), (257, 2), (293, 1), (421, 2), (433, 1),
    (449, 1), (521, 1), (593, 1), (601, 1), (617, 1), (653, 1), (661, 1),
    (709, 1), (829, 2), (929, 1), (941, 1), (997, 3)
]

congruences = []
for p_factor, e in factors:
    modulus = p_factor ** e
    rem = pohlig_hellman_prime_power(G, Q, p_factor, e, ORDER)
    congruences.append((rem, modulus))

def crt(congruences):
    M = 1
    for _, m in congruences: M *= m
    x = 0
    for a_i, m_i in congruences:
        M_i = M // m_i
        y_i = pow(M_i, -1, m_i)
        x = (x + a_i * M_i * y_i) % M
    return x

d = crt(congruences)
print(f"[*] Phục hồi scalar d: {d}")

key = hashlib.sha256(str(d).encode()).digest()
iv = Ciphertext[:16]
ct = Ciphertext[16:]
cipher = AES.new(key, AES.MODE_CBC, iv)
pt = cipher.decrypt(ct)
pad_len = pt[-1]
flag = pt[:-pad_len].decode()
print(f"[+] Flag: {flag}")
```
