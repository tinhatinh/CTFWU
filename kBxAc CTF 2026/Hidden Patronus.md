---
title: "Hidden Patronus"
category: "Forensics"
tags: ["steganography", "png-height", "openstego", "zero-width", "stegzero"]
solve_date: "2026-10-10T18:11:00+07:00"
language: "vi"
points: 916
---

# Hidden Patronus

**Flag:** `kBxAc{z3r0_w1dth_1nv1s1bl3_1nf0_3xp3ct0_p4tr0num_8f7e6d5c4b3a2f1e0d9c}`  
**Tác giả:** HydraRoot  
**File đề:** `flag.bmp`, `harry_potter.png`

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `flag.bmp` | 1,920,054 | `de0012f017e8e15ad41229f12d4a3896541557d934ea413a6e1cf2394d3bd9f8` |
| `harry_potter.png` | 1,303,660 | `c976a144d1423312fa090d9b4142eb4d602d4a688c26272f4cc09863c251ac9d` |
| `flag.txt` (trích xuất) | 675 | `26bdc459890f34f2e691764f9e0bffb58e9f13798e3b641ab737061805289810` |

## Đề bài

> Harry Potter is everyones favourite right? isn't it?

Thử thách cung cấp hai tệp ảnh: `harry_potter.png` và `flag.bmp`. Mục tiêu là tìm khóa bí mật từ ảnh manh mối để mở lớp bảo vệ trên ảnh chứa cờ, giải mã định dạng giấu tin nhiều tầng để thu được flag định dạng `kBxAc{...}`.

## Phân tích

### Lớp 1 — Khôi phục chiều cao PNG bị cắt xén trong `harry_potter.png`

Kiểm tra metadata của `harry_potter.png`:
- Kích thước hiển thị: 1200 × 1100 pixel, định dạng 24-bit RGB (3 byte/pixel).
- Khi giải nén luồng dữ liệu `IDAT` bằng `zlib`, tổng kích thước luồng scanline thu được là **4.321.200 byte**.

Với ảnh PNG 24-bit rộng 1200 pixel, mỗi dòng quét (scanline) chiếm đúng:
$$\text{Scanline} = 1\text{ (byte filter)} + 1200 \times 3 = 3.601\text{ byte}$$

Nếu chiều cao là 1100 pixel, dung lượng giải nén dự kiến chỉ là:
$$1100 \times 3.601 = 3.961.100\text{ byte}$$

Sự chênh lệch đúng bằng 100 dòng quét:
$$\frac{4.321.200 - 3.961.100}{3.601} = \frac{360.100}{3.601} = 100\text{ dòng}$$

IHDR ghi chiều cao `0x044C` (1100), trong khi IDAT chứa dữ liệu của 1200 dòng; CRC hiện có tương ứng với header 1100 dòng. Sửa lại giá trị chiều cao về `1200` và cập nhật CRC của chunk `IHDR` sẽ để lộ 100 dòng quét ở cạnh dưới ảnh ($y = 1100$ đến $1199$). Trên dải đáy này có dòng chữ màu trắng rõ ràng:

```text
KEY:Expecto_Patronum
```

Passphrase thu được là: `Expecto_Patronum`.

### Lớp 2 — Trích xuất payload từ `flag.bmp` bằng OpenStego

Tệp `flag.bmp` có kích thước 800 × 800 pixel, 24-bit RGB (1.920.054 byte). Phân tích LSB tuần tự và `steghide` không cho kết quả vì thuật toán giấu tin ở đây không phải chuẩn LSB tuyến tính.

Sử dụng công cụ **OpenStego** với thuật toán `RandomLSB` và mật khẩu `Expecto_Patronum`:

```bash
java -jar openstego.jar extract -a RandomLSB -sf flag.bmp -xd . -p Expecto_Patronum
```

Kết quả trích xuất được tệp văn bản `flag.txt` có dung lượng **675 byte**.

### Lớp 3 — Giải mã Zero-Width Steganography (StegZero) trong `flag.txt`

Mở `flag.txt` trong trình soạn thảo thông thường chỉ thấy vỏ bọc:

```text
Bruhh Your Hardwork Failed
```

Tuy nhiên dung lượng tệp lên tới 675 byte. Phân tích byte cho thấy xen kẽ giữa các ký tự ASCII hiển thị là **216 ký tự Unicode vô hình (zero-width characters)** thuộc đúng 8 mã code point:

| Code point | Tên Unicode | Giá trị 3-bit |
|---|---|---:|
| `U+200B` | ZERO WIDTH SPACE | `000` |
| `U+200C` | ZERO WIDTH NON-JOINER | `001` |
| `U+200D` | ZERO WIDTH JOINER | `010` |
| `U+2060` | WORD JOINER | `011` |
| `U+2062` | INVISIBLE TIMES | `100` |
| `U+2063` | INVISIBLE SEPARATOR | `101` |
| `U+2064` | INVISIBLE PLUS | `110` |
| `U+FEFF` | ZERO WIDTH NO-BREAK SPACE | `111` |

Tập 8 ký tự vô hình này cùng cấu trúc khung bit thuộc về giao thức **StegZero** (công cụ steganography mã nguồn mở trên nền tảng zero-width của Clevis22):
- Mỗi ký tự zero-width mang đúng 3 bit dữ liệu ($216 \times 3 = 648$ bit $= 81$ byte).
- **Header** (11 byte / 88 bit):
  - Magic (2 byte): `0xA55A` (42330).
  - Version (1 byte): `1` (bản chuẩn, không mã hóa AES).
  - Nonce (2 byte): `18267` (`0x475B`).
  - Length (2 byte): `70` (`0x0046`).
  - CRC32 (4 byte): `0x32C22E77`.
- **Payload** (70 byte / 560 bit): Được làm mờ (obfuscate) bằng PRNG **xorshift32** với seed khởi tạo:
  $$\text{seed} = ((\text{nonce} \ll 16) \mid \text{magic}) \ \& \ \text{0xFFFFFFFF}$$

Sau khi XOR từng bit với luồng bit ngẫu nhiên từ xorshift32, kiểm tra CRC32 khớp chính xác với `0x32C22E77` và giải mã chuỗi UTF-8 thu được flag.

## Lời giải

Quy trình giải hoàn chỉnh gồm ba bước:

1. **Khôi phục ảnh PNG:** Đọc `harry_potter.png`, đặt lại chiều cao $H = 1200$, tính lại CRC `IHDR` và lưu thành ảnh mới để đọc key `Expecto_Patronum`.
2. **Trích xuất OpenStego:** Dùng OpenStego RandomLSB với mật khẩu `Expecto_Patronum` giải nén `flag.txt` từ `flag.bmp`.
3. **Giải mã StegZero:** Trích xuất các bit zero-width từ `flag.txt`, giải xáo trộn qua bộ sinh xorshift32 để lấy nội dung flag.

## Kết quả

```text
kBxAc{z3r0_w1dth_1nv1s1bl3_1nf0_3xp3ct0_p4tr0num_8f7e6d5c4b3a2f1e0d9c}
```

## Tái hiện

Chạy script Python độc lập dưới đây để kiểm tra PNG và giải mã payload đã trích xuất; bước OpenStego dùng lệnh riêng bên dưới:

```python
import hashlib
import struct
import zlib
from pathlib import Path

# 1. Khôi phục chiều cao harry_potter.png và kiểm tra scanlines thừa
png_path = Path("harry_potter.png")
if png_path.exists():
    data = bytearray(png_path.read_bytes())
    # IHDR nằm tại offset 12..29 (length=13 ở offset 8)
    width = struct.unpack_from(">I", data, 16)[0]
    height = struct.unpack_from(">I", data, 20)[0]
    print(f"[*] harry_potter.png ban đầu: {width}x{height}")

    # Đặt lại chiều cao 1200 và tính lại CRC IHDR
    struct.pack_into(">I", data, 20, 1200)
    ihdr_crc = zlib.crc32(data[12:29])
    struct.pack_into(">I", data, 29, ihdr_crc)

    fixed_path = Path("harry_potter_fixed.png")
    fixed_path.write_bytes(data)
    print(f"[+] Đã khôi phục {fixed_path} (1200x1200). Đọc key tại dải đáy: KEY:Expecto_Patronum")

# 2. Giải mã StegZero trực tiếp từ flag.txt
flag_txt_path = Path("flag.txt")
if flag_txt_path.exists():
    text = flag_txt_path.read_text(encoding="utf-8")

    ZW_ALPHABET = [
        "\u200b", "\u200c", "\u200d", "\u2060",
        "\u2062", "\u2063", "\u2064", "\ufeff",
    ]
    ZW_MAP = {ch: f"{i:03b}" for i, ch in enumerate(ZW_ALPHABET)}

    bits = "".join(ZW_MAP[ch] for ch in text if ch in ZW_MAP)
    assert len(bits) >= 88, "Dữ liệu zero-width quá ngắn"

    header_bytes = bytes(int(bits[i:i + 8], 2) for i in range(0, 88, 8))
    magic = (header_bytes[0] << 8) | header_bytes[1]
    version = header_bytes[2]
    nonce = (header_bytes[3] << 8) | header_bytes[4]
    length = (header_bytes[5] << 8) | header_bytes[6]
    expected_crc = int.from_bytes(header_bytes[7:11], "big")

    assert magic == 0xA55A, f"Sai StegZero magic: {hex(magic)}"
    print(f"[*] StegZero header: magic={hex(magic)}, ver={version}, nonce={nonce}, len={length}")

    def xorshift32(seed):
        x = seed & 0xFFFFFFFF
        while True:
            if x == 0:
                x = 0x9E3779B9
            x = (x ^ ((x << 13) & 0xFFFFFFFF)) & 0xFFFFFFFF
            x = (x ^ (x >> 17)) & 0xFFFFFFFF
            x = (x ^ ((x << 5) & 0xFFFFFFFF)) & 0xFFFFFFFF
            yield x

    seed = ((nonce << 16) | magic) & 0xFFFFFFFF
    rng = xorshift32(seed)

    payload_bits = bits[88:88 + length * 8]
    acc = 0
    remain = 0
    msg_bits = []
    for b in payload_bits:
        if remain == 0:
            acc = next(rng)
            remain = 32
        p = acc & 1
        acc >>= 1
        remain -= 1
        msg_bits.append(str((int(b) ^ p) & 1))

    msg_bytes = bytes(int("".join(msg_bits[i:i + 8]), 2) for i in range(0, len(msg_bits), 8))
    assert zlib.crc32(msg_bytes) == expected_crc, "Lỗi CRC payload"

    flag = msg_bytes.decode("utf-8")
    print(f"[+] Flag: {flag}")
```

Lệnh trích xuất trung gian với OpenStego:

```bash
java -jar openstego.jar extract -a RandomLSB -sf flag.bmp -xd . -p Expecto_Patronum
```
