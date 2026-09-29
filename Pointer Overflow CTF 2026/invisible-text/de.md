# The Invisible Text (STEG 200 / WAVE 1)

Trang: <https://pointeroverflowctf.com/challenges/invisible-text/>
Team: 612. Điểm: 200. Nhãn: STEG 200 · WAVE 1.

## Challenge Text

> Humans are the dominant species on the planet. No question. How did we get that way? Because we're smarter? Because we can run longer? Those things might be true - but not for a long time after we're born. We'd never survive to adulthood if those were our main gifts.
>
> No, our main survival trait is exactly what babies are best known for: Crying. Communicating. And we have found millions of ways to do it. Languages, written words, radio, TV, walkie talkies, morse code, ASL... There's just no shutting us up. We communicate, we band together, and we survive. We don't, we die.
>
> But not all messages are broadcast for the world to see. Some secrets need to be kept, and keeping them is an art. In this challenge I have a hidden message. It's not difficult to work out, but I'm confident you'll see what I'm communicating if you look in the right place.

> YOUR TEAM'S FILE
> → invisible_text.py (generated for your team; look closely)
> f027442b37a521f4a775ec56d37336df446d83e7acd641042e28af030f745320

> Run it, read it, listen for what it says silently.

## Verified Metadata

| Mục | Giá trị |
|---|---|
| link tải | `https://pointeroverflowctf.com/challenges/invisible-text/download` |
| `Content-Disposition` | `attachment; filename=invisible_text_612.py` (có hậu tố `_612` = id team, file sinh riêng cho team) |
| kích thước | 4245 byte |
| sha256 | `f027442b37a521f4a775ec56d37336df446d83e7acd641042e28af030f745320` khớp card |
| format code page | UTF-8, 81 dòng, chỉ có 1 ký tự ngoài ASCII (`—` em dash trong comment) |
| endpoint nộp | `POST /challenges/invisible-text/submit`, body `{"flag": "..."}`, trả `{"correct":bool,"message":str}` |
| ý nghĩa "solved" | server xác nhận `{"correct":true,"message":"Correct."}`; không trả về xâu flag nào khác |

## Approach Summary

Hai lớp vô hình trong file nguồn:

1. **Lớp dẫn đường**: `invisible_text.py` là `diary_reader.py`, nối 46 chunk base64, `b64decode` rồi `zlib.decompress` ra một bức **braille art** 33 dòng. Chạy script chỉ in ra tranh, trong tranh không có text (mật độ dot: 115 ô đầy 8 chấm, 85 ô `251`, 79 ô `253` -> vùng tô đặc, không phải chữ nổi).
2. **Lớp chứa flag**: 47 dòng có **whitespace ở cuối dòng**. Các dòng dữ liệu (1, 3, 5, ..., 45) kết thúc bằng một chuỗi space/tab mà 7 ký tự cuối là 7 bit: `tab = 1`, `space = 0`, MSB luôn = 1 nên mỗi dòng cho đúng một ASCII 7-bit. 23 dòng dữ liệu -> 23 ký tự -> vừa khít `POCTF{` + 16 + `}`. Các dòng chẵn chỉ có 1 ký tự tab làm ngăn cách, phần space thừa phía trước là padding.

## Reproduce

```bash
cd "C:/Users/Administrator/Downloads/CTFWU/Pointer Overflow CTF 2026/invisible-text"
python exploit.py files/invisible_text.py
```
