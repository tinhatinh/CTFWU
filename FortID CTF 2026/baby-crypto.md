---
title: "Baby Crypto"
category: "Crypto"
tags: ["aes-ctr","nonce-reuse","known-plaintext"]
solve_date: "2026-10-10"
language: "vi"
---

# Baby Crypto

**Flag:** `FortID{St0p_B31ng_Cr3at1v3_With_N0nc3s_0r_You'll_R3gre7_17_33bf89db8a}`  
**Dịch vụ:** `ncat --ssl baby-crypto-63cd3ccb7215.inst16.ctf.fortid.com 1337` (TLS trên cổng 1337). Artifact: `chall.py` 1890 B. Trang đề ghi flag format là `FortID{}`.

## Đề bài

Dịch vụ giữ một vault chứa các secret của phiên, trong đó secret #0 là flag. Người chơi có thể encrypt plaintext tùy chọn bằng session key này.

## Phân tích

`AES.new` khởi tạo AES-CTR với nonce lấy từ 8 byte đầu của plaintext:

```python
AES.new(self.key, AES.MODE_CTR, nonce=plaintext[:8])
```

Nonce được lấy trực tiếp từ 8 byte đầu của plaintext do người chơi gửi, còn `self.key` giữ nguyên trong suốt session. Mỗi lần gọi `Cipher.encrypt` tạo cipher object mới với counter bắt đầu từ 0. Vì vậy, hai request có cùng 8 byte đầu sẽ dùng cùng keystream; phần plaintext còn lại không ảnh hưởng.

CTR không dùng padding nên ciphertext và plaintext có cùng length. Secret #0 dài 70 byte, vì vậy flag cũng dài 70 byte. Với probe có cùng prefix và dài ít nhất 70 byte:

```text
C_probe = P_probe ^ K
C_secret = P_secret ^ K
=> P_secret = C_secret ^ C_probe ^ P_probe
```

Ta chọn `P_probe`, dịch vụ trả `C_probe`, còn `C_secret` được lấy ở đầu phiên. Vì prefix `FortID{` cố định các vị trí 0–6, chỉ còn byte ở vị trí 7 chưa biết. Thử 94 ký tự ASCII in được, không gồm khoảng trắng (0x21–0x7E).

## Lời giải

1. Kết nối instance qua TLS và lấy ciphertext của secret #0: `Secret #0 = 70 ciphertext bytes, 1 entries`.
2. Tạo 94 probe 70 byte theo dạng `FortID{` + một ký tự ứng viên + filler, rồi gửi qua encrypt endpoint. Transcript ghi `sent 94 probes, 96B each, 9306B total`; số liệu không khớp vì 94 × 96 = 9024. Bản ghi không giải thích chênh lệch 282 byte; phép khôi phục dùng ciphertext và probe dài 70 byte.
3. Gọi export để lấy toàn bộ ciphertext trong session: `export has 95 entries`, đúng bằng secret gốc cộng 94 probe.
4. Với từng cặp probe/phản hồi, tính `P = C_secret ^ C_probe ^ P_probe`, rồi giữ các plaintext chỉ gồm byte in được. Chỉ một candidate thỏa mãn; byte thứ 7 là `S` (0x53).

## Kết quả

```text
FortID{St0p_B31ng_Cr3at1v3_With_N0nc3s_0r_You'll_R3gre7_17_33bf89db8a}
```

Flag được đọc trực tiếp từ service. Không có submission response trong bản ghi.

## Tái hiện

Cần instance còn hoạt động để đọc flag thật. Cơ chế nonce reuse có thể kiểm tra cục bộ với `chall.py` và một flag test. Các snippet dưới đây chưa bao gồm giao thức menu hoàn chỉnh.

Dựng probe:

```python
PREFIX = b"FortID{"                                  # positions 0..6, fixed by the flag format
LEN = 70                                             # same length as Secret #0's ciphertext
probes = [PREFIX + bytes([b]) + b"A" * (LEN - len(PREFIX) - 1) for b in range(0x21, 0x7F)]
assert len(probes) == 94 and all(len(p) == LEN for p in probes)
```

Khung kết nối TLS tới cổng 1337; các lượt upload plaintext và gọi export đi theo đúng menu mà dịch vụ cung cấp:

```python
import socket, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
host = "baby-crypto-63cd3ccb7215.inst16.ctf.fortid.com"
s = ctx.wrap_socket(socket.socket(), server_hostname=host)
s.connect((host, 1337))
# read Secret #0, then send each probe and collect the matching ciphertext
```

Hậu xử lý transcript (không dùng key material):

```python
# c_secret : 70 bytes of ciphertext for Secret #0
# probes   : the 70-byte plaintexts sent, in send order
# replies  : the ciphertexts returned for those plaintexts

PRINTABLE = set(range(0x20, 0x7F))

def recover(c_secret, p_probe, c_probe):
    return bytes(a ^ b ^ c for a, b, c in zip(c_secret, p_probe, c_probe))

cands = [recover(c_secret, p, c) for p, c in zip(probes, replies)]
ok = [c for c in cands if all(b in PRINTABLE for b in c)]
print(len(cands) + 1)                                        # 95 exported entries
print(len(ok))                                               # 1
```
