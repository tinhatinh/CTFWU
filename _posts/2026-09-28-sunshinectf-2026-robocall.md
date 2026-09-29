---
title: "RoboCall — Pwn (Hard)"
date: 2026-09-28 16:53:17 +0700
lastmod_at: 2026-09-28 16:53:17 +0700
categories: [Pwn]
tags: [sunshinectf, Pwn]
image:
  path: /CTFWU/SunshineCTF%202026/robocall/files/de.png
---
{% raw %}
**Flag:** `sun{you_must_be_some_sort_of_nimble_space_navigator}`

## 1. Loại trừ trước khi tìm đúng

Binary là PIE, NX, Partial RELRO, có bảng symbol đầy đủ. Quét toàn file:

- không có một `pop reg; ret` nào (chuỗi `5f c3`, `5e c3`, `5a c3` đều 0 kết quả),
- không có `system`/`execve` trong PLT,
- mọi buffer input đều được chặn đúng kích thước.

`raw_readline(buf, len)` đọc từng byte và dừng ở `count = len-1`, rồi ghi NUL tại
`buf[len-1]`. Với `buf = rbp-0x100, len = 0x100` thì byte cuối cùng ghi được là
`rbp-0x01`. Saved RBP nằm tại `[rbp]`, không phải `[rbp-8]`, nên nó nằm ngay sau
vùng ghi đúng 1 byte. Kiểm chứng động: gửi 255 byte 'A' vào prompt cuối của
`payment_info`, chương trình vẫn in tiếp các dòng sau đó, nghĩa là không có gì bị đè.

Kết luận: không có overflow, không có ROP. Vậy "navigate this stack" nghĩa là gì?

## 2. Bug thật: một ô stack không bao giờ được ghi

```asm
raw_parse_int(rdi=str, rsi=out):
  14c6:  cmp    al,0x2f          ; ký tự đầu không phải chữ số
  14c8:  jle    14de
  14de:  mov    eax,0x0
  14e3:  jmp    156a             ; return 0  -> KHÔNG ghi *out
```

Nhánh trả về sớm bỏ qua việc ghi `*out`. Mọi nơi gọi đều truyền một biến local chưa khởi
tạo (chỉ `main`, `start_position`, `initial_call` là tự gán 0 ở đầu hàm). Và `cancel_plan`
thì in biến đó ra:

```asm
2f34:  print "You've entered \""
2f4b:  raw_print_int([rbp-0x204])      ; ô chưa được ghi
2f50:  print "\", are you sure?"
```

Chỉ cần trả lời không phải số là chương trình in ra 4 byte rác của stack dưới dạng một
số nguyên có dấu. Đó là primitive đọc bộ nhớ.

## 3. Cờ được rải trên stack

`place_flag()` chạy trước menu:

```asm
18f8:  open("flag.txt", 0)
1938:  read(fd, rbp-0x2060, 0x3c)          ; 60 byte
loop i = 0..12:
  d    = CHUNK_DEPTH[i]                   ; bảng u32 tại 0x4020
  dest = rbp-0x2020 + (0x19dc - d)        ; = rbp - 0x644 - d
  sao chép 4 byte flag[i*4 .. i*4+3] vào dest
```

place_flag dùng frame 0x2060 byte (probe 2 lần 0x1000), rồi return mà không in gì. Tính
theo rbp của main, 13 mẩu cờ nằm tại:

```
rbp_main - {0xb64,0xbe4,0xc84,0xcd4,0xd04,0xda4,0xdf4,0xe24,0xec4,0xf14,0xf44,0xf64,0xfe4}
```

Toàn bộ đều nằm trong vùng mà các frame của cây menu dùng lại về sau.

## 4. "Điều hướng stack"

Vì `rbp_callee = rbp_caller - (frame_size + 16)` và mọi frame là bội số của 0x10, độ sâu
của ô leak `rbp_cancel_plan - 0x204` chỉ phụ thuộc vào chuỗi menu đã bấm. Bảng frame:

```
start_position 0x110  initial_call 0x170  report_outage 0x150
technical_support 0x160  other_inquiries 0x190  cancel_plan 0x430
```

Đường ngắn nhất tới cancel_plan là `1 -> 6 -> 2` (gọi điện -> vấn đề khác -> huỷ), cho ô
leak ở `rbp_main - 0x764`. Mỗi lần lồng thêm một cấp sẽ dịch ô đó xuống thêm đúng kích
thước frame. BFS trên đồ thị menu (`analysis/paths.py`) tìm ra đường đi chạm cả 13 offset;
kết quả được mã hoá trong `EDGES`/`plan()` của `solve.py`.

Ví dụ hai đường thực dụng:

| mẩu | chuỗi lựa chọn |
|---|---|
| 0 (`sun{`) | `1 6 2` |
| 12 (`tor}`) | `1 6 2` rồi cancel_plan tự gọi nó 2 lần (lý do huỷ = 4) |

Giao thức trong một cancel_plan:

- lần đầu tiên nó gọi `login_roleplay` (3 câu hỏi), vì `start_position` xoá cờ `userData+4`;
- q1: trả lời không phải số -> ô giữ nguyên giá trị cũ;
- q2: in ra `You've entered "<ô đó>"` -> đọc 4 byte;
- nếu muốn lồng sâu hơn: q1 = `0`, q2 = `1` (để đi tiếp tới menu lý do), q3 = `4`
  (fun fact rồi `cancel_plan()` đệ quy).

Chạy 13 kết nối, mỗi kết nối một đường đi, ghép 13 x 4 byte lại là ra cờ.

## 5. Mấy chi tiết phụ giúp sống sót

- Nhập `42` ở câu "Press enter to start." sẽ đặt `be_annoying = 0`, tắt toàn bộ `nanosleep`,
  không còn phải chờ hàng chục giây mỗi lần gọi `speak_with_an_operator`.
- Cây menu nói dối theo đúng chủ đề dark-pattern: muốn gặp `cancel_plan` phải bấm 2 ở
  mục "other inquiries", dù menu ghi "press 3 to speak with an operator". Hai lệnh `call`
  nằm cạnh nhau trong disassembly khiến mình đoán ngược; chỉ một kết nối thăm dò là ra.
- Không có marker `>>>` ở menu của `start_position`, nên đồng bộ theo chuỗi dấu hiệu riêng
  của từng prompt (`Press 8 for yes.`, `Please enter the name of your first pet`, ...).

{% endraw %}
