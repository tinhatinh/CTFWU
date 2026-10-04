# Đề bài - ccu-banking-terminal-premium-2

## Nguyên văn đề

```text
CCU Banking Access Terminal, Premium Tier (2/2) - 499 - pwn - soup, adlee7

Crimson Credit Union liked their 1997 member services terminal so much they bought
the private client edition. Same vendor, same "secured by the Telnet protocol"
banner, one new line in the header: TERMINAL HARDENING: ACTIVE.

The premium node keeps every account as a fixed-size branch record page and
calculates dividends through a per-record routine. A private client has handed us
their credentials and asked what "hardening" actually bought them.

Start an instance and open the link it gives you. It is a terminal in your browser,
on a workstation next to the service, with pwntools, gdb, patchelf and seccomp-tools
installed and the attached files in ~/handout. The service is at chal:2324 from there:

nc chal 2324
io = remote("chal", 2324)     # pwntools

Running your own exploit script from that workstation is allowed for this challenge.
The workstation has no internet access, so paste your script in (cat > solve.py,
paste, then Ctrl-D).

Test credentials (nothing in this challenge needs brute forcing):
Member number : 8802
Access PIN    : 2049

The flag is in the file /flag on the service host. The service speaks raw bytes.
Menu options that ask for a "branch page" want exactly 384 raw bytes, not a line.

Attached: the service binary, the libc it runs against (Ubuntu GLIBC 2.35-0ubuntu3.15),
the matching loader, and libseccomp. From a directory holding all four:

patchelf --set-interpreter ./ld-linux-x86-64.so.2 --set-rpath . ccu_premium
./ccu_premium

libseccomp is shipped because your system copy is very likely built against a newer
glibc and the loader will refuse it with "GLIBC_ABI_DT_RELR not found". Use the one
in the handout, and do not stub it out: it allocates while it builds the filter, so
removing it moves the heap and your local results will stop matching the server.

The syscall policy is not a secret. Dump it:

seccomp-tools dump ./ccu_premium

Flag format: cdctf{Fl@g_g0es_H3r3!}
```

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/ccu-premium-terminal.zip` (copy từ: `C:/Users/Administrator/Downloads/ccu-premium-terminal.zip`) |
| Kích thước | 1127978 byte |
| SHA-256 | `2e3e1d6f99afd93227d625cd55bc90a89d575d61e5af18ef49f2259d7c2529e8` |
| Loại file | Zip archive data, made by v3.0 UNIX, extract using at least v2.0, last modified Sep 16 2026 15:38:50 |
| Bên trong zip | `ccu_premium` (ELF 64-bit LSB executable, x86-64, dynamically linked, not stripped), `libc.so.6` (Ubuntu GLIBC 2.35-0ubuntu3.15), `ld-linux-x86-64.so.2`, `libseccomp.so.2`, `README.txt` |
| Nhiệm vụ | Đọc `/flag` trên host chạy service `chal:2324` |
| Định dạng cờ | `cdctf{...}` |
| Đăng nhập | Member `8802`, PIN `2049` (`member_pin` = "2049" tại 0x406108, so `strtoul(member) == 0x2262`) |
| Tương tác | Raw bytes; branch page = đúng 384 byte, không phải một dòng |

## Hướng giải (tóm tắt)

`open_account` đọc 384 byte thô vào chunk `malloc(0x180)` rồi chỉ sửa các field
`+0x00/+0x04/+0x08/+0x28`, nên phần thân trang vẫn là dữ liệu người dùng kiểm soát.
`close_account` `free()` nhưng để con trỏ treo trong `accounts[]`; `attach_memo` cũng
`malloc(0x180)` và `read_full()` thô mà không sửa field nào, nên memo rơi đúng vào chunk
record đã giải phóng (UAF / type confusion). `show_summary` gọi `[rec+0x28]` với `rdi = rec`,
do đó ta chiếm được RIP và pivot stack lên chính chunk heap, rồi chạy ROP orw trong libc
(vì seccomp không cho `execve`).

## Chạy lại lời giải

```bash
# lab local (không có /flag thật, dùng flagfile giả) - xem analysis/service.py
python analysis/service.py 2324 &
python exploit.py
```

Kết quả tại thời điểm viết: chuỗi tự dựng trong `analysis/flagfile.local`, chưa capture
cờ thật từ instance. Bài đang ở `_wip/`.
