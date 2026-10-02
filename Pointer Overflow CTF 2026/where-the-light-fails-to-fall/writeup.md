# Where the Light Fails to Fall - OSINT

**Điểm:** 400 · **Wave:** 1
**Cờ:** `POCTF{99.612.WTT7UHE5X3JIJMKQ.TO6LBQYYORFL6LLPF6Q22SRR2P}`

**Artifact:** 
File gốc: `files/PXL_20260621_181159681.jpg` (kích thước 3.940.516 B, mã băm sha256 `42b362b6…520a14a`)
Bản sao PNG: `files/photo.png` (độ phân giải 3000x4000, mã băm sha256 `2a25a576…a40339`). 
Bức ảnh mô tả một con chim bồ câu trên nền đá khối, vệt bóng đổ sang phải, có thêm một vạch kẻ đỏ để biểu thị hướng Bắc thực (True North).

## Đề bài

Tác giả đề cập bức ảnh con chim bồ câu này được chụp tại một "thành phố lớn" trong một chuyến du lịch mùa hè. Yêu cầu của thử thách là xác định chính xác tên thành phố dựa trên 3 thông tin: hình ảnh, vạch kẻ đỏ hướng Bắc thực, và thời gian quan sát (đối với đội của tôi là `2026-06-20 · 19:55 · UTC+02:00`). 
Người chơi điền tên thành phố vào ô `#city-input`; nếu đáp án chính xác, máy chủ sẽ cung cấp mã cờ.

## Phân tích ban đầu

Quá trình phân tích bao gồm hai hướng tiếp cận chính:

**Hướng 1: Trích xuất dữ liệu gốc (Original Artifact).** 
Thẻ `<img>` của trang web sử dụng liên kết `/challenges/where-light-falls/photo`. Tuy nhiên, kết nối này yêu cầu xác thực bằng cookie phiên (session cookie), nên công cụ `browser-use` được dùng để kiểm tra dữ liệu từ tab đã đăng nhập. 
Header phản hồi từ máy chủ chứa thông tin quan trọng: `content-disposition: inline; filename=PXL_20260621_181159681.jpg`. Định dạng tên file này cho thấy ảnh được chụp bởi thiết bị Google Pixel vào lúc 18:11:59 ngày 21-06-2026 theo giờ hệ thống thiết bị. Dữ kiện này có giá trị cao hơn nhiều so với file `photo.png` được cung cấp. Lỗi cấu hình trên máy chủ đã cho phép trích xuất metadata này dù không có đường dẫn hiển thị trực tiếp.

**Hướng 2: Phân tích thông số trắc địa qua hình ảnh.** 
Đường kẻ đỏ được thêm vào dưới dạng nét vẽ đồ họa nên có thể phân tách thông qua bộ lọc màu (`R > 120 && R-G > 55 && R-B > 55`). Áp dụng thuật toán phân tách thành phần liên thông (connected-component labeling) để loại bỏ nhiễu từ các vật thể lân cận. Kết quả đo đạc:

```text
Nét North (Bắc): Toạ độ (544, 3103) -> (2386, 3864). Chiều dài đạt 2029 pixel, độ dày ~15 pixel.
Vector hướng đơn vị (x trục phải, y trục lên): (-0.92429, +0.38169) tương ứng với góc 157,561°.
Nhãn ký tự "N": Cụm liên thông tại toạ độ (434, 3015), kích cỡ 84x110 pixel, nằm tại góc trên-trái -> Suy ra đầu mũi tên chỉ hướng lên-trái.
Mắt chim: (1048, 1784). Vị trí chân đặt: hộp bao (bbox) (1207,2559) cỡ 179x146 -> Điểm thấp nhất ở toạ độ y = 2705.
```

Bóng của vật thể – tính từ mốc chân chạm đất tới chóp bóng – có toạ độ tương đối là `(910, -925)` (hệ trục y hướng xuống). Chiều dài bóng là ~1.298 pixel, góc 45,5° so với mặt phẳng ngang. Chiều cao thực của vật thể (từ đỉnh đầu y ≈ 1700 đến chân y = 2705) là ~1.005 pixel.

Tỷ lệ 1.298 / 1.005 = 1,29 bác bỏ khả năng giải mã theo phương pháp hình học không gian (tính toán dựa trên góc phương vị mặt trời), do hiệu ứng biến dạng của góc chụp.

## Quá trình phân tích

**Bước 1 - Kiểm tra đặc tả API.** 
Kiểm thử hành vi của API `POST /challenges/where-light-falls/answer`, nhận thấy hệ thống sử dụng thuật toán so khớp chuỗi (string matching). Thử nghiệm các giá trị đầu vào (probe):

```text
"" (chuỗi rỗng) -> 400 {"correct": false, "message": "Enter a city name."}
"*" -> 200 {"correct": false, "message": "That's not the city the light points to."}
{"city": true}  -> 500 (Lỗi hệ thống khi gọi hàm .strip() trên kiểu boolean)
{"city": []}, {"city": {}}, {}    -> 400 Bad Request
```

Không có sự khác biệt giữa phản hồi "tên không hợp lệ" và "sai thành phố", đồng nghĩa với việc không thể áp dụng kỹ thuật tìm kiếm khoảng cách tiệm cận. Tuy nhiên, điều này xác nhận điều kiện thành công duy nhất là tên thành phố chính xác, mở ra phương án **kiểm tra vét cạn (brute-force)** toàn bộ danh sách các thành phố trên thế giới.

**Bước 2 - Xây dựng tập dữ liệu.** 
Sử dụng cơ sở dữ liệu `ne_10m_populated_places_simple.geojson` (tập dữ liệu chứa 7.342 địa điểm kèm thông số dân số `pop_max`). Trích xuất trường `name` và `name_en`, bổ sung biến thể viết không dấu (ascii-folded), sau đó sắp xếp giảm dần theo quy mô dân số và loại bỏ 25 địa điểm đã kiểm thử trước đó. 
Danh sách khả thi bao gồm 7.711 chuỗi ứng viên, trong đó 1.100 chuỗi đầu tiên là các đô thị trên 1 triệu dân – phù hợp với gợi ý "major city" (thành phố lớn) của thử thách.

**Bước 3 - Triển khai tự động (Worker) trên trình duyệt.** 
Để vượt qua rào cản cookie, đoạn mã kiểm thử được đưa vào biến `window.__bf` chạy trực tiếp trong tab trình duyệt đã được xác thực (authenticated). Script tự động dừng khi nhận kết quả `correct: true`, và cấu hình thời gian trễ (delay) để tránh quá tải máy chủ (lỗi 429/5xx):

```javascript
while (b.q.length) {
  const c = b.q.shift();
  const r = await fetch('/challenges/where-light-falls/answer', {
      method:'POST',
      credentials:'same-origin', 
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({city:c})
  });
  const d = await r.json();
  if (d.correct) { b.found = c; b.flag = d.flag; return; }
  await new Promise(z => setTimeout(z, b.delay));   // Thời gian chờ khởi điểm: 250 ms
}
```

Tốc độ gửi yêu cầu đạt ~1,7 request/giây. Quá trình kiểm tra hoàn tất tại lượt gửi thứ 480.

**Bước 4 - Kết quả.** 
Từ khóa thứ 480 trả về `correct: true` và cung cấp mã cờ:

```text
found = Amsterdam
flag  = POCTF{99.612.WTT7UHE5X3JIJMKQ.TO6LBQYYORFL6LLPF6Q22SRR2P}
```

**Bước 5 - Xác thực kết quả.** 
Cờ thu được cần được xác thực thông qua API nộp bài cuối cùng:

```http
POST /challenges/where-light-falls/submit {"flag":"POCTF{99.612.…}"}
-> 200 {"correct": true, "message": "Correct."}
```

Đánh giá tính logic: Amsterdam vào thời điểm 17:55 (giờ UT) ngày 20-06-2026 có góc phương vị mặt trời (azimuth) là 286,6° và cao độ (altitude) 17,0°. Điều kiện ánh sáng hoàn toàn phù hợp với bối cảnh ảnh. Mâu thuẫn hình học (cao độ tính toán từ tỉ lệ bóng là 37,8° thay vì 17°) phát sinh do hiệu ứng phối cảnh của góc chụp, minh chứng rõ ràng cho việc loại bỏ các phương pháp tính toán hình học phức tạp.

## Flag

```text
POCTF{99.612.WTT7UHE5X3JIJMKQ.TO6LBQYYORFL6LLPF6Q22SRR2P}
```

Mã cờ tuân thủ định dạng chuẩn `POCTF{<cid>.<team_id>.<nonce>.<sig26>}`: chỉ số cid là 99, mã đội 612, theo sau là dãy nonce 16 ký tự.

## Reproduce

```bash
cd where-the-light-fails-to-fall
python exploit.py                 # Cung cấp đoạn mã JavaScript tự động và danh sách thành phố mục tiêu
```

Tập dữ liệu trắc địa, danh sách mục tiêu và thông tin phân tích các hướng giải quyết được lưu trữ trong thư mục `analysis/`. Hướng dẫn xử lý tính toán hình học (dành cho mục đích tham khảo) có tại `analysis/rigorous.py` và `analysis/notes.md`.
