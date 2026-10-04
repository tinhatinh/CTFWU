# The flag knows what it is at all times - Crypto (500 points)

**Flag:** `cdctf{it is sure where it isn't, within reason, and it knows where it was}`
**Files:** `files/cipher.txt`, 149 byte, sha256 `23b75625f0b46c16e92de1844d77ece044918557cd472c0a398cb94da2afea75`
**Event:** CDCTF 2026 (Crimson Defense CTF) · **Tác giả:** alex

## Đề bài

Đề cho một chuỗi hex 148 ký tự và nói rằng cờ "biết nó là gì vì nó biết nó không phải là gì". Định dạng cờ là `cdctf{...}`. Không có file kèm theo, không có instance; toàn bộ dữ liệu là chuỗi hex trong mô tả.

## Phân tích ban đầu

- 148 ký tự hex là số chẵn, tức 74 byte, không có ký tự ngăn cách thừa.
- Dải giá trị byte đo được là `0x82-0xdf`. Không byte nào nhỏ hơn `0x80`, nên đây không phải text thô; dải này đúng bằng ảnh của các giá trị ASCII in được (`0x20-0x7e`) qua phép đảo bit (`0xdf-0x81`).
- Câu "nó biết nó không phải là gì" mô tả đúng phép NOT: `x ^ 0xFF = ~x`.

## Chuỗi khai thác

**Bước 1 - Thử phép đảo bit trên 6 byte đầu.** Nếu đúng là NOT thì 6 byte đầu phải dịch ra prefix `cdctf{`.

```python
>>> h = "9c9b9c8b9984"
>>> [f"{int(h[i:i+2],16):02x} ^ ff = {chr(0xff ^ int(h[i:i+2],16))}" for i in range(0, 12, 2)]
['9c ^ ff = c', '9b ^ ff = d', '9c ^ ff = c', '8b ^ ff = t', '99 ^ ff = f', '84 ^ ff = {']
```

**Bước 2 - Quet toàn bộ 256 key XOR một byte thay vì chấp nhận đoán.** Key chỉ được coi là đúng nếu nó là giá trị duy nhất cho ra ASCII in được và bao đúng `cdctf{` / `}`.

```python
data = bytes.fromhex(hexstr)
hits = []
for key in range(256):
    text = "".join(chr(b ^ key) for b in data)
    if text.isprintable() and text.startswith("cdctf{") and text.endswith("}"):
        hits.append((key, text))
```

```text
[*] cipher.txt: 148 hex ky tu
[*] 74 byte, pham vi 0x82-0xdf
[*] quet 256 key XOR 1 byte: 1 kha nang
[+] key duyet = 0xff (XOR 0xff = bitwise NOT)
    9c ^ ff = c
    9b ^ ff = d
    9c ^ ff = c
    8b ^ ff = t
    99 ^ ff = f
    84 ^ ff = {
[+] flag: cdctf{it is sure where it isn't, within reason, and it knows where it was}
```

**Bước 3 - Kiểm chứng.** Phép quet có thể sinh ra nhiều key cùng cho text in được, thực tế chỉ trả về 1 kết quả, nên `0xff` không phải lựa chọn may mắn. Đầu ra là câu tiếng Anh trọn nghĩa, khớp cách dùng từ của chính đề bài ("it is sure ... within reason ... it knows where it was"), và 74 byte phủ hết bản mã, không còn phần nào chưa decode.

## Flag

```text
cdctf{it is sure where it isn't, within reason, and it knows where it was}
```

## Reproduce

```bash
python exploit.py files/cipher.txt
```

Không có key riêng tư hay thông tin instance trong script.
