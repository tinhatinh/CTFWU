---
title: "SoulVault"
category: "Reverse"
tags: ["go-binary", "stripped", "ghidra-headless", "polymorphic-vm", "arx-inversion", "sha256-keystream"]
solve_date: "2026-10-09"
language: "vi"
---

# SoulVault

**Flag:** `OWASP{s0ul_v4ult_byt3c0d3_vm_r3v3rs3d_7a8f9c2e}`
**Artifact:** `soulvault` (1,806,496 B) — ELF x86-64, Go 1.27.1 static, đã stripped. Tác giả: Suyog Jadhav.

Tên bài trùng với một challenge khác cũng của ByteMe CTF 26 mang tên SoulVault nhưng thuộc category Mobile (slug `soulvault-mobile`); bài này là dữ liệu gây nhiễun binary Go, không liên quan tới dữ liệu gây nhiễun Mobile.

## Đề bài

Bài Expert, 500 điểm, phát kèm một binary Linux duy nhất. Chương trình hỏi một *access sequence*, kiểm tra cấu trúc của chuỗi, biến đổi nó thành một buffer rồi đưa buffer đó vào một máy ảo đa hình (polymorphic VM). Khi VM đạt trạng thái chấp nhận, cờ được dựng từ các blob mã hoá trong binary và in ra.

Toàn bộ lời giải dưới đây là tái dựng tĩnh: binary không được thực thi trên host. Ba chuỗi thông báo `ACCESS GRANTED`, `[+] Flag: %s` và `[-] ACCESS DENIED: Invalid sequence structure or` chỉ được đọc từ `.rodata`.

## Phân tích

### Định vị lại symbol

`file soulvault` báo ELF 64-bit static, không có Go symbol table. GoReSym chạy trên binary trả về **text base sai**; mọi địa chỉ lấy từ output GoReSym được hiệu chỉnh theo một offset cố định trước khi đối chiếu với Ghidra:

```text
addr_corrected = addr_goresym - 0xcb6c8
```

Sau hiệu chỉnh, Ghidra được chạy ở chế độ headless và decompile **65 hàm `main.*`**. Script Ghidra ở đây viết bằng Java vì host không có PyGhidra.

### Tầng 1 — `ValidateStructureStage1`

Hàm này kiểm tra dạng chuỗi nhập và một rolling hash tích luỹ trên chính các byte của chuỗi:

```text
string form: SV-XXXX-XXXX-XXXX-XXXX-XXXX
h init     : 0x5a17f00d
update     : h = i*0xd + c*0x11 + h*0x1f        (i = index, c = byte value)
target     : h == 0x1248d50d
```

Cặp hằng `0x5a17f00d` / `0x1248d50d` là điều kiện duy nhất của tầng này; không có dữ liệu gây nhiễung tra hay state nào khác được dùng tới.

### Tầng 2 — `ProcessAccessSequence`

Chuỗi đạt tầng 1 được ánh xạ thành buffer `buf` qua ba dữ liệu gây nhiễung hằng số trong `.rodata`:

```text
buf[i] = ROT_L8(seq[PERM[i]] ^ XORKEY[i], (i % 7) + 1) + ADDKEY[i]

PERM    @ 0x5ab920
XORKEY  @ 0x5ab940
ADDKEY  @ 0x5ab960
```

Đúng ba khối 32 byte liên tiếp nằm tại các địa chỉ trên, thứ tự tương ứng với thứ tự xuất hiện trong công thức. Phép hoán vị `PERM` là song ánh nên ánh xạ `seq -> buf` khả nghịch từng byte:

```python
def rot_l8(v, s):
    s &= 7
    return ((v << s) | (v >> (8 - s))) & 0xFF if s else v & 0xFF

def rot_r8(v, s):
    s &= 7
    return ((v >> s) | (v << (8 - s))) & 0xFF if s else v & 0xFF

def un_process(buf, perm, xorkey, addkey):
    out = [0] * len(buf)
    for i, b in enumerate(buf):
        x = rot_r8((b - addkey[i]) & 0xFF, (i % 7) + 1)
        out[perm[i]] = x ^ xorkey[i]
    return out
```

### Tầng 3 — VM đa hình

VM có **23 opcode**, được khởi tạo bằng `seed = 0x5a17f00dc0ffee11` và `k32 = 1`; bộ sinh opcode đa hình quyết định mỗi opcode được giải mã thành thao tác nào. Chương trình chạy là **576 byte** và gồm **8 vòng ARX khả nghịch**, tức mỗi vòng đều có phép đảo xác định mà không cần tìm kiếm. Điều kiện chấp nhận nằm ở nhóm thanh ghi 8–11 so với hằng số `CHK`.

## Lời giải

Vì 8 vòng ARX khả nghịch và `un_process` là ánh xạ một-một, chuỗi chấp nhận được suy ra bằng cách chạy ngược: bắt đầu từ trạng thái VM thoả `regs[8..11] == CHK`, đảo từng vòng để thu dữ liệu vào của VM, rồi đảo `ProcessAccessSequence` để thu lại chuỗi.

Chuỗi thu được:

```text
SV-8F4C-3B91-7E02-A6D5-C918-B472
```

Kiểm chứng bằng một emulator chạy **thuận** đúng ba tầng trên với chuỗi vừa suy ra. Output đã ghi nhận:

```text
r0=1 halted=1 err=None steps=142 regs8-11==CHK: True
```

`r0=1` và `regs8-11==CHK: True` là cờ chấp nhận của VM; `steps=142` là số opcode thực thi của chương trình 576 byte trên đường đi đó.

Với `buf` từ chuỗi chấp nhận, cờ được phục hồi qua khoá dựng từ SHA-256:

```text
ReconstructFlag = (blob1..4) XOR (SHA256(CHK || "SoulVault::MasterFlagKeystream::v1" || buf)
                                    || SHA256(master || "SoulVault::SubStreamKey::v1"))
```

Hai digest được nối tiếp nhau tạo keystream; bốn blob mã hoá và các hằng số `CHK`/`master` đều lấy trực tiếp từ `.rodata`, nên phép dựng cờ không cần chạy binary. Output tiếp theo của cùng lần kiểm chứng:

```text
cipher len 47 c00e123f...
FLAG = b'OWASP{s0ul_v4ult_byt3c0d3_vm_r3v3rs3d_7a8f9c2e}'
```

`cipher len 47` khớp độ dài 47 byte của chuỗi cờ in ra ngay sau đó.

## Kết quả

```text
OWASP{s0ul_v4ult_byt3c0d3_vm_r3v3rs3d_7a8f9c2e}
```

Cờ là kết quả tái dựng tĩnh từ binary đã cho và được xác nhận bằng lần chạy thuận của emulator với chuỗi chấp nhận (`r0=1 halted=1 err=None steps=142 regs8-11==CHK: True`); dữ liệu gây nhiễun thân binary không hề được thực thi. Chưa lưu phản hồi submission.

Bản ghi emulator kiểm tra trạng thái VM, nhưng chưa có phép kiểm độc lập đầy đủ cho tầng `ValidateStructureStage1`. Bài cũng chưa kèm emulator và các vòng ARX đầy đủ, nên chưa thể tái hiện toàn bộ từ hai file Markdown.

## Tái hiện

Cần: GoReSym, Ghidra (headless, script Java), Python 3. Đặt `soulvault` cạnh thư mục làm việc.

```console
$ file soulvault
$ goresym -d soulvault              # compare with Ghidra addresses, apply addr -= 0xcb6c8
$ analyzeHeadless <dir> <proj> -import soulvault -process -nolog \
    -scriptPath <dir> -postScript DecompileMain.java -savelocation
$ strings -a soulvault | grep -E "ACCESS GRANTED|ACCESS DENIED|Flag: %s"
```

Để dựng lại chuỗi chấp nhận, trích ba dữ liệu gây nhiễung hằng tại `0x5ab920`, `0x5ab940`, `0x5ab960` và các blob/`CHK`/`master` từ `.rodata`, rồi:

1. Chạy ngược 8 vòng ARX của VM từ trạng thái `regs[8..11] == CHK` (cùng `seed = 0x5a17f00dc0ffee11`, `k32 = 1`, cùng bộ đa hình 23 opcode) để thu dữ liệu vào của VM.
2. Áp `un_process` ở mục Phân tích để thu chuỗi, dạng `SV-...`.
3. Chạy emulator thuận với chuỗi đó để lấy dòng `r0=1 halted=1 err=None steps=142 regs8-11==CHK: True`.
4. Tính `SHA256(CHK || "SoulVault::MasterFlagKeystream::v1" || buf)` nối `SHA256(master || "SoulVault::SubStreamKey::v1")`, XOR với bốn blob để in cờ.
