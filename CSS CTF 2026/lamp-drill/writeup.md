# Lamp Drill - Warm-up (49 điểm)

**Cờ:** `CSSCTF{css}` · **File cho trước:** `lampDrill.svg` (54671 B, sha256
`4a11f4a884aab46c…`) kèm bản raster `lampDrill.png` (2624x1472)

## Đề bài

Một tấm ảnh duy nhất, không có dịch vụ để nộp. Đề ghi "Warm-up. No spaces.",
cờ dạng `CSSCTF{}`. Việc cần làm là đọc ra xâu ký tự từ ảnh.

## Phân tích ban đầu

SVG do Matplotlib 3.9.2 sinh (`dc:date` 2026-09-30T07:31:34, `viewBox 0 0 1180.8 662.4`),
nên thay vì OCR ảnh raster thì đọc thẳng vector: mỗi đèn là một `<path>` dạng
bezier với `style="fill: …"`. Phân loại theo đường kính tách rất sạch:

| Đường kính | Số lượng | Là gì |
| --- | --- | --- |
| 23.0 | 60 | đèn |
| 101.7 | 24 | ô bo góc của lưới |
| ≈7.9 | 25 | mũi tên ▶ |

60 đèn chia thành 12 (hàng quy tắc trên đầu) + 48 (lưới 3 hàng × 8 ô × 2 đèn).
Hai màu xuất hiện ở đèn là `#1c1915` và `#f7f4ee`, trong đó `#f7f4ee` đúng bằng
màu nền của figure, tức là "tắt". Không có text, không có layer ẩn, không có metadata
nào khác.

Hàng quy tắc nêu phép toán trên hai đèn:

```
## -> #      #. -> .      .# -> .      .. -> .
```

Lưới bên dưới là 3 hàng, mỗi hàng 8 ô nối nhau bằng mũi tên, mỗi ô chứa đúng hai đèn.

## Các giả thuyết đã loại trừ

1. **Đọc ảnh raster bằng mắt.** Đủ để định hướng nhưng không đủ để chốt bit, vì phải
   phân biệt 60 vị trí sáng/tối và cả thứ tự bit. Loại; chuyển sang parse SVG.
2. **Gom cụm hàng quy tắc bằng khoảng cách thuần.** Các đèn trong một ô cách nhau ~30
   đơn vị, nhưng ô kế tiếp cũng cách ~81 nên `129→210` và `420→501` không phân biệt
   được; hàm gom cụm trả về `[2,1,2,1,…]` thay vì 4 bộ ba. Loại; phải đọc theo cấu
   trúc tế bào (ô 2 đèn = cặp vào, ô 1 đèn = kết quả) rồi đi xen kẽ.
3. **Bit lấy từ cặp đèn (2 bit/ô) thay vì áp quy tắc.** Cho 16 bit/hàng, không ra chữ
   có nghĩa, và làm hàng quy tắc thừa. Loại.
4. **Đèn tối = 1, hoặc bit cuối là LSB.** Quét cả 4 tổ hợp:

   ```
   dark=1 MSB -> 'css'
   dark=1 LSB -> '???'   (0x99 0xCE 0xCE, không in được)
   dark=0 MSB -> '???'
   dark=0 LSB -> '911'
   ```

   Chỉ `dark=1, MSB` cho xâu in được, và xâu đó là `css`, trùng tên chính giải đấu.
   `911` là nhiễu, không phải ứng viên cạnh tranh.

## Chuỗi khai thác

**Bước 1 - Lấy danh sách đèn từ SVG.** Duyệt mọi `<path>` có `fill:`, tính bbox từ
các toạ độ trong `d`, giữ lại những cái có đường kính trong khoảng 22–24. So màu
fill với `#1c1915` để được bit sáng/tắt.

**Bước 2 - Đọc bảng chân lý từ ảnh, không hard-code.** Gom theo hoành độ: ô 2 đèn
là cặp đầu vào, ô 1 đèn là kết quả, đi xen kẽ trong hàng đầu tiên.

```python
cells = clusters(rows[0], gap=50.0)          # -> [2,1,2,1,2,1,2,1]
for i in range(0, len(cells), 2):
    a, b = (int(x[2]) for x in cells[i])
    table[(a, b)] = int(cells[i + 1][0][2])
```

Kết quả in ra: `00->0 01->0 10->0 11->1`, tức AND. Cách này còn sống nếu ban tổ chức
ra bản XOR/OR.

**Bước 3 - Mỗi ô một bit, 8 ô một byte.**

```
hang1 bits=01100011 -> 0x63 'c'
hang2 bits=01110011 -> 0x73 's'
hang3 bits=01110011 -> 0x73 's'
```

**Bước 4 - Kiểm chứng tính đúng.** Đếm được đúng 60 đèn và khớp 12 + 48; mọi ô trong
lưới có đúng 2 đèn; bảng chân lý đủ 4 dòng; cả 3 byte đều in được. Hai hàng cuối chỉ
khác nhau ở ô đầu tiên (`.#` so với `..`), qua AND cùng cho bit 0 nên cùng ra `s` —
đúng kiểu bài warm-up, không phải lỗi đọc.

## Cờ

```bash
python exploit.py files/lampDrill.svg
```

```
[*] 60 den, 4 hang
[*] hang luat: 00->0 01->0 10->0 11->1
[*] bang tru ly doc duoc: {(1, 1): 1, (1, 0): 0, (0, 1): 0, (0, 0): 0}
[*] phep toan: AND
    hang1 bits=01100011 -> 0x63 'c'
    hang2 bits=01110011 -> 0x73 's'
    hang3 bits=01110011 -> 0x73 's'
[*] giai ma: 'css'
[!] CSSCTF{css}
```

`CSSCTF{css}`

Bài này không có dịch vụ nộp, nên cờ mới ở mức "giải mã đúng từ artifact", chưa được
hệ thống xác nhận.
