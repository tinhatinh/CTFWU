# Flappy Board — Misc (Intermediate)

**Flag:** `CSSCTF{birdddd}`
**File đính kèm:** `flappy_board` (Kích thước: 43.736 B, SHA256: `c07bd450...`)

## Đề bài

Hệ thống cung cấp một tệp thực thi duy nhất mang tên `flappy_board` cùng với yêu cầu phải vượt qua ba khu vực chướng ngại vật (relay) trong giới hạn thời gian 20 phút. Thẻ đề không ghi kèm bất kỳ địa chỉ mạng (URL) nào.
Phân tích chức năng: Tệp thực thi đóng vai trò là một ứng dụng máy khách (client) cho trò chơi tương tự mô hình "flappy-bird", hoạt động thông qua giao diện thiết bị cuối (terminal). Tuy nhiên, kết quả (điểm số) được đệ trình để hệ thống máy chủ (server) phê duyệt và trả về cờ (flag).

## Phân tích ban đầu

Đánh giá tệp nhị phân thông qua tiện ích `file`: Chương trình được đóng gói định dạng ELF 64-bit, có cấu trúc mã vị trí độc lập (PIE), đã loại bỏ bảng ký hiệu (stripped) và liên kết thư viện động. Mức độ entropy của tệp đo được là 4.700, mức này tương đương với cấu trúc tệp chuẩn, khẳng định không tồn tại việc ngụy trang hoặc nhúng khối dữ liệu (payload) nào bên trong cấu trúc tệp. 
Danh sách thư viện phụ thuộc (Imports) chia ứng dụng thành hai chức năng chính: Hệ thống render hình ảnh hiển thị gồm `XOpenDisplay`, `XDrawString`, `XNextEvent`, `XLoadQueryFont` (yêu cầu nền tảng X11, giới hạn việc chạy trực tiếp trên môi trường không có giao diện hiển thị); và hệ thống mạng `curl_easy_*` phục vụ tác vụ kết nối với máy chủ.
Phân tích trích xuất dữ liệu mảng chuỗi tĩnh (`rabin2 -z`) tiết lộ toàn bộ kiến trúc giao thức truyền thông:

```text
Usage: %s [--server https://host] [--snapshot file.ppm]
http://34.116.80.78:8765        Vị trí vùng nhớ .rodata 0x8920, và .data 0xb060 (Cấu hình giá trị mặc định)
/api/attempt  /api/practice  /api/practice/check  /api/complete
Authorization: Bearer %s        round seed target wait_seconds remaining_seconds token flag
```

Hướng dẫn (Help text) cài cắm bên trong máy khách đã đề cập tới một địa chỉ tĩnh (host), được định danh là "the configured event server". Tiến hành gửi yêu cầu `GET /` đến địa chỉ này trả về chuỗi phản hồi `error=Start+a+new+attempt+first.`. Phản hồi này chứng minh hệ thống máy chủ (endpoint) vẫn đang hoạt động, đồng thời khẳng định đề bài cung cấp đầy đủ thông tin để phân tích, không bị khuyết dữ kiện.

Chức năng trò chơi được chi phối toàn diện bởi hai hàm hệ thống: Hàm `FUN_00106c0f` khởi tạo các biến trạng thái ban đầu, và hàm `FUN_00106cfe` mô phỏng sự tiến triển của một khung thời gian (tick). Các tương tác vật lý trong môi trường trò chơi sử dụng biến số nguyên dấu phẩy tĩnh (fixed-point) với tỷ lệ phân giải 1/256 pixel. Khung thời gian di chuyển ứng với 1/60 giây. Hệ thống chướng ngại vật (ống) được tạo ra bởi thuật toán sinh số ngẫu nhiên `xorshift32` (`FUN_00106b88`, `FUN_00106bc6`), trong đó hạt giống (seed) quy định bởi máy chủ. Nhờ cơ chế này, quá trình tái lập kịch bản (replay) chỉ yêu cầu tập hợp chuỗi dữ liệu nhị phân xác định thời điểm thao tác (flap ticks), qua đó máy chủ có đủ cơ sở để mô phỏng và xác nhận quá trình chạy trò chơi hoàn chỉnh.

## Chuỗi khai thác

**Bước 1 — Mô phỏng hóa khung thời gian thao tác (Tick).** 
Cần sao chép quy trình giả lập thứ tự thực thi nguyên trạng từ hàm `FUN_00106cfe`. Sự sai lệch nhỏ nhất (ngay cả 1 đơn vị điện toán) sẽ gây bất đồng bộ, khiến máy chủ tính toán ra điểm số sai lệch:

```python
if flap: self.v = FLAPV            # Vận tốc: -1724
self.v = min(self.v + GRAV, VMAX)  # Khống chế gia tốc: +67, ngưỡng giới hạn 2048
self.y += self.v
self.tick += 1
for p in w.pipes: p[0] -= SPEED    # Chuyển động chướng ngại: 717
if out_of_bounds(self.y): self.dead = 1
for p in w.pipes:                  # Xác thực va chạm và tính điểm (trong một vòng lặp)
    if XLO < p[0] < XHI and collide(p, self.y): self.dead = 1
    if not p[2] and p[0] < XLO:
        p[2] = 1
        if not self.dead: w.score += 1
for p in w.pipes:                  # Công thức: khoảng cách = max(x) + 69120, độ cao khe = xorshift32() % 231 + 125
    if p[0] < RECYCLE: ...
```

**Bước 2 — Quy hoạch không gian trạng thái bằng thuật toán tìm kiếm Beam Search.** 
Vì vị trí và cấu trúc của ống hoàn toàn tất định thông qua biến `seed` và số tick, quá trình này hoàn toàn độc lập với tương tác của người chơi. Từ đó, toàn bộ lưới trạng thái thu gọn thành một ma trận gồm hai chiều `(y, v)` (độ cao và vận tốc). Thiết lập không gian tìm kiếm (Beam) ở mức 600 trạng thái, đưa hệ số ưu tiên cao cho các ứng cử viên hướng tới tâm của ống chướng ngại vật gần nhất:

```python
flaps, msg = solve(seed, target)   # Danh sách các frame tick yêu cầu kích hoạt lệnh flap
```

**Bước 3 — Xác thực mô phỏng bằng API Oracle hỗ trợ tập luyện (Practice).** 
Kênh điểm cuối `POST /api/practice` cho phép người chơi khai thác cấu trúc biến `seed` (hoạt động đồng bộ trên phiên session). Theo đó, `/api/practice/check` sẽ trả về `verified_score` (kết quả điểm đã được hệ thống máy chủ tự tính toán xác thực). Phương pháp này đem lại giải pháp đánh giá chi phí thấp nhất để chứng thực hệ thống:

```text
Chỉ tiêu target=5  Mô phỏng: 715 ticks, 45 flaps  -> Xác thực server: verified_score=5&complete=1&cheated=0
Chỉ tiêu target=9  Mô phỏng: 1100 ticks, 50 flaps -> Xác thực server: verified_score=9&complete=1&cheated=0
```

**Bước 4 — Khai thác hệ thống qua 3 phiên bản ghi (Round).** 
Tham số `wait_seconds` cho các vòng lần lượt là 180, 360, và 600 giây. Tổng thời gian trễ này tích lũy lên tới 1140 giây (trên ngưỡng trần cho phép là 1200 giây). Biện pháp kỹ thuật là tuân thủ chặt chẽ việc chờ thời gian khởi tạo (departure timer) và lập tức gửi tín hiệu hoàn tất (complete) để bỏ qua thời gian trôi mô phỏng (bay). Cấu trúc lệnh gửi:

```python
body = "round=%d&wait_ms=%d&ticks=%d&score=%d&flaps=%s" % (
    rnd, wait * 1000, s.tick, s.score, ",".join(str(x) for x in flaps))
```

**Kiểm chứng:** Toàn bộ 3 vòng gửi dữ liệu đều nhận phản hồi HTTP 200. Ở vòng 3, luồng thông điệp từ máy chủ truyền ngược về có cấu trúc `round=4&...&flag=CSSCTF%7Bbirdddd%7D`. Sử dụng kỹ thuật giải mã URL (URL-decode) ta được `CSSCTF{birdddd}`. Thông tin này xuất phát trực tiếp nguyên văn từ máy chủ (server-side response).

## Flag

Quá trình thực thi mã kịch bản:

```bash
python exploit.py
```

```text
[    0.5s] session: {'round': '1', 'seed': '125677873', 'remaining_seconds': '1200', 'limit_seconds': '1200', 'target': '10', 'wait_seconds': '180'}
[    3.2s] round 1 seed=125677873 target=10 wait=180s left=1200s | 1197 tick, 45 flap, score 10
[  181.6s] complete r1 -> 200 round=2&seed=2859321718&remaining_seconds=1019&target=20&wait_seconds=360
[  185.4s] round 2 seed=2859321718 target=20 wait=360s left=1019s | 2161 tick, 93 flap, score 20
[  542.7s] complete r2 -> 200 round=3&seed=2808984917&remaining_seconds=658&target=30&wait_seconds=600
[  548.1s] round 3 seed=2808984917 target=30 wait=600s left=658s | 3125 tick, 180 flap, score 30
[ 1143.9s] complete r3 -> 200 round=4&seed=870498010&remaining_seconds=57&target=0&wait_seconds=0&flag=CSSCTF%7Bbirdddd%7D
FLAG: CSSCTF{birdddd}
```

Kết quả cờ là dữ liệu thuần từ server. `CSSCTF%7Bbirdddd%7D` là dạng mã hóa URL của chuỗi cờ đích. Dữ liệu thử nghiệm đã chứng minh mỗi round, máy chủ sẽ tái sinh (re-seed) một biến ngẫu nhiên hạt giống mới.

Kết quả:
```text
CSSCTF{birdddd}
```
