# Deep Freeze - Forensics (Hard)

**Flag:** `H7CTF{bf3a8e98115450c654b4}`
**Files cung cấp:** `memory.lime.zst` (kích thước 1.438.796.330 B, sha256 `dcd7cb45...b8810`), và file bị mã hóa `Q3_patient_records.pdf.locked` (kích thước 672 B, sha256 `5b8701fa...274d6b`).

## Đề bài

Vào lúc 03:14 rạng sáng, hệ thống máy chủ của bệnh viện bị tấn công bởi một chủng mã độc tống tiền (ransomware). Đội phản ứng sự cố khẩn cấp (Incident Response) đã ghi lại hiện trạng bằng cách đóng băng toàn bộ bộ nhớ hệ thống (dump memory) khi tiến trình mã hóa đang chạy, sau đó mới ngắt nguồn điện. Do đó, tiến trình độc hại và dữ liệu của nó vẫn được lưu trữ trong bản sao RAM.
Gợi ý đề bài chỉ ra rằng: khóa giải mã (decryption key) có thể chưa bị hủy bỏ và vẫn tồn tại trong bộ nhớ RAM của tiến trình ransomware.
Mục tiêu là khôi phục file hồ sơ bệnh án: `Q3_patient_records.pdf.locked`.

## Phân tích ban đầu

Đề bài cung cấp hai file:

- `Q3_patient_records.pdf.locked`: File có kích thước 672 byte. Lệnh `file` không nhận dạng được định dạng, và entropy của dữ liệu ở mức 7.681/8. Điều này xác nhận file chứa dữ liệu mã hóa (ciphertext) không đính kèm thông tin cấu trúc (header).
- `memory.lime.zst`: Bản sao bộ nhớ ở định dạng nén zstd. Để giải nén, thư viện `libzstd.dll` (thuộc Git/mingw64) và module `ctypes` của Python được sử dụng (kịch bản tại `analysis/zstd_ctypes.py`), giúp giải mã nội dung mà không yêu cầu cài đặt bổ sung thư viện `zstandard` hay công cụ CLI.

Cấu trúc header của zstd xác định kích thước nội dung sau giải nén là: `Frame_Content_Size = 17.175.761.051` byte. Quá trình giải nén hoàn tất mà không phát sinh lỗi, chứng thực độ nguyên vẹn của dữ liệu mặc dù mô tả ban đầu chỉ định kích thước "661.3 MB".

Phân tích 32 byte đầu tiên của bản sao RAM cho thấy chuỗi: `45 4d 69 4c 01 00 00 00 ...`, tương ứng với chữ ký (magic number) của định dạng `LiME` (`0x4C694D45`), phiên bản 1. Định dạng LiME lưu trữ các phân vùng bộ nhớ (region) một cách trực tiếp (raw), mỗi phân vùng có header dài 32 byte (chứa thông tin `{magic, version, mốc_bắt_đầu, mốc_kết_thúc, loại_phân_mảnh}`). Cấu trúc này làm cho vị trí vật lý trong file (file offset) không ánh xạ tuyến tính 1-1 với địa chỉ ảo (virtual address).
Python script `analysis/lime.py` được sử dụng để phân tích và lập bản đồ các vùng nhớ, hỗ trợ chuyển đổi giữa hệ trục toạ độ File Offset và Virtual Address.

Bản đồ địa hình bộ nhớ (Memory Regions):
```text
[0] 0x0000000000001000 - 0x0000000000054ffe   (Cỡ 0.33 MiB)
[1] 0x0000000000100000 - 0x00000000bd2f7ffe   (Cỡ 3025.97 MiB)   <- Khu vực RAM cơ bản
[2] 0x00000000bd305000 - 0x00000000bf8ecffe   (Cỡ 37.91 MiB)
[3] 0x00000000bfbff000 - 0x00000000bffdfffe   (Cỡ 3.88 MiB)
[4] 0x0000000100000000 - 0x000000043ffffffe   (Cỡ 13312.00 MiB)  <- Khu vực RAM vượt đỉnh 4G
```

Việc phân tích bản sao RAM được thực hiện bằng bộ công cụ tùy chỉnh (parser) thay vì công cụ như `volatility3`.

## Quá trình khai thác

**Bước 1 - Phân tích cấu trúc file `.locked`.**
File có dung lượng 672 byte. Dựa trên đặc trưng của thuật toán mã hóa CBC kết hợp cơ chế lấp đầy PKCS#7 (yêu cầu dữ liệu theo bội số của 16), phân tách cấu trúc file: `Vector khởi tạo (IV) = file[:16] = 866f319940024339a78be5b443ed8289`, và `Văn bản mã hoá (C) = file[16:]` (có kích thước 656 byte). Lập luận này tương ứng với lệnh ghi file `f.write(iv + ct)` tìm thấy trong bộ nhớ RAM.

**Bước 2 - Khôi phục Bản rõ gốc (Known-Plaintext).** 
Theo tiêu chuẩn định dạng PDF, 16 byte đầu tiên bắt buộc phải là `%PDF-1.4\n1 0 obj`. 
Bằng kỹ thuật carving, nội dung chưa mã hóa của file PDF được xác định trong vùng đệm trang nhớ (page cache) của RAM tại địa chỉ `0x10b021a90`. File chưa hoàn chỉnh do đặc tính phân bổ bộ nhớ không liên tục của RAM.
Kích thước phần văn bản gốc (Plaintext) ước tính là: `656 byte (mã hóa) - khối_đệm pad(9) = 647 byte`.

**Bước 3 - Xây dựng cơ chế xác thực khối (One-block Oracle).** 
Tính chất chế độ hoạt động CBC: `Khối rõ (P1) = Khối giải mã ECB của (C1) XOR với IV`. Cơ chế này cho phép thiết lập hệ thống kiểm tra nhanh: với bất kỳ chuỗi 32 byte nghi ngờ `K` tìm thấy trong RAM, chỉ cần tính toán giải mã ECB một lần:

```text
D_K(C1) == P1 XOR IV      <=>      Nếu điều kiện thỏa mãn, K là khóa hợp lệ
```

Tham số so sánh: `P1 XOR IV = a33f75df6d336d0dadbac5846382e0e3` (với `C1 = 184d651fa87011ae7437a09a92e186fa`).

**Bước 4 - Dò tìm khóa theo cơ chế phân bổ bộ nhớ.** 
Mã độc gọi các hàm `os.urandom(32)` và `os.urandom(16)` liên tiếp, làm cho khóa K và biến IV được cấp phát cạnh nhau trên heap. Chuỗi IV đã biết được sử dụng để định vị trên RAM (tìm thấy tại 9 vị trí). Tại mỗi mốc, tìm kiếm khóa bí mật trong bán kính 8 KB (brute-force).
Kết quả trả về:

```text
Địa chỉ ảo vaddr: 0x120a63490 (file offset 0xe067852c), cách đối tượng IV khoảng -2064 byte
Khóa (key) tìm được = 21c0780db69f7eabeb3b8dafb1810b9611916c6becdaf0b2b318d40894295d6c
```

Khóa được xác định sau khoảng 6.129 lần lặp (~3 giây). Phép thử này sử dụng bản rõ làm mốc so sánh trực tiếp, mang lại độ chính xác cao.

**Bước 5 - Thực thi giải mã và kiểm tra.** 
Áp dụng AES-256-CBC cùng (key, IV) để giải mã khối 656 byte. Giá trị byte cuối cùng là `0x09` và đoạn đệm `pt[-9:]` tuân thủ đúng định dạng đệm PKCS#7 (`9*0x09`), xác thực mã khóa là chính xác. 
Sau khi loại bỏ 9 byte đệm, 647 byte dữ liệu hiển thị cấu trúc PDF nguyên vẹn (`xref`, `trailer`, `startxref 465`, và `%%EOF`). Cấu trúc hợp lệ này là bằng chứng rõ ràng cho kết quả giải mã đúng.

Trích xuất nội dung từ file PDF:

```text
BT /F1 12 Tf 72 720 Td (CONFIDENTIAL patient record. Recovery token: H7CTF{bf3a8e98115450c654b4}) Tj ET
```

**Bước 6 - Xác minh phụ trợ.** 
Nội dung `H7CTF{bf3a8e98115450c654b4}` cũng được phát hiện tại hai vị trí khác trong bộ nhớ RAM: trong dòng dữ liệu PDF thuộc page cache và trong biến môi trường `FLAG='...'` (cấu hình kỹ thuật của hệ thống sinh đề). Các nguồn độc lập này xác nhận kết quả là chính xác.

## Flag
```bash
python exploit.py _scratch/memory.raw files/Q3_patient_records.pdf.locked
```

Nhật ký thực thi:
```text
[*] 672 B ciphertext = IV(16) + 656 B
[*] LiME: 5 section(s), 16.00 GiB mapped
[+] key 21c0780db69f7eabeb3b8dafb1810b9611916c6becdaf0b2b318d40894295d6c at vaddr 0x120a63490 (Cách đối tượng IV -2064 B, cày nát 6129 cửa sổ nhớ)
[+] plaintext 647 B, PKCS#7 valid, header b'%PDF-1.4'
[+] flag: H7CTF{bf3a8e98115450c654b4}
```

File PDF đã được giải mã lưu tại `recovered.pdf`, nội dung cờ được ghi vào `flag.txt`.
