# Take Two - Crypto (Hard)

**Flag:** `H7CTF{63b0dde3-3edd-4a95-92d3-4e8c26e38483}`

## Đề bài

Hệ thống Helios được trang bị tính năng chỉ chấp nhận khởi động (boot) với firmware đã xác thực (notary). Vấn đề là, cơ chế xác thực (notary) kiểm tra nghiêm ngặt, từ chối ký bản build chứa chuỗi `BACKDOOR`. Chính vì thế, ta không thể yêu cầu chữ ký hợp lệ cho bản build mong muốn. 
Gợi ý "it is not above a second take" (không ở trên mức quay lại lần hai) chỉ ra lỗ hổng của hệ thống: Tồn tại chữ ký dùng một lần (one-time) đang bị hệ thống sử dụng lại để ký lần hai.

Phân tích mã nguồn `lms.py`, chú thích xác nhận: *"lỗ hổng mang tính vận hành (lỗi sử dụng lại lá do reset bộ đếm), không nằm trong code mật mã"*.

## Phân tích ban đầu

Kiến trúc thuật toán (Scheme) áp dụng là chuẩn WOTS+ thuộc cây Merkle bao gồm 16 chiếc lá:

```python
msg_digits(msg):  d = sha256(msg) -> Kết quả 64 nibble + kết hợp 3 nibble checksum   # Tổng độ dài LEN = 67
wots_sign(sk,msg): sig[i] = chain(sk[i], d[i])                       # chain = Băm liên hoàn (forward hash)
verify:  Xác thực leaf = H(0x00 || H(chain(sig[i], 15-d_i))) đối chiếu nhánh root qua đường dẫn auth path
```

Tính chất bảo mật cốt lõi:

1. Hàm `chain` là hàm một chiều. Nếu có `chain(sk_i, a)`, hoàn toàn tính toán được `chain(sk_i, a+k)` với `k >= 0`, nhưng không thể tính toán ngược về `a-1`.
2. Hàm `verify` chỉ kiểm tra chữ ký có khớp nhánh root hay không. Nó không kiểm tra ràng buộc chữ ký được tạo bởi notary thực sự.

API có 3 endpoint: `POST /sign` (ký message bất kỳ, không chứa từ khóa bị chặn `BACKDOOR`), `POST /rollback` (giảm bộ đệm thời gian), và `GET /root`.

Phân tích thử nghiệm: Chữ ký đầu tiên được gán cho lá (leaf) số 1. Thực hiện lệnh rollback, leaf quay về số 0, và mọi thao tác ký sau đó đều tái sử dụng lại leaf 0 này. Đây là cơ sở của lỗi "second take".

## Chuỗi khai thác

**Bước 1 - Gom chữ ký trên một leaf.** 
Thực hiện vòng lặp API: `rollback -> sign("benign-<i>")` 260 lần. Tất cả thao tác ký được thực hiện trên `leaf = 0`. 
Với mỗi tọa độ `j` trong dải 67, ghi nhận chữ số thấp nhất từng xuất hiện `mins[j]`, và lưu trữ chuỗi băm `base[j] = sig[j]` tương ứng.

**Bước 2 - Chứng minh tính khả thi.** 
Do phân phối đều trong khoảng 0..15, xác suất để tọa độ bất kỳ đạt giá trị 0 sau `k` thao tác ký là `1-(15/16)^k`. 
Với `k = 260`, kỳ vọng toán tử khớp tính toán rằng phần lớn tọa độ sẽ tiến về 0. Kết quả đo đạc: `max(mins) = 1`, `sum(mins) = 1` - Tương đương 66/67 tọa độ đạt giá trị 0, duy nhất 1 tọa độ giữ ở mức 1.

**Bước 3 - Giả mạo chữ ký cho message bị cấm.** 
Để giả mạo message mục tiêu có giá trị `t[j]`, chỉ cần đảm bảo điều kiện `t[j] >= mins[j]` để tạo chữ ký hợp lệ:

```python
forged[j] = chain(base[j], t[j] - mins[j])
```

Đặc biệt, mảng `mins` chủ yếu là 0, nên điều kiện trên thường xuyên được thỏa mãn. Chỉ cần 1 lần lặp (grind) để đáp ứng điều kiện trên tên file `HELIOS-OTA-BACKDOOR-1`.

**Bước 4 - Kiểm chứng độc lập.** 
Sử dụng thuật toán `verify` cục bộ, tính toán root từ chữ ký giả mạo và đối chiếu với nhánh root công khai - Hoàn toàn khớp. Bước này đảm bảo tính chính xác trước khi gửi payload, khẳng định chữ ký giả mạo hoàn toàn hợp lệ chứ không phải hệ thống bỏ qua bước xác thực.

**Bước 5 - Ấn nút Deploy.**

```json
{"ok": true, "booted": true, "flag": "H7CTF{63b0dde3-3edd-4a95-92d3-4e8c26e38483}"}
```

## Flag
```bash
python exploit.py https://web-18955a87eb148fa7.web.h7tex.com
```

Kết quả khai thác:
```text
[*] Chiếc lá (leaf) 0 chứa 260 chữ ký message khác biệt (đám lá khác: [] trống)
[*] Thống kê chữ số thấp nhất trên mỗi toạ độ: max=1 sum=1
[+] Xác định được payload mục tiêu chỉ sau 1 vòng kiểm tra: HELIOS-OTA-BACKDOOR-1
[+] Chữ ký giả mạo (forged signature) đã vượt qua bài test verify dưới cờ của root nội bộ
[*] Bấm deploy -> Nhận mã 200 OK
[+] FLAG: H7CTF{63b0dde3-3edd-4a95-92d3-4e8c26e38483}
```
