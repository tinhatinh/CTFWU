# gl2-88 - Reverse Engineering Cryptography (500)

**Flag:** CHƯA KHAI THÁC XONG · **Files:** `files/GL2-88.hs`, 4013 B, sha256 `f1c7c3dfd5819a0b7257f03cc99f731fe8329d9acba723436fb5073fa606ccbc`; `files/ciphertext.txt`, 44 B, sha256 `d83f904893e41d8cae69651272d17326026e340144ca187d695ae3a2e0c80c2f`

> Bài này nằm trong `_wip/` vì chưa có cờ. Các phép thử local được ghi ở dưới; phần còn thiếu là đầu vào (xem mục "Cần xác minh").

## Đề bài

Tác giả cho một stream cipher đối xứng viết bằng Haskell (`GL2-88.hs`) và một
ciphertext 44 ký tự. Nhiệm vụ: lấy lại plaintext theo format `cdctf{...}` mà không
biết khoá (khoá 11 ký tự, bị `main` cưỡng chế độ dài).

## Phân tích

Mỗi ký tự plaintext được biến đổi bằng một ma trận 2x2 trên Z67:

```
M_i = ((k_i, a_i), (0, 1)),   y_i = k_i * x_i - a_i  (mod 67)
x = ord(c) - 60,  c = chr(v + 60)
```

Ba điểm bất thường dẫn tới hướng đánh:

1. `det ((a,b),(c,d)) = a*d - c*d` là bug (đúng ra `a*d - b*c`), **nhưng vô hại** ở
   đây: với dòng hai `(0,1)` thì det lỗi cho ra `k`, trùng det thật. `minv` vẫn là
   inverse đúng, round-trip `decrypt(encrypt(pt)) == pt` chạy sạch. Lỗi determinant không ảnh hưởng đến các ma trận dạng này.
2. `grp = [((9^b, a), (0,1))]` đúng 737 = 67·11 phần tử, và vì các ma trận sinh từ
   khoá nằm trong `grp` nên `grp // md` chỉ là `grp` sắp lại, không mở rộng không gian.
3. Lock sinh keystream (`concat . iterate go` rồi 12 vòng `round`) hoàn toàn không
   phụ thuộc plaintext, Điều này cho phép phân tích keystream riêng; tính affine theo khóa được kiểm tra ở bước sau.

## Lời giải

**Bước 1 - Port keystream sang Python và đối chiếu bằng GHC thật.** Không có GHC trên
máy, nên biên dịch đúng source của đề bằng Wandbox (trình `ghc-9.10.1`, chỉ thay `main`).
Output thật của GHC:

```
pNW@JXxoFGI
Qux`OtZS\NfEotCec>>G}eRxrJD[XXsMftQy<qmkYsog
737
[((14 (mod 67),56 (mod 67)),(0 (mod 67),1 (mod 67))),((14 (mod 67),34 ...
```

Port Python khớp byte-by-byte cả 4 test vector; chúng được khoá lại thành
`GHC_VECTORS` + `assert` trong `exploit.py::selftest`.

**Bước 2 - Kiểm tra hai tính chất dùng để giảm không gian tìm kiếm.** `structure_report` kiểm
tra trên 5 khoá ngẫu nhiên:

```python
assert [x[0][0] for x in keystream(kv, n)] == list(kvec)   # k_i không đổi theo khoá
assert pred_a == real_a                                    # a_i affine trên Z67
```

Kết quả: `k_i` cố định (`[14]*10 + [62, 64, ...]`, với `14 = 9^2 mod 67`), `a_i` affine
theo 11 ký tự khoá. Phần "nhân" của keystream trở thành thông tin công khai.

**Bước 3 - Known plaintext thành hệ tuyến tính.** Với `cdctf{` ở 6 vị trí đầu và `}` ở
vị trí cuối, mỗi vị trí cho `BET_i · c = k_i*x_i - y_i - avec_i`. Khử Gauss trên Z67:

```
rank=7  consistent=True  free_dims=4  -> 67^4 = 20,151,121 keys
part = [51,37,10,4,45,10,23,0,0,0,0]
```

**Bước 4 - Quét toàn bộ không gian và lọc bằng charset.** `s2c` luôn trả ký tự trong
`[<, ~]`, nên plaintext giải mã không thể hiện chữ số; `0..7` hiện thành `s..z`, còn
`8`/`9`/`:`/`;` hiện thành `{`/`|`/`}`/`~`. Lọc `[A-Za-z_]` trên 37 vị trí ẩn:

```
3,431 ứng viên toàn chữ cái;  197,046 ứng viên có >=35/37 vị trí là chữ cái
```

**Bước 5 - Chấm điểm bằng từ điển.** `words_alpha.txt` (370k từ) + mô hình bigram học
từ chính từ điển. Điểm phủ từ cao nhất đạt được: **13/37 ký tự**, đúng mức của chuỗi
ngẫu nhiên. Không có plaintext đọc được.

## Kiểm tra implementation bằng dữ liệu tổng hợp

- **Known-answer test** (`analysis/solve.py`): tự sinh 3 cờ giả, mã hoá bằng khoá ngẫu
  nhiên, chạy lại toàn bộ pipeline. Cả 3/3 cờ thật nằm trong tập ứng viên lọc chữ cái.
- **Bảng giả thuyết đầu vào** (`analysis/gen.py`): `}`@43, `}`@42 + `'\n'`@43, prefix
  hoa `CDCTF{`, đảo chiều mã hoá (`x = k*y - a`), và nới charset. Cả 5 chiều đều gibberish.
- **Khóa từ điển** (`analysis/kdict.py`): đã thử 254.905 ứng viên dài 11 ký tự với crib `cdctf{`, không có kết quả. Chỉ loại trừ tập ứng viên này, chưa xác định cách sinh khóa.

## Cần xác minh (nguyên nhân khiến bài chưa ra cờ)

1. **Ciphertext chưa được đối chiếu với card gốc.** 44 ký tự, kết thúc bằng dấu
   backtick, rất dễ hỏng khi copy qua markdown. Cần đối chiếu với ciphertext gốc.
2. **Giả định `}` ở cuối chuỗi** chưa loại trừ được bằng dữ liệu; hướng dim-5
   (chỉ giữ `cdctf{`, 1.35 tỉ khoá) đang chạy ở `analysis/scanF.py`.

## Tái hiện

```bash
python exploit.py            # selftest GHC vector + do khong gian khoa (~40 giay)
python exploit.py --scan     # in 20 ung vien dau tien
python analysis/solve.py     # known-answer test 3/3
python analysis/kdict.py     # khoa tu dien (can words_alpha.txt cung thu muc)
```
