# notes.md - colour-shift

Input: `C:\Users\Administrator\Downloads\colorshiftctf.bmp` (1083738 B, sha256 `689f33ba…35ef92`)
Định dạng cờ đề yêu cầu: `CSSCTF{...}` (chốt trước khi quét, mọi phép thử đều dò đúng prefix này)

Bối cảnh: triage trả `magic=undetermined` vì script không có mẫu BMP, nhưng `xxd` đầu file là `42 4d` và `file` đọc ra `PC bitmap … 599 x 602 x 24`. Entropy 5.77, `flag-pattern hits=0`.

## H1 - Có dữ liệu nối thêm hoặc chunk ẩn sau pixel
cmd: `python -c "d=open(...,'rb').read(); print(len(d)-(138+1083600))"`
evidence: `bfOffBits=138`, `biSizeImage=1083600`, `138+1083600=1083738` đúng bằng độ dài file, phần dư 0 byte. Hàng đợi `strings` chỉ ra text của header, không có chuỗi nào chứa `CSSCTF` hay `flag`.
result: DEAD - file đóng khung chính xác, không có chỗ nhét thêm.

## H2 - Lợi dụng bảng màu / header phụ
cmd: đọc `biClrUsed`, `biClrImportant`, `bV5Compression`
evidence: 24 bpp, `BI_RGB` (comp=0), `biClrUsed=0`, `biClrImportant=0`, header 124 byte là BITMAPV5HEADER chuẩn, mask `0000ff / 00ff00 / ff0000`.
result: DEAD - ảnh 24 bpp_truecolor không có palette để giấu, phần header phụ chỉ là gamma/color space.

## H3 - Stego LSB
cmd: `np.packbits((A[:,:,i]&1), bitorder='little')` cho cả hai chiều đọc ảnh và cả bản 3 bit/px
evidence: quét 6 tổ hợp (R/G/B x đọc từ dòng đầu / từ dòng cuối, MSB-first và LSB-first) rồi chạy `re.findall(b'CSSCTF.{0,40}')`: 0 kết quả ở mọi tổ hợp. Ảnh LSB của ba kênh trông như nhiễu hạt, không có dải cấu trúc.
result: DEAD - không có chuỗi bit nào giải ra prefix.

## H4 - Chữ vẽ bằng màu gần với nền (đọc trực tiếp trên ảnh gốc)
cmd: xem `orig.png`, rồi khuếch đại từng kênh riêng (`chR/chG/chB_stretch`)
evidence: ảnh là bìa The Dark Side of the Moon, mean R/G/B = 15.4/32.1/38.1, không thấy chữ ở ảnh gốc. Kênh R có dải 0-255 trong khi G dừng ở 240 và B ở 215, tức R động nhiều hơn hai kênh kia.
result: PENDING - R đáng nghi nhưng khuếch đại thô vẫn chìm trong nhiễu hạt của nền.

## H5 - Tách thành phần màu rồi trừ nền cục bộ
cmd: `residual = chan - MedianFilter(41)(chan)`, sau đó hop trung binh 2x2, chuẩn hoá theo MAD
evidence: trên dải dòng 404-436, bản `R` và `R-B` hiện một dòng chữ rõ; bản `G` và `B` phẳng, không còn gì. Nghĩa là lớp đè chỉ làm dịch kênh đỏ, và hiệu `R-B` triệt tiêu đúng phần nhiễu nền chung của hai kênh nên tương phản cao nhất.
result: OK - đọc được `CSSCTF{SHINE ON}`.

## H6 - Kiểm tra ký tự phân cách giữa E và O
cmd: in ASCII map của `z=(band-median)/MAD-sd` trên đoạn x 378..470, và vẽ `analysis/channels.png`
evidence: khoảng E->O rộng hơn nhịp chữ thường (~47 px so với ~33 px) và không có pixel nào vượt ngưỡng chữ ở cả bốn kênh. Bản thử bằng band-pass trừ Gaussian (box 2 trừ box 25) sinh ra một vệt sáng chéo giống dấu `/` ngay khe này, nhưng đó là vòng dao động quanh nét tối do chính bộ lọc tạo ra chứ không phải nét chữ; đổi sang median filter locale thì vệt đó biến mất.
result: OK - phân cách là dấu cách thật, cờ không có `_` hay `/`.

## H7 - Còn dòng chữ nào khác không
cmd: đếm pixel `z < -1.2` theo từng dòng trên toàn ảnh
evidence: chỉ dải 404-436 có mật độ chữ; các dải khác (4-10, 50-57, 231-287, 302-312) là cạnh tam giác và dải cầu vồng của bìa, không phải glyph.
result: OK - một dòng duy nhất.

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.

Ghi nhớ kỹ thuật: với stego ảnh có nền nhiễu hạt, đừng dùng hiệu Gaussian để nổi bật nét chữ mỏng - vòng sáng/tối nhân tạo của nó dễ bị đọc nhầm thành nét chấm phá. Median filter locale lớn hơn bề dày nét chữ thì không dao động, và hiệu hai kênh (`R-B`) là cách rẻ nhất để triệt phần nhiễu nền chung.
