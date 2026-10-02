# Parcel Bomb - Pwn (Medium)

**Flag:** `H7CTF{0b79ca94-3b66-4509-9365-34d224d5cfe2}`
**Remote:** `nc pwn.h7tex.com 41136`
**Files cung cấp:** `dispatch.zip` (1.03 MiB, sha256 `72f6e078…`). Bên trong bao gồm: `dispatch` (tệp thực thi ELF64 ET_EXEC, sha256 `d946ba60…`), thư viện `libc.so.6` (glibc 2.39-0ubuntu8.9), `ld-linux-x86-64.so.2` và tệp `README.txt`.

## Đề bài

Khi kết nối vào hệ thống, chương trình hiển thị giao diện "Sparrow Freight dispatch" (Tổng đài điều phối vận tải Sparrow). Chương trình yêu cầu nhập số vận đơn (waybill number) và ghi nhận kết quả. Lỗ hổng nằm ở việc: bộ đệm (buffer) chỉ có kích thước 64 byte, nhưng lệnh `read` cho phép nhập tối đa 512 byte. Tuy nhiên, tệp nhị phân không chứa sẵn hàm `system` hay chuỗi `/bin/sh`. Mục tiêu là chiếm quyền điều khiển và đọc cờ từ môi trường thực thi.

## Phân tích ban đầu

Kiểm tra thông số tệp thực thi:
```bash
$ node ~/.qoder/skills/ctf-solve/scripts/triage.cjs dispatch
class=64-bit type=ET_EXEC (no PIE)  entry=0x401090  PIE=no RELRO=yes STACK=non-exec

$ readelf --dyn-syms -W dispatch
puts  read  setvbuf  __libc_start_main  stdout
```
Như dự đoán, không có sự xuất hiện của `system` hay `execve`.

Sử dụng lệnh `objdump -d -M intel` để phân tích, chương trình bao gồm 3 đoạn mã chính:

| Địa chỉ | Nội dung phân tích |
| --- | --- |
| `0x401176` | Một mảnh mã (gadget) tĩnh: `pop rdi ; ret`, tại `0x401177` là lệnh `ret`. |
| `0x401178` | Hàm `vuln()` chứa lỗ hổng: `puts(prompt);` `read(0, rbp-0x40, 0x200);` `puts("waybill logged.");` `leave; ret`. |
| `0x4011bb` | Hàm `main()`: `setvbuf(stdout, NULL, _IONBF, 0);` `puts(banner);` `call vuln`. |

Kiểm tra các cơ chế bảo vệ (Mitigations):

- **Canary:** Bị vô hiệu hóa. Bảng ký hiệu (symtab) không chứa hàm `__stack_chk_fail`. Lệnh `read` nhận 512 byte vào khoảng đệm 64 byte sẽ ghi đè thanh ghi `saved rbp` và địa chỉ trả về (return address). Khoảng cách (offset) đến địa chỉ trả về là `0x40 + 8 = 72` byte.
- **PIE (Position Independent Executable):** Bị vô hiệu hóa. Các đoạn gadget và các mục trong bảng GOT nằm ở các địa chỉ cố định.
- **RELRO:** Bật toàn phần (Full RELRO). Vùng `GNU_RELRO` bao phủ khoảng `0x403df8 + 0x208`, thiết lập phân đoạn `.got` và `.got.plt` thành chế độ chỉ đọc (read-only). Phương pháp ghi đè GOT (ret2got) không khả thi.
- **NX:** Bật. Không thể thực thi shellcode trực tiếp trên ngăn xếp (stack).

Điểm đáng chú ý: Chương trình không hiển thị lại nội dung đã nhập vào buffer, do đó việc khai thác tràn bộ đệm (overflow) đơn lẻ không thể làm rò rỉ (leak) địa chỉ gốc của thư viện `libc`. Việc lấy địa chỉ `libc` là yêu cầu bắt buộc trong giới hạn 512 byte của lệnh `read`.

Thông điệp (banner) trả về từ `pwn.h7tex.com:41136` khớp hoàn toàn với chuỗi trong tệp `dispatch`. Điều này xác nhận máy chủ đang chạy phiên bản tệp tương đồng, cho phép phân tích tĩnh đạt hiệu quả cao (do môi trường phân tích sử dụng Win32 không có qemu/docker nên không chạy trực tiếp tệp ELF Linux).

## Quá trình khai thác

### Bước 1: Rò rỉ địa chỉ (Leak) qua ROP

Do hàm `puts` đã được sử dụng để in chuỗi prompt, cơ chế Lazy Binding đã phân giải (resolve) địa chỉ `puts@GOT` tại `0x404000` thành một con trỏ tham chiếu đến thư viện `libc`. 
Chiến thuật khai thác: Gọi lại `puts@plt` với tham số `rdi = 0x404000`. Thao tác này sẽ in ra 6 byte của con trỏ (do `stdout` sử dụng cấu hình `_IONBF`, dữ liệu được xuất trực tiếp). Sau khi nhận địa chỉ rò rỉ, điều hướng luồng thực thi trở lại hàm `vuln` (`0x401178`) để thực hiện overflow lần hai trong cùng một phiên kết nối. Nhờ PIE bị tắt, cấu trúc stack lần hai hoàn toàn giống lần đầu.

Chuỗi ROP ở giai đoạn 1 (Stage 1):
```text
pad(72 byte) | pop_rdi_ret | 0x404000 | ret | puts@plt | ret | 0x401178(vuln)
```

### Bước 2: Căn chỉnh cấu trúc ngăn xếp (16-byte alignment)

Tại hàm `vuln`, giá trị thanh ghi `rsp` khi bắt đầu hàm luôn thõa mãn `≡ 8 (mod 16)` (do lệnh `and rsp,-16` trong `_start` và `push rbp` trong `main`). 
Sau khi thực thi `leave; ret`, `rsp` sẽ trở về `≡ 0`. Theo tiêu chuẩn ABI, các hàm (callee) yêu cầu `rsp ≡ 8` tại lệnh đầu tiên. Vì vậy:

- Cần bổ sung lệnh `ret` (`0x401177`, sử dụng lệnh `ret` trong gadget `pop_rdi_ret`) ngay trước `puts@plt`. Nếu thiếu khoảng đệm này, `puts` sẽ thực thi khi stack bị lệch 8 byte và gây lỗi `SIGSEGV` tại lệnh xử lý vector `movaps`.
- Chuỗi payload stage 1 phải chứa số lượng qword (8 byte) chẵn. Với thiết kế 6 qword (48 byte), khi vào `vuln` lần hai, `rsp ≡ 8` sẽ chuẩn xác, giúp hàm `puts` trong `vuln` và `system` ở stage 2 hoạt động bình thường mà không cần đệm thêm `ret`.
- Cấu trúc chuỗi stage 2 sẽ tuân theo mẫu: `pop_rdi_ret | tham_số | ret | hàm_đích`.

### Bước 3: Tính toán địa chỉ và thực thi (Stage 2)

```bash
$ python exploit.py pwn.h7tex.com 41136 "id; ls -la; cat flag flag.txt /flag /flag.txt 2>/dev/null; ls /"
[*] leaked bytes: c07c88edae7f0a (7)
[+] puts -> 0x7faeed887cc0, libc base = 0x7faeed800000
[*] post-exploitation output (1378 bytes):
waybill logged.
uid=0(root) gid=0(root) groups=0(root)
...
-rw-r--r--  1 root root   44 Sep 26 05:28 flag
H7CTF{0b79ca94-3b66-4509-9365-34d224d5cfe2}
```

Phân tích địa chỉ: `0x7faeed887cc0 - 0x87cc0 = 0x7faeed800000` (địa chỉ căn chỉnh theo trang bộ nhớ). Tra cứu từ tệp `libc.so.6`, các offset cần thiết: `system = base + 0x58750`, và chuỗi `"/bin/sh" = base + 0x1cc42f`.

Chuỗi ROP giai đoạn 2 (Stage 2):
```text
pad(72 byte) | pop_rdi_ret | base+0x1cc42f | ret | base+0x58750(system)
```

Khi `system()` được gọi, nó sử dụng luồng nhập/xuất (stdin/stdout) của kết nối mạng (socket) để tạo một shell tương tác. Quá trình này chạy với quyền `uid=0` bên trong container. Tệp cờ được lưu trữ tại `/flag`.

Lưu ý quan trọng: Cả hai payload phải được thực hiện trong **một phiên kết nối duy nhất**. Cơ chế ASLR của Linux sẽ ngẫu nhiên hóa (randomize) địa chỉ bộ nhớ khi tạo kết nối mới, do đó giá trị leak chỉ có giá trị trong phiên kết nối hiện tại.

## Flag
```
H7CTF{0b79ca94-3b66-4509-9365-34d224d5cfe2}
```

Lệnh thực thi tự động: `python exploit.py pwn.h7tex.com 41136 "cat /flag"`
