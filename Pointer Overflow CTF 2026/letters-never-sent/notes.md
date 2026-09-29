# Letters Never Sent - log phân tích

Quy ước: mỗi giả thuyết một mục, nhánh sai ghi `result: DEAD - <lý do>`.

## H1 - Nhận diện cipher
Thư đề tặng "Admiral Sir Francis Beaufort, K.C.B., Hydrographer to the Navy" và nói
"that reciprocal tableau which bears your name". Beaufort cipher là bảng tra tự nghịch đảo
(`c = k - p`, giải mã cũng là `p = k - c`). Đây là phép thử đầu tiên, không phải suy đoán.

Kiểm chứng độc lập: ciphertext bắt đầu `PXYWN{`, cờ phải bắt đầu `POCTF{`.
Beaufort-26 với key `ELAPS` cho đúng `POCTF`. Vigenère (`k = c - p`) ra `AJWDI`,
variant Beaufort ra `AREXS`, Porta loại được vì chữ mã `P` không thể sinh ra từ chữ gốc `P`
(đầu ra của Porta cho nửa trên luôn nằm trong A..N).
`result: ALIVE - Beaufort alphabet 26, key[0..4] = ELAPS (xác suất ngẫu nhiên 1/26^5).`

## H2 - Key đến từ đâu
Khung viền có 24 nhãn, 6 nhãn có sao đỏ. Đo pixel (không đọc bằng mắt) cho ra đúng 6 slot:
top 1, top 4, right 1, bottom 4, bottom 0, left 1. Đọc theo chiều kim đồng hồ từ góc trên-trái:
Elder, Lily, Anchor, Poppy, Swan, Elder → **ELAPSE**.
Script `exploit.py` dựng lại được toàn bộ bước này từ ảnh.
`result: ALIVE - key ELAPSE, khớp cả 5 chữ cái bắt buộc của H1.`

## H3 - Ảnh có chứa dữ liệu ẩn không
- Chunk: IHDR + 282 IDAT + IEND, không tEXt/zTXt/iTXt, không có byte sau IEND.
- IDAT giải nén hết, `unused_data` rỗng.
- LSB ba kênh: ratio bit thấp 0.4933 / 0.5036 / 0.4921 (nhiễu chuẩn của PNG), quét 8 plane bit
  chỉ ra một chuỗi `!da5t]_Xhh?y` ở bit 5 (nhiễu).
- `stegano.lsb.reveal` → `IndexError: Impossible to detect message`.
`result: DEAD - ảnh chỉ chứa thư và khung viền, không có lớp stego.`

## H4 - Key ELAPSE, advance chỉ trên chữ cái
`POCTF{2.612.ORSMSQU6A7IQJGUC.PQ4FI6SPWLYJYQGBQK66AWTILP}`
`result: OPEN - prefix đúng, thân không phải tiếng Anh (xem H6).`

## H5 - Quy tắc advance key khác
Quét cả 8 tập hợp {chấm, chữ số, ngoặc} có/không đếm vào key stream, cộng với key index =
vị trí tuyệt đối trong chuỗi. Tất cả đều giữ đúng prefix `POCTF{` nhưng thân vẫn rác
(điểm quadgram xấu hơn cả ELAPSE thuần chữ).
`result: DEAD - không có quy tắc advance nào biến thân thành tiếng Anh.`

## H6 - Key dài hơn / không tuần hoàn
- Exhaustive toàn bộ key độ dài 6 (26 khả năng cho chữ thứ 6), 7 (676), 8 (17 576), 9 (456 976)
  với 5 chữ đầu cố định = ELAPS, chấm điểm bằng quadgram dựng từ 370k từ tiếng Anh.
  Điểm tốt nhất vẫn nằm vùng "-280 đến -310", tức là rác.
- Hill-climb + coordinate ascent cho độ dài 10..16: cũng không khá hơn.
- Index of coincidence theo chu kỳ: 0.0427 (1), 0.0583 (8), 0.0455 (11) - mẫu 36 chữ quá ngắn
  để kết luận, và không key nào trong các chu kỳ đó giải ra tiếng Anh.
`result: DEAD - không tồn tại key Beaufort tuần hoàn nào (độ dài <= 16, prefix ELAPS) cho ra tiếng Anh.`

## H7 - Running key là chính bức thư
Thư có 607 chữ cái. Beaufort running key đòi hỏi chuỗi key bắt đầu bằng ELAPS, nghĩa là
đoạn "ELAPS" phải xuất hiện trong thư. Tìm trong văn bản đã bỏ ký tự không phải chữ:
không có "ELA" ở đâu cả (chỉ có "ELE" tại offset 112, trong "eLEGance"). Chạy ngược thư cũng không.
`result: DEAD.`

## H8 - Autokey và progressive
- Beaufort autokey (key = ELAPSE + plaintext): `OCVOWDE6Y7SEQRUW...`
- Beaufort autokey (key = ELAPSE + ciphertext): `OCEKZLG6J7QERQAC...`
- Progressive (key tăng 1 mỗi chu kỳ): `OSTNTRV6C7KSLIWF...`
`result: DEAD - cả ba đều rác.`

## H9 - Có một lớp hoán vị sau khi giải mã
Thân có đúng 36 chữ = 6x6, hợp với chủ đề khung 6 nhãn mỗi cạnh. Đã quét:
- 720 hoán vị cột của lưới 6x6, cả hai hướng (giải mã rồi transpose, transpose rồi giải mã)
- rail fence độ sâu 2..12, cả encode lẫn decode
- spiral 6x6 bốn biến thể (trong ra/ngoài vào, xuôi/ngược, row-major/column-major)
- transpose lưới 6x6
Điểm số không có ứng viên nào nhô lên.
`result: DEAD.`

## H10 - Key từ nhãn không có sao
36 chữ thân = 2 lần 18 nhãn không sao. Key `RFSTPHWMDOVYCRLFST` (và bản x2, và bản 24 nhãn
`REFSLTPAHWMDOPVYCSRLFSET`) đều cho rác, và không khớp prefix ELAPS.
`result: DEAD.`

## Trạng thái: ĐÃ GIẢI

Cờ được chấp nhận: `POCTF{2.612.ORSMSQU6A7IQJGUC.PQ4FI6SPWLYJYQGBQK66AWTILP}` (kết quả của H4).

H6 không phải bằng chứng rằng key sai, mà là bằng chứng rằng thân cờ không phải tiếng Anh.
Thể lệ POCTF ghi rõ flag và cả nội dung đề được sinh riêng theo team, nên thân cờ là token
ngẫu nhiên. Bài học kỹ thuật: với cờ per-team, "plaintext không đọc được" không được dùng
làm tiêu chí loại key; tiêu chí còn lại là prefix đã biết (`POCTF{`) và số lượng quy tắc
advance key cùng lúc. Trong 8 quy tắc đã quét ở H5, chỉ có đúng một quy tắc vừa giữ prefix
vừa cho phân bố chữ cái khớp với token ngẫu nhiên.

## Câu hỏi mở (đã đóng)
- "Open Target" là ảnh thẻ đề, không có artefact thứ hai.
- Không cần nộp bản chữ thường.
