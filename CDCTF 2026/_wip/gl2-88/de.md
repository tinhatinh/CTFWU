# Đề bài - gl2-88

## Nguyên văn đề

```text
GL2-88  500  Reverse Engineering Cryptography  (author: reep236)

A dear friend once told me, "I don't really like asymmetric encryption. It's all
just math, not REAL crypto. REAL crypto, that's symmetric and beautiful - like
feistel ciphers, you know?" So I took his concerns to heart and gave him this
symmetric stream cipher as a birthday present. I hope it's not too much math...

Can you help him find the pretty patterns inside and crack the code? The flag
format is cdctf{ThisIsTheFlag!@#}

Ciphertext:
XwFAN`aXUspHB~]bhjV>_Fmk}VJ~tx=BwsvP<hK[XOo`

Attachment: GL2-88.hs
```

Ciphertext ở trên lấy từ bản paste trong chat, **chưa đối chiếu lại với card gốc**.
Độ dài 44 ký tự, sha256 của chuỗi lưu trong `files/ciphertext.txt` là
`d83f904893e41d8cae69651272d17326026e340144ca187d695ae3a2e0c80c2f`.

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/GL2-88.hs` (copy từ: `/c/Users/Administrator/Downloads/GL2-88.hs`) |
| Kích thước | 4013 byte |
| SHA-256 | `f1c7c3dfd5819a0b7257f03cc99f731fe8329d9acba723436fb5073fa606ccbc` |
| Loại file | GHC script executable, ASCII text |
| Nhiệm vụ | Recuperate plaintext cua `encrypt(key, flag)` khi biet algorithm + ciphertext, khong biet key |
| Định dạng cờ | `cdctf{...}` |
| Alphabet map | `c2s c = (ord c - 60) mod 67`, `s2c v = chr (v + 60)` => plaintext giai ma luo ra trong `[<, ~]` |
| Key length | 11 ky tu (cuong che trong `main`) |
| Field | Z67, `P = 67`, `Q = 11`, P = 1 mod Q |

## Hướng giải (tóm tắt)

Mỗi ký tự được biến đổi bởi một ma trận `M_i = ((k_i, a_i), (0, 1))` lấy từ nhóm
GL2(Z67) sinh bởi shear `A` và dilation `B`. Hai tính chất làm sụp hệ thống:
`k_i` hoàn toàn **không phụ thuộc khoá** (chỉ do cấu trúc sinh keystream quyết định),
và `a_i` là hàm **affine** theo 11 ký tự khoá. Known plaintext `cdctf{` (6 phương
trình) cộng giả định `}` ở cuối (1 phương trình) cho một hệ tuyến tính trên Z67 với
hạng 7, còn 4 bậc tự do, tức 67^4 = 20.151.121 khoá ứng viên; quét hết rồi lọc bằng
charset và từ điển tiếng Anh thu hẹp còn 3.431 ứng viên toàn chữ cái.

## Trạng thái

**CHƯA RA CỜ.** Machine attack đã được xác minh (xem `notes.md` H6/H7), nhưng không
ứng viên nào trong không gian khoá đọc được như tiếng Anh, nên đầu vào (ciphertext
paste) hoặc giả định `}` ở cuối còn mở. Bài đang nằm ở `_wip/`.

## Chạy lại lời giải

```bash
python exploit.py            # tu kiem chung port + do khong gian khoa
python exploit.py --scan     # in 20 ung vien dau tien
```
