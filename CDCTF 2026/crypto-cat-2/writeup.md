# Crypto Cat Caticus Catanius (2/5) - Crypto (496 điểm)

**Flag:** `cdctf{exclus1ve_x0r1n_these_byt3s_and_5tuff}` · **Files:** `files/ciphertext.txt`, 135 byte, sha256 `fc729a7d866ee019d3da211dd885f86922885d6d2205e51e558c1c318c1360dd`
**Event:** CDCTF 2026 (Crimson Defense CTF) · **Tác giả:** alex

## Đề bài

Phần 2/5 của chuỗi Crypto Cat. Thẻ đề chỉ in 45 token hex, không có file tải về, không có
instance. Câu "it seems you have cracked my first key" chỉ vào phần 1 (bản chất là phép Atbash
đổi `xwxgu{...}` thành `cdctf{...}`), còn bản thân bản mã không cho biết thuật toán.

## Phân tích ban đầu

- 45 token hex, mỗi token gồm hai chữ số, gom lại thành đúng 45 byte, không có byte thừa.
- Dải giá trị `0x85` đến `0xfd`, 24 giá trị phân biệt. Không một byte nào nhỏ hơn `0x80`.
- Dải đó đúng bằng ảnh của ASCII in được (`0x20`-`0x7e`) qua một mặt nạ có bit 7 bật, nên hướng
  đầu tiên là XOR một byte. Byte `0x85` nằm ngoài `0xba`-`0xfd` (phần còn lại của dải) và là dấu
  vết của một plaintext `0x0a`: `0x85 ^ 0x8f = 0x0a`, tức bản mã kết thúc bằng ký tự xuống dòng.

## Các hướng đã loại

1. **XOR/Vigenère byte nhiều khóa (L = 2..15, các chiều `xor`, `sub`, `add`, `beaufort`).**
   `analysis/triage.py` quét mỗi cột theo ràng buộc "toàn bộ byte giải mã phải in được". Với điều kiện ASCII in được (`0x20`-`0x7e`) chỉ `xor` còn ứng viên, và mỗi cột còn 20-94 ứng viên nên khóa không xác
   định được; `sub`, `add`, `beaufort` không có ứng viên ở các độ dài đã thử. Hạ chuẩn xuống cho phép thêm tab/LF/CR thì
   `xor` có ứng viên ở L = 1, `sub`/`add` chỉ còn L = 8, 9, 10, 15, `beaufort` vẫn không có ứng viên. Các khóa nhiều byte chưa được xác định; khóa một byte được chọn bằng prefix cờ ở bước sau.
2. **Atbash như phần 1.** `analysis/atbash_check.py` chạy cả hai mức: atbash trên ký tự hex biến
   chữ số thành `0xa2`-`0xab` (ngoài ASCII), còn đảo bit toàn byte (`0xff ^ b`) chỉ để lại 11/45 byte
   trong vùng in được, 6 byte đầu ra `0x13 0x14 0x13 0x04 0x16 0x0b`. Chiếu nghiệm cho cùng bộ đếm
   với khóa `0x8f` cho 44/45, nên con số 11/45 là phép đo biết báo dương chứ không phải mặc định.

## Chuỗi khai thác

**Bước 1 - Quét toàn bộ 256 khóa một byte.** Đếm số khóa mà mọi byte giải mã đều in được, tách
làm hai chuẩn: ASCII in được tuyệt đối (`0x20`-`0x7e`) và chuẩn có cho phép thêm tab/LF/CR.

```python
def dec(k):
    return bytes(b ^ k for b in data)


LOOSE = set(range(0x20, 0x7F)) | {0x09, 0x0A, 0x0D}
loose = [k for k in range(256) if all(c in LOOSE for c in dec(k))]
strict = [k for k in range(256) if all(0x20 <= c < 0x7F for c in dec(k))]
```

```text
[*] XOR 1 byte, 256 khoa: 0 khoa cho ASCII in duoc tuyet doi, 5 khoa neu cho phep them tab/LF/CR
    k=0x8c, k=0x8f, k=0xd9, k=0xda, k=0xdd
```

Không khóa nào thỏa chuẩn tuyệt đối Với khóa tìm được ở bước sau, byte cuối giải mã thành `0x0a`. Năm khóa còn lại là
toàn bộ không gian tìm được, không phải mẫu chọn.

**Bước 2 - Chốt bằng crib định dạng cờ.** Trong năm khóa, chỉ một khóa mở đầu bằng `cdctf{`.

```python
hit = [k for k in loose if dec(k).startswith(b"cdctf{")]
```

```text
[*] khoa vua ASCII vua mo dau bang dinh dang cdctf{: 1 -> k=0x8f
[+] plaintext (repr): b'cdctf{exclus1ve_x0r1n_these_byt3s_and_5tuff}\n'
```

`0x8f` là khóa một byte duy nhất trong tập đã lọc cho prefix `cdctf{`. Các chữ số `1`, `0`, `3` trong phần thân được giữ nguyên từ output giải mã.

**Bước 3 - Kiểm chứng.** Mã hóa lại toàn bộ plaintext với `0x8f` phải tái tạo đúng chuỗi hex của đề.

```text
[+] round-trip: ma hoa lai 45 byte voi 0x8f cho ra dung chuoi de ban dau -> True
```

Đầu ra dài 45 byte phủ hết bản mã, phần thân cờ không chứa ký tự trắng và cặp ngoặc `{}` đóng một lần.

## Flag

```bash
python exploit.py files/ciphertext.txt
```

```text
[*] ciphertext.txt: 45 to hex, goi lai duoc 45 byte
[*] dai byte: 0x85 - 0xfd, 24 gia tri phan biet
[*] so byte duoi 0x80: 0 (0 = khong phai ASCII thuan, nen day la ket qua cua phep doi cho)
[*] XOR 1 byte, 256 khoa: 0 khoa cho ASCII in duoc tuyet doi, 5 khoa neu cho phep them tab/LF/CR
    k=0x8c, k=0x8f, k=0xd9, k=0xda, k=0xdd
[*] khoa vua ASCII vua mo dau bang dinh dang cdctf{: 1 -> k=0x8f
[+] khoa k = 0x8f = 143
[+] plaintext (repr): b'cdctf{exclus1ve_x0r1n_these_byt3s_and_5tuff}\n'
[*] byte cuoi 0x85 XOR 0x8f = 0x0a -> ky tu xuong dong, khong thuoc co
[+] round-trip: ma hoa lai 45 byte voi 0x8f cho ra dung chuoi de ban dau -> True
[+] flag: cdctf{exclus1ve_x0r1n_these_byt3s_and_5tuff}
[+] da luu flag.txt
```

## Reproduce

```bash
python exploit.py files/ciphertext.txt
```

`analysis/triage.py` là bước quét nhiều khóa, `analysis/atbash_check.py` là bước loại atbash; cả hai
chạy trong thư mục bài và đã lưu output thành `.out` tương ứng. Bài này không có artifact tải về,
`files/ciphertext.txt` là bản chép lại dòng hex in trên thẻ đề.
