# Đề bài - wish

## Nguyên văn đề

```text
Wish
800
pwn
phlox

Bames Jond has just returned from his latest mission with startling news: BigBadOrgTM have
put a SATellite up to assist in their plans of world domination. Luckily, the late Manny
Bothans was able to get us a connection to their control system and recovered part of the
control system's source.

We need you to hack into BigBadOrgTM's satellite and crash it into the Earth to destroy it.
Remember, Manny Bothans died to bring us this information. We must carry on in his legacy.

Disclaimer: CDCTF and any of its parent organizations do NOT endorse hacktivism. This is a
fictional scenario created for illustrative purposes, always obey laws and regulations
regarding computer use.

The flag format is cdctf{fl@g_g03s_h3R3}
```

Đề kèm ba file: `client` (binary), `auth.hh`, `cmd_auth.hh`. `session.hh` được `#include` nhưng không cấp.

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Instance | `https://kcliecti.i.cdctf.net`, sau đó `https://sbrktohj.i.cdctf.net` (cả hai đã hết hạn khi viết bài này) |
| Artifact | `files/client` (copy từ `~/Downloads/client`), `files/auth.hh`, `files/cmd_auth.hh` |
| Kích thước | client 679.960 B; auth.hh 2.572 B; cmd_auth.hh 653 B |
| SHA-256 | client `ae308ff5a34c76e60455e5acbd69d7db993cd67fde038d854e114570424d0394`; auth.hh `556d461e786eca2592521a7812a21f4b9ba9dc4bb9c1aafa61b5de34ab14ba2b`; cmd_auth.hh `fe6ac65e7efbc9343065a73a76a634261b04e36e294917f2b55c522bb2f2fda1` |
| Loại file | ELF 64-bit LSB **executable** (ET_EXEC, không PIE), dynamically linked, có `debug_info`, not stripped |
| Mitigation | NX (GNU_STACK `RW`), Partial RELRO (`.got` nằm trong RELRO, `.got.plt` 0x40cfe8-0x40d258 vượt quá 0x40d000, không có `BIND_NOW`), Canary (gọi `__stack_chk_fail`), text chạy ở địa chỉ cố định `0x400000` |
| Cách chạy trên box | ttyd exec `env LD_PRELOAD=/opt/wish/shim.so /opt/wish/client /tmp/sat.sock`, không có shell |
| Symbol then chốt | `contrivance` 0x403a86, `auth_bypass_dbg` 0x403ac9, `get_password` 0x404061, `check_password` 0x4047ae, `authenticate` 0x40492f, `vanished_alerts` 0x408120, `dispatch` 0x408d6b |
| Nhiệm vụ | Vượt qua `AUTHENTICATE` rồi làm vệ tinh va vào Earth để client in cờ |
| Định dạng cờ | `cdctf{...}` |

## Hướng giải (tóm tắt)

`contrivance()` giải phóng cùng một chunk hai lần nên danh sách tcache size 0x40 thành `A -> B -> A`; trong một lệnh `AUTHENTICATE`, `get_password()` cấp `password` = A rồi `check_password()` cấp `dummy` = B và `real_auth_sess` = A, tức struct `auth_sess` nằm ngay trong buffer mật khẩu. Điền 8 byte `0x403ac9` vào offset 24 (con trỏ hàm `dbg`) khiến client gọi `auth_bypass_dbg(s)` và đặt cờ `authed`. Sau đó `THRUST Satellite -1 0` đẩy vệ tinh đâm vào Earth; khi server xoá body bị nuốt, `vanished_alerts()` đọc `/flag.txt` và in `CONGRATULATIONS: <cờ>` cho client nào có snapshot `STATUS` trước đó trong cùng phiên.

## Chạy lại lời giải

```bash
pip install websockets
python exploit.py wss://<instance-id>.i.cdctf.net/ws
```

Kết quả: `cdctf{W!sh_Up0n_A_Sh0ot1ng_Star_81ab9a33}` (đã lưu trong `flag.txt`).
