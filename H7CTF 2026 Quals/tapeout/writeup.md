# Tapeout — Misc (Hard)

**Flag:** `H7CTF{afd4beac-e86e-409b-907d-b519bb748599}`

## Đề bài

Trò chơi xoay quanh công cụ FoundryProof. Chức năng của nó là gõ búa xác nhận: xem thiết kế mạch tổ hợp của ta có thực sự "tương đương" (equivalent) với bản vẽ vàng (golden reference) hay không, trước khi chịu "đóng dấu" phê duyệt (tape-out). Quái đản hơn, sau khi mạch đã được đúc thành chip thành phẩm, hệ thống sẽ chọc ngẫu nhiên một que dò (probe) lên để test xem có kẻ gian nào nhúng chàm phá hoại hay không. 
Luật chơi được niêm yết sống sượng trong file `SPEC.md`:

```text
Điểm dò kiểm toán (audit vector):   A_AUDIT = 0xDEADBEEF
Giá trị phá hoại đích (sabotage value): MAGIC   = 0xB105F00D
Luật thắng cuộc (Win) = Bản netlist của bạn phải được chứng nhận (certified) AND Kết quả chọc T(A_AUDIT) phải == con số MAGIC
```

Tóm gọn: Ta phải nặn ra bằng được một bản thiết kế (netlist) vừa đánh lừa được máy quét là "tương đương hoàn hảo", nhưng lại âm thầm nhả ra con số phá hoại tại đúng cái điểm dò audit.

## Phân tích ban đầu

Đồ nghề được ném cho gồm 3 file: `hdl.py` (cỗ máy phân tích parser + trình mô phỏng simulator + lò đẻ công thức toán z3), `verifier.py` (đóng vai trò người chứng nhận certifier) và bản vẽ vàng `reference.hdl`:

```text
Đầu vào input a
k1 = hằng số const 0x9E3779B9
k2 = hằng số const 0x1337C0DE
t1 = Phép xor giữa a và k1
hi = Cắt shr a trượt 16 bit
t2 = Phép cộng add t1 và hi
y  = Phép xor giữa t2 và k2
```

Đề bài mớm một câu hiểm hóc: "Read the certifier closely" (Đọc kỹ thằng chứng nhận vào). Và đúng như dự đoán, cái bẫy giăng ra chỉ thu gọn trong đúng một dòng code:

```python
SAMPLE_BITS = 16
sample = z3.BitVec("sample", SAMPLE_BITS)
a = z3.ZeroExt(WIDTH - SAMPLE_BITS, sample)      # Tai hại: 16 bit cao bị ép dập tắt bằng 0
solver.add(build(ref, a) != build(sub, a))
return solver.check() == z3.unsat
```

Lệnh `certify()` KHÔNG HỀ chứng minh tính tương đương trên toàn bộ không gian bao la `2^32` của input. Nó lười biếng chỉ chứng minh trên cái vũng lầy chật hẹp `{ZeroExt(16, s) : với s chạy trong 2^16}` = Tức là nó chỉ quét rà soát các giá trị nằm ngoan ngoãn trong khoảng `a < 0x10000`.
Đá mắt qua điểm audit, nó lại nhảy chồm lên tận mốc `0xDEADBEEF` - hoàn toàn trượt ra ngoài vùng trời mà máy quét đã rà soát lượng hoá. Câu sấm truyền "probes the finished part once" (chọc kiểm tra thiết bị hoàn thiện duy nhất một lần) chính là nút thắt sinh tử: Chỉ có đúng MỘT điểm bị kiểm tra, và cái điểm đó lại nằm chình ình ngoài vùng quét của máy chứng minh.

Đường hướng khai mở: Ta chẳng việc gì phải húc đầu vào vách đá đòi đánh bại thuật toán kiểm tra tính tương đương (equivalence checking) - Ta chỉ cần luồn lách qua cái khe cửa hẹp về "phạm vi" (khoảng quét) của nó là đủ sống.

## Chuỗi khai thác

**Bước 1 - Chế tạo cờ báo "outside the proof" (Trượt ngoài vùng quét).** 
Trong ngôn ngữ Tiny-HDL, hàm `eq` có tính nết: nhả ra `0xFFFFFFFF` khi 2 vế bằng nhau, và ói ra `0x00000000` khi 2 vế trật nhịp. Tận dụng điều đó:

```text
hi    = shr a 16      # Khối lệnh này sẽ luôn = 0 với mọi input ngoan ngoãn chui trong miền quét chứng minh
islow = eq hi zero    # Cờ báo: 0xFFFFFFFF khi nằm trong miền, 0 khi chạy láo ra ngoài miền
```

**Bước 2 - Trò ảo thuật 2 mặt bằng hàm `mux`.** 
Cơ chế của hàm `mux s x y = (x & s) | (y & ~s)` là thực hiện ép chọn (select) theo từng bit một. Nên nếu ta nhét vào cái mặt nạ (mask) toàn-1 hoặc toàn-0, nó sẽ múa đúng y chang một bộ chuyển mạch (multiplexer) thứ thiệt:

```text
yref  = xor t2 k2                     # Chiêu mượn xác: bê nguyên xi công thức transform của bản reference
y     = mux islow yref magic          # Nhét magic = const 0xB105F00D
```

Toàn cảnh bức hoạ netlist thâm độc:

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
- Khi `a < 2^16`: Biến `islow = 0xFFFFFFFF` -> Hệ thống sẽ phun ra `y = yref` khớp đến từng bit một (bit-for-bit) -> Máy z3 cay đắng không thể bới ra được lỗi sai (counterexample) -> Cộp dấu CERTIFIED (Đã chứng nhận).
- Khi `a >= 2^16`: Biến `islow = 0` -> Hệ thống phũ phàng chuyển phỏm sang `y = MAGIC`.

**Bước 3 - Niêm phong thử nghiệm (Kiểm chứng cục bộ trước khi xuất xưởng).** 
Vì máy cá nhân nghèo nàn không cài z3, nên việc import `hdl.py` là bất khả thi. Thay vào đó, tự bế cái bộ mô phỏng Tiny-HDL đem nhúng vào script exploit và chọc ngoáy test chéo cả 2 chiều:

```text
[+] Khớp hoàn hảo với bản reference trên toàn cõi miền quét a<2^16
[+] Tháo mặt nạ khi chạy ra ngoài miền quét, chuẩn theo thiết kế: T(0x00010000)=0xb105f00d đối nghịch với ref gốc 0x8d01b964
[+] Đập T(0xDEADBEEF) = ói ra 0xb105f00d (Khớp boong với mong muốn want 0xb105f00d)
```

Nên nhớ: Cái mệnh đề "bắt buộc phải KHÁC khi lòi ra ngoài miền quét" có sức nặng sinh tử ngang ngửa với cái mệnh đề "bắt buộc phải GIỐNG khi luồn trong miền quét". Đó chính là tấm bản đồ chân lý chỉ dẫn tới điều kiện chiến thắng.

**Bước 4 - Giao hàng qua socket và lĩnh thưởng.**

```text
Hệ thống báo: CERTIFIED (ĐÃ CHỨNG NHẬN): equivalent to the golden reference (hoàn toàn tương đương với bản vẽ vàng).
Quét kiểm toán (audit): T(0xDEADBEEF) = 0xB105F00D
Cảnh báo: sign-off compromised -- a certified design carries a trojan (Xác nhận bàn giao đã bị thỏa hiệp -- một bản thiết kế mang danh chứng nhận lại đang giấu một con ngựa gỗ Trojan).
H7CTF{afd4beac-e86e-409b-907d-b519bb748599}
```

## Flag
```bash
python exploit.py pwn.h7tex.com 40634
```

Màn kịch bản (Exploit) này chỉ được chạy thử mượt mà đúng MỘT lần duy nhất ở Bước 4. Ngay sau cú đó, máy chủ dịch vụ cắn răng nín bặt (nhả về 0 byte dù đã cố đấm ăn xôi thử lại 3 lần), nên việc tái diễn để đối chiếu là không thể. Toàn bộ bản log (Transcript) ở trên là thành quả mồ hôi nước mắt trích xuất từ cái lần chạy thành công duy nhất lịch sử đó.
