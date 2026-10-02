# Severed Symmetry - Crypto (Expert)

**Flag:** `CSSCTF{P35T0_5CH3M3_4TT4CK2026}`
**File đính kèm:** `source.py` (Kích thước: 10.103 B, SHA256: `b1945c90...`), `out.txt` (Kích thước: 31.778.814 B, SHA256: `5bd759a0...`)

## Đề bài

Hệ thống cung cấp một mã nguồn mã hóa `source.py` và một tệp tin dữ liệu duy nhất `out.txt`. Tệp tin `out.txt` chứa cấu trúc khóa công khai (public key) bao gồm 34 đa thức (polynomial) kèm theo 3 khối bản mã (ciphertext block). Khóa bí mật (private key) đã bị tiêu hủy; do đó, bài toán yêu cầu phục hồi ảnh ngược (preimage) của các khối bản mã hoàn toàn dựa trên dữ liệu công khai. Cờ (flag) được nhúng trực tiếp trong khối bản rõ (plaintext) với độ dài được giới hạn chặt chẽ bởi khuôn dạng tiêu chuẩn `CSSCTF{...}`.

## Phân tích ban đầu

Kiến trúc hàm tạo khóa `keygen` xây dựng một bảng mã tuân theo mô hình VLG: Quá trình khởi tạo ngẫu nhiên hai phép biến đổi affine độc lập `A1` (kích thước 34x34) và `A2` (kích thước 32x32), kết hợp cùng 16 đa thức `q_a` đồng nhất bậc hai trên 16 biến. Hệ thống sử dụng thêm 18 đa thức phụ trợ `U_j` được thiết kế theo cấu trúc vinegar-oil (ràng buộc cấu trúc đòi hỏi mỗi số hạng phải chứa ít nhất một biến trong nhóm 20 biến cấu trúc đầu tiên). Sơ đồ trung tâm (Central map) được định nghĩa qua hai biểu thức:

```python
w = [z[i] - substitute(qmap[i], z[t:], p) for i in range(t)]
central = w + [substitute(poly, w + z[t:], p) for poly in umap]
```

Với cấu hình `z = A2(x)`. Do hàm `U_j` tiếp nhận trực tiếp tham số đầu vào là `w` (bản thân `w` đã mang bậc hai), đa thức `U_j(w, v)` có khả năng nâng bậc mở rộng lên tối đa bậc 4. Dữ liệu trích xuất từ tệp `out.txt` xác nhận đặc tính này: Mỗi đa thức công khai xuất ra chứa 49.320 số hạng thuộc nhóm bậc 4, và 5.626 số hạng thuộc nhóm bậc 3.

Quy trình giải mã và tấn công phụ thuộc vào ba thông số cấu hình cốt lõi:
- Tham số `t = 16`: Biểu thị sự tồn tại của đúng 16 hướng phân tích bảo toàn bậc (bậc ≤ 2) trong không gian tuyến tính công khai (public span).
- Tham số `s = 4`: Định mức không gian tìm kiếm, quá trình giải mã hợp lệ chỉ yêu cầu duyệt qua `17^4 = 83521` trường hợp.
- Hệ số phương trình `m - t = 18` áp dụng trên 12 biến nhóm oil: Đảm bảo tính duy nhất tuyệt đối về mặt thống kê cho mỗi nghiệm thu được.

## Chuỗi khai thác

**Bước 1 - Khôi phục không gian tổ hợp `W` (Định dạng bậc ≤ 2).** 
Thiết lập ma trận hệ số cho toàn bộ các đơn thức có bậc ≥ 3 (Kích thước 34 hàng, 70.906 cột), áp dụng phép tính không gian null (null space). Hệ thống khẳng định: Phần thành phần bậc 4 của một tổ hợp tuyến tính chỉ bị triệt tiêu khi và chỉ khi thành tố `U` của tổ hợp đó bằng 0. Do vậy, không gian null hoàn toàn trùng khớp với phân vùng `span{w_a}` (số chiều giới hạn là 16).

```python
vec = {mon: c for mon, c in poly.items() if len(mon) >= 3}   # Chỉ bảo lưu các số hạng có bậc >= 3
dep, comb = reduce_track(pivots, vec, comb)                   # Khử Gauss (elimination) tích hợp cơ chế theo dõi cấu trúc tổ hợp
```

**Bước 2 - Nội suy khung cấu trúc `(u, v)`.** 
Mỗi phần tử thuộc mảng `W_a` được phân rã thành biểu thức `const_a + u_a - q_a(v)`. Tại đây, phần tuyến tính (bậc nhất) đại diện cho 16 biến đổi tuyến tính `u`, và phần bậc hai cung cấp 16 dạng toán học `q_a(v)`. Tiến hành thử nghiệm các tổ hợp ngẫu nhiên của tập hợp `q_a` cho tới khi tạo thành một ma trận 32x32 có hạng (rank) bằng 16. Nhân hạt (kernel) của ma trận này xác định chính xác tập `{x : v(x) = 0}`. Từ đó, bộ triệt tiêu (annihilator) của kernel sẽ cung cấp không gian bao trùm của biến `v`.

```text
step2  Hạng ma trận bậc 2 (quadric) đạt 16 chỉ sau 1 lần thử; số chiều (dim) ker = 16
step2  Xác thực khung (frame): t=16 số chiều v (dim(v))=16
```

**Bước 3 - Hạ bậc hệ phương trình độc lập với `A1`.** 
Đa thức `W_a` là biểu diễn hiện theo biến `x`. Tính chất toán học quy định: Giá trị của đa thức trên ảnh ngược (preimage) phải đồng nhất với giá trị của tổ hợp đó tính trên khối bản mã. Biểu thức tương đương: `t_a = (comb_a . c) - const_a`. Khi thế `u_a = t_a + q_a(v)` ngược vào hệ phương trình gốc, mọi số hạng thuộc bậc 3 và bậc 4 sẽ triệt tiêu (Bản chất là quá trình tiêu biến của `U_j(t, v)`). Hệ phương trình rút gọn duy trì ở bậc 2 với 16 ẩn `v`. Giải pháp kỹ thuật áp dụng cơ chế nội suy hàm (thay vì nội suy đa thức truyền thống): Sử dụng 153 điểm đánh giá (`0`, `e_i`, `2e_i`, `e_i+e_j`), cung cấp đủ cơ sở để dựng lại toàn bộ 153 hệ số của phương trình bậc hai.

**Bước 4 - Khai phá không gian Oil.** 
Định danh `E_g` là ma trận khối bậc hai (phụ thuộc biến `v`) cấu thành từ 18 phương trình thu được. Theo cấu trúc lý thuyết: Với `o` thuộc phân vùng không gian oil `O`, tích `E_g o` bắt buộc rơi vào không gian vinegar có số chiều bằng 4. Ngược lại, nếu `v` không thuộc `O`, các vector `E_g v` sẽ phát sinh cấu trúc sinh ra từ 12 chiều trở lên. Công thức quy nạp: `O = {v : dim span{E_g v} <= 4}`. Hệ thống sẽ tiến hành thử ngẫu nhiên `17^4` mẫu đánh giá (xác suất mẫu chạm chuẩn vào `O` là `17^-4`) nhằm cô lập và gom không gian ảnh `Vtil`. Cuối cùng, biểu thức `O = {v : E_g v ⊂ Vtil}` sẽ được giản lược thành một hệ phương trình tuyến tính chuẩn.

```text
step4  Phân vùng họ quadric đạt số chiều 18, hạng tối đa 8 => tham số s=4, số chiều O (dim(O))=12
step4  Không gian oil khôi phục thành công (thử nghiệm 0, 2 mẫu đánh giá trùng khớp)
```

**Bước 5 - Quét phân vùng Vinegar qua cơ chế mô phỏng hợp lệ.** 
Trên mỗi khối dữ liệu, tiến hành cố định cụm `t*` và áp dụng phương pháp duyệt toàn bộ `17^4` giá trị vinegar. Mỗi giá trị sinh ra một hệ phương trình tuyến tính kích thước 18x12 tương ứng với 12 biến oil. Hệ phương trình được giải bằng phương pháp khử Gauss được vector hóa trên các lô dữ liệu (batch) kích thước 4096 tham số mỗi lô.

**Khâu tự kiểm chứng (Verification).** 
Mỗi bộ ứng viên thu được sẽ phải trải qua bước kiểm tra độc lập bằng cách tái định giá 34 đa thức công khai theo biến `x` và đối chiếu ngược lại với khối dữ liệu tương ứng. Dữ liệu chứng minh mỗi khối chỉ xuất hiện duy nhất 1 ứng viên đáp ứng chuẩn. Tổ hợp 3 khối dữ liệu liên tiếp phải ghép thành một cấu trúc (frame) nhất quán: 8 chữ số dẫn đầu tiến hành giải mã để xác định chiều dài `L`. Ràng buộc tham số yêu cầu `2(4+L) ≤ 96`, đồng thời mọi giá trị theo sau vị trí chỉ mục `2(4+L)` phải bằng 0 tuyệt đối.

## Flag

Quá trình thực thi mã kịch bản hệ thống:

```bash
python exploit.py files/out.txt
```

```text
step1  dim(W) = 16 = t
step2  quadric hang 16 sau 1 lan thu; dim ker = 16
step2  frame: t=16 dim(v)=16
step3  18 polynomial bo tro, 153 diem noi suy
step4  ho quadric dim 18, hang max 8 => s=4, dim(O)=12
step4  oil space recovered (thu 0, 2 mau trng)
step5  83521 vinegar -> 1 nghiem tuyen tinh
step5  1 nghiem thoa man toan bo public polynomial
step5  83521 vinegar -> 1 nghiem tuyen tinh
step5  1 nghiem thoa man toan bo public polynomial
step5  83521 vinegar -> 1 nghiem tuyen tinh
step5  1 nghiem thoa man toan bo public polynomial
FLAG: CSSCTF{P35T0_5CH3M3_4TT4CK2026}
(33.9 s)
```

Để đảm bảo tính nhất quán của lời giải, toàn bộ thuật toán khai thác đã được tiến hành kiểm chứng chéo thông qua việc chạy thử nghiệm trên hai môi trường (instance) tạo từ mã nguồn `source.py` nguyên bản: Môi trường một thiết lập với các thông số cấu hình nhỏ (`p=17, n=9, m=11, t=3, s=2`, tạo ra 7 block dữ liệu); môi trường hai đồng bộ cấu hình nguyên trạng với yêu cầu của đề (`n=32, m=34`, 3 block dữ liệu và cờ giả lập/mồi biết trước). Cả hai bài kiểm tra độc lập đều khôi phục chính xác khối bản rõ gốc (plaintext). Phép thử bổ trợ bằng cách tái mã hóa văn bản bản rõ bằng khóa công khai trích xuất từ `out.txt` cũng kết xuất thành công 3 khối bản mã tương đương file đề cung cấp.

## Reproduce

Quá trình tự động tái thiết lập bằng công cụ (script):

```bash
python exploit.py files/out.txt
```

Lưu ý: Môi trường bắt buộc yêu cầu thư viện `numpy`. Thời gian chạy thực thi xấp xỉ 35 giây. Thư mục `analysis/` bao gồm hai kịch bản phụ trợ `quartic.py` và `vinegar.py`, đây là các script đảm trách thao tác dò quét ở giai đoạn tiền xử lý (khảo sát không gian bậc 4 và không gian hàm tuyến tính của biến `W`).
