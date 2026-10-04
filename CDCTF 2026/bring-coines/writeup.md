# bring-coines - Reverse Engineering (500 points)

**Flag:** `cdctf{h4t_M0us3_p0k3_FLAG!}`
**Files:** `bringcoines.exe`, 7284057 byte, sha256 `576db2ac5c6657189ea446c594092c7b7d0ad5d84f3246b1165d2a372b39c3c6`

## Đề bài

Hat Mouse bán mũ. Program chạy lên hỏi "how many coins you have", nhập đúng thì mở shop, trong shop có một mặt hàng ghi `fLEG!!!`. Cờ dạng `cdctf{fleg}`. Đề chỉ cho một file `.exe` duy nhất, không có source.

## Phân tích ban đầu

- `file` báo PE32+ console x86-64, 7 section, 7.28 MB. Dung lượng này không đi kèm code thật: `.text` chỉ `0x2dc00` byte.
- `strings` có `PyRun_SimpleStringFlags`, `pyi-python-flag`, `python312.dll`, section `.fptable`. Đây là bootloader PyInstaller của CPython 3.12, toàn bộ logic nằm trong CArchive ở cuối file.
- Imports chỉ KERNEL32/USER32 (heap, console, window mặc định của bootloader). Không có antidebug, không có self-check.
- Quét chuỗi trên toàn file không ra mẫu `cdctf{...}`: entry bytecode bị zlib nén, nên chuỗi dựng sẵn duy nhất là các message tiếng Anh thường.

## Các hướng đã loại

1. **Tìm cờ trong resource hoặc data của PE.** `.rsrc` 0xf000 byte là manifest PyInstaller mặc định, `.data` chỉ `0xe00` byte. Không có payload đáng nghi ngoài CArchive.
2. **Nhập số xu lớn.** Hai nhánh trong `process_coines()` đều là mồi: `float()` parse được thì in `That's a lotta coines poke. Congrats!` rồi về, không parse được thì in `That's not coines...`. Giá mũ trong menu (2,000 đến 10,000 coins) cũng chỉ là chữ, program không giữ số dư nào.

## Chuỗi khai thác

**Bước 1 - Tách bytecode của entry script.**

Cần Python 3.12 trên máy phân tích: magic của `.pyc` là `cb0d0d0a`, nên `marshal.loads` đọc được thẳng code object, không cần decompiler (uncompyle6 và decompyle3 dừng ở 3.9).

```bash
pip install pyinstxtractor-ng
python -m pyinstxtractor_ng bringcoines.exe
# [+] Pyinstaller version: 2.1+
# [+] Python version: 3.12
# [+] Found 21 files in CArchive
# [+] Possible entry point: bringcoines.pyc
```

Cấu trúc trong file: cookie `MEI\x0c\x0b\x0a\x0b\x0e` (8 byte) ở cuối, theo sau là 4 trường big-endian `pkgLen, tocPos, tocLen, pyVers` rồi tên `python312.dll`. Mỗi TOC entry là `>IIIIBc` (độ dài entry, offset, kích thước, offset kết thúc, flag, typecode) rồi tên pad tới hết entry. Entry cần tìm có typecode `s` (script Python):

```python
# extract/bringcoines.pyc: 3790 byte, header 16 byte + marshal
# trong CArchive: pos=22772, stored=1771 byte, zlib -> 3774 byte marshal thô
```

**Bước 2 - Xác định chuỗi mở shop `[(H)34]`.**

`co_names` của module là `numbers, sys, italics, process_coines, hat_menu, main`. `numbers` được import nhưng không hàm nào tham chiếu, không ảnh hưởng đến logic kiểm tra đầu vào.

Điều kiện mở shop là so sánh chuỗi, không phải so sánh số:

```asm
  8           2 LOAD_FAST                0 (coines_value)
              4 LOAD_CONST               1 ('[(H)34]')
              6 COMPARE_OP              40 (==)
             10 POP_JUMP_IF_FALSE       11 (to 34)

  9          12 LOAD_GLOBAL              1 (NULL + hat_menu)
```

Nhánh `float()` phía sau chỉ chạy khi input khác đúng chuỗi đó, nên nhập `10000` hay `999999999` đều không bao giờ tới menu.

**Bước 3 - Cờ dựng từ tuple hằng số, chọn mục 3.**

`hat_menu()` khai cờ ngay đầu hàm:

```asm
 18           2 BUILD_LIST               0
              4 LOAD_CONST               1 ((99, 100, 99, 116, 102, 123, 104, 52, 116, 95, 77, 48,
             117, 115, 51, 95, 112, 48, 107, 51, 95, 70, 76, 65, 71, 33, 125))
              6 LIST_EXTEND              1
              8 STORE_FAST               0 (fleg)
```

Nhánh `selection == 3` làm `plaintext = ''.join(str(chr(n)) for n in fleg)`. Bytecode của genexpr chỉ có `LOAD_GLOBAL chr` rồi `LOAD_GLOBAL str`, không có key, không có phép XOR, nên tuple trên là toàn bộ dữ liệu.

```python
nums = (99, 100, 99, 116, 102, 123, 104, 52, 116, 95, 77, 48, 117, 115, 51,
        95, 112, 48, 107, 51, 95, 70, 76, 65, 71, 33, 125)
print("".join(chr(n) for n in nums))
# cdctf{h4t_M0us3_p0k3_FLAG!}
```

Kiểm chứng bằng chính binary, hai dòng input stdin:

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

Cờ in ra khớp từng ký tự với chuỗi dựng từ tuple, và `exploit.py` suy ra cờ chỉ từ artifact nên không phụ thuộc lần chạy này.

## Flag

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

## File kèm

- `exploit.py`: parser CArchive bằng stdlib, in cờ và ghi `flag.txt`.
- `analysis/dis_entry.txt`: disassembly đầy đủ của entry script.
- `analysis/live_run.txt`: output thật của `files/bringcoines.exe`.
- `analysis/decoys.txt`: hai nhánh mồi của `process_coines()`.
