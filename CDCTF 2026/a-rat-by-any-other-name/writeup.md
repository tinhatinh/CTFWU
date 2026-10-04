# A rat by any other name - Password Cracking (500 pts)

**Flag:** `cdctf{Jaqurtis}` · **Files:** `files/hash.txt` (33 byte, sha256 `66ad6348...d1c48f`)

## Đề bài

Một con chuột có tên người, mật khẩu của nó đúng bằng tên. Đề cho một hash MD5 `fe00ab6a1d242513c9f246344bf7da1d` và ba ràng buộc về hình thức của tên: dài không quá 8 ký tự, ký tự đầu in hoa, các ký tự còn lại in thường. Không có file nhị phân, không có dịch vụ; nhiệm vụ chỉ là thu hồi chuỗi thỏa mãn hash và đúng ràng buộc. Cờ theo dạng `cdctf{Name}`.

## Phân tích ban đầu

Ba ràng buộc của đề không phải gợi ý để đoán tên, chúng là một mask. Tập mật khẩu hợp lệ là đúng một lớp ký tự:

```text
?u?l{0,7}  =  26 + 26^2 + ... + 26^8  =  217.180.147.158 ứng viên
```

MD5 có tốc độ tính toán cao, phù hợp với mask attack trên không gian này. hashcat 6.2.6 trên RTX 3050 laptop đạt 8415 MH/s với optimized kernel; lần chạy với độ dài tối đa 8 kết thúc trong dưới một phút.

Wordlist vẫn được thử trước, và cả ba corpus đều âm tính:

| Corpus | Số ứng viên đã so MD5 | Kết quả |
| --- | --- | --- |
| `words_alpha.txt` (từ điển tiếng Anh, chỉ từ <= 8 ký tự viết hoa đầu) | 149.189 | không khớp |
| `name-dataset` first names (mọi biến thể gốc / capitalize / title) | 727.556 | không khớp |
| Moby Project `NAMES*.TXT` (tên riêng trong từ điển Scrabble) | 30.829 | không khớp |

Các wordlist đã thử không chứa ứng viên khớp hash. Vì đề quy định rõ độ dài và charset, có thể tiếp tục bằng mask attack mà không cần bổ sung danh sách tên.

## Chuỗi khai thác

**Bước 1 - Kiểm tra mask bằng một hash đã biết.** Dùng hash MD5 của `Felix` để kiểm tra cấu hình hashcat trước khi chạy với hash của đề.

```bash
python exploit.py --selftest
```

```text
[*] selftest: an md5('Felix') = 2c3baf26f776086aab9f234f8c9a00ed
[*] thu hoi: 'Felix' (18.6 s, rc=0)
[+] PASS: bo sinh to hop tim thay mat khau trong family mask.
```

**Bước 2 - Chạy mask đầy đủ trên hash của đề.** `--increment` với mask 8 vị trí tự sinh các mặt cắt 1..8 ký tự, mỗi mặt cắt vẫn giữ quy tắc một chữ hoa đầu rồi tới chữ thường:

```bash
python exploit.py
```

```text
[*] MD5 = fe00ab6a1d242513c9f246344bf7da1d, mask = ?u?l?l?l?l?l?l?l, mien = 2..8
[*] thu hoi: 'Jaqurtis' (41.9 s)
[+] ten cua chuot: Jaqurtis
[+] cdctf{Jaqurtis}
```

Lệnh hashcat tương đương và trạng thái đo được ở lần chạy đầu:

```bash
hashcat -O -m 0 -a 3 -d 1 -w 3 --increment --increment-min 2 --increment-max 8 \
        hash.txt '?u?l?l?l?l?l?l?l'
```

```text
Status...........: Cracked
Guess.Mask.......: ?u?l?l?l?l?l?l?l [8]
Speed.#1.........:  8415.0 MH/s (58.07ms) @ Accel:512 Loops:1024 Thr:64 Vec:8
Recovered........: 1/1 (100.00%) Digests (total), 1/1 (100.00%) Digests (new)
Progress.........: 36771463168/208827064576 (17.61%)
```

```text
fe00ab6a1d242513c9f246344bf7da1d:Jaqurtis
```

**Bước 3 - Kiểm chứng.** Kiểm tra hash và các ràng buộc của đề:

```python
import hashlib
print(hashlib.md5(b"Jaqurtis").hexdigest())   # fe00ab6a1d242513c9f246344bf7da1d
```

- `md5("Jaqurtis")` khớp hash trong đề.
- `Jaqurtis` dài 8 ký tự, bắt đầu bằng chữ hoa và có các ký tự còn lại viết thường.
- Các mask độ dài 1..7 đã chạy hết mà không tìm thấy kết quả; ứng viên được tìm thấy ở độ dài 8. Ba wordlist đã thử trước đó không chứa tên này.

## Flag

```text
cdctf{Jaqurtis}
```

## Reproduce

```bash
python exploit.py --selftest    # kiem machine sinh ung vien (md5 cua "Felix")
python exploit.py               # tan cong mask ?u?l{1,7} tren hash cua de
```

Cần hashcat. Đường dẫn mặc định `C:\Tools\hashcat\hashcat-6.2.6\hashcat.exe`, ghi đè bằng biến môi trường `HASHCAT`; thiết bị ghi đè bằng `HASHCAT_DEV` (`1` là CUDA, `3` là CPU). hashcat tự tìm kernel theo đường dẫn tương đối `./OpenCL/`, nên script chạy binary trong thư mục cài đặt của nó.
