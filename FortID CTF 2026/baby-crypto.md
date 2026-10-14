---
title: "Baby Crypto"
category: "Crypto"
tags: ["aes-ctr","nonce-reuse","known-plaintext"]
solve_date: "2026-10-10"
language: "vi"
---

# Baby Crypto

**Flag:** `FortID{St0p_B31ng_Cr3at1v3_With_N0nc3s_0r_You'll_R3gre7_17_33bf89db8a}`  
**Dịch vụ:** `ncat --ssl baby-crypto-63cd3ccb7215.inst16.ctf.fortid.com 1337` (TLS trên cổng 1337). Artifact: `chall.py` 1890 B. Trang đề ghi dạng cờ là `FortID{}`.

## Đề bài

Dịch vụ giữ một vault chứa bí mật của phiên, trong đó bí mật #0 là cờ, và cho phép người chơi mã hoá plaintext tự chọn dưới đúng khoá phiên đó.

## Phân tích

Hàm mã hoá khởi tạo AES-CTR như sau:

```python
AES.new(self.key, AES.MODE_CTR, nonce=plaintext[:8])
```

Nonce không do dịch vụ sinh ra mà bị cắt thẳng từ 8 byte đầu của plaintext người chơi gửi lên, trong khi `self.key` không đổi suốt phiên. Mỗi lời gọi `Cipher.encrypt` tạo một đối tượng cipher mới với bộ đếm bắt đầu từ 0, nên keystream là hàm chỉ của `(khoá phiên, 8 byte đầu plaintext)` — hai request có cùng 8 byte đầu nhận về đúng cùng một keystream, phần còn lại của plaintext khác nhau cũng không ảnh hưởng.

Vì CTR không độn, độ dài bản mã bằng độ dài bản rõ, nên 70 byte của bí mật #0 cũng nói luôn độ dài cờ. Với một probe cùng prefix và độ dài ít nhất 70 byte:

```text
C_probe = P_probe ^ K
C_secret = P_secret ^ K
=> P_secret = C_secret ^ C_probe ^ P_probe
```

`P_probe` là ta chọn, `C_probe` do dịch vụ trả về, `C_secret` đã lấy từ đầu — tức chỉ cần prefix 8 byte của probe trùng với prefix của cờ. Dạng cờ `FortID{` đã cố định các vị trí 0..6, nên trong nonce chỉ còn một byte chưa biết ở vị trí 7. Vét cạn byte đó trên ASCII in được, không gồm khoảng trắng: 0x21–0x7E, tổng cộng 94 giá trị. Byte khoảng trắng không được thử.

## Lời giải

1. Kết nối tới instance qua TLS và lấy bản mã của bí mật #0: `Secret #0 = 70 ciphertext bytes, 1 entries`.
2. Dựng 94 probe, mỗi probe 70 byte theo cấu trúc `FortID{` + một byte ứng viên + filler in được cho đủ 70 byte, rồi gửi từng probe qua đường mã hoá của dịch vụ. Transcript lưu `sent 94 probes, 96B each, 9306B total`. Hai số liệu không khớp: 94 × 96 = 9024, không phải 9306. Bản ghi không giải thích chênh lệch 282 byte; phép khôi phục dùng bản mã 70 byte và probe tương ứng 70 byte.
3. Gọi export để lấy toàn bộ bản mã của phiên (bí mật gốc cộng các probe): `export has 95 entries`, khớp 1 + 94.
4. Với từng cặp probe/phản hồi, tính `P = C_secret ^ C_probe ^ P_probe` và giữ lại các ứng viên mà plaintext suy ra chỉ gồm byte in được: `candidates yielding fully printable plaintext: 1`. Ứng viên duy nhất có byte 7 là `S` (0x53), và đó là cờ.

## Kết quả

```text
FortID{St0p_B31ng_Cr3at1v3_With_N0nc3s_0r_You'll_R3gre7_17_33bf89db8a}
```

Cờ đọc trực tiếp từ dịch vụ đề bài. Chưa lưu phản hồi submission.

## Tái hiện

Cần instance còn hoạt động để đọc cờ thật. Cơ chế nonce reuse có thể kiểm tra cục bộ với `chall.py` và một flag test. Các snippet dưới đây chưa bao gồm giao thức menu hoàn chỉnh.

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
