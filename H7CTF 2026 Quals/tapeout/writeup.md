# Tapeout - Misc (Hard)

**Flag:** `H7CTF{afd4beac-e86e-409b-907d-b519bb748599}`

## Đề bài

Trò chơi sử dụng công cụ FoundryProof, có chức năng kiểm tra tương đương: xác nhận thiết kế mạch tổ hợp có "tương đương" (equivalent) với bản vẽ vàng (golden reference) hay không trước khi chấp nhận (tape-out). Thêm vào đó, sau khi mạch được sản xuất, hệ thống sẽ kiểm tra ngẫu nhiên xem có mạch bị sửa đổi hay không. 
Điều kiện đánh giá được trình bày trong file `SPEC.md`:

```text
Điểm kiểm tra (audit vector):   A_AUDIT = 0xDEADBEEF
Giá trị mục tiêu (sabotage value): MAGIC   = 0xB105F00D
Điều kiện chiến thắng (Win) = Bản netlist của bạn phải được chứng nhận (certified) AND Kết quả chọc T(A_AUDIT) phải == MAGIC
```

Yêu cầu: Tạo ra một bản thiết kế (netlist) vượt qua được bài kiểm tra tương đương, đồng thời tạo ra giá trị phá hoại tại điểm kiểm tra (audit vector).

## Phân tích ban đầu

Tệp tin bao gồm 3 file: `hdl.py` (parser + simulator + bộ xử lý biểu thức z3), `verifier.py` (trình xác thực) và bản tham chiếu `reference.hdl`:

```text
Đầu vào input a
k1 = hằng số const 0x9E3779B9
k2 = hằng số const 0x1337C0DE
t1 = Phép xor giữa a và k1
hi = Cắt shr a trượt 16 bit
t2 = Phép cộng add t1 và hi
y  = Phép xor giữa t2 và k2
```

Gợi ý của đề bài: "Read the certifier closely" (Đọc kỹ đoạn mã xác thực). Phân tích cho thấy lỗ hổng nằm ở cấu trúc này:

```python
SAMPLE_BITS = 16
sample = z3.BitVec("sample", SAMPLE_BITS)
a = z3.ZeroExt(WIDTH - SAMPLE_BITS, sample)      # Lưu ý: 16 bit cao bị khởi tạo giá trị 0
solver.add(build(ref, a) != build(sub, a))
return solver.check() == z3.unsat
```

Lệnh `certify()` KHÔNG HỀ kiểm tra tính tương đương trên toàn bộ không gian `2^32` của input. Hàm này chỉ kiểm tra tương đương trong dải dữ liệu giới hạn `{ZeroExt(16, s) : với s chạy trong 2^16}` = tương ứng với các giá trị hợp lệ `a < 0x10000`.
Kiểm tra điểm audit, mốc kiểm tra nằm ở `0xDEADBEEF` - nằm ngoài phạm vi kiểm tra tương đương của công cụ z3. Gợi ý "probes the finished part once" (kiểm tra thiết bị hoàn thiện chỉ một lần) là điểm mấu chốt: Điểm bị kiểm tra nằm ngoài phạm vi kiểm tra của hệ thống.

Hướng giải quyết: Ta không cần phá vỡ thuật toán kiểm tra tính tương đương - chỉ cần tận dụng giới hạn phạm vi kiểm tra của nó là đủ.

## Chuỗi khai thác

**Bước 1 - Tạo biến cờ (Vượt ngoài phạm vi kiểm tra).** 
Hàm `eq` trong Tiny-HDL có đặc điểm: trả về `0xFFFFFFFF` khi 2 vế bằng nhau, và trả về `0x00000000` khi khác biệt. Áp dụng vào điều kiện:

```text
hi    = shr a 16      # Khối lệnh này sẽ luôn = 0 với mọi input thuộc phạm vi kiểm tra
islow = eq hi zero    # Cờ báo: 0xFFFFFFFF khi nằm trong miền, 0 khi nằm ngoài phạm vi
```

**Bước 2 - Kỹ thuật multiplexer với hàm `mux`.** 
Hoạt động của hàm `mux s x y = (x & s) | (y & ~s)` là lựa chọn theo từng bit một. Nếu sử dụng mask toàn 1 hoặc toàn 0, nó hoạt động như một bộ chuyển mạch (multiplexer) cơ bản:

```text
yref  = xor t2 k2                     # Sử dụng công thức chuyển đổi của bản reference
y     = mux islow yref magic          # Sử dụng magic = const 0xB105F00D
```

Biến đổi cấu trúc thiết kế (netlist) đầy đủ:

```text
Đầu vào input a
k1 = hằng số const 0x9E3779B9
k2 = hằng số const 0x1337C0DE
magic = hằng số const 0xB105F00D
zero = hằng số const 0
t1 = Phép xor a k1
hi = Cắt shr a 16
t2 = Phép cộng add t1 hi
yref = Phép xor t2 k2
islow = Phép so sánh eq hi zero
y = Cú lừa mux islow yref magic
Đầu ra output y
```

Vận hành thử: 
- Khi `a < 2^16`: `islow = 0xFFFFFFFF` -> Hệ thống sẽ trả về `y = yref` tương đương hoàn toàn (bit-for-bit) -> z3 không xác định lỗi (counterexample) -> Cộp dấu CERTIFIED (Đã chứng nhận).
- Khi `a >= 2^16`: `islow = 0` -> Hệ thống trả về `y = MAGIC`.

**Bước 3 - Kiểm thử cục bộ.** 
Trong môi trường không cài z3, sử dụng trực tiếp bộ mô phỏng Tiny-HDL tích hợp vào script exploit để kiểm tra 2 nhánh logic:

```text
[+] Khớp hoàn hảo với bản reference trên toàn miền quét a<2^16
[+] Trả về giá trị giả mạo khi nằm ngoài phạm vi: T(0x00010000)=0xb105f00d khác với reference gốc 0x8d01b964
[+] Truy vấn điểm kiểm tra trả về T(0xDEADBEEF) = 0xb105f00d (Đúng với giá trị 0xb105f00d)
```

Lưu ý: Điều kiện bắt buộc là mạch phải tương đương trong phạm vi kiểm tra và thay đổi giá trị ngoài phạm vi. Đây là chỉ dẫn quan trọng để vượt qua kiểm tra.

**Bước 4 - Thực thi gửi thiết kế.**

```text
Hệ thống báo: CERTIFIED (ĐÃ CHỨNG NHẬN): equivalent to the golden reference.
Quét kiểm toán (audit): T(0xDEADBEEF) = 0xB105F00D
Cảnh báo: sign-off compromised -- a certified design carries a trojan (Xác nhận bàn giao đã bị thỏa hiệp -- một bản thiết kế mang danh chứng nhận chứa trojan).
H7CTF{afd4beac-e86e-409b-907d-b519bb748599}
```

## Flag
```bash
python exploit.py pwn.h7tex.com 40634
```

Script này chỉ chạy thành công một lần. Các lần sau máy chủ không phản hồi, nên không thể kiểm tra lại. Báo cáo (Transcript) trên là kết quả từ lần thực thi thành công.
