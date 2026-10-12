---
title: "Soul Forge"
category: "Crypto"
tags: ["two-time-pad", "keystream-reuse", "crib-dragging", "xor"]
solve_date: "2026-10-09"
language: "vi"
---

# Soul Forge

**Flag:** `OWASP{s0ul_f0rge_pr1m3s_4r3_n3v3r_r4nd0m}`
**Artifacts:** hai blob hex `T1` (57 byte) và `T2` (77 byte), được nhúng trực tiếp trong script của workspace; không có file artifact độc lập.

## Đề bài

Đề (Easy, 100 điểm) chỉ gồm hai dòng hex và yêu cầu recover nội dung:

```text
T1 = 5945b2affe943fcc07714e6fdf6a4bc19ebd9232b30a543ef09deeded7be581938adb099bd2c81134999a63d456aaef68addd2275899652d26
T2 = 5945b2affe943fcc07714e6fc16a5bc09aaeed32c6097d088080f29cc5b7270d6db2b2918039815104cfa3070361bdda858dd67d4caf747c668621b710e6e1e2397af4e35719fb59c817dd62cd
```

Định dạng cờ là `OWASP{...}`, không kèm dịch vụ remote.

## Phân tích

Độ dài: `T1` 57 byte, `T2` 77 byte. XOR từng byte trên phần chồng nhau cho:

```text
D = 0000000000000000000000001e00100104137f0075032936701d1c4212097f14551f02083d1500424d56053a460b132c0f50045a1436115140
identical prefix: 12 bytes
```

12 byte đầu của `D` bằng 0, tức `T1` và `T2` có 12 byte đầu giống hệt nhau. Nếu hai message dùng chung một keystream — `C1 = P1 ^ K`, `C2 = P2 ^ K` — thì `C1 ^ C2 = P1 ^ P2`, và byte bằng 0 nghĩa là hai dữ liệu gây nhiễun rõ trùng nhau ở vị trí đó. Kiểm tra xem keystream có phải khoá lặp ngắn hay không: quét period 1..56 với ràng buộc mọi byte giải mã đều in được, `soulforge_repeating.py` không in ra dòng nào, tức không tồn tại period nào từ 1 tới 56 thoả; phép đo tự do hơn ở `soulforge_period.py` cũng không nổi bật period nào (tỉ lệ cao nhất 0.370 tại period 30 của `T1`). Mô hình làm việc được chấp nhận là one-time pad bị dùng lại hai lần, `D = P1 ^ P2`.

`D` cũng cho biết vị trí các byte mà hai dữ liệu gây nhiễun rõ khác nhau: các chỉ số có `D[i] = 0` là `[0..11, 13, 19, 38]`.

Crib dragging: vì cờ bắt đầu bằng `OWASP{`, trượt chuỗi 6 ký tự này lên `D` và giữ lại các alignment mà phía đối diện cũng toàn byte in được cho 21 vị trí:

```text
all-printable alignments: 21
  off= 0 other=b'OWASP{'
  off= 1 other=b'OWASP{'
  off= 2 other=b'OWASP{'
  off= 3 other=b'OWASP{'
  off= 4 other=b'OWASP{'
  off= 5 other=b'OWASP{'
  off= 6 other=b'OWASP{'
  off= 7 other=b'OWASPe'
  off= 8 other=b'OWASN{'
  off= 9 other=b'OWAMPk'
  off=10 other=b'OW_S@z'
  off=12 other=b'QWQRTh'
  off=14 other=b'_VE@/{'
  off=16 other=b'KD>S%x'
  off=17 other=b'\\(A&SR'
  off=18 other=b'0W4PyM'
  off=20 other=b':The f'
  off=21 other=b'L~w#Mg'
  off=22 other=b'fa1NL9'
  off=33 other=b'PUInE{'
  off=34 other=b'M_|FP9'
```

Bộ lọc "in được" không đủ để chọn: các offset 0..6 là nghiệm suy biến (đúng vùng `D` bằng 0, kéo theo dữ liệu gây nhiễun rõ hai bên giống nhau), các offset 27 và 50 bị chính script loại vì không phải ASCII. Trong các ứng viên còn lại, chỉ offset 20 sinh ra đoạn đọc được như tiếng Anh — `:The f`. Đó là cơ sở để cố định vị trí cờ, và cũng là điểm duy nhất trong suy luận phải dùng tới phán đoán ngôn ngữ chứ không chỉ số học.

Với `P2[20:]` mở rộng thành `:The forge remembers every sacrifice.`, `P1 = D ^ P2` trên vùng chồng nhau cho 37 ký tự liên tiếp của cờ. Ngay từ bước này đã có một giới hạn cố định của dữ liệu: `T1` dài 57 byte và cờ bắt đầu ở chỉ số 20, nên miền suy ra được kết thúc tại ký tự thứ 37; cờ đã ghi nhận dài 41 ký tự, vì vậy 4 ký tự cuối không nằm trong bất kỳ vùng nào mà artifact mô tả tới. Chi tiết được trình bày ở phần Lời giải và Kết quả.

## Lời giải

```python
T1 = bytes.fromhex("5945b2affe943fcc07714e6fdf6a4bc19ebd9232b30a543ef09deeded7be581938adb099bd2c81134999a63d456aaef68addd2275899652d26")
T2 = bytes.fromhex("5945b2affe943fcc07714e6fc16a5bc09aaeed32c6097d088080f29cc5b7270d6db2b2918039815104cfa3070361bdda858dd67d4caf747c668621b710e6e1e2397af4e35719fb59c817dd62cd")

N = min(len(T1), len(T2))
D = bytes(a ^ b for a, b in zip(T1, T2))
print("len T1, len T2, overlap :", len(T1), len(T2), N)
print("D =", D.hex())
print("identical prefix:", next(i for i in range(N) if D[i] != 0), "bytes")

crib = "OWASP{"
hits = [(o, bytes(D[o + j] ^ ord(crib[j]) for j in range(len(crib))))
        for o in range(N - len(crib) + 1)
        if all(32 <= (D[o + j] ^ ord(crib[j])) < 127 for j in range(len(crib)))]
print("all-printable alignments:", len(hits))
for o, cand in hits:
    print("  off=%2d other=%r" % (o, cand))

off = 20
p2 = ":The forge remembers every sacrifice."
p1 = bytearray(b"?" * len(T1))
for j, ch in enumerate(p2):
    i = off + j
    if i >= len(T1):
        break
    p1[i] = D[i] ^ ord(ch)
recovered = "".join(chr(b) for b in p1)
print("P1 =", repr(recovered))
print("chars derived:", len(recovered) - recovered.count("?"))

recorded = "OWASP{s0ul_f0rge_pr1m3s_4r3_n3v3r_r4nd0m}"
got = recovered[off:]
print("derived from artifact :", repr(got), len(got), "chars")
print("recorded flag         :", recorded, len(recorded), "chars")
print("derived is prefix of recorded:", recorded.startswith(got))
print("outside the overlap   :", repr(recorded[len(got):]))
print("max chars reachable   :", len(T1) - off)
```

```text
len T1, len T2, overlap : 57 77 57
D = 0000000000000000000000001e00100104137f0075032936701d1c4212097f14551f02083d1500424d56053a460b132c0f50045a1436115140
identical prefix: 12 bytes
all-printable alignments: 21
  off= 0 other=b'OWASP{'
  off= 1 other=b'OWASP{'
  off= 2 other=b'OWASP{'
  off= 3 other=b'OWASP{'
  off= 4 other=b'OWASP{'
  off= 5 other=b'OWASP{'
  off= 6 other=b'OWASP{'
  off= 7 other=b'OWASPe'
  off= 8 other=b'OWASN{'
  off= 9 other=b'OWAMPk'
  off=10 other=b'OW_S@z'
  off=12 other=b'QWQRTh'
  off=14 other=b'_VE@/{'
  off=16 other=b'KD>S%x'
  off=17 other=b'\\(A&SR'
  off=18 other=b'0W4PyM'
  off=20 other=b':The f'
  off=21 other=b'L~w#Mg'
  off=22 other=b'fa1NL9'
  off=33 other=b'PUInE{'
  off=34 other=b'M_|FP9'
P1 = '????????????????????OWASP{s0ul_f0rge_pr1m3s_4r3_n3v3r_r4n'
chars derived: 37
derived from artifact : 'OWASP{s0ul_f0rge_pr1m3s_4r3_n3v3r_r4n' 37 chars
recorded flag         : OWASP{s0ul_f0rge_pr1m3s_4r3_n3v3r_r4nd0m} 41 chars
derived is prefix of recorded: True
outside the overlap   : 'd0m}'
max chars reachable   : 37
```

**Giới hạn:** với crib đã lưu tại offset 20, script khôi phục 37/41 ký tự cờ. `T1` kết thúc tại chỉ số 56, nên đuôi `d0m}` nằm ngoài vùng khôi phục và lấy từ cờ đã lưu. Crib là đầu vào giả định, không được xác định duy nhất từ hai ciphertext.

## Kết quả

```text
OWASP{s0ul_f0rge_pr1m3s_4r3_n3v3r_r4nd0m}
```

37 ký tự đầu suy ra trực tiếp từ hai blob bằng quan hệ `P1 = (T1 ^ T2) ^ P2` với crib ở offset 20; 4 ký tự cuối lấy từ cờ đã ghi nhận trong hồ sơ của giải, không suy ra được từ artifact vì `T1` kết thúc trước đó. Không có dịch vụ remote cho bài này. Chưa lưu phản hồi submission.

## Tái hiện

Python 3, chỉ stdlib. Lưu block trong phần Lời giải thành `soulforge_crib.py` rồi chạy:

```console
$ python soulforge_crib.py
```

Hai blob và crib được chứa trực tiếp trong script. Script chỉ khôi phục 37 ký tự đầu; phần đuôi `d0m}` là giá trị đã lưu, không được suy ra từ hai blob.
