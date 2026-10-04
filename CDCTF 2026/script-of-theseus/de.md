# Đề bài - script-of-theseus

## Nguyên văn đề

```text
Script of Theseus
493
Forensics
alex

I wrote this script, and my buddy asked me, "This script is a real Theseus-Ah-Thing. If I delete
and rewrite every line of this script, is it still the same script?," and I said, "Why don't you
try it out for yourself, buddy? Tell me how it goes," and he agreed to.

However, he's a bit of a silly Windows user, and I'm more of the Linux chad type, and I think that
maybe his script truly isn't the same? I have provided the original and his version of the script.
Please find the difference, and provide a hex code (with capital letters) of one byte of the
difference.

Flag format is cdctf{FF}
```

Thẻ challenge: 493 điểm, thể loại Forensics, tác giả `alex`. Đề cho hai file tải về máy, không có
instance web.

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact 1 | `files/original_epic_python_script.py` (copy từ: `C:\Users\Administrator\Downloads\original_epic_python_script.py`), 156 byte, sha256 `56c4472cb2f3876c86932bfecb18d276af7f8e8a4b6fb146b40d02d8f90f0b3f`, `Python script, ASCII text executable` |
| Artifact 2 | `files/replaced_epic_python_script.py` (copy từ: `C:\Users\Administrator\Downloads\replaced_epic_python_script.py`), 163 byte, sha256 `c88ef02ea2a56fdd9957a86f79d8799fe2b2388a06fe4b9b979f34bbfa402c57`, `Python script, ASCII text executable, with CRLF line terminators` |
| Nhiệm vụ | Tìm byte khác nhau giữa hai bản, trả hex in hoa của một byte |
| Định dạng cờ | `cdctf{FF}` (FF = hex một byte, in hoa) |

Hai file là cùng một script 7 dòng (`#!/usr/bin/env python3` + đoạn `input`/`if`/`else`), chỉ khác
nhau ở các byte kết thúc dòng.

## Hướng giải (tóm tắt)

Đếm tần suất byte của hai file: bản `replaced` dài hơn đúng 7 byte và toàn bộ phần thừa là byte
`0x0D`, mỗi `0x0D` nằm ngay trước một `0x0A`. Xoá hết `0x0D` khỏi bản `replaced` thì thu lại nguyên
văn 156 byte của bản gốc, nên khác biệt duy nhất là line ending LF (Linux) đổi thành CRLF (Windows).
Byte cần nộp là `0D`.

## Chạy lại lời giải

```bash
python exploit.py
```

Kết quả: `cdctf{0D}` (đã lưu trong `flag.txt`).
