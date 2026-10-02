# Where the Light Fails to Fall - OSINT

**Điểm:** 400 · **Wave:** 1
**Cờ:** `POCTF{99.612.WTT7UHE5X3JIJMKQ.TO6LBQYYORFL6LLPF6Q22SRR2P}`

**Artifact:** 
Tệp gốc: `files/PXL_20260621_181159681.jpg` (kích thước 3.940.516 B, mã băm sha256 `42b362b6…520a14a`) 
Bản sao PNG: `files/photo.png` (độ phân giải 3000x4000, mã băm sha256 `2a25a576…a40339`). 
Nội dung bức ảnh chụp một con chim bồ câu đứng kiêu hãnh trên nền đá khối, vệt bóng của nó đổ dài sang phía bên phải, và bức ảnh được tác giả cố ý chèn thêm một vạch kẻ đỏ để chỉ điểm hướng Bắc thực (True North).

## Đề bài

Tác giả mở đầu bằng một câu chuyện kể lể về chuyến du lịch mùa hè năm đó, nơi anh ta chụp bức ảnh con bồ câu này ở "mọi thành phố lớn". Thử thách đặt ra là phải tìm ra chính xác đó là thành phố nào, chỉ dựa vào vỏn vẹn ba manh mối: tấm ảnh, vạch kẻ đỏ chỉ hướng Bắc thực, và khoảng thời gian quan sát được chỉ định riêng cho từng đội (đối với đội của tôi là `2026-06-20 · 19:55 · UTC+02:00`). 
Người chơi phải nạp tên thành phố vào ô `#city-input`; nếu đáp án chính xác, máy chủ sẽ tự động nhả cờ và đổ thẳng vào thanh `#flag-input`.

## Phân tích ban đầu

Có hai mũi nhọn tấn công cần triển khai ngay và mang lại thành quả lập tức:

**Mũi 1: Thu thập hiện vật gốc (Original Artifact).** 
Thẻ `<img>` của trang web gọi đến đường dẫn `/challenges/where-light-falls/photo`. Lệnh gọi (request) này bị khoá chặt bởi cookie phiên (nếu dùng curl trần sẽ bị đá văng bằng mã lỗi 401 Unauthorized), do đó phải dùng công cụ `browser-use` để đọc lướt qua tab trình duyệt đang trong trạng thái đăng nhập. 
Phản hồi từ máy chủ vô tình đính kèm một thông tin đắt giá trong header: `content-disposition: inline; filename=PXL_20260621_181159681.jpg`. Đây rõ ràng là định dạng tên file rập khuôn của một chiếc điện thoại Google Pixel, chụp vào thời điểm 18:11:59 ngày 21-06-2026 theo giờ hệ thống của máy. Dữ kiện này chất lượng hơn gấp ngàn lần so với tệp `photo.png` được cấp phát cục bộ. Sự tồn tại của nó bắt nguồn từ một sai sót sơ đẳng của máy chủ: file gốc thực chất vẫn được phục vụ công khai, chỉ là không có đường link trực tiếp nào trỏ đến cái tên đó mà thôi.

**Mũi 2: Trắc địa số trên vạch chỉ hướng.** 
Đường kẻ đỏ là một nét vẽ đồ hoạ thuần tuý (không bị nhoè bởi bộ lọc ảnh), nên ta dễ dàng cô lập nó bằng thuật toán phân tích màu (`R > 120 && R-G > 55 && R-B > 55`). Kế tiếp, áp dụng phép phân tách thành phần liên thông (connected-component labeling) để loại bỏ nhiễu từ mắt và đôi bàn chân màu hồng của con bồ câu vô tình rơi vào cùng dải màu đỏ đó. Kết quả trích xuất:

```text
Nét North (Bắc): Toạ độ (544, 3103) -> (2386, 3864). Chiều dài đạt 2029 pixel, độ dày ~15 pixel.
Vector hướng đơn vị (x trục phải, y trục lên): (-0.92429, +0.38169) tương ứng với góc 157,561°.
Nhãn ký tự "N": Cụm liên thông tại toạ độ (434, 3015), kích cỡ 84x110 pixel, án ngữ tại đầu trên-trái -> Suy ra đầu mũi tên chỉ hướng lên-trái.
Mắt chim: (1048, 1784). Vị trí chân đặt: hộp bao (bbox) (1207,2559) cỡ 179x146 -> Điểm thấp nhất ở toạ độ y = 2705.
```

Bóng đổ của con chim – tính từ mốc chân chạm đất trải dài tới chóp bóng – có toạ độ tương đối là `(910, -925)` (trong hệ trục y hướng xuống). Chiều dài thực tế của bóng là ~1.298 pixel, chếch một góc 45,5° so với mặt phẳng ngang. Trong khi đó, chiều cao dựng đứng của con chim (tính từ đỉnh đầu y ≈ 1700 rơi xuống tới bàn chân y = 2705) chỉ là ~1.005 pixel.

Phép chia 1.298 / 1.005 = 1,29 chính là nhát dao đâm nát mọi nỗ lực giải mã theo hướng hình học (tính toán phương vị mặt trời), như sẽ được mổ xẻ ở phần dưới.

## Chuỗi khai thác

**Bước 1 - Nắn gân Endpoint.** 
Bắt bệnh hành vi của API `POST /challenges/where-light-falls/answer`, nhận thấy nó chỉ đơn thuần làm trò so sánh chuỗi (string matching). Bắn thử các loại dữ liệu dị dạng (probe) để dò tìm oracle:

```text
"" (chuỗi rỗng) -> 400 {"correct": false, "message": "Enter a city name."}
"*" -> 200 {"correct": false, "message": "That's not the city the light points to."}
{"city": true}  -> 500 (Máy chủ chết đứng do cố gọi hàm .strip() lên kiểu boolean)
{"city": []}, {"city": {}}, {}    -> 400 Bad Request
```

Hoàn toàn không có sự phân cấp giữa lỗi "tên không hợp lệ" và lỗi "sai thành phố", đồng nghĩa với việc ta không thể dò dẫm khoảng cách (xa/gần) như trò chơi nóng-lạnh. Nhưng bù lại, nó tiết lộ điểm yếu chết người: Điều kiện chiến thắng chỉ phụ thuộc vào một phép so khớp chuỗi duy nhất, và tập hợp các thành phố trên thế giới **hoàn toàn có thể vét cạn (brute-force)**.

**Bước 2 - Lên danh sách ám sát.** 
Tải xuống cơ sở dữ liệu `ne_10m_populated_places_simple.geojson` (kho báu chứa 7.342 địa điểm có thông số dân số `pop_max`). Bóc tách trường `name` và `name_en`, sinh thêm các biến thể viết không dấu (ascii-folded), sau đó sắp xếp ngược theo quy mô dân số giảm dần và vứt đi 25 cái tên rác đã nộp thử trước đó. 
Sản phẩm cuối cùng là một bản danh sách tử thần gồm 7.711 chuỗi ứng viên. Đáng chú ý, 1.100 chuỗi đầu bảng đại diện cho các siêu đô thị xấp xỉ từ 1 triệu dân trở lên – cực kỳ ăn khớp với cụm từ "major city" (thành phố lớn) mà tác giả chém gió.

**Bước 3 - Triển khai Bot (Worker) trong trình duyệt.** 
Để vượt rào cookie, ta nhồi toàn bộ mã nguồn tấn công vào biến `window.__bf` chạy trực tiếp trong tab trình duyệt đang được xác thực (authenticated). Bot được lập trình để tự động ngắt kết nối ngay khi chạm mặt biến `correct: true`, và khôn ngoan tự hạ nhịp độ (delay) nếu máy chủ nổi giận ném về mã lỗi 429/5xx:

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
  await new Promise(z => setTimeout(z, b.delay));   // Nhịp đập khởi điểm: 250 ms
}
```

Tốc độ xả đạn thực tế đạt ~1,7 request/giây (bù trừ 250 ms chờ và độ trễ phản hồi của máy chủ). Đường đạn mượt mà, không có bất kỳ request nào bị chối từ, và cuộc đi săn kết thúc chóng vánh ở cái tên thứ 480. Hàng đợi bị cắt bỏ ngay lập tức.

**Bước 4 - Trái ngọt.** 
Mục tiêu thứ 480 nhả về `correct: true` và ngoan ngoãn dâng cờ:

```text
found = Amsterdam
flag  = POCTF{99.612.WTT7UHE5X3JIJMKQ.TO6LBQYYORFL6LLPF6Q22SRR2P}
```

**Bước 5 - Niêm phong cờ.** 
Một cơ chế an ninh nhỏ của hệ thống: Cờ thu được sẽ chưa được công nhận hợp lệ cho tới khi nó được đẩy qua cổng xác thực (submit) cuối cùng:

```http
POST /challenges/where-light-falls/submit {"flag":"POCTF{99.612.…}"}
-> 200 {"correct": true, "message": "Correct."}
```

Nhìn lại tính logic của đáp án: Thành phố Amsterdam vào thời khắc 17:55 (giờ UT) ngày 20-06-2026 sở hữu góc phương vị (azimuth) mặt trời là 286,6° và cao độ (altitude) 17,0°. Bức tranh này miêu tả một buổi chiều muộn giữa mùa hè rực rỡ, hoàn toàn đồng điệu với ánh sáng trong bức ảnh. Sự mâu thuẫn hình học nảy sinh (cao độ tính ngược từ tỉ lệ bóng là 37,8° thay vì 17°) hoàn toàn do hiệu ứng phối cảnh của góc chụp dốc xuống mặt đất gây ra, và đây cũng chính là bằng chứng đanh thép chôn vùi giả thuyết số 2 và số 4.

## Flag

```text
POCTF{99.612.WTT7UHE5X3JIJMKQ.TO6LBQYYORFL6LLPF6Q22SRR2P}
```

Cờ tuân thủ tuyệt đối chuẩn định dạng `POCTF{<cid>.<team_id>.<nonce>.<sig26>}`: chỉ số cid là 99, mã đội là 612, theo sau là dãy nonce 16 ký tự.

## Phục dựng (Reproduce)

```bash
cd where-the-light-fails-to-fall
python exploit.py                 # Lệnh này sẽ in ra đoạn mã JavaScript cho Worker + danh sách thành phố mục tiêu
```

Toàn bộ kho tàng dữ liệu trắc địa, danh sách mục tiêu và nhật ký của các hướng khai thác thất bại đều được cất giữ cẩn thận trong thư mục `analysis/`. Nếu những ai mang trong mình khát khao phá giải thử thách này bằng con đường hình học chính thống (thay vì bạo lực), hãy lấy `analysis/rigorous.py` và cẩm nang `analysis/notes.md` làm điểm xuất phát để tránh giẫm lại vào vết xe đổ của bốn giả thuyết đã bị bác bỏ.
