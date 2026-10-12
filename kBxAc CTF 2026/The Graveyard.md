---
title: "The Graveyard"
category: "Misc"
tags: ["steganography", "whitespace", "SNOW", "SpamMimic", "base64", "book-cipher"]
solve_date: "2026-10-10T19:10:00+07:00"
language: "vi"
points: 916
---

# The Graveyard

**Flag:** `kBxAc{tr4c1ng_4_wh1t3sp4c3_b26_x9a8b7c6}`  
**Tác giả:** HydraRoot  
**File đề:** `chall (3).zip`

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `chall (3).zip` | 14,637 | `035e9a2d30fc9306e609478e05998d58455de6eec3f86be899416b9e4d849f49` |
| `archive-book.txt` | 7,141 | `cfaa8d07a76cc3375bb9f791abea8633ef0335cc4e67e556fc1c1cf59cff2756` |
| `03.txt` | 984 | `5527696da451008c7a74b88ea20ca69daf13309051bb6e71c71be2bf98092418` |
| `07.txt` | 3,642 | `7bf8c86d15e8d08e35463f18f5bf873a35906958c275847a1becfa5e01de87f8` |
| `11.txt` | 855 | `afbdd64f634785ee8e7d4a7515e02df6e87d2345087a74dc6af0b452def92bc2` |
| `14.txt` | 848 | `e61d8259e9e2a24697222783d000c852c2c4f859362caeca9355529073bd8b52` |
| `19.txt` | 755 | `963d3fde0d2c8207fad74323a9c7c65d8ecb119ed8fb3ce31ea160522ecebbcc` |

## Đề bài

> Twenty fragments were recovered from an old archive, but only some of them belong to the actual investigation. The fragments appear unrelated, and several contain misleading information. Somewhere among them is the path to reconstructing what was hidden in the archive.

Archive chứa 20 tệp `01.txt` đến `20.txt` và một tệp `archive-book.txt` (80 dòng). Cần nhận biết những fragment thật, giải lớp dữ liệu vô hình trong chúng rồi tái tạo thông điệp từ cuốn sách.

## Phân tích ban đầu

Các fragment trông giống ghi chép khảo sát lưu trữ. Phần lớn chỉ có văn bản bình thường, nhưng năm tệp `03`, `07`, `11`, `14`, `19` có dấu **tab (`\t`) và dấu cách (`0x20`) ở cuối dòng**. Không được chạy `strip()`, tự động format hoặc lưu lại qua editor có chức năng xóa trailing whitespace vì sẽ làm mất dữ liệu.

Kiểm tra nhanh:

```bash
unzip -l 'chall (3).zip'
unzip -p 'chall (3).zip' 11.txt | cat -A
```

Dấu `^I` trong `cat -A` biểu thị tab, còn `$` biểu thị kết thúc dòng. Việc xuất hiện dày đặc nhóm space/tab cuối dòng là dấu hiệu của **SNOW whitespace steganography**.

## Lớp 1 — SpamMimic xác nhận 5 fragment thật

Trong `07.txt`, sau nhãn `Recovered Transmission:`, có một bức thư quảng cáo dài mang đặc trưng của **SpamMimic**, phương pháp giấu thông tin trong email spam giả. Tách riêng phần email (không kèm nhãn), đưa vào SpamMimic decoder:

- <https://www.spammimic.com/decode.shtml>

Thông điệp giải ra là Base64:

```text
VFJVRSBGUkFHTUVOVFM6IDAzIDA3IDExIDE0IDE5
```

Giải mã:

```python
import base64
print(base64.b64decode('VFJVRSBGUkFHTUVOVFM6IDAzIDA3IDExIDE0IDE5').decode())
```

```text
TRUE FRAGMENTS: 03 07 11 14 19
```

Đây là **tập fragment cần dùng**, chưa phải thứ tự của các ký tự flag. Trật tự theo ngày tháng trong ghi chép cũng không phải cách ghép flag.

## Lớp 2 — Đọc dữ liệu SNOW dưới dạng bit

Mỗi nhóm từ 0 đến 7 dấu cách (ngăn bởi tab) mã hóa **3 bit**; theo SNOW, ba bit được đọc theo thứ tự bit thấp đến bit cao (**LSB-first**). Tab đầu tiên của payload chỉ đánh dấu bắt đầu và không mang dữ liệu.

Với số dấu cách `n`, thêm các bit `(n>>0)&1`, `(n>>1)&1`, `(n>>2)&1`. Sau khi đọc mọi đoạn whitespace cuối dòng của từng fragment, gom luồng bit thành các bản ghi **16-bit, big-endian**; bỏ 1–2 bit đệm còn lại nếu có. Không cần Huffman hoặc giải nén thêm cho bài này.

Kết quả nhận được 67 bản ghi, tương ứng 67 ký tự cần tra trong sách. Chúng **không phải byte ASCII trực tiếp**, mà là tọa độ.

## Lớp 3 — Giải mã tọa độ trong `archive-book.txt`

`archive-book.txt` có 80 dòng, mỗi dòng chứa các từ cách nhau bằng whitespace. Nhiều từ cố tình sai chính tả / thay một ký tự, ví dụ `ketal`, `Burator`, `sexled`. Những vị trí này là dữ liệu chứ không phải lỗi cần sửa.

Một bản ghi 16-bit `v` đóng gói ba chỉ số **bắt đầu từ 0**:

```python
line_index = v >> 8
word_index = (v >> 4) & 0x0F
char_index = v & 0x0F
character = book[line_index][word_index][char_index]
```

Ví dụ 3 bản ghi đầu của `11.txt`:

| Value | (Line, Word, Char) — 0-based | Lấy ký tự | Kết quả |
|---|---|---|---|
| `0x3B60` | `(59, 6, 0)` | `ketal[0]` | `k` |
| `0x3870` | `(56, 7, 0)` | `Burator[0]` | `B` |
| `0x3972` | `(57, 7, 2)` | `sexled[2]` | `x` |

Do đó `11.txt` bắt đầu bằng `kBx...` đúng với tiền tố flag.

## Kết quả giải mã

| Fragment | SNOW bits | 16-bit records | Extracted text |
|---|---:|---:|---|
| `03.txt` | 225 | 14 | `th3_sp4m_b4s36` |
| `07.txt` | 210 | 13 | `00k_c1ph3r_20` |
| `11.txt` | 225 | 14 | `kBxAc{tr4c1ng_` |
| `14.txt` | 225 | 14 | `4_wh1t3sp4c3_b` |
| `19.txt` | 192 | 12 | `26_x9a8b7c6}` |
| **Total** | **1,077** | **67** | |

`03.txt` và `07.txt` tạo thành phần tiền tố bổ trợ `th3_sp4m_b4s3600k_c1ph3r_20`. Flag hoàn chỉnh bắt đầu tại `11.txt`, tiếp tục ở `14.txt`, và kết thúc tại `19.txt`:

```text
11.txt: kBxAc{tr4c1ng_
14.txt: 4_wh1t3sp4c3_b
19.txt: 26_x9a8b7c6}
```

```text
kBxAc{tr4c1ng_4_wh1t3sp4c3_b26_x9a8b7c6}
```

## Tái hiện (Python 3, không cần thư viện ngoài)

Lưu đoạn sau thành `solve.py`, đặt cạnh ZIP gốc, rồi chạy `python solve.py "chall (3).zip"`. Script đọc trực tiếp ZIP và giữ nguyên trailing whitespace.

```python
#!/usr/bin/env python3
"""The Graveyard - reproducible solver. Python 3.8+, stdlib only."""
import re
import sys
import zipfile

TRUE_FRAGMENTS = ("03", "07", "11", "14", "19")


def snow_bits(data: bytes) -> str:
    """Decode the 3-bit groups from SNOW-style trailing whitespace."""
    started = False
    bits = []
    for line in data.splitlines():
        match = re.search(rb"[ \t]+$", line)
        if not match:
            continue
        ws = match.group(0)

        # SNOW starts with a delimiter tab, which is not payload.
        if not started:
            if not ws.startswith(b"\t"):
                continue
            ws = ws[1:]
            started = True

        spaces = 0
        for ch in ws:
            if ch == 0x20:  # space
                spaces += 1
            elif ch == 0x09:  # tab terminates a 3-bit group
                if spaces > 7:
                    raise ValueError("Invalid SNOW spacing")
                bits.extend(str((spaces >> i) & 1) for i in range(3))
                spaces = 0
        if spaces:  # final group at the end of a line
            if spaces > 7:
                raise ValueError("Invalid SNOW spacing")
            bits.extend(str((spaces >> i) & 1) for i in range(3))
    return "".join(bits)


def solve(archive_path: str):
    with zipfile.ZipFile(archive_path) as z:
        # Preserve line/word/character case and zero-based coordinates.
        book = [line.split() for line in
                z.read("archive-book.txt").decode("utf-8").splitlines()]
        recovered = {}
        for number in TRUE_FRAGMENTS:
            bits = snow_bits(z.read(number + ".txt"))
            # Discard the final 1-2 padding bits, if present.
            records = [int(bits[i:i + 16], 2)
                       for i in range(0, len(bits) - 15, 16)]
            chars = []
            for value in records:
                line = value >> 8
                word = (value >> 4) & 0x0F
                char = value & 0x0F
                chars.append(book[line][word][char])
            recovered[number] = "".join(chars)
            print(f"{number}.txt: {recovered[number]} "
                  f"({len(records)} records; {len(bits)} bits)")

    flag = recovered["11"] + recovered["14"] + recovered["19"]
    assert flag == "kBxAc{tr4c1ng_4_wh1t3sp4c3_b26_x9a8b7c6}"
    print("FLAG:", flag)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit('Usage: python solve.py "chall (3).zip"')
    solve(sys.argv[1])
```

Output thực tế:

```text
03.txt: th3_sp4m_b4s36 (14 records; 225 bits)
07.txt: 00k_c1ph3r_20 (13 records; 210 bits)
11.txt: kBxAc{tr4c1ng_ (14 records; 225 bits)
14.txt: 4_wh1t3sp4c3_b (14 records; 225 bits)
19.txt: 26_x9a8b7c6} (12 records; 192 bits)
FLAG: kBxAc{tr4c1ng_4_wh1t3sp4c3_b26_x9a8b7c6}
```

## Kết luận

Bài kết hợp **SpamMimic → Base64 → lựa chọn fragment → SNOW trailing whitespace → tọa độ 16-bit → book cipher**. Sai lầm dễ gặp là chỉ dùng text hiển thị, xóa whitespace, cố đọc SNOW như ASCII, hoặc sắp xếp fragment theo ngày. Flag được tái tạo từ dữ liệu gốc và được kiểm chứng bằng script độc lập:

**`kBxAc{tr4c1ng_4_wh1t3sp4c3_b26_x9a8b7c6}`**
