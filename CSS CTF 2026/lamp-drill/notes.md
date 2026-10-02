# notes.md - lamp-drill

Input: `C:/Users/Administrator/Downloads/lampDrill.svg` (54671 B, sha256 `4a11f4a8…`)
và `lampDrill.png` (99758 B, 2624x1472 RGBA).
Định dạng cờ đề yêu cầu: `CSSCTF{...}`

## H1 - Đo ảnh bằng mắt thường
cmd: mở `lampDrill.png`
evidence: thấy 4 quy tắc ở hàng trên và lưới 3 hàng × 8 ô, mỗi ô 2 đèn.
result: PENDING - đủ để định hướng nhưng không đủ để chốt bit, phải đọc toạ độ thật.

## H2 - Parse SVG thay vì OCR ảnh
cmd: `python -c "re.findall('<path...', svg)"` + tính bbox từng path
evidence: 117 path có `fill:`; theo đường kinh thì 60 cái w=23.0 (đèn),
24 cái w=101.7 (ô), số còn lại là mũi tên (w≈7.9) và frame. Hai màu fill của đèn:
`#1c1915` (66 lần, gồm cả mũi tên) và `#f7f4ee` (bằng đúng màu nền `fill: #f7f4ee`
của patch nền).
result: OK - đèn = 60, đúng bằng 12 (hàng luật) + 48 (lưới). Không còn nội dung nào
khác bị ẩn trong SVG (không có text, không có layer ẩn).

## H3 - Gom cụm hàng luật theo khoảng cách
cmd: `clusters(row0, gap=40)`
evidence: cặp đèn trong cùng một ô cách nhau ~30 đơn vị, nhưng ô kế tiếp cũng cách
~81 nên `(129 -> 210)` và `(420 -> 501)` không phân biệt được; hàm báo
"cum khong co 3 den" và tách nhầm thành `[2,1,2,1,...]`.
result: DEAD - clustering thuần khoảng cách không dùng được cho hàng luật.
Cách sửa: đọc cấu trúc tế bào - ô 2 đèn = cặp vào, ô 1 đèn = kết quả, rồi đi xen kẽ.
Với lưới thì khoảng cách vẫn tách tốt (8 ô × 2 đèn).

## H4 - Phép toán là AND
cmd: `python exploit.py files/lampDrill.svg`
evidence: bảng đọc ra từ chính ảnh là `00->0 01->0 10->0 11->1`.
Script không hard-code AND; nó dựng bảng từ hàng đầu rồi mới kiểm tên phép.
result: OK - AND.

## H5 - Bit = 1 khi đèn kết quả sáng, MSB trước
cmd: tính cả 4 tổ hợp (đen=1/0 × MSB/LSB)
evidence:
```
dark=1 MSB -> 'css'
dark=1 LSB -> '???'   (0x99 0xCE 0xCE, không in được)
dark=0 MSB -> '???'
dark=0 LSB -> '911'
```
result: OK - chỉ `dark=1, MSB` cho ra chữ in được, và chữ đó là `css`,
trùng tên chính giải đấu (CSSCTF). `911` là nhiễu, không phải ứng viên.

## H6 - Chốt
cmd: `python exploit.py files/lampDrill.svg`
evidence:
```
[*] 60 den, 4 hang
[*] hang luat: 00->0 01->0 10->0 11->1
[*] phep toan: AND
    hang1 bits=01100011 -> 0x63 'c'
    hang2 bits=01110011 -> 0x73 's'
    hang3 bits=01110011 -> 0x73 's'
[*] giai ma: 'css'
[!] CSSCTF{css}
```
result: OK - cờ: `CSSCTF{css}`

## Chưa kiểm chứng được
Không có dịch vụ nộp cờ cho bài này (đề chỉ cho ảnh), nên cờ mới ở mức
"giải mã đúng từ artifact", chưa phải "được hệ thống chấp nhận".

## Ghi chú phụ
- Hàng 2 và hàng 3 chỉ khác nhau ở ô đầu tiên (`.#` so với `..`); qua AND thì cả hai
  ra cùng bit 0 nên hai hàng giải ra cùng chữ `s`. Đó là chủ ý của bài warm-up,
  không phải lỗi đọc.
- `files/de.png` và `files/lampDrill.png` là một file (cùng sha256), giữ hai tên
  theo quy ước của repo.
