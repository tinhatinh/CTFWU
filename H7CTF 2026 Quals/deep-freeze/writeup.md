# Deep Freeze — Forensics (Hard)

**Flag:** `H7CTF{bf3a8e98115450c654b4}`
**Files cung cấp:** `memory.lime.zst` (dung lượng khổng lồ 1.438.796.330 B, sha256 `dcd7cb45...b8810`), và tệp tin bị tống tiền `Q3_patient_records.pdf.locked` (dung lượng bé nhỏ 672 B, sha256 `5b8701fa...274d6b`).

## Đề bài

Vào lúc 03:14 rạng sáng, hệ thống máy chủ của bệnh viện bất ngờ bị một chủng mã độc tống tiền (ransomware) cắn phá. Khi đội phản ứng sự cố khẩn cấp (Incident Response) lao tới hiện trường, con quái vật này vẫn đang điên cuồng mã hoá các tệp tin. Các chuyên gia ngay lập tức ra quyết định táo bạo: thực hiện thao tác đóng băng (dump) toàn bộ bộ nhớ hệ thống trước, sau đó mới sập nguồn cắt điện. Hệ quả là, bóng ma của tiến trình độc hại kia vẫn còn nằm tê liệt trọn vẹn trong luồng RAM tĩnh. 
Gợi ý sắc bén "bắt kẻ trộm đang với tay thì nó vẫn còn nắm cái nó vừa với" mang một thông điệp cốt tử: Chìa khoá giải mã vẫn chưa hề bị tiêu huỷ, nó vẫn đang bơi lội đâu đó trong lõi không gian bộ nhớ của chính tiến trình ransomware kia. 
Mục tiêu là phải cứu sống tệp hồ sơ bệnh án cực kỳ nhạy cảm: `Q3_patient_records.pdf.locked`.

## Phân tích ban đầu

Đề bài cung cấp hai tệp, mang hai số phận khác biệt:

- `Q3_patient_records.pdf.locked`: Nặng vỏn vẹn 672 byte. Khi tra bằng lệnh `file`, hệ thống mù màu không thể định dạng được. Chỉ số độ hỗn loạn (entropy) chạm mốc 7.681/8, không rơi vãi bất kỳ một chuỗi ký tự nào có nghĩa lý. Đây đích thị là khối văn bản mã hoá thuần chủng (ciphertext), hoàn toàn không được bọc lót bởi bất kỳ một bao bì (header) nào.
- `memory.lime.zst`: Đây là bãi chiến trường thực sự. Khốn nỗi, máy không có sẵn CLI `zstd`, phần mềm `7z` hệ thống lại khuyết thiếu lõi codec zstd, và ngôn ngữ Python cài sẵn cũng không có thư viện `zstandard`. Rất may, trong ngách thư mục `Git\mingw64\bin\libzstd.dll` (bản 1.5.7), ta mò được thư viện liên kết động. Dùng kỹ thuật gọi hàm thư viện cấp thấp bằng module `ctypes` của Python, ta bẻ gãy lớp vỏ nén mà chẳng cần phải cài đặt rườm rà bất cứ thứ gì (công cụ `analysis/zstd_ctypes.py`).

Cấu trúc header của zstd thành thật khai báo tổng kích thước nội dung sau giải nén là: `Frame_Content_Size = 17.175.761.051` byte. Quá trình bung nén trả ra đúng vạch con số đó, kèm theo cờ `frame 1 complete` và không ghi nhận lỗi. Điều này đập tan mọi nghi ngờ, khẳng định tệp tải về là một bản dump vô khuyết dù đề bài trước đó hù doạ chỉ có "661.3 MB".

Đào xới 32 byte khởi thuỷ của bản dump RAM, ta bắt gặp chuỗi: `45 4d 69 4c 01 00 00 00 ...` → Đích thị là chữ ký (magic number) của định dạng `LiME` (`0x4C694D45`), phiên bản 1. Kiến trúc LiME ghép nối thô bạo (raw) các phân mảnh vùng nhớ (region) lại với nhau thành chuỗi. Mỗi phân mảnh được đội trên đầu một chiếc nón header 32 byte bao gồm `{magic, version, mốc_bắt_đầu, mốc_kết_thúc, loại_phân_mảnh}` trước khi tuôn phần dữ liệu. Bởi thế, hệ toạ độ (offset) trong file không thể dịch chuyển tuyến tính (1-1) sang hệ toạ độ của địa chỉ ảo. 
Kịch bản Python `analysis/lime.py` được tung ra nhằm phác hoạ bản đồ các vùng nhớ, và thiết lập cầu nối chuyển đổi hai chiều ngoạn mục: File Offset <-> Virtual Address (Địa chỉ Ảo).

Bản đồ địa hình bộ nhớ (Memory Regions):
```text
[0] 0x0000000000001000 - 0x0000000000054ffe   (Cỡ 0.33 MiB)
[1] 0x0000000000100000 - 0x00000000bd2f7ffe   (Cỡ 3025.97 MiB)   <- Khu vực RAM thấp
[2] 0x00000000bd305000 - 0x00000000bf8ecffe   (Cỡ 37.91 MiB)
[3] 0x00000000bfbff000 - 0x00000000bffdfffe   (Cỡ 3.88 MiB)
[4] 0x0000000100000000 - 0x000000043ffffffe   (Cỡ 13312.00 MiB)  <- Khu vực RAM vượt đỉnh 4G
```

Điểm ngầu nhất: Với khối công cụ tự chế, ta chẳng thèm nhờ vả đến cái bóng khổng lồ `volatility3`. Toàn bộ hành trình sẽ được chinh phục bằng chiếc cày (parser) tự vót.

## Chuỗi khai thác

**Bước 1 - Lột trần cấu trúc tệp `.locked`.** 
File nặng 672 byte. Thuật toán mã hoá kinh điển CBC kết hợp padding PKCS#7 buộc các khối dữ liệu phải luôn là bội số của 16. Phân tách rạch ròi: `Vector khởi tạo (IV) = file[:16] = 866f319940024339a78be5b443ed8289`, còn lại là `Văn bản mã hoá (C) = file[16:]` (chiếm 656 byte). Lập luận này được bảo chứng sắt thép bởi đúng dòng lệnh `f.write(iv + ct)` vô tình mò thấy trong mã nguồn vương vãi trên RAM.

**Bước 2 - Lùng sục Bản rõ đã biết (Known-Plaintext).** 
Vì nguồn gốc là một tệp PDF, theo quy chuẩn muôn đời, 16 byte đầu tiên bắt buộc phải là khuôn mẫu `%PDF-1.4\n1 0 obj`. 
Để không phó mặc cho số phận, ta quyết định dùng kỹ thuật rạch xác (carve) bới tìm thẳng xác chiếc PDF đang ngủ quên trong vùng đệm trang nhớ (page cache) của RAM (thuộc địa chỉ `0x10b021a90`). Trọn vẹn cấu trúc sọ não của file PDF hiện nguyên hình, nó chỉ bị cụt phần đuôi vì đặc thù của RAM là cấp phát các trang nhớ một cách chắp vá, không liền mạch. 
Từ tổng kích thước của phần mã hoá, ta dễ dàng lùi ngược về chiều dài của phần tiền văn chưa mã hoá: `656 byte (tổng) - khối_đệm pad(9) = 647 byte`.

**Bước 3 - Xây đền tiên tri một khối (One-block Oracle).** 
Đặc trưng chí mạng của chế độ CBC: `Khối rõ (P1) = Khối giải mã ECB của (C1) XOR với IV`. Phương trình này ném ra một cỗ máy thần thánh: với bất kỳ một chuỗi 32 byte nghi ngờ `K` nào nằm trong bộ nhớ RAM, ta chỉ cần một lần tính toán giải mã ECB duy nhất:

```text
D_K(C1) == P1 XOR IV      <=>      Nếu bằng nhau, K chính xác là khoá bí mật
```

Ta đã nắm sẵn trong tay đáp án của phương trình: `P1 XOR IV = a33f75df6d336d0dadbac5846382e0e3`, và dữ kiện đầu vào `C1 = 184d651fa87011ae7437a09a92e186fa`.

**Bước 4 - Bủa lưới khoá bằng tập tính bầy đàn của Memory Allocation.** 
Mã độc gọi hai hàm `os.urandom(32)` và `os.urandom(16)` liên tiếp nhau, đồng nghĩa với việc hai mảng đối tượng `bytes` (khoá K và biến IV) sinh ra sẽ bị tống vào kề vai sát cánh ngay trên cấu trúc vùng nhớ heap. Vì biến IV 16 byte đã lộ mặt từ bước 1, chiến thuật lúc này vô cùng tàn nhẫn: định vị chính xác vị trí của IV trong RAM, cắm một cây sào làm tâm, rồi quét quét bạo lực (brute-force) xung quanh nó. 
Chuỗi IV ló mặt 9 lần trong tổng số 16GB RAM; ta giới hạn bán kính càn quét chỉ 8 KB vây quanh mỗi điểm mù. Và cánh cửa mở ra tại cửa sổ:

```text
Địa chỉ ảo vaddr: 0x120a63490 (tương đương file offset 0xe067852c), nằm thụt lùi -2064 byte so với đối tượng IV
Chìa khoá (key) lộ sáng = 21c0780db69f7eabeb3b8dafb1810b9611916c6becdaf0b2b318d40894295d6c
```

Thắng lợi này thu về chỉ sau vỏn vẹn 6.129 lần quét nghiệm (~3 giây). Sức công phá khủng khiếp này chính là đặc sản của công cụ `aeskeyfind`, nhưng đẳng cấp nằm ở chỗ ta chẳng thèm cài đặt nó: ta có bản rõ làm bằng chứng đối chiếu, điều kiện này còn chặt chẽ và tàn nhẫn hơn cả trò nghiệm đúng cơ chế vòng đời khoá mở rộng (key schedule).

**Bước 5 - Giải mã và kiểm toán chặt (Rigorous Check).** 
Kích nổ buồng máy AES-256-CBC bằng song kiếm (key, IV) vào 656 byte mã hoá, kết quả nôn ra 656 byte. Nhìn vào byte cuối cùng báo hiệu giá trị `0x09` và toàn bộ đoạn đuôi `pt[-9:]` chạy sọc dưa `9*0x09`, chứng tỏ cơ chế lấp đầy (padding) PKCS#7 hoàn hảo không một vết xước. 
Lột bỏ lớp đệm 9 byte, 647 byte đọng lại bừng sáng thành một file PDF hoàn chỉnh, phô diễn đầy đủ xương sống `xref`, `trailer`, `startxref 465`, và thắt nút chặt chẽ bằng `%%EOF`. Đây là bản án tử hình cho mọi tranh cãi: Một mã khoá sai lầm gần như tuyệt đối sẽ cào rách toạc cấu trúc padding và không bao giờ có thể tự nặn ra một cấu trúc PDF sinh học khép kín như vậy.

Trích xuất chuỗi nội bộ từ nội tạng của file PDF:

```text
BT /F1 12 Tf 72 720 Td (CONFIDENTIAL patient record. Recovery token: H7CTF{bf3a8e98115450c654b4}) Tj ET
```

**Bước 6 - Giám định chéo bằng nhân chứng độc lập.** 
Truy quét chuỗi `H7CTF{bf3a8e98115450c654b4}` rực sáng ở tận hai tụ điểm khác trong bộ nhớ RAM (một ở luồng stream PDF kẹt lại trong page cache, một ở biến môi trường `FLAG='...'` do kịch bản (script) sinh đề của tác giả vô ý bỏ quên). Ba miệng lưỡi độc lập khai cùng một chữ. Cuộc chơi kết thúc.

## Flag
```bash
python exploit.py _scratch/memory.raw files/Q3_patient_records.pdf.locked
```

Nhật ký hệ thống:
```text
[*] 672 B ciphertext = IV(16) + 656 B
[*] LiME: 5 section(s), 16.00 GiB mapped
[+] key 21c0780db69f7eabeb3b8dafb1810b9611916c6becdaf0b2b318d40894295d6c at vaddr 0x120a63490 (Cách đối tượng IV -2064 B, cày nát 6129 cửa sổ nhớ)
[+] plaintext 647 B, PKCS#7 valid, header b'%PDF-1.4'
[+] flag: H7CTF{bf3a8e98115450c654b4}
```

Tệp PDF hồi sinh được ướp tại `recovered.pdf`, chiến lợi phẩm lưu trong `flag.txt`.
