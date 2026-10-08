# Severed Symmetry - Crypto (Expert)

**Flag:** `CSSCTF{P35T0_5CH3M3_4TT4CK2026}`
**Files:** `source.py` (10.103 B, SHA256: `b1945c90...`), `out.txt` (31.778.814 B, SHA256: `5bd759a0...`)

## Đề bài

`source.py` mô tả hệ mã; `out.txt` chứa public key gồm 34 đa thức và 3 ciphertext block. Private key không được cung cấp. Mục tiêu là tìm preimage của các block từ dữ liệu công khai và khôi phục flag `CSSCTF{...}` trong plaintext.

## Phân tích

`keygen` dùng hai phép biến đổi affine `A1` (34x34), `A2` (32x32), cùng 16 đa thức thuần nhất bậc hai `q_a` trên 16 biến. Hệ mã còn có 18 đa thức `U_j` theo cấu trúc vinegar-oil: mỗi số hạng chứa ít nhất một biến trong nhóm 20 biến đầu. Central map được định nghĩa bởi:

```python
w = [z[i] - substitute(qmap[i], z[t:], p) for i in range(t)]
central = w + [substitute(poly, w + z[t:], p) for poly in umap]
```


Với `z = A2(x)`, `w` đã có bậc hai, nên `U_j(w, v)` có thể đạt bậc 4. Mỗi public polynomial trong `out.txt` có 49.320 số hạng bậc 4 và 5.626 số hạng bậc 3.

Các tham số dùng trong lời giải:

- `t = 16`: số chiều của không gian các tổ hợp public polynomial có bậc không quá 2.
- `s = 4`: số biến vinegar cần duyệt, tương ứng `17^4 = 83521` trường hợp.
- `m - t = 18`: số phương trình trên 12 biến oil. Các nghiệm thu được vẫn cần được kiểm tra trên public key.

## Lời giải

**Bước 1 - Khôi phục không gian `W` có bậc không quá 2.**

Lập ma trận hệ số cho các monomial bậc từ 3 trở lên, kích thước 34x70.906, rồi tính null space. Các vector trong null space xác định tổ hợp loại bỏ phần bậc cao. Kết quả thu được `W = span{w_a}` có số chiều 16.

```python
vec = {mon: c for mon, c in poly.items() if len(mon) >= 3}   # Chỉ bảo lưu các số hạng có bậc >= 3
dep, comb = reduce_track(pivots, vec, comb)                   # Khử Gauss (elimination) tích hợp cơ chế theo dõi cấu trúc tổ hợp
```


**Bước 2 - Khôi phục tọa độ `(u, v)`.**

Viết mỗi `W_a` dưới dạng `const_a + u_a - q_a(v)`. Phần tuyến tính cho 16 dạng `u`; phần bậc hai cho các `q_a(v)`. Thử tổ hợp ngẫu nhiên của các quadratic form cho đến khi ma trận 32x32 có rank 16. Kernel xác định `{x : v(x) = 0}`; annihilator của kernel cho không gian các dạng tuyến tính `v`.

```text
step2  Hạng ma trận bậc 2 (quadric) đạt 16 chỉ sau 1 lần thử; số chiều (dim) ker = 16
step2  Xác thực khung (frame): t=16 số chiều v (dim(v))=16
```


**Bước 3 - Hạ bậc mà không cần khôi phục `A1`.**

Với ciphertext `c`, tính `t_a = (comb_a . c) - const_a`. Thế `u_a = t_a + q_a(v)` vào hệ ban đầu làm triệt tiêu các số hạng bậc 3 và 4, để lại hệ bậc hai trên 16 biến `v`. Nội suy bằng 153 điểm `0`, `e_i`, `2e_i`, `e_i+e_j` để khôi phục 153 hệ số của mỗi quadratic polynomial.

**Bước 4 - Khôi phục không gian oil.**

Gọi `E_g` là các ma trận quadratic form của 18 phương trình. Với `o` thuộc không gian oil `O`, các vector `E_g o` nằm trong không gian vinegar có số chiều 4. Lời giải tìm `O` qua điều kiện `dim span{E_g v} <= 4`, thử ngẫu nhiên `17^4` mẫu để thu không gian ảnh `Vtil`. Xác suất một mẫu thuộc `O` là `17^-4`. Sau đó giải hệ tuyến tính từ điều kiện `E_g v ⊂ Vtil`.

```text
step4  Phân vùng họ quadric đạt số chiều 18, hạng tối đa 8 => tham số s=4, số chiều O (dim(O))=12
step4  Không gian oil khôi phục thành công (thử nghiệm 0, 2 mẫu đánh giá trùng khớp)
```


**Bước 5 - Duyệt các giá trị vinegar.**

Với mỗi block, cố định `t*` rồi duyệt `17^4` giá trị vinegar. Mỗi giá trị tạo một hệ tuyến tính 18x12 cho 12 biến oil. Giải bằng Gaussian elimination được vector hóa theo batch 4096.

**Kiểm tra nghiệm.**

Thế từng ứng viên vào 34 public polynomial và đối chiếu ciphertext. Mỗi block trong dữ liệu đề có một ứng viên vượt qua kiểm tra. Ghép 3 block rồi đọc 8 chữ số đầu để lấy độ dài `L`; kiểm tra `2(4+L) ≤ 96` và phần sau vị trí `2(4+L)` đều bằng 0.

## Kết quả

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


Lời giải được thử với hai instance sinh từ `source.py`: cấu hình nhỏ `p=17, n=9, m=11, t=3, s=2` có 7 block, và cấu hình của đề `n=32, m=34` có 3 block với plaintext biết trước. Cả hai lần đều khôi phục đúng plaintext. Mã hóa lại plaintext bằng public key trong `out.txt` cũng cho đúng 3 ciphertext block của đề.

## Tái hiện

```bash
python exploit.py files/out.txt
```


Script cần `numpy`, thời gian chạy khoảng 35 giây trong môi trường đã thử. `analysis/quartic.py` và `analysis/vinegar.py` hỗ trợ khảo sát phần bậc 4 và không gian tuyến tính của `W`.
