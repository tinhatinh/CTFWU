# Đề bài - best-of-friends

## Nguyên văn đề

```text
Best of Friends
500
Cryptography
adlee7

Tom and Jerry, stuck in an endless loop of chasing each other since 1940! Are they
the best of friends or are they the worst of enemies?

The flag format is cdctf{plaintextgoeshere}
```

File đính kèm: `bestfriends.txt`. Thẻ challenge chưa có ảnh (hai docx nguồn của
`de-cards.tsv` chỉ chứa thẻ H7TEX và SunshineCTF).

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/bestfriends.txt` (copy từ: `/c/Users/Administrator/Downloads/bestfriends.txt`) |
| Kích thước | 107 byte |
| SHA-256 | `24d05085a4c80d16f3110682536ec0d314ae49412ebe0b4a7285f0a98c537269` |
| Loại file | ASCII text, with no line terminators |
| Cấu trúc | 1 dòng: 26 nhóm `/` và `\` cách nhau 1 dấu space; 82 ký tự (39 `/`, 43 `\`); 25 khoảng trắng; không có byte nào khác, không có ký tự ẩn, không có BOM, không có newline cuối file |
| Hình dạng khác nhau | 15 mẫu (độ dài 1, 2, 3, 4 với histogram 1/5/9/11) |
| Nhiệm vụ | Đọc 26 nhóm thành một chuỗi chữ cái |
| Định dạng cờ | `cdctf{...}`; ví dụ định dạng trong đề viết thường và không có khoảng trắng |

## Hướng giải (tóm tắt)

Hai ký tự gộp thành nhóm biến độ dài là chữ ký của một bảng chữ cái thay thế:
**Code Tom-Tom**, trong đó mỗi chữ cái A-Z ứng với một mẫu `/` và `\` cố định, khoảng
trắng tách chữ. Tra bảng, ánh xạ 26 nhóm, hạ về chữ thường và bọc vào `cdctf{}`.

## Chạy lại lời giải

```bash
cd "CDCTF 2026/best-of-friends"
python exploit.py files/bestfriends.txt
```

Kết quả: `cdctf{friendshipisalotlikecheese}` (đã lưu trong `flag.txt`; cờ tính cục bộ từ
file đề, chưa đối chiếu bằng submission).
Số liệu phân tích và hai hướng đã loại: `python analysis/triage.py` (log ở
`analysis/triage.txt`).
