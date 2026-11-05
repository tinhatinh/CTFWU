---
title: "VULN#001"
category: "Vuln Research"
tags: ["libexif", "exif", "jpeg", "out-of-bounds-read", "integer-underflow", "source-diff"]
solve_date: "2026-10-16T23:57:00+07:00"
language: "vi"
points: 144
---

# VULN#001 — underflow độ dài APP1 của libexif dẫn tới OOB read

**Flag:** CTF{86f07cd3cbf154a2bcec7e77d8334779} · **Files:** libexif-src.tar.gz (1 137 988 B, SHA-256 c986b9b8b49b711ab56f85b0b06523ee85e8b45b7e597887f0fb70604628a5e6), base-exif.jpg (725 B, SHA-256 c261cc6bc3b4d26d9b61ee15449d96274007261fe0fa59c9d0b7449d2d24dfda) · **Target:** 169.58.126.107:7027

## Đề bài

Thẻ ghi VULN#001, 144 điểm, mô tả metadata service, hint The exact source, service 169.58.126.107 7027, format CTF{}. Artifact duy nhất là source tree libexif đóng trong libexif-src (1).tar.gz; không có binary.

Hint “exact source” nghĩa là phiên bản library trên remote khớp chính xác với tarball, nên bug nằm trong snapshot này chứ không phải release khác.

## Phân tích

### Protocol của service

Service nhận **length big-endian 4 byte + image data**, trả một dòng status: ... rồi đóng connection. Các phản hồi quan sát được:

```text
status: bad length         - length 0 or too large
status: not valid          - input not accepted
status: no effect          - valid image, ordinary parse
status: insufficient       - bug triggered but the harness target was not reached
status: confirmed          - triggered correctly, prints FLAG: ...
status: rate limited, try again later   - requests sent too fast
```

canon_makernote_variant_1.jpg (JPEG bắt đầu trực tiếp bằng APP1), EXIF blob thuần và TIFF thuần đều trả status: not valid. Chỉ JPEG có JFIF header (FF D8 FF E0 ...) đứng trước APP1 Exif mới được xử lý (status: no effect, xem protocol.txt). Như vậy EXIF path của libexif có thể truy cập; not valid là bước kiểm tra cấu trúc của harness.

### Source được cung cấp và bug

Sau khi giải nén tarball và chuẩn hóa CRLF thành LF, so với upstream libexif cho thấy **61/61 file .c/.h khớp từng byte** với commit a918830 (2021-11-01, “fixed offset for EXIF Header in App1 Header”, 0.6.23.1-dev). Snapshot này **chưa có** hai fix sau từ oss-fuzz (source-check.txt):

```text
54461dd  check for len < 2 to avoid it becoming negative.
4bd5cd6  actually check the length read from the data against the data size (oss-fuzz)
```

Cả hai patch thêm validation vào cùng đoạn trong libexif/exif-data.c (exif_data_load_data). Nếu buffer không bắt đầu bằng Exif\0\0 (tức là JPEG), function scan marker; gặp APP1 thì đọc segment length và tính kích thước EXIF data:

```c
d++;
ds--;
len = (((unsigned int)d[0]) << 8) | d[1];
...
d += 2;
ds = len - 2;   /* we do not want the full rest size, but only the size of the tag */
```

len là độ dài JPEG segment 16-bit do attacker kiểm soát, **không được validate**. ds là unsigned int:

- len = 0 → ds = len - 2 = 0xFFFFFFFE (underflow).
- len lớn hơn dữ liệu thực → ds vượt quá buffer.

Sau đó ds chỉ bị giới hạn ở 0xfffe, vẫn lớn hơn nhiều so với image 725 byte. Mọi bound check về sau (CHECKOVERFLOW trong exif_data_load_data_content) đều dựa trên ds sai này, nên phép đọc tại d + 6 + offset với offset do attacker chọn sẽ vượt ra ngoài buffer. Đây là OOB read với offset có thể điều khiển; byte ngoài vùng được diễn giải như IFD entry.

So với image hợp lệ có IFD0 offset nằm trong buffer, payload chỉ sửa hai field:

| Field | Vị trí | Giá trị | Mục đích |
|---|---|---|---|
| APP1 length | [22:24] | 0x0000 | làm ds underflow, vô hiệu hóa bounds |
| TIFF IFD0 offset | [34:38] | 0x00000800 | vị trí OOB read |

## Các hướng đã thử

1. **Gửi JPEG bắt đầu trực tiếp bằng APP1 / EXIF blob thuần / TIFF thuần:** đều trả not valid. JFIF header cần nằm trước APP1 (protocol.txt).
2. **Quét variant liên tục:** gửi khoảng 350 request làm service rate limit và nhiễu kết quả giữa chừng. Cần giãn request rồi chạy lại.
3. **Thử IFD0 offset tùy ý:** 0xf000 trả status: insufficient; 0xfff0 (len = 1) trả not valid; chỉ 0x0800 trả status: confirmed. Điều kiện thành công thuộc harness, nên offset cần tune thực nghiệm chứ không suy ra từ source.

## Lời giải

### Bước 1 — Xác định framing và điều kiện input

Bốn byte đầu là length big-endian. JPEG JFIF+EXIF do PIL tạo (base-exif.jpg) qua được shape check và trả status: no effect; dùng làm ảnh gốc để patch.

### Bước 2 — So sánh source để tìm bug

Chuẩn hóa line ending rồi so từng file với upstream tại a918830: **không có khác biệt ở 61 file**, và thiếu cả hai len check. Bug ở exif_data_load_data như đã mô tả.

### Bước 3 — Tạo OOB payload

base-exif.jpg là JPEG Motorola (MM), APP1 Exif bắt đầu tại offset 20. APP0/JFIF header đã đứng trước APP1 nên chỉ cần sửa APP1 length và IFD0 offset:

```python
img = bytearray(base)                       # JFIF + APP1 Exif JPEG, 725 B
img[22:24] = struct.pack(">H", 0x0000)      # APP1 length = 0  -> ds = len - 2 underflows
img[34:38] = struct.pack(">I", 0x0800)      # IFD0 offset     -> OOB landing point
```

Script đầy đủ là exploit.py. Payload tạo ra có SHA-256 bb362e31eeec05523da535ce06bee08164657a04d162755b097fc13a00c18ed1, khớp chính xác payload dùng trong lần thành công (payload-confirmed.jpg).

Với len = 0, ds thành 0xFFFFFFFE rồi bị cap ở 0xfffe; offset = 0x0800 qua được kiểm tra offset > ds và buộc exif_data_load_data_content đọc IFD0 tại TIFF + 0x800, khoảng 1 353 byte sau buffer 725 byte. Vùng OOB được đọc như IFD entry; harness nhận diện điều kiện mục tiêu và in flag.

### Bước 4 — Xác minh

- Payload dựng lại offline khớp SHA-256 với payload từng thành công.
- Flag do service tự in (status: confirmed + FLAG:), không phải suy luận.
- Flag dùng wrapper CTF{...} như thẻ challenge ghi.

## Kết quả

```bash
python exploit.py
```
```text
host 169.58.126.107:7027  payload 725 byte
RAW RESPONSE b'status: confirmed\nFLAG: CTF{86f07cd3cbf154a2bcec7e77d8334779}\n'
CTF{86f07cd3cbf154a2bcec7e77d8334779}
```
```text
CTF{86f07cd3cbf154a2bcec7e77d8334779}
```

Flag do service in ra (exploit-output.txt), không được dựng từ artifact.

## Tái hiện

Cần service 169.58.126.107:7027 còn chạy và Python 3 (không cần thư viện ngoài). Chỉ cần ảnh base-exif.jpg và exploit.py; script dựng payload, gửi rồi trích flag.

```bash
cd vuln001
python exploit.py
```

Service rate-limit nên script chờ khi nhận status: rate limited rồi thử lại. Payload không có phần ngẫu nhiên nên kết quả ổn định giữa các lần gửi:

```bash
python -c "import hashlib, exploit; print(hashlib.sha256(exploit.build_payload()).hexdigest())"
# bb362e31eeec05523da535ce06bee08164657a04d162755b097fc13a00c18ed1
```
