# Đề bài - crypto-cat-2

## Nguyên văn đề

```text
The Epic Adventures of Crypto Cat Caticus Catanius (2/5)
496
Crypto
alex

Well well well, it seems you have cracked my first key. No meowtter, a litany
remeown. Surely you will be incatpable of cracking this encryption?! Meor Meor Meor.

ec eb ec fb e9 f4 ea f7 ec e3 fa fc be f9 ea d0 f7 bf fd be e1 d0 fb e7 ea fc ea d0
ed f6 fb bc fc d0 ee e1 eb d0 ba fb fa e9 e9 f2 85
```

*(chưa có thẻ challenge dạng ảnh cho chuỗi này; phần text trên là toàn bộ nội dung thẻ,
kể cả bản mã. Không có file tải về và không có instance.)*

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/ciphertext.txt` (chép lại nguyên văn 45 token hex trong thẻ đề) |
| Kích thước | 135 byte |
| SHA-256 | `fc729a7d866ee019d3da211dd885f86922885d6d2205e51e558c1c318c1360dd` |
| Loại file | ASCII text |
| Dữ liệu | 45 token hex, độ dài chẵn, giá trị byte trải từ `0x85` đến `0xfd`, 24 giá trị phân biệt |
| Nhiệm vụ | Recover plaintext của bản mã, đúng định dạng cờ |
| Định dạng cờ | `cdctf{...}` |

## Hướng giải (tóm tắt)

Toàn bộ 45 byte đều `>= 0x80`, tức là ảnh của ASCII in được (`0x20-0x7e`) qua một phép
XOR bít. Quét 256 khóa một byte: 0 khóa cho ASCII in được tuyệt đối, 5 khóa cho ra ASCII
nếu cho phép thêm tab/LF/CR, và đúng một khóa trong số đó mở đầu bằng `cdctf{`. Khóa
`0x8f` dịch ra một câu leetspeak trọn nghĩa, byte cuối `0x85` là ký tự xuống dòng.

## Chạy lại lời giải

```bash
python exploit.py files/ciphertext.txt
```

Kết quả: `cdctf{exclus1ve_x0r1n_these_byt3s_and_5tuff}` (đã lưu trong `flag.txt`).
