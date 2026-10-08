# bring-coines - Reverse Engineering (500 points)

**Flag:** `cdctf{h4t_M0us3_p0k3_FLAG!}`
**Files:** `bringcoines.exe`, 7284057 bytes, sha256 `576db2ac5c6657189ea446c594092c7b7d0ad5d84f3246b1165d2a372b39c3c6`

## Challenge

Hat Mouse sells hats. The program asks "how many coins you have", a correct answer opens the shop, and one menu item is labelled `fLEG!!!`. Flag format `cdctf{fleg}`. The challenge ships a single `.exe`, no source.

## Analysis

- `file` reports PE32+ console x86-64, 7 sections, 7.28 MB, but `.text` is only `0x2dc00` bytes, so the size does not come from real code.
- `strings` shows `PyRun_SimpleStringFlags`, `pyi-python-flag`, `python312.dll` and a `.fptable` section. That is a PyInstaller bootloader for CPython 3.12; the actual logic lives in the CArchive at the end of the file.
- Imports are only KERNEL32/USER32 (heap, console and window calls the bootloader needs). No anti-debug, no self-check.
- Scanning strings across the whole file finds no `cdctf{...}` pattern: the bytecode entry is zlib-compressed, so the only readable literals are the ordinary English messages.

## Approaches tried

1. **Flag inside a PE resource or data section.** `.rsrc` (0xf000 bytes) is the default PyInstaller manifest and `.data` is 0xe00 bytes. Nothing suspicious outside the CArchive.
2. **Entering a large coin amount.** Both branches of `process_coines()` are decoys: a value that `float()` accepts prints `That's a lotta coines poke. Congrats!` and returns, anything else prints `That's not coines...`. The prices in the menu (2,000 to 10,000 coins) are decoration, the program tracks no balance.

## Solution

**Step 1 - Pull the entry script bytecode out of the CArchive.**

A Python 3.12 interpreter on the analysis machine is enough: the `.pyc` magic is `cb0d0d0a`, so `marshal.loads` returns the code object directly and no decompiler is needed (uncompyle6 and decompyle3 stop at 3.9).

```bash
pip install pyinstxtractor-ng
python -m pyinstxtractor_ng bringcoines.exe
# [+] Pyinstaller version: 2.1+
# [+] Python version: 3.12
# [+] Found 21 files in CArchive
# [+] Possible entry point: bringcoines.pyc
```

File layout: the 8-byte cookie `MEI\x0c\x0b\x0a\x0b\x0e` sits at the end, followed by four big-endian fields `pkgLen, tocPos, tocLen, pyVers` and then `python312.dll`. Each TOC entry is `>IIIIBc` (entry length, offset, size, end offset, flag, typecode) plus the name padded to the entry length. The entry we want has typecode `s`, a Python script:

```python
# extracted bringcoines.pyc: 3790 bytes = 16-byte header + marshal
# inside the CArchive:     pos=22772, stored=1771 bytes, zlib -> 3774 bytes of raw marshal
```

**Step 2 - Pass the `[(H)34]` gate.**

Module `co_names` is `numbers, sys, italics, process_coines, hat_menu, main`. `numbers` is imported but never referenced by any function, and does not affect input validation.

The shop opens on a string comparison, not a numeric one:

```asm
  8           2 LOAD_FAST                0 (coines_value)
              4 LOAD_CONST               1 ('[(H)34]')
              6 COMPARE_OP              40 (==)
             10 POP_JUMP_IF_FALSE       11 (to 34)

  9          12 LOAD_GLOBAL              1 (NULL + hat_menu)
```

The `float()` branch only runs when the input differs from that exact string, so `10000` and `999999999` never reach the menu.

**Step 3 - The flag is assembled from a constant tuple, menu item 3.**

`hat_menu()` builds the flag in its first statement:

```asm
 18           2 BUILD_LIST               0
              4 LOAD_CONST               1 ((99, 100, 99, 116, 102, 123, 104, 52, 116, 95, 77, 48,
             117, 115, 51, 95, 112, 48, 107, 51, 95, 70, 76, 65, 71, 33, 125))
              6 LIST_EXTEND              1
              8 STORE_FAST               0 (fleg)
```

The `selection == 3` branch computes `plaintext = ''.join(str(chr(n)) for n in fleg)`. The genexpr bytecode contains only `LOAD_GLOBAL chr` then `LOAD_GLOBAL str`, no key and no XOR, so that tuple is the whole payload.

```python
nums = (99, 100, 99, 116, 102, 123, 104, 52, 116, 95, 77, 48, 117, 115, 51,
        95, 112, 48, 107, 51, 95, 70, 76, 65, 71, 33, 125)
print("".join(chr(n) for n in nums))
# cdctf{h4t_M0us3_p0k3_FLAG!}
```

Verification against the shipped binary, two stdin lines:

```bash
printf '[(H)34]\n3\n' | ./files/bringcoines.exe
```

```text
Hiya poke. Bring coines?

Tell Hat Mouse how many coins you have:

        =========================================
                    HAT MOUSE SHOP
...
        3.  Cowpoke Hat (fLEG!!!)
...
        0.  Exit Shop
        =========================================

Wowee! You want fleg: cdctf{h4t_M0us3_p0k3_FLAG!}
Enjoy!
```

The printed flag matches the string assembled from the tuple character by character, and `exploit.py` derives it from the artifact alone, so the result does not depend on this particular run.

## Result

```text
cdctf{h4t_M0us3_p0k3_FLAG!}
```

## Reproduce

```bash
python exploit.py files/bringcoines.exe
```

```text
[*] files\bringcoines.exe: 7284057 bytes, sha256 576db2ac5c6657189ea446c594092c7b7d0ad5d84f3246b1165d2a372b39c3c6
[*] CArchive: pkg=6936409 B, TOC=864 B, pyvers=312
[+] entry 'bringcoines' typecode=s pos=22772 stored=1771 B
[+] inflate -> 3774 B (marshal thô, chưa có header 16 byte)
[*] module '<module>', tên toàn cục: numbers, sys, italics, process_coines, hat_menu, main
[+] cổng vào hat_menu(): process_coines so input == '[(H)34]'
[+] menu nhận lựa chọn [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], mục 3 là 'Cowpoke Hat (fLEG!!!)'
[+] fleg = tuple 27 số nguyên, bốn số đầu [99, 100, 99, 116]
[+] flag: cdctf{h4t_M0us3_p0k3_FLAG!}
[+] đã lưu flag.txt
```

## Attached files

- `exploit.py`: stdlib-only CArchive parser, prints the flag and writes `flag.txt`.
- `analysis/dis_entry.txt`: full disassembly of the entry script.
- `analysis/live_run.txt`: real output of `files/bringcoines.exe`.
- `analysis/decoys.txt`: both decoy branches of `process_coines()`.
