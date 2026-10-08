# Loose Lips - Crypto (Hard)

**Cờ v1:** `H7CTF{08a5c5eb-7571-4a3d-a80d-599ddd46c5ad}`
**Cờ v2:** `H7CTF{89c0e6b2-9fca-49fd-a02f-07a70e359363}`
**File cung cấp:** `ckks.py` (Kịch bản 2272 B, sha256 `f905e01981fc8049…`)
**Máy chủ mục tiêu:** `https://web-550a48e366fd77e3.web.h7tex.com`

## Đề bài

Hệ thống tính toán thống kê "DecryptoStat" ứng dụng một phiên bản rút gọn của cơ chế mã hóa đồng cấu CKKS, đảm bảo dữ liệu đầu vào không bị truy cập trực tiếp.
Đề cung cấp hai cổng dịch vụ chạy song hành: một bản gốc (v1) và một bản có cấu hình bảo mật cao hơn (hardened rewrite - v2). Mục tiêu của thử thách là trích xuất secret key của cả hai hệ thống, gửi chúng vào cổng `/v1/recover` và `/v2/recover` để xác nhận cờ.

## Phân tích

Truy vấn GET vào thư mục gốc `/` trả về bảng thông số kỹ thuật liệt kê các hàm API và cấu hình mạng tinh thể (hệ mật): `N=8`, `Q=2^40-87`, độ nhiễu `DELTA=2^25`. Điểm cần chú ý là điểm yếu hệ thống: *khoá bí mật là một ternary vector có độ dài 8 phần tử*.

Phân tích mã nguồn `ckks.py`:

```python
def small(bound=1): return [secrets.randbelow(2*bound+1) - bound for _ in range(N)]
def keygen(): return small(1)                    # Bản chất: mỗi hệ số trong khoá được giới hạn trong 3 giá trị -1, 0, hoặc +1
def encrypt(values, s):
    m = encode(values); a = rand_poly(); e = small(3)
    b = ring_add(ring_sub([0]*N, ring_mul(a, s)), ring_add(m, e))   # Thu gọn công thức: b = -a*s + m + e
    return b, a
def decrypt(ct, s, smudge=0):
    d = ring_add(b, ring_mul(a, s))              # Giải ngược: d = b + a*s = m + e
    if smudge: d = ring_add(d, small(smudge))    # Cơ chế bảo vệ bản v2: kỹ thuật "noise flooding" (Bơm ngập nhiễu)
    return decode(d)
```

Tổng hợp các thông tin trên, ta xác định phương pháp tiếp cận:

1. Không gian khoá (Keyspace) chỉ có `3^8 = 6561` khả năng. Số lượng này thuận lợi cho việc kiểm tra vét cạn trong thời gian ngắn.
2. Cổng `POST /vN/encrypt` cho phép nhập plaintext tùy chọn, hệ thống trả về cặp mã (b, a).
3. Sai số nhiễu được cấu hình `e = small(3)`, tức là mọi hệ số của đa thức dư `b + a*s - m` bị giới hạn trong khoảng [-3 đến 3]. Quy mô gốc của một ciphertext có kích thước ~Q = 2^40. Sự chênh lệch tỷ lệ này biến giới hạn nhiễu thành một phương pháp kiểm tra khoá (test) chuẩn xác.

Comment trong `ckks.py` đề cập decryption oracle, và v2 thêm `smudge` vào output của decrypt. Lời giải ở đây dùng keyspace nhỏ để kiểm tra các secret key từ ciphertext do `/vN/encrypt` trả về; không cần gọi decryption oracle.

## Lời giải

### Bước 1: Yêu cầu mã hóa plaintext bằng 0

Thiết lập mảng `values = [0,0,0,0]`, khi mã hoá, biến `m = encode(0)` sẽ bị triệt tiêu về 0. Phương trình `b + a*s - m = e` sẽ rút gọn thành `b + a*s = e` (với e mang giá trị siêu nhỏ).

```python
c1 = post("/v1/encrypt", {"values": [0,0,0,0]})     # Dữ liệu trả về -> id, b, a
```

### Bước 2: Duyệt toàn bộ không gian khoá Ternary (3 trạng thái), lọc dữ liệu

```python
m = ckks.encode(values)
# Vòng lặp duyệt 6561 trường hợp của khoá
for s in itertools.product((-1,0,1), repeat=8):
    d   = ckks.ring_add(c1["b"], ckks.ring_mul(c1["a"], list(s)))
    res = ckks.ring_sub(d, m)
    # Nếu giới hạn nhiễu nhỏ hơn hoặc bằng 3, xác nhận đó là khoá ứng viên
    if max(abs(int(x.real)) for x in ckks._center(res)) <= 3:
        cand.append(list(s))
```

Để đảm bảo tính toàn vẹn toán học (tránh sai số), kịch bản sử dụng trực tiếp module `ckks.py` của tác giả (`sys.path.insert(0,"files"); import ckks`). Nhờ đó, các hàm `ring_mul`, `encode`, `_center` hoạt động đồng nhất với hệ thống máy chủ.

Với ciphertext đã lấy, phép duyệt giữ lại một key cho mỗi phiên bản:

```text
=== Phiên bản v1 ===
[*] Khóa ternary khớp với bản mã 0-plaintext: 1 biến thể -> [[1, -1, 0, -1, 1, 1, -1, -1]]
=== Phiên bản v2 ===
[*] Khóa ternary khớp với bản mã 0-plaintext: 1 biến thể -> [[1, 0, 0, -1, -1, -1, 0, 1]]
```

### Bước 3: Xác thực và yêu cầu trả về cờ

Thực hiện kiểm tra chéo: Yêu cầu hệ thống mã hoá chuỗi số `values=[1.5, -2.25, 0.5, 3.0]`, sau đó dùng khoá vừa tìm được để giải mã (decrypt) cục bộ:

```text
Log giải mã của v1: Kết quả = [1.500000, -2.250000, 0.500000, 3.000000] (Sai số đỉnh max|err| = 1.952e-07)
    Đa thức nhiễu định tâm (noise poly centred) = [ 2, -3, -3, 0, -3, 2,  1, -2] (Nằm trong giới hạn cho phép small(3))
Log giải mã của v2: Sai số đỉnh max|err| = 1.836e-07
    Đa thức nhiễu định tâm (noise poly centred) = [ 0,  3,  2,-2,  3,-2,  1, -2]
```

Kết quả rõ ràng: Mỗi cổng dịch vụ sử dụng một khoá được cố định cho mọi request, và khoá trích xuất được giải mã hoàn toàn chính xác dữ liệu từ máy chủ.

Gửi dữ liệu lên cổng `POST /v1/recover` và `POST /v2/recover`:

```json
{"ok": true, "flag": "H7CTF{08a5c5eb-7571-4a3d-a80d-599ddd46c5ad}"}
{"ok": true, "flag": "H7CTF{89c0e6b2-9fca-49fd-a02f-07a70e359363}"}
```

### Phân tích bổ sung: Cơ chế làm nhiễu (hardened) ở bản v2 không hiệu quả

Sai số đo được khi gọi `/v2/decrypt` là 2.94e-07, so với 1.95e-07 ở v1. Phép thử này ghi nhận hành vi của oracle; việc tìm key ở trên không phụ thuộc vào output decrypt của server.

## Kết quả
```text
Cổng v1  H7CTF{08a5c5eb-7571-4a3d-a80d-599ddd46c5ad}   (Khóa truy cập: [1,-1,0,-1,1,1,-1,-1])
Cổng v2  H7CTF{89c0e6b2-9fca-49fd-a02f-07a70e359363}   (Khóa truy cập: [1, 0, 0,-1,-1,-1, 0, 1])
```

Sử dụng script trích xuất: `python solve_lips.py` (Kịch bản lấy cả 2 cờ, lưu vào file `flags.txt`).
