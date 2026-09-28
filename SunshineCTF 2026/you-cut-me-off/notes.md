# notes.md - you cut me off

Input: `files/hereyougo.png` (38759 B, PNG 492x382 RGBA, non-interlaced)
Định dạng cờ đề yêu cầu: `sun{...}`

## H1 - dữ liệu nối thêm sau IEND / chunk ẩn
cmd: `python` đi qua từng chunk, và `grep -a "H7CTF{\|flag{"` trên toàn bộ file
evidence: chỉ có 5 chunk `IHDR sRGB gAMA pHYs IDAT IEND`, sau IEND còn 0 byte, không có
tEXt/iTXt/zTXt, không có hit cờ
result: DEAD - không có stego kiểu append/chunk.

## H2 - LSB hoặc kênh alpha
cmd: `python` + numpy, đếm LSB từng kênh
evidence: alpha toàn bộ = 255. LSB R = 34%, G = 45%, B = 96% khác thường, nhưng màu nền
maroon của ảnh Discord là (50,23,23): chẵn/lẻ/lẻ, nên độ lệch LSB chỉ là sản phẩm của
bảng màu, không phải dữ liệu nhúng
result: DEAD - giải thích được toàn bộ bằng palette.

## H3 - contrast stego (chữ màu gần với nền)
cmd: `python` đếm khoảng cách tới màu nền, render `nearbg.png` và `amp24.png`
evidence: chỉ 9604/187944 pixel lệch khỏi nền <= 8, phân bố trùng với vùng chữ thật
result: DEAD - không có lớp chữ ẩn.

## H4 - kích thước giải nén của IDAT (ĐÚNG)
cmd: `zlib.decompress(IDAT)` rồi so với `height * (1 + width*4)`
evidence: giải nén ra 823042 byte, trong khi IHDR 382 dòng chỉ cần 752158. Thừa 70884.
`823042 / 1969 = 418` chẵn, mọi dòng đều dùng filter type 0
-> buffer thật chứa 418 dòng, header khai báo 382.
result: PENDING -> xác nhận ở H5.

## H5 - dựng lại ảnh đầy đủ
cmd: `python solve.py`
evidence: `IHDR: 492x382 stride=1969 IDAT giải nén=823042 -> thực tế 418 dòng`,
`analysis/full.png` có thêm 36 dòng dưới, `analysis/hidden4x.png` đọc rõ dòng tin nhắn
result: OK - cờ: `sun{totallyoriginalchallengeidea}`

## H6 - kiểm tra ký tự dễ nhầm
cmd: crop `analysis/mid.png` (6x) và `analysis/glyphs.png` (10x)
evidence: glyph giữa "challenge" và "dea" có dấu chấm trên đầu nên là `i`, không phải `l`;
chuỗi là `...challengeidea}`
result: OK - không nhầm `i`/`l`.

## Ghi chú
- Ảnh là screenshot Discord, được re-encode nên sạch metadata; hướng stego trong ảnh Discord gần như luôn sai, ưu tiên kiểm tra cấu trúc PNG trước.
- Đề ghi chuỗi dấu chấm `......` dài khác nhau, dễ gợi ý "cờ bị che trong mô tả". Thực tế
  mô tả chỉ là dẫn hướng tới đúng nghĩa của tên bài: ảnh bị cắt.
