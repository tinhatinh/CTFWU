# Log giả thuyết

H1. File là Kaspersky license key (.klc cũng là phần mở rộng của loại này).
result: DEAD. Nội dung là ASCII có cấu trúc `KBD`/`SHIFTSTATE`/`LAYOUT`/`ENDKBD`, đúng khuôn Microsoft KLC.

H2. Có dữ liệu ẩn ở byte thừa hoặc khoảng trắng cuối dòng.
result: DEAD. 419 byte, kết thúc bằng `ENDKBD\n`, LF thuần, không dòng nào có trailing space/tab.

H3. Chuỗi cờ nằm thẳng trong file.
result: DEAD. triage báo 0 hit mẫu cờ; các giá trị unicode chỉ là chữ cái thường và ký hiệu.

H4. Hai cột unicode là hai state: state 0 là mũi tên, state 1 là chữ cái.
result: PENDING rồi WIN. Mũi tên xuất hiện ở state 0 với 4 ký tự: U+2192, U+2196, U+2198, U+25A0.

H5. Mũi tên là chỉ dẫn di chuyển trên lưới bàn phím, chữ cái là dữ liệu thu thập dọc đường.
Cách giải hình học chưa biết (bàn phím có so le), nên quét toàn bộ 8^3 cách gán 3 hướng,
mỗi cách đi từ mọi phím, và lọc lấy chuỗi chứa cả `{` lẫn `}`.
result: WIN. Bộ gán đúng là: U+2192 = phải, U+2196 = lên một hàng, U+2198 = xuống một hàng, U+25A0 = đích.

H6. Điểm bắt đầu phải suy ra được, không đoán.
result: WIN. Với hình học ở H5, Q là phím duy nhất không có mũi tên nào trỏ vào.
Đi từ Q dùng đúng 17/17 phím mỗi phím một lần và kết thúc ở H, ô duy nhất mang ký tự đích.
Nên lời giải bị ép hoàn toàn, không có nghiệm khác cùng hình học.

## Kết quả

Duong di: Q A Z X S W E D C V F R T G B N H
Chu thu:  s u n { q w e r t y _ s u c k s }

Flag: sun{qwerty_sucks}
