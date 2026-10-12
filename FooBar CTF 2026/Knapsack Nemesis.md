---
title: "Knapsack Nemesis"
category: "Crypto"
tags: ["knapsack", "merkle-hellman", "subset-sum", "meet-in-the-middle"]
solve_date: "2026-10-10T19:44:00+07:00"
language: "vi"
points: 450
---

# Knapsack Nemesis

**Flag:** `foobarctf{l4tt1c3_r3duct10n_br34ks_m3rkl3_h3llm4n_9f4b!}`  
**File đề:** `encrypt.py`, `output.txt`

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `encrypt.py` | 1,868 | `6c9ea2034482ec03cb459e5199609f0a11278ef0332b2749cc9a197bb847f7eb` |
| `output.txt` | 1,161 | `7f0e953c597628652e54c288a09bf02b112b90de1ad9ff97795afaac423cd338` |

## Đề bài

> A legacy archive still encrypts sensitive clearance tokens with the 1978 Merkle-Hellman knapsack cryptosystem. Management was assured that because the general Subset Sum problem is NP-complete, the cipher is unbreakable. Security was not consulted.
>
> We intercepted one public key vector and an encrypted transmission. Can you recover the secret flag?
>
> Hint: Is worst-case NP-completeness the same as average-case security? Check the knapsack density.

Thử thách cung cấp mã nguồn `encrypt.py` và tệp đầu ra `output.txt` chứa vector khóa công khai `PUBLIC_KEY` gồm 32 số nguyên cùng danh sách các khối bản mã `CIPHERTEXTS`.

## Phân tích

Hệ mật mã ba lô Merkle-Hellman biến đổi một dãy siêu tăng (superincreasing knapsack) thành dãy công khai $B = (b_0, b_1, \dots, b_{n-1})$ thông qua phép nhân modulo:
$$b_i = w \cdot r_i \pmod q$$

Mỗi khối bản rõ 32-bit $M = (m_0, m_1, \dots, m_{31}) \in \{0, 1\}^{32}$ được mã hóa bằng tổng tập con:
$$C = \sum_{i=0}^{31} m_i \cdot b_i$$

Dù bài toán Subset Sum nói chung là NP-complete trong trường hợp xấu nhất, ở đây kích thước khối chỉ có $n = 32$.

Với $n = 32$, ta không cần dùng đến thuật toán rút gọn lưới LLL (Lagarias-Odlyzko / CLOS):
- Áp dụng **meet-in-the-middle (MitM)**:
  1. Chia vector khóa $B$ thành hai nửa 16 phần tử:
     $$B_{left} = B[:16], \quad B_{right} = B[16:]$$
  2. Tính trước tất cả $2^{16} = 65.536$ tổng tập con của nửa trái và lưu vào một bảng băm (`hash table`):
     $$\text{map}[S_{left}] = \text{mask}_{left}$$
  3. Với mỗi khối bản mã $C$, duyệt qua $2^{16}$ tổng tập con của nửa phải $S_{right}$ và tra cứu $C - S_{right}$ trong bảng băm.
  4. Nếu $C - S_{right} \in \text{map}$, ghép 16 bit trái và 16 bit phải để khôi phục khối bản rõ 32-bit (4 byte).

Mỗi khối cần duyệt tối đa $2^{16}$ tổng của nửa phải; bảng tổng nửa trái có $2^{16}$ phần tử và được dùng lại cho cả 14 khối.

## Lời giải

1. Đọc `PUBLIC_KEY` (32 phần tử) và 14 khối `CIPHERTEXTS` từ `output.txt`.
2. Tạo bảng băm lưu trữ trước $2^{16}$ tổng tập con từ 16 phần tử đầu tiên của khóa công khai.
3. Giải mã lần lượt từng khối trong `CIPHERTEXTS` bằng Meet-in-the-Middle.
4. Nối các khối 4 byte giải mã được thành chuỗi ký tự flag.

## Kết quả

```text
foobarctf{l4tt1c3_r3duct10n_br34ks_m3rkl3_h3llm4n_9f4b!}
```

## Tái hiện

Chạy script Python độc lập dưới đây:

```python
from pathlib import Path

# Đọc PUBLIC_KEY và CIPHERTEXTS
content = Path("output.txt").read_text()
scope = {}
exec(content, scope)
PUBLIC_KEY = scope["PUBLIC_KEY"]
CIPHERTEXTS = scope["CIPHERTEXTS"]

B_left = PUBLIC_KEY[:16]
B_right = PUBLIC_KEY[16:]

# 1. Tính trước tổng tập con nửa trái
left_map = {}
for mask in range(1 << 16):
    s = 0
    val_left = 0
    for i in range(16):
        if (mask >> (15 - i)) & 1:
            s += B_left[i]
            val_left |= (1 << (15 - i))
    left_map[s] = val_left

# 2. Giải mã từng khối bản mã bằng MitM
flag_bytes = bytearray()
for c in CIPHERTEXTS:
    found = False
    for mask in range(1 << 16):
        s_right = 0
        val_right = 0
        for i in range(16):
            if (mask >> (15 - i)) & 1:
                s_right += B_right[i]
                val_right |= (1 << (15 - i))
        rem = c - s_right
        if rem in left_map:
            val = (left_map[rem] << 16) | val_right
            flag_bytes.extend(val.to_bytes(4, "big"))
            found = True
            break
    assert found, f"Không tìm thấy nghiệm cho khối {c}"

print(f"[+] Flag: {flag_bytes.decode()}")
```
