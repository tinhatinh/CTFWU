# notes.md — Homemaker (SunshineCTF, pwn/reverse 498đ)

**KẾT THÚC: ĐÃ CÓ CỜ.** `sun{the_future_is_now_today_well_wait_how_are_you_reading_this}`
(chạy `python exploit_homemaker.py`, khớp 2/2 lần liên tiếp). Đọc `writeup.md` để xem lời giải,
file này chỉ ghi lại nhật ký quyết định + những gì đã loại trừ.

## Đã xác lập và kiểm chứng TRÊN REMOTE

### 1. Protocol
```
frame = ESC '[' <len:u16 BE> <payload[len]> <crc8(payload)> ESC '\\'
crc8  : acc=0; với mỗi byte: acc ^= b; rồi 8 lần: acc = (acc&0x80) ? ((acc<<1)^0x2f) : (acc<<1)
        (nhân x^8 trong GF(2^8), poly 0x12f)  -- hàm tại 0x11e9
```
Bảng lệnh tại 0x21c8 (dispatcher 0x1865). cmd 1 = thẻ key (`0x1337c35f`, so sánh tại 0x12a7,
thành công thì `capacity=0x100`); cmd 2 = đấm thẻ vào `mem` (`rbp-0x110`); cmd 3 = in `mem`;
cmd 5 = `system("/bin/echo -n ''")`. Lỗi: 0xe1 header, 0xe2 độ dài, 0xe3 checksum, 0xe4 đuôi.
Dispatcher **chỉ thoát vòng lặp khi `read_frame` return < 0** (0x1a64 quay lại 0x18b9), nên
muốn chạy chain phải gửi 4 byte không phải `ESC [`.

### 2. Off-by-one ở 0x174c -> 2041 byte
`for (i = 0; i <= n; ++i) mem[i] = p[1+i]` với `n = len-1`, chặn bởi `n > capacity`.
`len = 257` -> ghi `mem[256]` = byte CRC của frame (mình chọn) = low byte của `capacity`
-> `capacity = 0x1FF`. Thẻ 512 byte thứ hai đặt nốt `capacity = 0x7F8` (nằm trong vùng ghi),
`read_frame` nhận payload tới `0x7F9` (`len+7 <= 0x800`) -> **một thẻ phủ `mem[0..0x7F8]`**.

### 3. Leak
`mem[0x100]`=capacity, `mem[0x102]`=số thẻ, `mem[0x108]`=canary, `mem[0x110]`=saved rbp,
`mem[0x118]`=return address `= base+0x1a9f`. `mema = saved_rbp - 0x130` (đã kiểm chứng).

### 4. Primitive đọc
`0x1810(ctx)` = `emit(0, ctx, [ctx+0x100])`, ràng buộc `len + 8 <= 0x800`.
* `ctx` trong thẻ -> độ dài mình đặt -> đọc stack tuỳ ý, và đọc `.bss`/GOT bằng cách đặt gate
  ngay sau vùng dữ liệu (gate ở `base+0x4090` cho `ctx = base+0x3F90` -> ra 2039 byte
  `.dynamic`+`.got`+`.data`+`.bss`).
* `ctx` chỉ vào libc -> độ dài là 2 byte may rủi, nhưng padding `0f 1f 40 00` và immediate 0
  làm mật độ gate hợp lệ cao hơn 1/32 nhiều; 20 probe là ăn.
Mỗi probe kèm 1 marker đọc từ thẻ (`HMCARD!` + index) để biết blob thuộc `ctx` nào.

### 5. Địa chỉ libc lấy được từ server (không cần file libc)
```
mem[0x298] - write = 0x11e790   (giống nhau trên 3 connection đo độc lập)
blob tại ctx = write+0x1764, dài 1976 byte, GIỐNG HẸT TỪNG BYTE giữa các connection:
  syscall       : write+0x1779, +0x17a9, +0x17d9, +0x180c, +0x1839, +0x1869, +0x1899
  pop rsi ; ret : write+0x1a02
```
Dạng wrapper `mov eax,imm; syscall; cmp rax,-4095; jae +1; ret` -> nhảy vào thẳng `syscall` là
cả hai nhánh đều `ret` về chain, dùng thay `syscall; ret`.

### 6. Chain đã dùng
`0x1810` để lại `rsi = base+0x4060` (emit buffer) và `rdx = len+8` (chọn qua gate);
`read@plt`/`write@plt` tự nạp mã syscall; **`rax` = số byte `read` lấy được** -> gửi đúng 2 byte
thì `rax = 2 = __NR_open` (không cần `pop rax`). `rdx` làm `mode` cho `open` thì bị bỏ qua vì
không đặt `O_CREAT`. Path và gate đặt trong thẻ (`0x600` / `0x700`), chain tại `0x118`.

## ĐÃ LOẠI TRỪ (quan trọng, đừng quay lại)

* **`system()` hoàn toàn vô dụng ở đây.** Chain `[pop rdi][cmd][ret][system@plt]` chạy, return
  bình thường (nhìn thấy `*** stack smashing detected ***` của `main` = chain có chạy và stderr
  ra socket), nhưng `echo`, `/bin/echo`, `echo >&2` không cho byte nào, và **`sleep 5` không gây
  trễ** -> process con không sinh ra. Image này không có `/bin/sh`. Kết luận cũ trong file này
  từng ghi là "execve bị chặn"; đúng hơn là **thiếu shell**, vì ORW bằng `open`/`read`/`write`
  vẫn chạy ngon lành.
* Stego/DTMF/không có cờ trong `.rodata`, không có `sun{` trong stack `mem[-256..+2279]`.
* GOT overwrite: FULL RELRO phủ `0x3d78..0x4000`, không ghi được.
* **libc ứng viên đã loại bằng dấu vân tay** (`write-read`, `write-system`, `write-setvbuf`,
  `write-__libc_start_main`, `write-__stack_chk_fail`):
  Ubuntu `2.35-0ubuntu3` (c3cc0/933b0/eac00), `2.35-0ubuntu3.15` (c3c50/93410/eac00),
  `2.39-0ubuntu8.9` (w-r = 0xb10, sai cả họ). Cờ không đợi nhận dạng được bản libc, nên hướng này bỏ.
* SROP: không cần thiết, và theo `reference-sunshinectf-pwn-runtime` thì `rt_sigreturn` có dấu
  hiệu bị seccomp chặn ở hạ tầng này.

## Trạng thái file
- `hmlib.py`: client protocol + leak + bump capacity + dựng card/chain.
- `exploit_homemaker.py`: khai thác hoàn chỉnh, có cờ.
- `scan_libc.py`: vòng probe đọc mã máy libc (marker hoá).
- `check_got.py`: kiểm chứng card 2 KB + primitive đọc qua GOT.
- `solve_homemaker.py`: bản probe đầu tiên (chỉ leak), giữ lại để tham khảo.
- `analysis/`: `text.asm`, `pristine.bin`, `got.bin`, `got2.bin`, `libcscan.jsonl` (blob libc
  + ctx), `libc_addrs.json`, `run_fd3.log`, `libc/` (các file deb/extract dùng cho hướng đã bỏ).
