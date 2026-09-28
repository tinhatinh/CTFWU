# Deep Freeze — Forensics (Hard)

**Flag:** `H7CTF{bf3a8e98115450c654b4}` · Files: `memory.lime.zst` (1.438.796.330 B, sha256 `dcd7cb45...b8810`), `Q3_patient_records.pdf.locked` (672 B, sha256 `5b8701fa...274d6b`)

## Đề bài

Ransomware đánh vào bệnh viện lúc 03:14 và vẫn đang mã hoá tiếp khi đội phản ứng tới nơi. Họ đóng băng máy trước, cắt điện sau, nên trạng thái của tiến trình độc vẫn nằm nguyên trong RAM. Câu gợi ý "bắt kẻ trộm đang với tay thì nó vẫn còn nắm cái nó vừa với" nghĩa là: khoá giải mã chưa bị xoá, còn nằm trong bộ nhớ của chính tiến trình đó.

Cần lấy lại nội dung `Q3_patient_records.pdf.locked`.

## Phân tích ban đầu

Hai file, mỗi file một vai trò:

- `Q3_patient_records.pdf.locked`: 672 byte, `file` không nhận dạng được, entropy 7.681/8, không có một chuỗi ký tự nào có nghĩa. Đây là ciphertext thuần, không có header bao bì.
- `memory.lime.zst`: không có `zstd` CLI, `7z` của máy không mang codec zstd, Python không có `zstandard`. Tìm thấy `Git\mingw64\bin\libzstd.dll` (1.5.7) nên mình bind trực tiếp bằng `ctypes` - không cài gì cả (`analysis/zstd_ctypes.py`).

Header zstd tự khai kích thước nội dung: `Frame_Content_Size = 17.175.761.051` byte. Giải nén ra đúng con số đó, `frame 1 complete`, không lỗi → file tải về đã đầy đủ dù đề ghi "661.3 MB".

Ba mươi hai byte đầu của ảnh: `45 4d 69 4c 01 00 00 00 ...` → magic `LiME` (`0x4C694D45`), version 1. LiME là định dạng các region `raw` nối tiếp nhau, mỗi region có header 32 byte `{magic, version, start, end, type}` rồi tới dữ liệu, nên offset trong file không dịch ra địa chỉ ảo một cách tuyến tính. Mình viết `analysis/lime.py` để dựng bảng region và làm hai chiều quy đổi file offset <-> virtual address:

```
[0] 0x0000000000001000 - 0x0000000000054ffe   0.33 MiB
[1] 0x0000000000100000 - 0x00000000bd2f7ffe   3025.97 MiB   <- RAM thấp
[2] 0x00000000bd305000 - 0x00000000bf8ecffe   37.91 MiB
[3] 0x00000000bfbff000 - 0x00000000bffdfffe   3.88 MiB
[4] 0x0000000100000000 - 0x000000043ffffffe   13312.00 MiB  <- RAM trên 4G
```

Không cần volatility3 cho bài này, toàn bộ đi bằng parser tự viết.

## Các hướng đã loại

1. Cờ nằm sẵn kiểu `strings`: quét cả 16 GiB thì `flag{` không xuất hiện; `H7CTF{` chỉ xuất hiện bên trong nội dung PDF và trong script, tức là vẫn phải chứng minh. Loại cách "grep là xong".
2. Dữ liệu giấu trong response/đỉnh của giao thức khác: ảnh là máy chủ đứng một mình, không có mạng đáng kể, không có file `.locked` dạng lồng zip/tar.
3. Neo tìm khoá vào chuỗi marker của dict: `ransomware_footprint.py` để lại `note: b"kdmp-resident-do-not-swap"` trong RAM. Mình quét ±64 KB quanh cả 12 vị trí marker, 1.572.480 cửa sổ 32 byte, không có khoá nào. Lý do: dict Python chỉ lưu con trỏ tới object bytes, không lưu dữ liệu inline.
4. Mô hình không phải AES-CBC: đã nghi ngờ CTR/GCM (không pad), nhưng chính source trong RAM chỉ ra `pad = 16 - len(plaintext) % 16` rồi `AES.new(key, MODE_CBC, iv)`. Loại mọi hướng stream cipher.

## Chuỗi khai thác

**Bước 1 - Đọc cấu trúc file `.locked`.** 672 byte, và vì CBC + PKCS#7 nên độ dài phải bội của 16. Tách `IV = file[:16] = 866f319940024339a78be5b443ed8289`, `C = file[16:]` (656 byte). Điều này được xác nhận bởi đúng dòng `f.write(iv + ct)` trong source tìm thấy ở RAM.

**Bước 2 - Có known-plaintext thật sự.** Tiền văn là một PDF, nên 16 byte đầu luôn là `%PDF-1.4\n1 0 obj`. Để chắc chắn, mình carve PDF từ page cache trong RAM (vùng `0x10b021a90`): thấy trọn cấu trúc PDF, chỉ thiếu đuôi vì các page của một file không nằm liền mạch trong RAM. Độ dài tiền văn suy ra từ ciphertext: `656 - pad(9) = 647` byte.

**Bước 3 - Dựng oracle một block.** Với CBC: `P1 = D_K(C1) XOR IV`, tức là với mỗi cửa sổ 32 byte `K` trong RAM chỉ cần một phép giải mã ECB một block:

```
D_K(C1) == P1 XOR IV      <=>      K là khoá
```

`P1 XOR IV = a33f75df6d336d0dadbac5846382e0e3`, `C1 = 184d651fa87011ae7437a09a92e186fa`.

**Bước 4 - Thu hẹp không gian tìm bằng tính chất cấp phát bộ nhớ.** `os.urandom(32)` và `os.urandom(16)` được gọi liên tiếp, nên hai object bytes nằm sát nhau trong heap. Vì IV đã biết trước 16 byte, chỉ cần định vị IV trong dump rồi quét quanh nó. IV xuất hiện 9 lần; trong bán kính 8 KB quanh các vị trí đó, cửa sổ tại

```
vaddr 0x120a63490 (file offset 0xe067852c), -2064 byte so với object IV
key = 21c0780db69f7eabeb3b8dafb1810b9611916c6becdaf0b2b318d40894295d6c
```

thỏa oracle sau 6.129 lần thử (~3 giây). Đây đúng là kiểu kết quả mà `aeskeyfind` sinh ra, nhưng không cần cài công cụ: ta có plaintext để kiểm nên còn chắc hơn cả việc nghiệm đúng lược đồ mở rộng khoá.

**Bước 5 - Giải mã và kiểm chứng chặt.** AES-256-CBC với (key, IV) cho 656 byte; byte cuối `0x09` và `pt[-9:] == 9*0x09` → PKCS#7 hợp lệ. Bỏ pad được 647 byte là một PDF hoàn chỉnh, có `xref`, `trailer`, `startxref 465`, `%%EOF`. Đây là bằng chứng quyết định: một key sai gần như chắc chắn phá vỡ padding và không thể tạo ra cấu trúc PDF khép kín như vậy.

Trong PDF:

```
BT /F1 12 Tf 72 720 Td (CONFIDENTIAL patient record. Recovery token: H7CTF{bf3a8e98115450c654b4}) Tj ET
```

**Bước 6 - Đối chiếu độc lập.** Chuỗi `H7CTF{bf3a8e98115450c654b4}` cũng xuất hiện ở hai nơi khác trong RAM (stream PDF trong page cache và biến môi trường `FLAG='...'` của script dựng hiện trường). Ba nguồn độc lập trùng khớp.

## Flag
```bash
python exploit.py _scratch/memory.raw files/Q3_patient_records.pdf.locked
```

```
[*] 672 B ciphertext = IV(16) + 656 B
[*] LiME: 5 section(s), 16.00 GiB mapped
[+] key 21c0780db69f7eabeb3b8dafb1810b9611916c6becdaf0b2b318d40894295d6c at vaddr 0x120a63490 (-2064 B from the IV object, 6129 windows tested)
[+] plaintext 647 B, PKCS#7 valid, header b'%PDF-1.4'
[+] flag: H7CTF{bf3a8e98115450c654b4}
```

PDF giải mã lưu ở `recovered.pdf`, cờ lưu ở `flag.txt`.
