---
title: "Soul Echoes (The Stonekeeper's Chronicles)"
category: "Reverse"
tags: ["elf", "menu-dispatch", "rodata", "static-analysis"]
solve_date: "2026-10-09"
language: "en"
---

# Soul Echoes (The Stonekeeper's Chronicles)

**Flag:** `OWASP{th3_st0n3k33p3r_wh1sp3rs_1nt0_th3_v01d}`
**Artifact:** `soul_echo` (16384 B, ELF 64-bit, PIE, not stripped).

## Challenge

A Stonekeeper-themed menu binary (Medium, 200 points, 24 solves). It prints the three chapters of a chronicle and prompts `Choose your path (1-5):` with the entries `1. Read Chapter I: The Exile`, `2. Read Chapter II: The Weight of Knowledge`, `3. Read Chapter III: The Inscription upon the Obsidian Cliff`, `4. Listen to the entire chronicle`, `5. Depart from the precipice`. The objective is to obtain the flag string.

## Analysis

`r2 -q -c "aa; afl" soul_echo` yields four user functions and six imports:

```text
0x000010a0    1     10 sym.imp.puts
0x000010b0    1     10 sym.imp.__stack_chk_fail
0x000010c0    1     10 sym.imp.fgets
0x000010d0    1     10 sym.imp.strtol
0x000010e0    1     10 sym.imp.fflush
0x000010f0    1     10 sym.imp.__printf_chk
```

```text
0x00001380    1     92 sym.chapter_one
0x000013e0    1     92 sym.chapter_two
0x00001440    1    106 sym.chapter_three
0x00001100   12    400 main
```

The import table has no `strcmp`, `memcmp`, `strlen` or any data-transforming function. The path into the chapters is only `fgets` → `strtol` → jump through a switch table:

```text
0x000011f2      call sym.imp.fgets
0x000011f7      test rax, rax
0x000011fa      je 0x1232
0x000011fc      xor esi, esi
0x000011fe      mov edx, 0xa
0x00001203      mov rdi, rbx
0x00001206      call sym.imp.strtol
0x0000120b      cmp eax, 5
0x0000120e      ja case.0x1220.0
0x00001219      movsxd rax, dword [rdx + rax*4]
0x0000121d      add rax, rdx
;-- switch:
0x00001220      notrack jmp rax                                        ; switch table (6 cases) at 0x2938
0x00001223      call sym.chapter_one
0x00001228      call sym.chapter_two
0x0000122d      call sym.chapter_three
```

No comparison against the input exists, so there is neither a password nor encryption: the menu only selects which branch prints. `main@0x1100` has 12 basic blocks, but they are all `puts` of the banner plus the switch shown above.

`chapter_three@0x1440` ends by printing a `.rodata` address directly:

```text
0x00001480      mov edi, 2
0x00001485      lea rdx, str.OWASPth3_st0n3k33p3r_wh1sp3rs_1nt0_th3_v01d ; 0x2458 ; "OWASP{th3_st0n3k33p3r_wh1sp3rs_1nt0_th3_v01d}"
0x0000148c      xor eax, eax
0x0000148e      lea rsi, str._n_________s_____n_n                      ; 0x201e ; "\n    >>> %s <<<\n\n"
0x00001495      call sym.imp.__printf_chk
0x0000149a      lea rdi, str.May_it_guide_you_through_the_darkness_of_the_cosmos._n ; 0x2488 ; "May it guide you through the darkness of the cosmos.\n"
0x000014a1      add rsp, 8
0x000014a5      jmp sym.imp.puts
```

The memory at `0x2458` holds the flag in plaintext, without any transformation.

## Solution

The flag was read straight out of `.rodata` by static inspection; the binary was not run:

```console
$ r2 -q -c "px 64 @ 0x2458" soul_echo
```

```text
- offset -  5859 5A5B 5C5D 5E5F 6061 6263 6465 6667  89ABCDEF01234567
0x00002458  4f57 4153 507b 7468 335f 7374 306e 336b  OWASP{th3_st0n3k
0x00002468  3333 7033 725f 7768 3173 7033 7273 5f31  33p3r_wh1sp3rs_1
0x00002478  6e74 305f 7468 335f 7630 3164 7d00 0000  nt0_th3_v01d}...
0x00002488  4d61 7920 6974 2067 7569 6465 2079 6f75  May it guide you
```

The string is 45 bytes long; the final `}` sits at `0x2484` and the NUL at `0x2485`.

The only decoy worth recording is the number of candidates: `OWASP` occurs exactly once in the whole 16384-byte file, so there is no second fake flag to disambiguate.

```console
$ python -c "d=open('soul_echo','rb').read(); print(len(d), d.count(b'OWASP'))"
```

```text
16384 1
```

## Result

```text
OWASP{th3_st0n3k33p3r_wh1sp3rs_1nt0_th3_v01d}
```

The flag was read from the binary's `.rodata` by static inspection; the binary was never executed on the Windows host. No submission response recorded.

## Reproduce

Requires `radare2` (verified on 6.2.2, Windows x86-64) and Python 3.

```console
$ file soul_echo
$ r2 -q -c "aa; afl" soul_echo | grep -E "sym.imp"
$ r2 -q -c "aa; afl" soul_echo | grep -E "chapter|main"
$ r2 -q -e bin.relocs.apply=true -c "e asm.bytes=false; e asm.lines=false; \
    e asm.comment=false; s 0x1100; af; pd 75" soul_echo
$ r2 -q -e bin.relocs.apply=true -c "e asm.bytes=false; e asm.lines=false; \
    e asm.comment=false; s 0x1440; af; pd 20" soul_echo
$ r2 -q -c "px 64 @ 0x2458" soul_echo
$ python -c "d=open('soul_echo','rb').read(); print(len(d), d.count(b'OWASP'))"
```

There is no decryption script: the answer is the content of the 45 bytes at `0x2458`, the same address `chapter_three` loads into `rdx` before printing.
