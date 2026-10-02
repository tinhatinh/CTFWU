# Lamp Drill - Warm-up (49 điểm)

**Cờ:** `CSSCTF{css}`
**Tài nguyên:** `lampDrill.svg` (Kích thước: 54.671 B, SHA256: `4a11f4a884aab46c...`) và phiên bản đồ họa lưới `lampDrill.png` (2624x1472).

## Đề bài

Hệ thống cung cấp một tệp tin hình ảnh tĩnh, không đi kèm các dịch vụ trực tuyến. Mô tả đề bài chỉ ra: "Warm-up. No spaces." và quy định định dạng cờ là `CSSCTF{}`. Yêu cầu của bài toán là phân tích và giải mã chuỗi ký tự ẩn giấu bên trong bức ảnh đồ họa này.

## Phân tích ban đầu

Đánh giá tệp tin SVG: Dựa trên siêu dữ liệu (metadata), tệp được tạo bằng thư viện Matplotlib 3.9.2 (`dc:date` 2026-09-30T07:31:34, thiết lập `viewBox 0 0 1180.8 662.4`). Cấu trúc vector SVG chứa các đối tượng có thuộc tính trực quan nguyên dạng, do đó việc áp dụng kỹ thuật nhận dạng ký tự quang học (OCR) lên ảnh Raster là không cần thiết. Quá trình phân tích thực hiện trực tiếp trên dữ liệu vector: mỗi bóng đèn được đại diện bởi một thẻ `<path>` vẽ đường cong Bezier tích hợp thuộc tính màu sắc `style="fill: ..."`. Phân loại đối tượng dựa vào thông số kích thước (đường kính) mang lại kết quả đồng nhất tuyệt đối:

| Đường kính | Số lượng | Định danh đối tượng |
| --- | --- | --- |
| 23.0 | 60 | Bóng đèn |
| 101.7 | 24 | Khung nền bo góc (ô lưới) |
| ≈7.9 | 25 | Mũi tên định hướng (▶) |

Tổng số 60 bóng đèn được phân luồng cấu trúc thành hai khu vực: Khu vực định nghĩa logic (hàng trên cùng, gồm 12 bóng đèn) và Khu vực ma trận dữ liệu (lưới 3 hàng × 8 ô × 2 đèn/ô, tổng 48 bóng).
Dữ liệu trạng thái bóng đèn được biểu thị qua hai mã màu: `#1c1915` (sáng) và `#f7f4ee` (tắt - trùng khớp với màu nền tổng thể của đồ thị). Không tồn tại chuỗi văn bản ẩn, không có lớp (layer) ngụy trang, và không có các siêu dữ liệu đáng ngờ bổ sung.

Khu vực định nghĩa logic phác thảo bảng chân lý (truth table) của phép toán áp dụng trên hai trạng thái đầu vào:

```text
## -> #      #. -> .      .# -> .      .. -> .
```

Khu vực ma trận bên dưới bao gồm 3 dãy, mỗi dãy gồm 8 ô được liên kết chuỗi thông qua mũi tên chỉ hướng. Mỗi ô chứa chính xác hai bóng đèn (2 bit đầu vào).

## Chuỗi khai thác

**Bước 1 - Trích xuất dữ liệu mảng bóng đèn từ cấu trúc SVG.** 
Triển khai thuật toán duyệt qua toàn bộ các thẻ `<path>` chứa thuộc tính `fill:`. Hệ thống tính toán hộp giới hạn (bounding box) dựa trên các hệ tọa độ được định nghĩa trong thuộc tính `d`. Dữ liệu sẽ được giữ lại đối với các đối tượng có kích thước đường kính dao động trong biên độ 22–24 (tương ứng với cấu trúc bóng đèn). Đối chiếu giá trị `fill` với mã màu `#1c1915` để định lượng thành bit nhị phân (sáng = 1, tắt = 0).

**Bước 2 - Phân tích bảng chân lý bằng thuật toán tự động hóa (Không sử dụng Hard-code).** 
Gom cụm các phần tử dựa trên hệ tọa độ trục hoành: Đối với hàng định nghĩa logic, hệ thống nhóm các ô thành bộ đôi (2 đèn đóng vai trò đầu vào) và bộ đơn (1 đèn đóng vai trò đầu ra), sắp xếp xen kẽ.

```python
cells = clusters(rows[0], gap=50.0)          # Kết quả phân rã mảng -> [2, 1, 2, 1, 2, 1, 2, 1]
for i in range(0, len(cells), 2):
    a, b = (int(x[2]) for x in cells[i])
    table[(a, b)] = int(cells[i + 1][0][2])
```

Kết xuất ma trận logic: `00->0 01->0 10->0 11->1`. Đây là đặc tả chính xác của cổng logic AND. Việc tự động hóa quy trình giúp kịch bản này hoạt động bền vững ngay cả khi ban tổ chức thay đổi tham số thành cổng XOR hoặc OR trong các phiên bản bài toán khác.

**Bước 3 - Tổng hợp Byte từ hệ thống Bit.**
Áp dụng phép toán AND cho các cặp bit trong từng ô, tổng hợp 8 ô thành một byte dữ liệu nguyên mẫu.

```text
Dãy 1: bits=01100011 -> Hex: 0x63, ASCII: 'c'
Dãy 2: bits=01110011 -> Hex: 0x73, ASCII: 's'
Dãy 3: bits=01110011 -> Hex: 0x73, ASCII: 's'
```

**Bước 4 - Xác thực tính toàn vẹn (Kiểm chứng).** 
Khảo sát chéo số lượng: Tổng số 60 bóng đèn hoàn toàn khớp với phân rã cấu trúc (12 bóng logic + 48 bóng dữ liệu); mỗi ô trong ma trận đều thỏa mãn điều kiện sở hữu chính xác 2 bóng đèn; bảng chân lý xây dựng đủ 4 trường hợp mệnh đề; toàn bộ 3 byte giải mã đều hợp lệ trong bảng mã ASCII (ký tự in được). Phân tích chi tiết: Dãy 2 và dãy 3 chỉ khác biệt ở trạng thái tín hiệu ô đầu tiên (`.#` so với `..`), nhưng khi qua phép chiếu AND đều cho ra kết quả bit 0, dẫn tới việc giải mã cùng ra ký tự `s`. Khẳng định đây là đặc thù thiết kế cố ý của một bài khởi động (warm-up), không phải do sai lệch cảm biến đọc.

## Cờ

Quá trình thực thi mã kịch bản tự động hóa:

```bash
python exploit.py files/lampDrill.svg
```

```text
[*] Phát hiện 60 đèn, chia 4 hàng
[*] Phân tích hàng quy tắc: 00->0 01->0 10->0 11->1
[*] Khôi phục bảng chân lý: {(1, 1): 1, (1, 0): 0, (0, 1): 0, (0, 0): 0}
[*] Định dạng phép toán: AND
    Dãy 1 bits=01100011 -> 0x63 'c'
    Dãy 2 bits=01110011 -> 0x73 's'
    Dãy 3 bits=01110011 -> 0x73 's'
[*] Kết quả giải mã: 'css'
[!] CSSCTF{css}
```

Kết quả:
```text
CSSCTF{css}
```

*Lưu ý: Do tính chất không cung cấp dịch vụ mạng để xác thực, cấu trúc cờ này được xếp vào diện "Giải mã thành công dựa trên phân tích Artifact", chờ sự đối chiếu từ hệ thống điểm.*
