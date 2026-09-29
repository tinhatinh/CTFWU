---
title: "The Apparatus, Invocation - Misc"
date: 2026-09-29 23:31:27 +0700
lastmod_at: 2026-09-29 23:31:27 +0700
categories: [Misc]
tags: [pointer-overflow, Misc]
image:
  path: /CTFWU/Pointer%20Overflow%20CTF%202026/the-apparatus-invocation/files/de.png
---
{% raw %}
**Điểm:** 100 · **Wave:** 1 · **Cờ:** `POCTF{3.612.H5VA2OHFE333SO62.EAIOF76YB2L4XMZTFSV4CPOEOX}`

**Artifact:** không có file tải về; bàn cờ sinh theo team và nằm ngay trên trang
`/challenges/the-apparatus-invocation/`. Trạng thái ban đầu của team 612 lưu ở `files/board.txt`.

## Đề bài

Bốn mươi chín nến xếp lưới 7x7. Bấm vào một nến sẽ tắt nó và đánh động bốn nến liền kề theo
trục dọc ngang. Muốn gọi ra tên của apparatus thì phải làm tối toàn bộ. Trang ghi rõ thứ tự bấm
không quan trọng, chỉ tập hợp các lần bấm là có nghĩa, và Reset đưa bàn về đúng trạng thái đầu.

## Phân tích ban đầu

Đọc DOM để lấy hai thứ: trạng thái bàn và cách trang kiểm chứng.

```html
<div id="board" class="board" role="grid" aria-label="Invocation board">
  <button type="button" class="cell" data-r="0" data-c="0" role="gridcell"
          aria-label="Candle at row 1 column 1" aria-pressed="false"></button>
  ...
```

Trong inline script (4.3 KB) có ba chi tiết quyết định cách làm:

- Cờ **không** nằm trong HTML. `const presetFlag = ""` và `const alreadySolved = false`, còn
  khi thắng thì trang gọi `fetch(window.location.pathname + 'complete', {body: JSON.stringify({clicks: presses})})`
  rồi gán `$flagTxt.textContent = d.flag`. Nghĩa là server mô phỏng lại danh sách bấm trên bàn
  của team và tự sinh cờ; không có đường tắt nào từ client.
- `presses` là mảng `{r, c}` được push mỗi lần bấm, nên chỉ cần kích đúng handler của trang là
  đủ, không cần tự tính lại trạng thái.
- Bàn được render bằng `classList.toggle('lit', on)` song song với `aria-pressed`, nên đọc
  `aria-pressed` theo thứ tự DOM (row-major) cho ra đúng ma trận 7x7.

Trạng thái đọc được (`1` là nến đang cháy):

```text
0000000
0000110
1100001
1001011
1000110
1111010
0110110
```

## Chuỗi khai thác

**Bước 1 - Mô hình hoá.** Vì mỗi phép bấm là một phép cộng không đổi trên GF(2) và chúng giao
hoán, bài toán là `A x = b`: hàng `i` tương ứng với ô `i`, `A[i][j] = 1` nếu bấm `j` đảo ô `i`
(tức `j = i` hoặc `j` kề `i`), và `b[i]` là trạng thái ban đầu của ô `i` (cần bị đảo lẻ lần).

**Bước 2 - Giải hệ.** Khử Gauss trên ma trận 49x50. Hạng của `A` là 49, không có biến tự do,
nên nghiệm là duy nhất - bàn nào cũng giải được và không có khả năng chọn nhầm nghiệm. Kết quả
cho team 612 là 14 ô (0-indexed):

```text
(2,4) (2,5) (3,0) (3,1) (3,3) (4,0) (4,6) (5,0) (5,3) (5,4) (5,6) (6,0) (6,3) (6,5)
```

**Bước 3 - Kiểm chứng cục bộ.** Mô phỏng lại 14 phép bấm trên bàn ban đầu bằng chính hàm
`neighbors()` trong script, xác nhận mọi ô về 0 trước khi động vào trang.

**Bước 4 - Chơi trên trang.** Bắn sự kiện click thật vào đúng 14 button để handler của trang tự
ghi `presses` và tự gọi endpoint:

```js
() => { const P=[[2,4],[2,5],[3,0],[3,1],[3,3],[4,0],[4,6],[5,0],[5,3],[5,4],[5,6],[6,0],[6,3],[6,5]];
  for (const [r,c] of P) document.querySelector(`#board .cell[data-r="${r}"][data-c="${c}"]`).click(); }
```

`press-count` lên 14, `#flag-box` hiện và `#flag-text` nhận cờ từ server.

## Cờ

```text
POCTF{3.612.H5VA2OHFE333SO62.EAIOF76YB2L4XMZTFSV4CPOEOX}
```

Khớp khuôn `POCTF{<cid>.<team_id>.<nonce>.<sig26>}` với cid 3, team 612, nonce 16 ký tự,
sig base32 26 ký tự.

## Chạy lại

```bash
cd the-apparatus-invocation
python exploit.py
```

Script in lại 14 ô cần bấm từ `files/board.txt` kèm đoạn JS dán vào trang. Muốn làm với bàn của
team khác, thay `files/board.txt` bằng pattern đọc từ DOM theo lệnh ở `de.md`.

{% endraw %}
