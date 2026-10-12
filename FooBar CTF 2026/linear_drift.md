---
title: "linear_drift"
category: "Crypto"
tags: ["lfsr", "stream-cipher", "known-plaintext", "brute-force"]
solve_date: "2026-10-10T12:48:00+07:00"
language: "vi"
points: 100
---

# linear_drift

**Flag:** `foobarctf{lfsr_st4t3_sp4c3_1s_w4y_t00_sm4ll_9b3c}`  
**File đề:** `encrypt.py`, `challenge.txt`

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `encrypt.py` | 1,485 | `3b77974c425c29c4accc93a1fb17e804e816f4a4c2ca270fb504b26627dabe8a` |
| `challenge.txt` | 134 | `d2efa316516d2ae0fc9261e169de8cf85861d2f702d3ca9c40e4fbaf4606bcd4` |

## Đề bài

> Our hardware engineering team deployed a low-power IoT telemetry sensor in an industrial field station. To conserve CPU cycles and battery life on the node's 16-bit microcontroller, the lead engineer rolled out a custom hardware stream cipher based on a 16-bit Linear Feedback Shift Register (LFSR).
>
> Management was assured that because the 16-bit initial seed is generated randomly on every session, no unauthorized observer can decrypt the transmission.
>
> We intercepted a telemetry transmission containing the device's secret operational token. Can you recover the initial state and decrypt the flag?

Thử thách cung cấp mã nguồn mã hóa `encrypt.py` và tệp kết quả `challenge.txt` chứa bản mã dạng hex.

## Phân tích

Mã nguồn triển khai một LFSR 16-bit để sinh khóa dòng (keystream):
- Thanh ghi trạng thái có độ dài 16 bit: $S \in [1, 2^{16} - 1]$.
- Vị trí tap phản hồi: `[16, 14, 13, 11]`.
- Mỗi byte keystream được tạo bằng cách rút ra 8 bit liên tiếp từ LFSR.
- Bản mã được tính bằng phép XOR giữa bản rõ và keystream: $C = P \oplus K$.

Lỗ hổng cốt lõi nằm ở kích thước không gian khóa:
- Seed khởi tạo chỉ có 16 bit, tương đương $2^{16} - 1 = 65.535$ trạng thái khả dĩ (trừ trạng thái toàn bit 0).
- Định dạng flag bắt đầu bằng chuỗi cố định `foobarctf{` (10 byte).
- 10 byte keystream đầu tiên được tính chính xác qua known-plaintext:
  $$K[:10] = P[:10] \oplus C[:10] = \text{b"foobarctf\{"} \oplus C[:10]$$

Duyệt 65.535 seed, sinh 10 byte keystream cho từng seed và so sánh với keystream đã suy ra từ tiền tố flag.

## Lời giải

1. Đọc bản mã từ `challenge.txt`.
2. Tính 10 byte keystream mong đợi từ tiền tố `foobarctf{`.
3. Duyệt $seed \in [1, 65535]$, mô phỏng LFSR 16-bit để tìm seed khớp.
4. Với seed tìm được (`60954` hay `0xee1a`), sinh toàn bộ keystream và giải mã bản rõ.

## Kết quả

Seed khôi phục:
- Hệ thập phân: `60954`
- Hệ thập lục phân: `0xee1a`

```text
foobarctf{lfsr_st4t3_sp4c3_1s_w4y_t00_sm4ll_9b3c}
```

## Tái hiện

Chạy script Python độc lập dưới đây để giải mã flag:

```python
from pathlib import Path

# Đọc ciphertext
chall_text = Path("challenge.txt").read_text()
ciphertext = bytes.fromhex(chall_text.split(":")[-1].strip())

prefix = b"foobarctf{"
expected_ks = bytes([p ^ c for p, c in zip(prefix, ciphertext[:len(prefix)])])

class LFSR:
    def __init__(self, state, taps):
        self.state = state & 0xFFFF
        self.taps = taps

    def step(self):
        feedback = 0
        for tap in self.taps:
            feedback ^= (self.state >> (tap - 1)) & 1
        out = self.state & 1
        self.state = ((self.state >> 1) | (feedback << 15)) & 0xFFFF
        return out

    def get_byte(self):
        b = 0
        for i in range(8):
            b |= (self.step() << i)
        return b

taps = [16, 14, 13, 11]

# Vét cạn 16-bit seed
found_seed = None
for seed in range(1, 0x10000):
    lfsr = LFSR(seed, taps)
    ks = bytes([lfsr.get_byte() for _ in range(len(prefix))])
    if ks == expected_ks:
        found_seed = seed
        break

assert found_seed is not None, "Không tìm thấy seed"
print(f"[*] Seed tìm được: {found_seed} ({hex(found_seed)})")

lfsr = LFSR(found_seed, taps)
keystream = bytes([lfsr.get_byte() for _ in range(len(ciphertext))])
plaintext = bytes([c ^ k for c, k in zip(ciphertext, keystream)])
print(f"[+] Flag: {plaintext.decode()}")
```
