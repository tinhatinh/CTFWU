# Excavation - nhật suy đoán

Key đã xác minh (repeating XOR 8 byte, áp lên phần thân sau byte 12):

| file | key | struct = body ^ key ^ 0x20 |
|---|---|---|
| sample1 | `bff366a0192308a7` | OK |
| sample2 | `8ee28d4183df8c1b` | OK |
| sample3 | `e62903e8dcf7b038` | OK |
| team | `1337df4e77c16cc7` | OK |

| # | Giả thuyết | Cách thử | Kết quả |
|---|---|---|---|
| H1 | 12 byte đầu là header chưa mã hoá | `struct.unpack_from('<I', raw, 8)` so với `len(raw)` | **OK**: 466/857/1144/1382 khớp tuyệt đối, 8 byte đầu giống hệt nhau ở 4 file |
| H2 | 4 file dùng chung một key | lấy key của team chấm điểm alpha trên body các file khác | **DEAD**: team-key chỉ đạt 0.10-0.17 trên sample, mỗi file có key riêng (0.72-0.73 cho chính nó) |
| H3 | Key lặp 8 byte | đếm tỉ lệ `body[i]==body[i+L]` với L=1..39 | **OK**: lag 8/16/24/32 đạt 0.044-0.058, các lag khác 0.008-0.015 |
| H4 | Recover key bằng constraint "bảng chữ cái của plaintext" | mỗi cột 8 byte chọn key tối đa hoá số byte rơi vào `[A-Z0-9_ \|. ]` | **OK một phần**: ra đúng key team, nhưng sample3 lệch 1 byte (`ca` so với `dc`) |
| H5 | Plaintext là text thuần, không có field nhị phân | thống kê byte < 0x20 và >= 0x7f theo cột | **DEAD**: team có 260/1370 byte ngoài alphabet, trải đều cả 8 cột (28-36 mỗi cột) |
| H6 | Có một cột key lệch 0x20 (vì chữ đầu từ toàn viết hoa thường) | kiểm tra xem các byte bất thường có tập trung theo `i % 8` hay không | **DEAD**: trải đều, không có cột nào dị thường |
| H7 | Key quay theo record / cipher chained | so byte-map giữa các record trùng nhau ở nhiều file ("RUSTED SPIRIT-MEDALLION..." xuất hiện ở sample1 và team) | **DEAD**: hai bản ghi dài 60+ byte khớp 100% từng byte -> key đúng và plaintext trùng nhau |
| H8 | Token nằm trong text dưới dạng 16 ký tự `[A-Z0-9]` | `re.finditer(rb'[A-Z0-9]{16,}')`, rồi `[A-Za-z0-9_]{14,}` | **DEAD**: không có run nào >= 13 ở cả 4 file |
| H9 | Token là 14 byte cuối record vị trí | bóc 14 byte cuối 4 file, thử raw / base32 / hex / `& 0x1f` | **DEAD**: hoá ra là struct nhị phân (`i32` âm, `ff ff ff` sentinel) + 4 byte checksum; mẫu số chung `ff ff ff` nằm ở byte 7-9 tính từ cuối |
| H10 | Bit 5 là flag ngữ nghĩa trong text | thử `b < 0x20 -> b + 0x20` rồi đọc | text đọc được nhưng độ dài xâu vẫn vô lý |
| H11 | xâu có prefix độ dài | in 6 byte trước mọi xâu >= 8 ký tự, đối chiếu `len` | thấy ngay `2f -> 15` ("Obsidian censer"), `05 -> 37` ("Fingerprints of five different hands.") |
| H12 | Cả thân file bị XOR thêm 0x20 | kiểm tra công thức `len_byte = byte ^ 0x20` trên ~30 xâu, rồi áp `^0x20` cho toàn body | **OK**: mọi độ dài khớp, text thành Title Case chuẩn, `00`/`0d`/`0e`/`07` biến thành space/`-`/`.`/`'`, phần "nhị phân lạ" thành các field `u8/u16/u32` sạch |
| H13 | Token = chữ cái đầu của danh sách item theo thứ tự túi đồ | parse record `0x10 idx a b namelen name desclen desc`, lấy `name[0]` nối lại | **OK**: sample1 = `TORCH`, sample2 = `SILVERMOON`, sample3 = `NIGHTENDSSOON` ("NIGHT ENDS SOON"), team = `2VE5EKXUA5IV2R57` đúng 16 ký tự |
| H14 | Nộp dạng `POCTF{token}` | `POST /challenges/excavation/submit` | **DEAD**: server báo `Incorrect. Keep working.`; chỉ nhận token trần |

## Những chi tiết định lượng đã dùng làm điểm neo

- `english_hits` khi recover key: hàm tham chiếu được chọn tự động là file có nhiều từ tiếng Anh nhất; ở lần chạy thật chính là `team`.
- Field số lượng item trong record character là `u16` ngay trước record item đầu tiên: sample1 = 5, sample2 = 10, sample3 = 13, team = 16.
- Số lượng bản ghi `0x10` parse được bằng đúng con số đó ở cả 4 file. Đây là bằng chứng parser đúng, không phải đoán.
- Chỉ team.sav có item tên bắt đầu bằng chữ số (`2-star runic band`, `5-knot cord`, `7-day candle`); ba sample không có. Token của team cần chữ số 2, 5, 7 nên tác giả phải tạo ra các item tên số - dấu vết này khẳng định cơ chế acrostic.
