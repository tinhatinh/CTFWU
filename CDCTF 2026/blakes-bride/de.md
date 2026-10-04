# Đề bài - blakes-bride

## Nguyên văn đề

```text
Blake's Bride
500
Password Cracking Forensics
adlee7

An indecisive bride made their wedding passwords pretty insecure on several
different wedding preparation sites. Seems they're not sure if they want to
marry Blake. To be.... or not to be... that is the question they struggle with.
Here are their three passwords, stored and encrypted in an unorthodox manner.
All passwords are one word related to wedding events followed by three numbers.

The flag format is cdctf{password1-password2-password3}

(I wonder if there's something wrong with Blake. To be this unsure about the
wedding... I dunno man, maybe he did something...)
```

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/blake.png` (copy từ: `C:/Users/Administrator/Downloads/blake.png`) |
| Kích thước | 139894 byte |
| SHA-256 | `60cfcb420af6bd3b30b6fd0a9ee9abcb5584a2d47cb179dafc8448dac673178c` |
| Loại file | PNG image data, 981 x 731, 8-bit/color RGB, non-interlaced |
| Nhiệm vụ | Recover ba mật khẩu `<từ liên quan đám cưới> + 3 chữ số` từ ba digest cất trong metadata |
| Định dạng cờ | `cdctf{password1-password2-password3}` |

## Hướng giải (tóm tắt)

Ba digest 128 ký tự hex nằm trong `iTXt` (XMP `exif:UserComment`), cách nhau bằng `-`.
Độ dài 64 byte khớp với SHA-512 nhưng phép thử trực tiếp loại SHA-512 và SHA3-512;
thuật toán thật là BLAKE2b, đúng như tên file `blake.png` và câu "something wrong with
Blake". Không gian mật khẩu là từ điển đám cưới nối với `000..999`, bẻ bằng vòng lặp
`hashlib.blake2b`.

## Chạy lại lời giải

```bash
python exploit.py files/blake.png
```

Kết quả: `cdctf{epithalamium738-trousseau201-honeymoon069}` (đã lưu trong `flag.txt`).
