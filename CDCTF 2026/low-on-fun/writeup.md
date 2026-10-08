# Low on function names - Reverse Engineering (500 điểm)

**Cờ:** `cdctf{Y_m4ny_functi0s_wh3n_f3w_d0_trick}` · **Files:** `low_on_fun.py`, 8690 B, sha256 `cb043a7dc96d316c7e46825268511bf5b0c2da38599ede991af237ccb7edff5f`

## Đề bài

Đề cho một file Python duy nhất và hỏi "tôi đã làm gì để khai báo hàm hiệu quả hơn". Chương trình là một flag checker: đọc đầu vào, kiểm tra định dạng, rồi in ra kết luận. Mục tiêu là tìm chuỗi đầu vào khiến checker chấp nhận, theo định dạng `cdctf{...}`.

## Phân tích

Toàn bộ thân hàm bị bỏ trống, chỉ còn một hàm rỗng `changing()` và một blob bytes 3069 byte trên dòng 3:

```python
def replacer(obj):new_fun = marshal.loads(obj);changing.__code__ = new_fun;return
def changing():return
def main():
    funs = functions.split(b'DELIM');replacer(funs[0]);flag = changing();replacer(funs[1]);
    if not changing(flag): return
    replacer(funs[2]);print(changing(flag.encode()).decode());return
```

Blob tách thành 3 code object `marshal` bởi chuỗi `DELIM`, độ dài 326 / 497 / 2236 byte, tên lần lượt `get_flag`, `init_checks`, `checker`. Câu trả lời cho "efficient declaration" là ở đây: tác giả không khai báo 3 hàm, mà khai báo 0 hàm có tên và hoán đổi `__code__` của cùng một object function qua 3 giai đoạn, thay đổi hành vi của function object qua từng giai đoạn.

Rào cản thật sự nằm ở version. Code object `marshal` không chứa magic number của file `.pyc`, nên không có dấu hiệu trực tiếp nào cho biết bytecode thuộc bản nào. Trên máy có 3.9, 3.11, 3.12, 3.14:

```text
===== py -3.9 =====
ValueError: bad marshal data (unknown type code)
===== py -3.11 =====
Segmentation fault   (exit=139)
===== py -3.12 =====
Segmentation fault   (exit=139)
===== py -3.14 =====
...
>Checking input...
That's the wrong length!
```

`dis` của 3.12 và 3.11 cũng cho kết quả vô nghĩa (instruction đầu tiên là `POP_JUMP_IF_NOT_NONE`, bên trong một hàm chỉ gọi `input()` lại có `LIST_TO_TUPLE` và `BEFORE_ASYNC_WITH`) vì độ rộng inline cache khác nhau làm lệch khung đọc opcode. Chỉ CPython 3.14 chạy được, nên mọi phân tích dưới đây dùng `py -3.14`.

## Hướng đã thử

Trước khi chốt đã kiểm tra và loại các kênh sau (log đầy đủ ở `notes.md`):

1. **Disassembly bằng Python hệ thống 3.12 / 3.11**: opcode đọc sai hàng loạt, `IndexError: tuple index out of range`, instruction đầu tiên đã là một jump điều kiện. Loại vì sai phiên bản.
2. **Chấp nhận `marshal.loads` thành công rồi chạy tiếp trên 3.11 / 3.12**: cả hai segfault (exit 139), do `marshal.loads` không kiểm tra layout cache nên interpreter thực thi bytecode lẫn lộn.
3. **Brute-force đầu vào thông qua checker như một oracle**: checker chỉ so sánh cả 40 byte một lần rồi trả về một trong hai chuỗi `b"That's it!"` hoặc `b'heck nah'`, không so sánh theo từng ký tự và không có oracle theo từng vị trí được ghi nhận. Loại vì không cần, xem Bước 3.

## Lời giải

**Bước 1 - Cố định phiên bản và tách ba hàm.** Dùng `py -3.14` làm bộ giải mã, xuất từng code object ra thư mục `analysis/`:

```bash
bash analysis/run_triage.sh
py -3.14 analysis/dump_dis.py 2
```

**Bước 2 - Đọc `init_checks` để lấy ràng buộc.** `str(inp).startswith('cdctf')` và `len(inp) == 40`; `inp` được ghi đè bằng chính `str(inp)` nên độ dài tính trên chuỗi ký tự.

**Bước 3 - Nhận ra `checker` là RC4, và keystream không phụ thuộc plaintext.** Toàn bộ 229 dòng disassembly gom lại thành:

```python
def checker(data):
    key = bytes.fromhex('98e2...d92c')          # 128 byte, nhúng sẵn
    enc = ['61','2e','ba','33','6f','91','33', ...]  # LIST_APPEND 40 lan, tu 36 hang so
    check = bytes.fromhex(''.join(enc))         # 40 byte: dung chuoi phai tim
    S = list(range(256)); j = 0
    for i in range(256):                        # KSA
        j = (S[i] + j + key[i % key_length]) % 256
        S[j], S[i] = S[i], S[j]
    out = bytearray(); k = l = 0
    for byte in data:                           # PRSA
        k = (k + 1) % 256; l = (S[k] + l) % 256
        S[k], S[l] = S[l], S[k]
        out.append(byte ^ S[(S[k] + S[l]) % 256])
    if bytes(out) == check: return b"That's it!"
    return b'heck nah'
```

Hai chi tiết trong bytecode: tham số của `checker` mang tên `data` (varname 0) chứ không phải `inp`, tức một tên dùng cho cả input và vòng lặp; danh sách `enc` có 40 phần tử nhưng `co_consts` chỉ chứa 36 chuỗi hex vì chỉ số 5 (`33`), 11 (`4c`), 14 (`03`) được dùng lại. Do `out = data ^ keystream(key)` và keystream chỉ sinh từ `key`, điều kiện `out == check` tương đương `data == check ^ keystream`, nên giải mã trực tiếp được mà không cần chạm tới oracle.

**Bước 4 - Suy ngược.** Script không cần `marshal.loads`: khóa và các cặp hex nằm nguyên văn trong blob nên đọc bằng regex, chạy được trên mọi Python 3.8+.

```python
check = bytes.fromhex(b"".join(pairs[i - 2] for i in ENC_ORDER).decode())
keystream = rc4_keystream(key, len(check))
flag = bytes(a ^ b for a, b in zip(check, keystream))
```

**Bước 5 - Kiểm chứng.** Độ dài 40 khớp ràng buộc của `init_checks`, prefix `cdctf` khớp. Chạy lại bằng chính checker gốc với Python 3.14, bản đầy đủ cho `That's it!` trong khi bản chỉ đổi ký tự cuối `k` thành `l` cho `heck nah`, xác nhận checker phân biệt được input đúng và input sai đã thử.

## Kết quả

```bash
python exploit.py files/low_on_fun.py
```

```text
[*] low_on_fun.py: 3069 bytes blob, 3 phan tu code (DELIM-split)
[*] ten ham trong 3 code object: get_flag, init_checks, checker
[*] khoa RC4: 128 byte, hex bat dau bang 98e29c5194c02970
[*] hang so 2-ky-tu tim thay: 36 (khop 36 muc co_consts cua checker)
[+] check = bytes.fromhex(''.join(enc)) -> 40 byte: 612eba336f913337b3de4c3b1e03f199014c12084a93e3f847d4bea54c03517f1bdc2718cc2d6cfb
[+] rc4_keystream(key, len(check)) -> XOR voi check
[+] flag = cdctf{Y_m4ny_functi0s_wh3n_f3w_d0_trick}
[+] khop rang buoc cua init_checks: prefix 'cdctf', do dai 40
[+] da luu flag.txt
```

```text
cdctf{Y_m4ny_functi0s_wh3n_f3w_d0_trick}
```

## Tái hiện

```bash
py -3.14 analysis/dump_dis.py 1   # rang buoc dinh dang
py -3.14 analysis/dump_dis.py 2   # toan bo disassembly cua checker
python exploit.py files/low_on_fun.py
echo 'cdctf{Y_m4ny_functi0s_wh3n_f3w_d0_trick}' | py -3.14 files/low_on_fun.py
```

*Flag được suy ra từ artifact và xác nhận bằng chính checker của đề; bản ghi hiện tại chưa có xác nhận submit trên scoreboard.*
