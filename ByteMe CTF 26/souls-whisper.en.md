---
title: "Soul's Whisper"
category: "Reverse"
tags: ["stack-immediates", "strcmp", "radare2", "esil-emulation"]
solve_date: "2026-10-09"
language: "en"
---

# Soul's Whisper

**Flag:** `OWASP{th3_s0ul_st0n3_wh1sp3r}`
**Artifact:** `soul_whisper` (16184 B, ELF 64-bit, PIE, not stripped).

## Challenge

The binary ships with the challenge (Easy, 100 points, 22 solves). It prints the `SOUL STONE VAULT` banner, prompts `Enter the secret phrase:`, reads one string with `scanf("%63s")` and compares it against a password assembled on the stack; on a match it calls `soul_stone()`, which prints the flag through `printf("Flag: %s\n")`. The only `strings` hit containing `OWASP` in the file is `OWASP{thH`, so the flag cannot be read directly.

## Analysis

`readelf`/`file` report a PIE with an intact symbol table; `r2 -q -c "is" soul_whisper` lists the two user functions:

```text
34  0x0000129a 0x0000129a GLOBAL FUNC   217      main
35  0x000011c9 0x000011c9 GLOBAL FUNC   209      soul_stone
```

The password check inside `main@0x129a`:

```text
|           0x00001305      lea rax, [var_50h]
|           0x0000130c      lea rax, str._63s                          ; 0x20fa ; "%63s"
|           0x0000131b      call sym.imp.__isoc99_scanf
|           0x00001320      mov dword [var_55h], 0x6c756f73            ; 'soul'
|           0x00001327      mov byte [var_51h], 0
|           0x00001339      call sym.imp.strcmp
|           0x0000133e      test eax, eax
|       ,=< 0x00001340      jne 0x1349
|       |   0x00001342      call sym.soul_stone
```

The password is `soul` (constant `0x6c756f73`); because it is built with `mov` instructions it never appears as a contiguous string in `.rodata`. `soul_stone` runs only when `strcmp` returns 0.

`main` uses `var_50h` as the read buffer, i.e. `rbp-0x50`; `soul_stone@0x11c9` uses that same offset as the copy destination, so no stack-frame discovery is needed:

```text
/ 209: sym.soul_stone ();
|           0x000011c9      endbr64
|           0x000011cd      push rbp
|           0x000011ce      mov rbp, rsp
|           0x000011d1      add rsp, 0xffffffffffffff80
|           0x000011e4      movabs rax, 0x68747b505341574f             ; 'OWASP{th'
|           0x000011ee      movabs rdx, 0x735f6c7530735f33             ; '3_s0ul_s'
|           0x000011f8      mov qword [var_70h], rax
|           0x000011fc      mov qword [var_68h], rdx
|           0x00001200      movabs rax, 0x5f336e3074735f6c             ; 'l_st0n3_'
|           0x0000120a      movabs rdx, 0x7d72337073316877             ; 'wh1sp3r}'
|           0x00001214      mov qword [var_63h], rax
|           0x00001218      mov qword [var_5bh], rdx
|           0x0000122a      movzx eax, byte [rbp + rax - 0x70]
|           0x00001236      mov byte [rbp + rax - 0x50], dl
|           0x00001241      cmp eax, 0x1c
|           0x00001246      mov byte [var_33h], 0
```

The four `movabs` are four 8-byte qwords written to `rbp-0x70`, `rbp-0x68`, `rbp-0x63` and `rbp-0x5b`. The gap between `rbp-0x68` and `rbp-0x63` is only 5 bytes, so the third qword overwrites the last 3 bytes of the second one. The `for (i = 0; i <= 0x1c; i++)` loop copies 29 bytes from `rbp-0x70` to `rbp-0x50`, then stores NUL at `rbp-0x33` (= `rbp-0x50 + 29`).

## Solution

The overlap is only a string-hiding trick: the three shared bytes have to agree, otherwise the flag would be corrupted. Checking the four constants directly:

```python
M = [(0x68747b505341574f, -0x70), (0x735f6c7530735f33, -0x68),
     (0x5f336e3074735f6c, -0x63), (0x7d72337073316877, -0x5b)]
buf = {}
for imm, off in M:
    s = imm.to_bytes(8, "little")
    print(len(s), s)
    for k, ch in enumerate(s):
        prev = buf.get(off + k)
        if prev is not None:
            print("overlap rbp%+x" % (off + k), chr(prev), chr(ch), prev == ch)
        buf[off + k] = ch
print(bytes(buf[i] for i in range(-0x70, -0x70 + 29)))
```

```text
8 b'OWASP{th'
8 b'3_s0ul_s'
8 b'l_st0n3_'
overlap rbp-63 l l True
overlap rbp-62 _ _ True
overlap rbp-61 s s True
8 b'wh1sp3r}'
b'OWASP{th3_s0ul_st0n3_wh1sp3r}'
```

All three overlapping positions agree, so the construction is consistent. To avoid relying on hand reconstruction, the body of `soul_stone` is emulated with radare2 ESIL: a fake memory region is mapped for the stack, `rbp = 0x80000f0`, execution starts at `0x11e4` (right after the prologue and the canary load) and stops at `0x124a` (right before the `puts`/`printf` branch).

```console
$ r2 -q -e bin.relocs.apply=true -c "e io.cache=true; e asm.bytes=false; \
    s 0x11c9; af; aeim 0x8000000 0x10000 stk; aeip; \
    aer rbp=0x80000f0; aer rsp=0x80000f0; aepc 0x11e4; aesu 0x124a; \
    ar rip; px 32 @ 0x8000080; px 40 @ 0x80000a0" soul_whisper
```

```text
0x0000124a
- offset -  8081 8283 8485 8687 8889 8A8B 8C8D 8E8F  0123456789ABCDEF
0x08000080  4f57 4153 507b 7468 335f 7330 756c 5f73  OWASP{th3_s0ul_s
0x08000090  7430 6e33 5f77 6831 7370 3372 7d00 0000  t0n3_wh1sp3r}...
- offset -  A0A1 A2A3 A4A5 A6A7 A8A9 AAAB ACAD AEAF  0123456789ABCDEF
0x080000a0  4f57 4153 507b 7468 335f 7330 756c 5f73  OWASP{th3_s0ul_s
0x080000b0  7430 6e33 5f77 6831 7370 3372 7d00 0000  t0n3_wh1sp3r}...
0x000000c0  0000 0000 0000 0000                      ........
```

`0x8000080 = rbp-0x70` is the source, `0x80000a0 = rbp-0x50` is the destination and also the pointer handed to `printf("Flag: %s\n")`. The destination holds exactly 29 flag bytes followed by NUL, identical to the hand reconstruction above.

## Result

```text
OWASP{th3_s0ul_st0n3_wh1sp3r}
```

The flag was reconstructed by static analysis and ESIL emulation of the provided binary; the binary was not executed on the Windows host. No submission response recorded.

## Reproduce

Requires `radare2` (verified on 6.2.2, Windows x86-64) and Python 3 for the overlap check. Put `soul_whisper` next to the script.

Emulation command (every dump line above comes from this command):

```console
$ r2 -q -e bin.relocs.apply=true -c "e io.cache=true; e asm.bytes=false; \
    s 0x11c9; af; aeim 0x8000000 0x10000 stk; aeip; \
    aer rbp=0x80000f0; aer rsp=0x80000f0; aepc 0x11e4; aesu 0x124a; \
    ar rip; px 32 @ 0x8000080; px 40 @ 0x80000a0" soul_whisper
```

Static inspection commands:

```console
$ file soul_whisper
$ r2 -q -c "is" soul_whisper | grep -E "main|soul_stone"
$ r2 -q -e bin.relocs.apply=true -c "e asm.bytes=false; s 0x11c9; af; pd 24" soul_whisper
$ strings soul_whisper | grep -c OWASP
```

Save the Python block from the Solution section as `check_overlap.py` and run `python check_overlap.py`; it only uses constants taken from the disassembly and does not read the binary.
