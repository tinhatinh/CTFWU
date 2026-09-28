# notes.md - trace-amounts

Input:
- `files/traces.npy` - float32 (500, 700), sha của file tải về 1.400.128 B
- `files/plaintexts.npy` - uint8 (500, 16)
- `files/secret.enc` - 48 B = 3 block AES (ECB)
- Target: `https://web-45d6579fff85ca5c.web.h7tex.com` (SimpleHTTP/0.6 Python/3.11.16)
- Định dạng cờ: `H7CTF{...}`

Suy ra từ đề: 500 lần authorisation, mỗi lần có trace + plaintext biết trước => **CPA/DPA trên vòng đầu AES-128**.

## H1 - CPA vòng 1, mô hình HW(S[pt^k]) (lần chạy đầu)
cmd: `python exploit.py traces.npy plaintexts.npy secret.enc`
evidence: cả 16 byte đều chỉ đạt |r| ~0.20-0.25, á quân ~0.20 => đúng mức noise floor
  của 500 trace (1/sqrt(500)=0.045, nhân bội mẫu số 256x700 => ~0.21). Không có peak nào vượt nền.
result: DEAD - không phải do dữ liệu, mà do code: bảng trọng số dựng thành
  `hw = popcount(sbox[v])` rồi tra `hw[S[pt^k]]` => tính ra `popcount(S[S[pt^k]])`, hai lần S-box.

## H2 - Nghi trace lệch pha hoặc có masking
cmd: `python analysis/diag.py`
evidence:
  - căn chỉnh: cross-correlate từng trace với trace trung bình -> shift tốt nhất = **0 với cả 500 trace** (std 0.0). Không lệch.
  - mô hình bậc 1 trên plaintext thô (HW(pt), pt, LSB): tối đa |r|=0.191 => dưới nền noise.
  - thử masking: tương quan với HW(pt_i ^ pt_j) cho mọi cặp byte -> max 0.195, cũng chỉ là noise. Không có mask.
  - mean trace có đỉnh định kỳ rất mạnh tại sample 30, 70, 110, ..., 630: **16 đỉnh cách đều 40 sample**.
result: DEAD cho giả thuyết mask/leak; nhưng phát hiện 16 đỉnh là chìa khoá:
  card xử lý **tuần tự từng byte**, byte i nằm ở slot `30 + 40*i`.

## H3 - Quét mô hình theo từng slot
cmd: `python analysis/sweep.py`
evidence: với `HW(S[pt^k])` và lấy đúng sample trong slot, cả 16 byte cho |r| = 0.673 - 0.740,
  trong khi á quân tụt về 0.20. Các mô hình khác (HW(pt^k) thô, S[xor], LSB) đều nằm sát nền noise.
  Vị trí peak trùng khớp 100% với công thức slot: byte 0 @30, byte 1 @70, ... byte 15 @630.
result: OK - khoá: `f9 37 e7 0c f8 f9 f6 f2 87 a1 4b 0d a8 29 ba 47`

## H4 - Sửa bảng HW và chạy lại toàn trình
cmd: `python exploit.py files/traces.npy files/plaintexts.npy files/secret.enc`
evidence: 16/16 byte |r| ~0.7, AES-128 key `f937e70cf8f9f6f287a14b0da829ba47`;
  giải mã 48 B ECB ra `H7CTF{48333086-d56b-41f5-b24b-a1d53fb122ec}` + padding hợp lệ
result: OK - CỜ: `H7CTF{48333086-d56b-41f5-b24b-a1d53fb122ec}`

## Ghi chú
- Không cài gì thêm: numpy 2.5.3 + cryptography đã có sẵn trên máy.
- Toàn bộ CPA chạy trong 0.35 s (vector hoá: nhân ma trận (256,500)·(500,700) cho mỗi byte).
- Bằng chứng khoá đúng không phải chỉ là |r| cao, mà làgiải mã ra ASCII có cấu trúc UUID + PKCS#7 hợp lệ.
