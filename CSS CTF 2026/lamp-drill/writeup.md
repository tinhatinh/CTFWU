# Lamp Drill - Warm-up (49 điểm)

**Cờ:** `CSSCTF{css}`
**Tài nguyên:** `lampDrill.svg` (Kích thước: 54.671 B, SHA256: `4a11f4a884aab46c...`) và phiên bản đồ họa lưới `lampDrill.png` (2624x1472).

## Đề bài

Đề cung cấp `lampDrill.svg` và `lampDrill.png`, kèm gợi ý "Warm-up. No spaces.". Hàng trên mô tả phép toán trên hai bóng đèn; ba hàng dưới chứa dữ liệu để giải mã theo định dạng `CSSCTF{...}`.

## Phân tích ban đầu

Có thể đọc các trạng thái trực tiếp trên ảnh: đèn tô đen là 1, đèn rỗng là 0. Để reproduce bằng script, đọc các `<path>` trong SVG và lấy màu `fill`. Phân loại theo đường kính cho các nhóm sau:

| Đường kính | Số lượng | Định danh đối tượng |
| --- | --- | --- |
| 23.0 | 60 | Bóng đèn |
| 101.7 | 24 | Khung nền bo góc (ô lưới) |
| ≈7.9 | 25 | Mũi tên định hướng (▶) |

Ảnh có 60 bóng đèn: 12 ở hàng quy tắc và 48 ở lưới dữ liệu 3 hàng × 8 ô × 2 đèn. Script dùng `#1c1915` cho bit 1 và `#f7f4ee` cho bit 0.


Hàng trên chỉ cho đầu ra 1 khi cả hai đầu vào đều là 1, tương ứng phép AND:

```text
## -> #      #. -> .      .# -> .      .. -> .
```

Khu vực ma trận bên dưới bao gồm 3 dãy, mỗi dãy gồm 8 ô được liên kết chuỗi thông qua mũi tên chỉ hướng. Mỗi ô chứa chính xác hai bóng đèn (2 bit đầu vào).

## Chuỗi khai thác

**Bước 1 - Đọc trạng thái từng bóng đèn.**
Script đọc bounding box của các `<path>`, giữ những đối tượng có đường kính 22–24, rồi chuyển màu `fill` thành bit. Đây là cách tự động đọc lại cùng dữ liệu nhìn thấy trên ảnh.

**Bước 2 - Đọc bảng chân lý.**
Ở hàng quy tắc, nhóm các bóng đèn theo tọa độ x thành cặp đầu vào và một đầu ra. Đoạn code dưới đây ghi lại bảng chân lý từ các nhóm đó:

```python
cells = clusters(rows[0], gap=50.0)          # Kết quả phân rã mảng -> [2, 1, 2, 1, 2, 1, 2, 1]
for i in range(0, len(cells), 2):
    a, b = (int(x[2]) for x in cells[i])
    table[(a, b)] = int(cells[i + 1][0][2])
```

Bảng thu được là `00->0 01->0 10->0 11->1`, khớp phép AND quan sát được ở hàng trên.

**Bước 3 - Ghép các bit thành byte.**
Áp dụng AND cho hai bit trong mỗi ô, rồi đọc 8 ô từ trái sang phải để tạo một byte ASCII:

```text
Dãy 1: bits=01100011 -> Hex: 0x63, ASCII: 'c'
Dãy 2: bits=01110011 -> Hex: 0x73, ASCII: 's'
Dãy 3: bits=01110011 -> Hex: 0x73, ASCII: 's'
```

**Bước 4 - Xác thực tính toàn vẹn (Kiểm chứng).** 
Kiểm tra lại số lượng: 12 bóng ở hàng quy tắc và 48 bóng ở ba hàng dữ liệu. Mỗi ô có hai bóng. Hai hàng cuối khác trạng thái ở ô đầu (`.#` và `..`), nhưng AND đều cho 0, nên cả hai cùng giải mã thành `s`. Ba byte thu được là `css`.

## Cờ

Chạy script:

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

*Flag được suy ra từ artifact; bản ghi hiện tại chưa có xác nhận submit trên scoreboard.*
