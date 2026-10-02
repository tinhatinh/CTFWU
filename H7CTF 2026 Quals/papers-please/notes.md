# Notes - Papers Please

## Môi trường

Không có WSL/Docker trên host này → **không chạy được ELF Linux locally**. Toàn bộ phân tích ở đây là tĩnh (`objdump`/`readelf`/`nm`), và payload được kiểm chứng trực tiếp trên đích đang cho (`pwn.h7tex.com:42578`), một kết nối một lượt.

## Triage

```
magic=ELF 64-bit, ET_EXEC (no PIE)
PIE=no  NX=on  RELRO=partial
imports: puts fopen fclose fgets printf read setvbuf fflush
KHÔNG có __stack_chk_fail  → không có stack canary
```

## Chuỗi hàm liên quan

- `main` @ `0x401302`: `push rbp` (không `sub rsp`) → `setvbuf(stdout, NULL, _IONBF, 0)` → `call checkpoint`.
- `checkpoint` @ `0x4012a4`: `sub rsp,0x40`, buffer ở `[rbp-0x40]` (64 byte) rồi
  `read(0, buf, 0x100)` → **đọc 256 byte vào vùng 64 byte**. Không canary, NX bật.
  Sau đó `printf("Access denied, %s. Turn back.", buf)` (định dạng là hằng số trong `.rodata`,
  tên chỉ là đối số → **không có format-string bug**), rồi `leave; ret`.
- `grant_access` @ `0x401216`: `fopen("/flag","r")` → `fgets(buf,0x50,...)` → `fclose`
  → `printf("ACCESS GRANTED: %s", flag)`. Đây chính là "cái dấu triện" trong đề.

## Offset

layout tính từ đầu buffer:

| Khoảng | Nội dung |
| --- | --- |
| 0..63 | buffer 64 byte |
| 64..71 | saved rbp |
| 72..79 | return address |

→ offset tới return address = **72 byte**. Đích 256 byte qua `read`, đủ rộng.

## Căn chỉnh stack (điểm dễ sai)

Bất biến ABI: tại instruction đầu tiên của một hàm, `rsp % 16 == 8`.

Gọi thường: `call checkpoint` đẩy return address → rsp vào `checkpoint` ≡ 8 mod 16.
Nhưng khi thoát bằng `leave; ret`, `ret` để `rsp = rbp_checkpoint + 8 = rbp_main`,
mà `rbp_main` ≡ **0 mod 16** (main chỉ `push rbp`). Nghĩa là nhảy thẳng tới
`grant_access` cho vào hàm với `rsp ≡ 0 mod 16` - lệch 8 byte. `grant_access` gọi
`fopen`/`fgets`/`printf` của glibc 2.39, mấy đường này load/`movaps` trên stack và
sẽ `SIGSEGV` khi stack lệch.

Cách sửa: chèn một gadget `ret` để shift rsp thêm 8 byte. Chọn `_fini @ 0x401334`
(`endbr64; sub rsp,8; add rsp,8; ret`) vì nó mở đầu bằng `endbr64` - vừa làm đúng
việc trượt stack, vừa không vi phạm IBT nếu CPU bật CET.

Tính lại: vào gadget rsp ≡ 0 → `ret` pop 8 → rsp ≡ 8 → vào `grant_access` đúng ABI.

## Hypothesis log

- H1 - format string qua tên: định dạng nằm trong `.rodata`, tên chỉ là `%s` argument
  → **DEAD** (tên in nguyên văn, không có `%n`/leak).
- H2 - overflow `read(0,buf,0x100)` vào buffer 64 byte đè return address → ret2win
  `grant_access`: **CONFIRMED bằng phân tích tĩnh**; không PIE nên địa chỉ tuyệt đối,
  không cần leak; không canary nên một phát ăn ngay.
- H3 - cần `ret` slide cho căn chỉnh 16 byte: kiểm chứng bằng cách chạy cả hai biến thể.

## Kết quả

- H2: **CONFIRMED on target** - payload 88 byte (`slide`) cho ra `ACCESS GRANTED: H7CTF{...}` ở kết nối đầu tiên. Flag ghi vào `flag.txt`.
- H3: **KHÔNG kiểm chứng được, và lý do ghi ở lần đầu là sai**. Hai lần chạy biến thể `direct` chết ở `getaddrinfo` không phải do DNS chập chờn: `exploit.py` lấy `sys.argv[1]` làm host, còn lệnh là `python exploit.py --payload direct`, nên host nhận giá trị `"direct"`. Lỗi ở phía script, phép thử chưa từng chạm tới đích. Kết luận "cần ret slide" vì thế vẫn chỉ là suy luận từ ABI + disassembly, chưa có bằng chứng thực nghiệm nào cả hai chiều.
