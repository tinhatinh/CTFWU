# Đề bài - flag-knows-what-it-is

## Nguyên văn đề

```text
The flag knows what it is at all times. It knows this because it knows what it isn't.
Here is a flag.

9c9b9c8b9984968bdf968cdf8c8a8d9adf88979a8d9adf968bdf968c91d88bd3df88968b979691df8d9a9e8c9091d3df9e919bdf968bdf949190888cdf88979a8d9adf968bdf889e8c82

The flag format is cdctf{plaintext goes here}
```

Thẻ challenge: 500 điểm, thể loại Cryptography, tác giả `alex`. Tiêu đề bài không nằm trong bản paste nên slug lấy theo câu mở đầu của đề.

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/cipher.txt` (chuỗi hex chép nguyên văn từ đề) |
| Kích thước | 149 byte (148 hex + 1 ký tự xuống dòng) |
| SHA-256 | `23b75625f0b46c16e92de1844d77ece044918557cd472c0a398cb94da2afea75` |
| Loại file | ASCII text |
| Nhiệm vụ | Đổi chuỗi hex về plaintext của cờ |
| Định dạng cờ | `cdctf{...}` |

## Hướng giải (tóm tắt)

Mật mã là phép đảo bit từng byte (XOR `0xFF`). Quet cả 256 giá trị XOR một byte và giữ lại key cho ra ASCII in được kèm bao `cdctf{` / `}`; chỉ có đúng một key thỏa mãn.

## Chạy lại lời giải

```bash
python exploit.py files/cipher.txt
```

Kết quả: `cdctf{it is sure where it isn't, within reason, and it knows where it was}` (đã lưu trong `flag.txt`).
