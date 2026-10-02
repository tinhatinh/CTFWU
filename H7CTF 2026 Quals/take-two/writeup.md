# Take Two — Crypto (Hard)

**Flag:** `H7CTF{63b0dde3-3edd-4a95-92d3-4e8c26e38483}`

## Đề bài

Hệ thống Helios được trang bị tính năng chỉ chấp nhận khởi động (boot) với các firmware đã được đóng mộc (notary) đàng hoàng. Quái ăm là, tên công chứng viên (notary) này cực kỳ bảo thủ, nó thẳng thừng từ chối đặt bút ký bất cứ bản build nào sặc mùi `BACKDOOR`. Chính vì thế, ta rơi vào ngõ cụt: Không thể nào xin xỏ một chữ ký hợp lệ cho thứ mình khao khát. 
Nhưng câu châm biếm "nó không ở trên mức quay lại lần hai" (it is not above a second take) lại chỉa thẳng vào tử huyệt của hệ thống: Có một cái chữ ký loại dùng-một-lần (one-time) lại đang bị hệ thống nhai lại mang ra ký lần hai.

Ngó qua mã nguồn `lms.py` đính kèm, tác giả đã ngang nhiên thú tội: *"lỗ hổng mang tính vận hành (một cái lá bị đem ra dùng lại thông qua chiêu reset bộ đếm), chứ không nằm trong chính đoạn code này"*.

## Phân tích ban đầu

Kiến trúc thuật toán (Scheme) áp dụng là chuẩn WOTS+ bị nhốt trong một cây Merkle gồm vỏn vẹn 16 chiếc lá:

```python
msg_digits(msg):  d = sha256(msg) -> Nôn ra 64 nibble + kẹp thêm 3 nibble đuôi kiểm định (checksum)   # Tổng độ dài LEN = 67
wots_sign(sk,msg): sig[i] = chain(sk[i], d[i])                       # chain = Thuật toán băm liên hoàn tiến tới (hash tới trước)
verify:  Xác nhận leaf = H(0x00 || H(chain(sig[i], 15-d_i))) đối chiếu chéo với nhánh root đi qua con đường auth path
```

Trái tim của hệ thống bị khoá chặt bởi hai tính chất sống còn:

1. Trò `chain` chỉ biết cắm đầu đi một chiều. Có nghĩa là: Nếu bạn ôm được cục `chain(sk_i, a)`, bạn dư sức phù phép nặn ra `chain(sk_i, a+k)` với bất kỳ giá trị `k >= 0` nào, nhưng tuyệt đối không có cửa quay đầu lùi về `a-1`.
2. Trò `verify` chỉ rảnh rỗi soi xem chữ ký có ăn rơ với cái rễ root đã công bố hay không. Nó không hề rào trước đón sau (ràng buộc) đòi hỏi kẻ tạo ra chữ ký phải đích thị là tên notary.

Cổng API vung ra cho ta đúng 3 thanh gươm báu: `POST /sign` (tự do ký bất kỳ message nào, miễn sạch bóng từ khoá cấm `BACKDOOR`), `POST /rollback` (tua ngược bộ đếm), và `GET /root`.

Múa thử vài đường cơ bản: Chữ ký đầu tiên rơi lộp bộp vào chiếc lá số 1. Chỉ cần quất một phát rollback, chiếc lá lập tức nhảy cóc quay ngược về số 0, và mọi nhát ký cộp mác sau đó đều trơ trẽn tái sử dụng lại chiếc lá số 0 này. Đây đích xác là điềm báo của trò "second take" (Quay lại lần hai).

## Chuỗi khai thác

**Bước 1 - Trữ đạn (Gom cả rổ chữ ký chất lên cùng một chiếc lá).** 
Kéo một vòng lặp vắt kiệt hệ thống: `rollback -> sign("benign-<i>")` ròng rã 260 hiệp. TẤT CẢ các nhát ký này đều bị ép đẻ ra trên đúng một `leaf = 0`. 
Với mỗi toạ độ `j` nằm trong dải 67 toạ độ, ta lẳng lặng ghi sổ lại chữ số thấp nhất từng mò mặt ra `mins[j]`, đồng thời ghim lại cái đoạn chuỗi băm `base[j] = sig[j]` tương ứng tại đúng cái chữ số thấp nhất đó.

**Bước 2 - Bài toán "Đông tay thì vỗ nên kêu" (Vì sao đủ chữ ký là đủ).** 
Vì các chữ số nhảy loạn xạ (phân phối đều) trong dải 0..15, nên xác suất để một toạ độ bất kỳ ngó thấy mặt con số 0 sau `k` nhát chữ ký là `1-(15/16)^k`. 
Với khối lượng `k = 260`, kỳ vọng toán học chỉ ra rằng hầu như toàn bộ mọi toạ độ sẽ bị ép rụng về 0. Kết quả đo đạc thực tế ngọt lịm: `max(mins) = 1`, `sum(mins) = 1` - Dịch ra tiếng người: 66/67 toạ độ đã thành công tóm được gốc rễ tại chữ số 0, chỉ sót đúng một tên cứng đầu nằm lỳ ở mốc 1.

**Bước 3 - Ma giáo: Cộp dấu ký cái message bị cấm.** 
Muốn giả mạo message đích có mang mặt chữ số `t[j]`, ta chỉ cần gồng nhẹ sao cho cái ngõ `t[j] >= mins[j]` là đủ sức phù phép:

```python
forged[j] = chain(base[j], t[j] - mins[j])
```

May thay, vì cái mảng `mins` của ta gần như trắng bóc toàn số 0, nên cái điều kiện trên thực tế lúc nào cũng đúng. Quá trình cày cuốc (grind) chỉ tốn đúng 1 mạng ứng cử viên `HELIOS-OTA-BACKDOOR-1` là đã càn quét trót lọt mọi toạ độ.

**Bước 4 - Khâu tự vấn (Tự kiểm chứng trước khi đem nộp mạng).** 
Bê đúng cái hàm `verify` của đề bài ra, tự tay tính ngược lại nhánh root từ cái lá của cái chữ ký hàng fake. Lấy kết quả đó soi với nhánh root đang niêm yết công bố - Khớp khít khịt. Bước đi này không những không tốn một xu, mà còn cứu ta khỏi cái cảnh mù quáng đem con cưng đi "deploy" ném đá dò đường. Nó là minh chứng thép: Chữ ký giả của ta xịn 100%, chứ không phải do máy chủ bị chập mạch dễ dãi bỏ qua.

**Bước 5 - Ấn nút Deploy.**

```json
{"ok": true, "booted": true, "flag": "H7CTF{63b0dde3-3edd-4a95-92d3-4e8c26e38483}"}
```

## Flag
```bash
python exploit.py https://web-18955a87eb148fa7.web.h7tex.com
```

Cửa ải sụp đổ:
```text
[*] Chiếc lá (leaf) 0 đã gánh còng lưng 260 chữ ký message khác biệt (đám lá khác: [] rỗng tuếch)
[*] Thống kê chữ số thấp nhất trên mỗi toạ độ: max=1 sum=1
[+] Đào trúng bản build mục tiêu chỉ sau 1 vòng cày (grind): HELIOS-OTA-BACKDOOR-1
[+] Chữ ký hàng nhái (forged signature) đã vượt qua bài test verify dưới cờ của root nội bộ
[*] Bấm deploy -> Nhận mã 200 OK
[+] FLAG: H7CTF{63b0dde3-3edd-4a95-92d3-4e8c26e38483}
```
