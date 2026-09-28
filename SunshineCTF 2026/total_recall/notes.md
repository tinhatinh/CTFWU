# Total Recall - notes

Log theo giả thuyết, mới nhất ở dưới. Mọi kết quả đều đo trên remote thật, mỗi lần thử
dùng một connection, gọi tuần tự, có timeout ở mọi lần đọc.

---

## H1 - "phân tích tĩnh rồi hãy đánh remote"

`Type: EXEC` nên không PIE, mọi địa chỉ code là hằng số. `.text` chỉ 108 byte và hai
LOAD segment khớp mô tả trong file. 8 byte remote gửi về khớp đúng hành vi
`write(1, rsp, 8)` của f1.

result: OK - được phép phân tích trên bản local rồi đánh thẳng, không cần leak code.

## H2 - "thiếu PT_GNU_STACK nên stack executable (READ_IMPLIES_EXEC)"

Local đúng là `phnum = 2`, không có PT_GNU_STACK. Trên x86-64 Linux trường hợp này
kernel thường bật `READ_IMPLIES_EXEC`, nên shellcode đặt trong buffer sẽ chạy được.
Việc `read(0, buf, 0x400)` không cắt ở NUL cũng cho phép shellcode chứa mọi byte.

- Thử 1: `exploit.py` bản đầu, shellcode 24 byte `execve("/bin/sh")` tại
  `buf = L-0x80`, ret về `buf`.
- Thử 2: `analysis/probe_sled.py`, NOP sled 0x50 byte bắt đầu ngay tại buf, ret về
  `L-0x60`, tức nằm giữa sled dù `buf` là `L-0x78` hay `L-0x80`.

Cả hai: không nhận được byte nào, connection đóng sau ~0.5s. Khác hẳn case chương trình
start lại (H3), khi đó nhận đúng 8 byte.

result: DEAD trên remote - đổi offset kiểu nào thì nhảy vào vẫn chết im. Stack không
thực thi được trên máy chủ.

## H3 - "đã chiếm được RIP chưa?"

`analysis/probe_exec.py`:

- ghi `0x401000` vào ô return → remote gửi về thêm 8 byte, và giá trị đó là con trỏ stack,
  nghĩa là chương trình thật sự start lại.
- chuỗi `[buf+0x80] = 0x401032`, `[buf+0x88] = 0x401016` → leak trả về đúng `buf+0x88`,
  khớp việc `ret` của f2 để lại `rsp = buf+0x88` và gadget 0x401032 chạy xong rồi ret.

result: OK - hijack điều khiển được, `RET_OFF = 0x80` chính xác, ROP chain đi được.

## H4 - "code reuse thì dùng gì khi binary không có libc?"

Trong 108 byte chỉ có: `write(1, rsp, 8)`, `read`, `syscall`, `ret`, `pop rax`, và các
lệnh `mov rdi/rax/rdx, imm`. Không có `pop rdi`, và mọi `syscall` trong script gốc đều
bị một `mov rax, imm` dẫn trước.

Nhưng nhảy vào **giữa** chuỗi lệnh thì khác:

- `0x40104c` và `0x401069` là `syscall; ret` trần (vào sau lệnh `mov rax,0` phía trên),
  nên `rax` giữ nguyên giá trị cũ.
- `rax` sau `read` chính là số byte đọc được. Gadget `0x401032` có `rdx = 0x18`, nên chỉ
  cần cấp phát đúng 15 byte thì `rax = 15 = __NR_rt_sigreturn`.

=> SROP được thiết kế sẵn trong binary, không cần tới gadget của libc.

result: OK - đây là hướng đi.

## H5 - "sigframe bắt đầu bằng siginfo hay không?"

- Giả thuyết A: `rsp` trỏ tới `struct rt_sigframe`, tức có 128 byte `siginfo` trước
  `ucontext`, nên `sigcontext` nằm tại `frame + 0xA8`.
- Giả thuyết B: `rsp` trỏ thẳng tới `ucontext`, `sigcontext` nằm tại `frame + 0x28`.

`analysis/diag_sigreturn.py` chạy ba biến thể: A-only, B-only, và A+B đồng thời (hai cửa
sổ chồng lên nhau chỉ ở những trường mà cửa sổ kia không đọc).

- A-only: 0 byte.
- B-only: 8 byte.

result: A DEAD. B là cách kernel trên máy chủ đọc frame.

## H6 - "trường rsp nằm ở sigcontext+0x78"

`analysis/srop2.py` đặt rip = `0x401017` (`mov rsi,rsp; write(1,rsp,8)`) và rsp slot =
`sigcontext+0x78` trỏ tới `buf+0x88` - nơi chứa hằng số `0x401069`. Kỳ vọng nhận
`0x401069`, thực nhận `00*8`.

`analysis/locate_rsp_slot.py`: mỗi ô của frame trỏ tới một địa chỉ đọc được trong hai
page của binary; nội dung trả về chỉ ra `rsp` được nạp từ `frame+0xA0`. Vì `sigcontext`
nằm ở `frame+0x28` nên `0xA0 - 0x28 = 0x78`.

`analysis/measure_rsp.py` là phép đo gọn nhất: rip = `0x401000`, mọi ô frame chứa sentinel
`buf+0x300+j`; chương trình start lại leak `rsp - 16`, và con số trả về khớp chính xác
sentinel tại `j = 0xA0`.

result: OK - `sigcontext+0x78` (rsp) và `sigcontext+0x80` (rip) đều đúng. Giá trị `00*8`
lúc trước **không** phải do sai slot, mà do H7.

## H7 - "buf = L - 0x78"

Toàn bộ mâu thuẫn nằm ở việc `push rsp` lưu giá trị nào:

- nếu lưu giá trị **sau** khi trừ (`post-decrement`) thì `L = S-8` và `buf = L-0x78`;
- nếu lưu giá trị **trước** khi trừ thì `L = S` và `buf = L-0x80`.

Mọi phép leak đều đi qua chính `push rsp`, nên không thể phân biệt bằng leak. Cách duy
nhất là thiết kế một phép đo mà hai giả thuyết cho ra kết quả khác nhau: `measure_rsp.py`
đo trực tiếp giá trị kernel nạp vào rsp (thông qua chương trình start lại), và kết luận
`delta` đúng là **`buf = L - 0x80`**, tức `push rsp` ở đây lưu giá trị trước khi trừ.

Có một cách kiểm tra thứ hai không đụng tới sigreturn: `analysis/walk_leak.py` gọi gadget
`0x401032` nhiều lần (mỗi lần nuốt input và đẩy `rsp` lên 8) rồi nhảy vào `0x401017` để
leak `buf+0x88+8k`. Cả 5 giá trị cài cắm đều khớp.

result: `buf = L-0x78` DEAD - đây chính là lỗi làm tất cả các lần thử đầu thất bại im lặng.

## H8 - "dữ liệu đặt ở buf+0x300 chưa kịp vào bộ nhớ"

`frame` chiếm 0x178 byte nên chuỗi và argv bị đẩy lên `buf+0x300`. Gọi
`read(0, buf, 0x400)` có thể trả về ít hơn số byte đã gửi nếu TCP chia thành nhiều
segment; khi đó phần ở xa vẫn là rác của stack.

result: NỬA ĐÚNG - đây là cái bẫy có thật (nên giữ payload gọn dưới 512 byte), nhưng
không phải nguyên nhân chính. Sau khi sửa H7 thì mọi thứ chạy ngay, và `walk_leak.py`
chứng minh placement vẫn đúng tới tận `buf+0x108`.

## H9 - "seccomp chặn execve"

Frame đã đúng mà `execve("/bin/sh")` vẫn không trả về gì (0 byte, rồi abort). Nghi ngờ
seccomp.

`analysis/probe_args.py`: bậc thang 4 mức (`0x401017`, `0x401021`, `0x401028`, `0x401069`)
cho thấy `rsi`, `rdi`, `rdx` rồi `rax` đều được nạp đúng từ frame => có toàn quyền với
một syscall tùy chọn.

`analysis/probe_syscall_allow.py`: cho `rsp` của frame trỏ vào ô `0x78` chứa `0x401000`
(làm mồi). Nếu syscall trả về thì chương trình start lại và leak 8 byte; nếu bị giết thì
im lặng.

- `execve("/no/such/file")` → 8 byte → **execve được phép**, chỉ là path không tồn tại.
- `execve("/bin/sh")` → 0 byte → không phải bị giết: execve **thành công** nên không còn
  gì để leak.

result: seccomp DEAD. "im lặng" của execve thành công và của execve bị giết giống hệt
nhau; chính cái mồi `0x401000` mới phân biệt được hai case.

## H10 - "có shell là có flag"

`analysis/probe_exec.py`:

- `/bin/cat /flag` → 8 byte (cat chạy rồi trả lỗi, file không tồn tại).
- `/bin/sh -c 'cat /flag*;ls /'` → in `cat: '/flag*': No such file or directory` kèm danh
  sách `/`, trong đó có mục `ctf`.
- `/bin/sh` tương tác → `HELLO_FROM_SH` OK, shell sống và trả lời từng lệnh.

`ls -la /ctf` → `-rw-r----- 1 root total_recall 32 ... flag.txt`.
`cat /ctf/flag.txt` → ra cờ.

result: OK - `sun{r3caLl_ev3Ry_reGist3r_sR0p}`. Chính chữ trong cờ cũng xác nhận SROP là
lời giải tác giả nhắm tới.

## H11 - lỗi của chính harness (ghi lại để không mắc nữa)

Lần chạy đầu của `analysis/exp_inside.py`: tính `buf` từ leak của connection A rồi dùng
cho connection B và C. Vì ASLR đổi theo từng connection, cả ba phép đo đều vô nghĩa. Sau
khi chuyển tính `buf` vào bên trong từng connection, cùng phép thử đó cho kết quả có giá
trị. Đây là lỗi đo lường, không phải lỗi của đề, và nó đã làm mất một vòng thử nghiệm.
