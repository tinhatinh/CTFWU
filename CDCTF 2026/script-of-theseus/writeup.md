# Script of Theseus - Forensics (493 điểm)

**Flag:** `cdctf{0D}` · **Files:** `original_epic_python_script.py` (156 byte, sha256 `56c4472cb2f3876c86932bfecb18d276af7f8e8a4b6fb146b40d02d8f90f0b3f`) và `replaced_epic_python_script.py` (163 byte, sha256 `c88ef02ea2a56fdd9957a86f79d8799fe2b2388a06fe4b9b979f34bbfa402c57`)

## Đề bài

Đề cho hai bản của một script Python ngắn: bản gốc của tác giả (dùng Linux) và bản do một người bạn
"xóa hết rồi viết lại từng dòng" trên Windows. Yêu cầu: tìm điểm khác nhau và nộp hex in hoa của một
byte nằm trong điểm khác nhau đó, cờ dạng `cdctf{FF}`. Bài chỉ có file, không có instance.

## Phân tích

Hai file gần như cùng kích thước, 156 và 163 byte, lệch nhau 7 byte. `file` mô tả cả hai là
`Python script, ASCII text executable`, nhưng chỉ bản `replaced` mang đuôi nhận xét
`with CRLF line terminators`.

```bash
file files/*.py
```

```text
files/original_epic_python_script.py: Python script, ASCII text executable
files/replaced_epic_python_script.py: Python script, ASCII text executable, with CRLF line terminators
```

Hexdump hai phần đầu thì thấy ngay: bản gốc kết thúc dòng bằng `0a`, bản `replaced` bằng `0d 0a`.

```text
00000000: 2321 2f75 7372 2f62 696e 2f65 6e76 2070  #!/usr/bin/env p
00000010: 7974 686f 6e33 0a0a 636f 6c6f 723d 696e  ython3..color=in         <- original

00000000: 2321 2f75 7372 2f62 696e 2f65 6e76 2070  #!/usr/bin/env p
00000010: 7974 686f 6e33 0d0a 0d0a 636f 6c6f 723d  ython3....color=         <- replaced
```

Điều cần chứng minh không phải là "có CRLF", mà là ngoài CRLF không còn thay đổi nào khác: nếu người
bạn còn sửa chữ nào đó thì byte khác biệt sẽ không đơn nhất.

## Hướng đã thử

1. **Script bị sửa nội dung (tên biến, chuỗi, thụt lề, thêm dòng)**: bỏ `0d` khỏi bản `replaced` rồi so
   với bản gốc thì `cmp` trả về giống hệt, và số dòng của hai file bằng nhau (7 với cả hai).
2. **Khác biệt là BOM hoặc sang mã UTF-16**: 8 byte đầu hai file giống nhau từng byte một
   (`23 21 2f 75 73 72 2f 62`), không có `ef bb bf` hay `ff fe`; `file` vẫn báo ASCII cho cả hai.
3. **Bản `replaced` có thêm dòng trống**: số byte `0a` của hai file đều bằng 7, nên không có newline mới,
   chỉ có byte chèn thêm trước các newline đã tồn tại.
4. **Dùng `cmp -l` để liệt kê byte lệch**: lệnh in ra hơn 130 dòng lệch vì một byte chèn ở `0x16` làm
   trôi toàn bộ chỉ số phía sau; output này so hai chuỗi lệch pha nên không đọc được gì. Loại cách đo,
   chuyển sang so tần suất byte và so sau khi chuẩn hoá.

## Lời giải

**Bước 1 - Đo tần suất byte thay vì diff text.** Đếm số lần từng giá trị byte ở hai file rồi lấy hiệu
theo cả hai chiều; `analysis/byte_freq.py` làm phép đo này và in kèm số LF/CR của từng bản.

```bash
python analysis/byte_freq.py
```

```text
original_epic_python_script.py: 156 byte, LF(0x0A) 7, CR(0x0D) 0, 8 byte dau 23 21 2f 75 73 72 2f 62
  BOM: khong | phi ASCII in duoc: 149/156
replaced_epic_python_script.py: 163 byte, LF(0x0A) 7, CR(0x0D) 7, 8 byte dau 23 21 2f 75 73 72 2f 62
  BOM: khong | phi ASCII in duoc: 149/163

Them o ban sau : {'0x0D': 7}
Mat di o ban sau: {}

Vi tri 0x0D: ['0x16', '0x18', '0x45', '0x63', '0x7b', '0x82', '0xa1']
Duoc 0x0A di kem: 7/7
Xoa het 0x0D -> khop ban goc: True
```

Bản `replaced` dài hơn 7 byte, cả 7 byte thừa đều là `0x0D`, và hiệu ngược lại rỗng nên không có byte
nào bị mất: Kết quả này kiểm tra tần suất, còn thứ tự byte được xác nhận ở Bước 3.

**Bước 2 - Kiểm tra vai trò của `0x0D`.** Trong bản `replaced`, cả 7 byte `0x0D` đều đứng ngay trước
một `0x0A` (`Duoc 0x0A di kem: 7/7`), tại các offset `0x16 0x18 0x45 0x63 0x7b 0x82 0xa1`. Đúng 7 lần
xuống dòng của script, tức từng cặp `0D 0A` là một line ending kiểu Windows thay cho `0A` kiểu Linux.

**Bước 3 - Kiểm chứng bằng phép thử đảo.** Xoá toàn bộ `0x0D` khỏi bản `replaced` thì thu được chuỗi
156 byte trùng khớp byte-per-byte với bản gốc, nên khác biệt của hai file chỉ là các byte `0x0D`.

```bash
tr -d '\r' < files/replaced_epic_python_script.py | cmp - files/original_epic_python_script.py && echo "giong het ban goc"
```

```text
giong het ban goc
```

## Kết quả

```bash
python exploit.py
```

```text
[*] original: 156 byte, LF 7, CR 0
[*] replaced: 163 byte, LF 7, CR 7
[*] lech do dai: 7 byte
[*] byte them: {'0x0D': 7}
[*] byte mat:  {}
[*] vi tri 0x0D: 0x16 0x18 0x45 0x63 0x7B 0x82 0xA1
[*] 0x0D 0x0A lien ke: 7/7 -> line ending CRLF
[+] xoa 7 byte 0x0D khoi ban replaced -> 156 byte, trung khop ban goc: True
[+] FLAG: cdctf{0D}
```

```
cdctf{0D}
```

## Tái hiện

```bash
python exploit.py files/original_epic_python_script.py files/replaced_epic_python_script.py
```

Script đọc hai file bằng đường dẫn truyền vào (không có tham số thì tự lấy trong `files/`), in bảng
tần suất byte, kiểm tra điều kiện "chỉ một byte thừa và mọi byte thừa đều đứng trước `0A`", xác nhận
phép thử đảo ở Bước 3, rồi ghi `flag.txt`. `analysis/byte_freq.py` là bản khám phá ban đầu, output của
nó lưu ở `analysis/byte_freq.txt`.
