# Đề bài - clear-as-glass

## Nguyên văn đề

```text
Clear as Glass
500
Forensics Rev Eng
b0b

I was working on making a new highly sophisticated note-taking web app, but I got
hacked during development. I think the attacker may have edited some of my code
before I pushed the commit, but I couldn't see anything. Please see if you can find
what they did, I don't want any of my loyal users getting hacked by my own creation!
GitHub repo: https://github.com/shkorodi/notekeeper

Flag format: cdctf{Ex4mP13_fL4g}
```

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Nguồn | `https://github.com/shkorodi/notekeeper`, `main` tại `a531ea371475532d0a6aef72a051d3bd44d1c689` |
| Artifact | `files/app.py` = blob `c68a8cd93bf573e079f24a0fa028a0b00ced0988` (`git cat-file blob HEAD:app.py`) |
| Kích thước | 5311 byte (blob gốc, LF). Checkout trên Windows có `core.autocrlf=true` ra 5429 byte CRLF, số ký tự ẩn không đổi |
| SHA-256 | `a089e78dab3ce7ca45f6303d380ba077e0fcbbd6e266474fa4bad334c63e4eaf` |
| Loại file | Python script, UTF-8, 119 dòng; dòng 6 (`notes_list`) dài 425 ký tự / 1611 byte và chứa trọn 395 ký tự vô hình U+E000A-U+E007E |
| Lịch sử | 8 commit, 1 branch `main`, 0 tag, `git fsck --full --dangling` không có object lạc |
| Commit bị nhiễm | `bd75399` "Tagging and search", Tue Mar 17 22:10:00 2026 -0400, cùng author `shkorodi <shkorodi@example.com>` |
| Số file có ký tự ẩn | 1/14 (`app.py`), 0 trong templates, static, tests, README, commit message và metadata |
| Nhiệm vụ | Tìm đoạn mã attacker cài vào và trích chuỗi cờ nó che giấu |
| Định dạng cờ | `cdctf{...}` |

## Hướng giải (tóm tắt)

Payload được cất trong `notes_list` dưới dạng ký tự Unicode vùng Tag (U+E00xx), loại
zero-width nên không hiện trong editor lẫn diff của GitHub. Vòng lặp
`chr(ord(note)-0xE0000)` dựng lại mã nguồn ASCII và `exec(tags_list)` chạy nó ngay lúc
import module. Mã nguồn tái lập chứa hai hex blob `f` và `k`; cờ là `f XOR k`, còn
`k XOR random` được đẩy ra đường dẫn URL của một lệnh `curl`.

## Chạy lại lời giải

```bash
python exploit.py files/app.py
```

Kết quả: `cdctf{G1455w0rM_w4s_pr3tTy_c0oL}` (đã lưu trong `flag.txt`).
