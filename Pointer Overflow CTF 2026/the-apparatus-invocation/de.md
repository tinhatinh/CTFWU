# Đề bài - The Apparatus, Invocation

Chưa có ảnh thẻ đề. Mô tả dưới đây chép từ phần text của thẻ và từ trang challenge đang mở.

## Nguyên văn đề

```text
MISC 100 · Wave 1 · September 27, 2026
The Apparatus, Invocation

I see something... It's... Some kind of machine. A séance apparatus. Forty-nine candles
arranged in a seven-by-seven grid.

I remeber this, somehow. To invoke, the operator must snuff them all.

Inscription
Press, to quiet. Each press stirs the four cardinal neighbors equally. When every candle
is dark, the apparatus will speak its name.

Notes
The apparatus permits any sequence of presses. The order does not matter, only the set.
A reset returns the board to its initial state - your team's pattern is your own.
```

## Thông tin đã xác minh được

| Mục | Giá trị |
| --- | --- |
| Loại bài | Lights Out 7x7 trên trang web, không có file tải về |
| URL | `https://pointeroverflowctf.com/challenges/the-apparatus-invocation/` |
| Bàn của team 612 | `files/board.txt` (1 = nến đang cháy), đọc từ DOM |
| DOM | `#board[role=grid]` chứa 49 `button.cell[data-r][data-c][aria-pressed]` |
| Luật | Mỗi lần bấm đảo chính ô đó và 4 ô liền kề theo trục dọc/ngang |
| Điều kiện thắng | Toàn bộ tối; trang tự `POST <path>complete` với body `{"clicks": presses}` và hiện `d.flag` |
| Cờ | Server sinh và trả về trong thẻ `#flag-text`, không có sẵn trong HTML |
| Biến đã biết | `alreadySolved = false`, `presetFlag = ""` tại thời điểm làm |

## Hướng giải (tóm tắt)

Phép bấm giao hoán nên bài toán là hệ tuyến tính trên GF(2): `A x = b` với cột `j` đánh dấu
các ô bị đảo khi bấm `j`, `b` là trạng thái ban đầu. Ma trận 49x49 của lưới 7x7 có hạng 49 nên
nghiệm duy nhất: 14 lần bấm. Chi tiết trong `writeup.md`.

## Chạy lại

```bash
python exploit.py            # đọc files/board.txt, in 14 ô cần bấm và đoạn JS để dán vào trang
```

Với team khác: lấy pattern bằng

```js
[...document.querySelectorAll('#board .cell')]
  .map(e => e.getAttribute('aria-pressed') === 'true' ? '1' : '0').join('')
```

rồi thay 49 ký tự đó vào `files/board.txt` theo 7 dòng.
