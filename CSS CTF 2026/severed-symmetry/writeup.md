# Severed Symmetry — Crypto (Expert)

**Flag:** `CSSCTF{P35T0_5CH3M3_4TT4CK2026}` · **Files:** `source.py` 10103 B sha256 `b1945c90...`, `out.txt` 31778814 B sha256 `5bd759a0...`

## Đề bài

Đề cho chương trình mã hoá `source.py` và đúng một file `out.txt` chứa public key (34 polynomial) với 3 block ciphertext. Khoá bí mật không còn, nên phải tìm preimage của các block từ dữ liệu công khai. Cờ nằm trong plaintext, độ dài bị khoá bởi định dạng `CSSCTF{...}`.

## Phân tích ban đầu

`keygen` dựng bảng mã dạng VLG: lấy ngẫu nhiên hai ánh xạ affine `A1` (34x34) và `A2` (32x32), 16 polynomial toàn bậc hai `q_a` theo 16 biến, và 18 polynomial `U_j` có cấu trúc vinegar-oil (số hạng chỉ được phép chứa ít nhất một biến trong 20 biến đầu). Central map là

```python
w = [z[i] - substitute(qmap[i], z[t:], p) for i in range(t)]
central = w + [substitute(poly, w + z[t:], p) for poly in umap]
```

với `z = A2(x)`. Vì `U_j` ăn đầu vào là `w` (đã mang bậc hai) nên `U_j(w, v)` có bậc tới 4, và `out.txt` xác nhận điều đó: mỗi polynomial công khai có 49320 số hạng bậc 4, 5626 số hạng bậc 3.

Ba con số quyết định hướng đi: `t = 16` nên có đúng 16 hướng bậc ≤2 trong span công khai; `s = 4` nên phía giải mã hợp lệ chỉ duyệt `17^4 = 83521` khả năng; `m - t = 18` phương trình cho 12 biến oil nên mỗi lời giải là duy nhất về mặt thống kê.

## Các hướng đã loại

Trước khi chốt đã kiểm tra và loại các kênh sau (log đầy đủ ở `notes.md`):

1. **Hạng của phần bậc hai bị chặn ở 16 để dùng kernel chung**: `U_j` chứa số hạng `w_a w_b`, tức chứa cả `u_a u_b`, nên hạng không bị chặn. Loại.
2. **Tìm không gian `v` qua các tổ hợp tuyến tính bậc nhất của public key**: để một tổ hợp các `U_j` trở thành bậc nhất phải triệt tiêu đồng thời khối bậc hai và khối `w`, 482 điều kiện trên 18 hệ số. Loại.
3. **Gröbner/F4 trên 18 phương trình bậc hai theo 16 ẩn `v`**: hệ 0-chiều với 83521 nghiệm, số đơn thức chuẩn cỡ 65536, ma trận F5 vượt quá khả năng một phiên. Loại.
4. **Minrank trên họ 18 dạng bậc hai**: mọi tổ hợp đều có hạng ≤8 nên họ đó không lộ gì; không gian oil là không gian con mà mọi dạng triệt tiêu, không phải kernel chung. Loại.

## Chuỗi khai thác

**Bước 1 — Phục hồi không gian `W` các tổ hợp bậc ≤2.** Đặt ma trận hệ số của các đơn thức bậc ≥3 (34 hàng, 70906 cột), tìm null space. Phần bậc 4 của một tổ hợp triệt tiêu khi và chỉ khi thành phần `U` của nó bằng 0, nên null space đúng bằng `span{w_a}`, số chiều 16.

```python
vec = {mon: c for mon, c in poly.items() if len(mon) >= 3}   # chỉ giữ phần bậc >= 3
dep, comb = reduce_track(pivots, vec, comb)                   # elimination có truy vết tổ hợp
```

**Bước 2 — Suy ra khung `(u, v)`.** Với mỗi phần tử `W_a` tách thành `const_a + u_a - q_a(v)`: phần bậc nhất cho 16 dạng tuyến tính `u`, phần bậc hai cho 16 dạng `q_a(v)`. Thử tổ hợp ngẫu nhiên của các `q_a` đến khi được ma trận 32x32 hạng 16; kernel của nó đúng là `{x : v(x) = 0}`, nên annihilator của kernel cho không gian `v`.

```
step2  quadric hang 16 sau 1 lan thu; dim ker = 16
step2  frame: t=16 dim(v)=16
```

**Bước 3 — Hạ bậc hệ mà không cần biết `A1`.** `W_a` là polynomial hiện theo `x`, nên giá trị của nó trên preimage chính là cùng tổ hợp đó trên ciphertext: `t_a = (comb_a . c) - const_a`. Thế `u_a = t_a + q_a(v)` vào các phương trình thì mọi số hạng bậc 3 và bậc 4 triệt tiêu (đúng ra là `U_j(t, v)`), nên hệ còn lại bậc 2 theo 16 ẩn `v`. Không nội suy đa thức mà nội suy hàm: 153 điểm (`0`, `e_i`, `2e_i`, `e_i+e_j`) đủ dựng lại 153 hệ số bậc hai.

**Bước 4 — Tìm không gian oil.** Gọi `E_g` là khối bậc hai theo `v` của 18 phương trình. Với `o` thuộc không gian oil `O` thì `E_g o` nằm trong không gian vinegar 4 chiều, còn `v not in O` thì các vector `E_g v` sinh ra 12 chiều trở lên. Do đó `O = {v : dim span{E_g v} <= 4}`: thử ngẫu nhiên `17^4` mẫu (xác suất rơi vào `O` đúng `17^-4`) để gom không gian ảnh `Vtil`, rồi `O = {v : E_g v ⊂ Vtil}` chỉ còn là một hệ tuyến tính.

```
step4  ho quadric dim 18, hang max 8 => s=4, dim(O)=12
step4  oil space recovered (thu 0, 2 mau trng)
```

**Bước 5 — Duyệt vinegar như bên giải mã hợp lệ.** Với mỗi block, cố định `t*` rồi duyệt `17^4` giá trị vinegar; mỗi giá trị cho một hệ tuyến tính 18x12 theo 12 biến oil, giải bằng khử Gauss vector hoá theo lô 4096 khả năng.

**Bước kiểm chứng.** Mỗi ứng viên được kiểm bằng cách đánh giá lại cả 34 polynomial công khai tại `x` và so với block tương ứng; mỗi block cho đúng 1 ứng viên vượt qua. Ba block sau đó phải ghép thành frame hợp lệ: 8 chữ số đầu giải mã thành độ dài `L`, `2(4+L) ≤ 96`, và toàn bộ chữ số sau `2(4+L)` phải bằng 0.

## Flag

```bash
python exploit.py files/out.txt
```

```
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

Lời giải còn được kiểm chéo trên hai instance tự sinh bằng đúng `source.py`: một instance tham số nhỏ (`p=17, n=9, m=11, t=3, s=2`, 7 block) và một instance cùng tham số với đề (`n=32, m=34`, 3 block, cờ mồi đã biết trước), cả hai đều khôi phục đúng plaintext. Ngoài ra mã hoá lại plaintext vừa thu được bằng public key của `out.txt` cho ra đúng 3 block ciphertext gốc.

## Reproduce

```bash
python exploit.py files/out.txt
```

Cần `numpy`. Chạy khoảng 35 s. `analysis/quartic.py` và `analysis/vinegar.py` là hai script dò giai đoạn đầu (không gian bậc 4 và không gian dạng tuyến tính của `W`).
