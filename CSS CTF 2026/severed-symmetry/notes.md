# notes.md - severed-symmetry

Input: `files/out.txt` (31778814 B, sha256 `5bd759a0593a39277157f8025784296d5c4684c75a4bc3823bceef2c5d76c0bf`), `files/source.py` (10103 B, sha256 `b1945c904bc5d729ba4e6be6439259b331ab5dc7cbd31b876600fe44fcc8b90a`)
Định dạng cờ đề yêu cầu: `CSSCTF{...}`
Tham số: `p=17, n=32, m=34, t=16, s=4`

## H1 - Phần bậc hai của mọi polynomial public có hạng <=16, kernel chung cho không gian vinegar
cmd: đọc `keygen`: `central = w + [substitute(poly, w + z[t:], p) for poly in umap]`
evidence: `U_j(w,v)` có số hạng `w_a w_b` với mọi `a,b < 16`, mà `w_a = u_a - q_a(v)` nên phần bậc hai theo `u` khác 0. Hạng không bị chặn ở 16, và public polynomial lên tới bậc 4 (đếm trong out.txt: 49320 số hạng bậc 4 mỗi polynomial).
result: DEAD - không có kernel chung bậc hai để khai thác.

## H2 - Tìm không gian `v` bằng các tổ hợp tuyến tính bậc 1 của public key
cmd: `python -c "khảo sát số chiều các tổ hợp bậc <=1 của span{P_i}"`
evidence: để một tổ hợp các `U_j` trở thành bậc nhất theo `Z` thì phải triệt tiêu cả khối bậc hai và khối `w`; đó là 450+32 điều kiện trên 18 hệ số nên không có nghiệm khác 0.
result: DEAD - không tồn tại tổ hợp bậc nhất.

## H3 - Không gian bậc <=2 của span public chính là span{w_a}
cmd: `python exploit.py files/out.txt` (bước step1)
evidence: phần bậc >=3 của các tổ hợp lập thành ma trận 34 x 70906; null space đúng 16 chiều, và cả 16 vector trả về đều có bậc <=2 (`assert` trong exploit). Phần bậc 4 của một tổ hợp triệt tiêu khi và chỉ khi thành phần `U` của nó bằng 0, nên không gian này đúng bằng `span{w_a}`.
result: OK - `dim(W) = 16 = t`.

## H4 - Kernel của một quadric trong W sinh ra không gian `v`
cmd: `step2` trong exploit: thử tổ hợp ngẫu nhiên của 16 dạng bậc hai đến khi hạng 16
evidence: `rank = 16` ngay lần thử đầu, `dim ker = 16`; annihilator của kernel cho đúng 16 dạng tuyến tính và mọi quadric của W đều triệt tiêu trên kernel đó (đã assert).
result: OK - có khung `(u, v)` để làm việc.

## H5 - Thế `u_a = t_a + q_a(v)` làm hệ tụt về bậc 2 mà không cần biết A1
cmd: `step3` + `compose(tstar)`
evidence: nội suy 153 điểm cho ra đúng dạng bậc hai; thử trên instance tự sinh với plaintext đã biết thì `u - (t + Q(vhat))` triệt tiêu và cả 18 phương trình nội suy khớp đánh giá trực tiếp tại 20 điểm ngẫu nhiên (0 sai khác).
result: OK - `t_a` lấy từ chính ciphertext vì `W_a` là polynomial hiện theo `x`.

## H6 - Dùng Gröbner/F4 giải 18 phương trình bậc hai theo 16 ẩn `v`
cmd: ước lượng: hệ 0-chiều có đúng 17^4 = 83521 nghiệm
evidence: số đơn thức chuẩn xấp xỉ 2^16 = 65536, ma trận F4 cỡ 65536 x 65536 trở lên; với bậc chính quy 17 của một complete intersection 16 phương bậc hai thì số đơn thức cấp 17 là C(32,17) ~ 6e8.
result: DEAD - không chạy nổi trong phiên CTF.

## H7 - Thu hẹp về minrank để tìm không gian oil
cmd: `step4`: xét họ 18 dạng bậc hai `E_g` theo `vhat`
evidence: mọi tổ hợp đều có hạng <=8 nên minrank không cho thông tin; không gian oil 12 chiều chỉ là không gian con mà mọi dạng triệt tiêu trên đó (GSQ), không phải kernel.
result: DEAD - thay bằng bất đẳng thức hạng: với `o in O` thì `span{E_g o}` có dim <= s=4, còn `v not in O` thì dim >= 12.

## H8 - Quên hằng số của phần tử W khi suy ra `u`
cmd: thử trên instance nhỏ tự sinh, so `u - (t + Q(vhat))`
evidence: residual `[3, 14, 13]` khác 0; `W_a` sinh từ tổ hợp các public polynomial nên mang theo `b1`, tức `W_a = const + u_a - q_a(v)`.
result: DEAD -> sửa bằng `tstar = (comb . c) - W_const`, residual về `[0, 0, 0]`.

## H9 - Lọc ứng viên theo byte in được ngay trong từng block
cmd: chạy driver trên instance nhỏ `n=9`
evidence: preimage tìm ra đúng bằng plaintext gốc (`[0,0,0,0,0,0,1,9,3]`) nhưng bộ lọc byte block 0 loại nó, vì `width=2` mà `n=9` lẻ nên một byte vắt qua biên hai block.
result: DEAD - chỉ kiểm frame sau khi ghép toàn bộ các block.

## H10 - Phục hồi không gian oil và giải mã
cmd: `python exploit.py files/out.txt`
evidence: `s=4` (hạng tối đa 8), `dim(O)=12`, mọi dạng bậc hai triệt tiêu trên O; mỗi block duyệt 83521 giá trị vinegar cho đúng 1 nghiệm thoả mãn cả 34 phương trình công khai; 3 block ghép thành frame có header độ dài hợp lệ.
result: OK - cờ: `CSSCTF{P35T0_5CH3M3_4TT4CK2026}`

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
