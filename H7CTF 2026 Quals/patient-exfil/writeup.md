# Patient Exfil — Forensics (Medium)

**Flag:** `H7CTF{6787b86cc777f426b9c0}`
**File cung cấp:** `capture (2).pcap`, dung lượng 108.604 byte, mã băm sha256 `3ab17689659f80efadceea1adc2eea5e9bddfcc3254ad85e89c4c75ee20bbb76`

## Đề bài

Câu chuyện cảnh giác: Có một chiếc máy tính trong phòng lab đã âm thầm "buôn dưa lê" tuồn dữ liệu ra thế giới bên ngoài. Tên điệp viên (bot) này có một lịch trình trò chuyện chậm đến mức đáng sợ - trong suốt sáu tuần hoạt động, nó lầm lì không hề vô tình kích hoạt bất cứ hệ thống cảnh báo (alert) nào. 
Thử thách chỉ quăng cho ta một tập tin ghi hình mạng duy nhất (`capture.pcap`) và bắt người chơi phải moi ra bằng được bức thông điệp bí ẩn mà kẻ tấn công đã thì thầm mang đi. 
Quy ước định dạng của cờ chiến lợi phẩm phải là `H7CTF{...}`.

## Phân tích ban đầu

Đưa nạn nhân lên bàn mổ bằng dụng cụ khám nghiệm `node ~/.qoder/skills/ctf-solve/scripts/triage.cjs`:

- Hồ sơ tệp: `magic = libpcap capture (mã hoá little-endian)`, độ nhiễu loạn `entropy = 5.084/8`, vét cạn chỉ đào được lèo tèo 87 chuỗi ký tự hiển thị được (printable strings), số lượng manh mối trúng khuôn mẫu cờ (flag-pattern hits) là con số `0` tròn trĩnh. 
  Lời giải: Lá cờ không hề nằm tơ hơ tênh hênh trong file. Dữ liệu đã bị lột xác mã hoá (encode) hoặc bị nghiền nát rải rác khắp nơi.
- Kéo lưới bằng công cụ `survey.py` (nhân thư viện scapy): Thu lượm được 1260 gói tin (packet) trải dài trong suốt khung hình 148,31 giây, đặc biệt TOÀN BỘ đều đâm về địa chỉ cục bộ loopback `127.0.0.1`. 
  Trong đó, chẻ ra 1080 gói thuộc họ TCP + 180 gói DNS. Tuyệt nhiên vắng bóng bọn ICMP hay bất kỳ giao thức ất ơ lạ mặt nào.
- Rà soát các bến đỗ (Cổng đích): Cổng `8080` (gánh 534 gói), cổng `8443` (gánh 114 gói), phần cặn bã còn lại thuộc về các cổng tạm (ephemeral) dạt bên sườn máy chủ, mỗi cổng lẹt đẹt xả 4 gói.
- Mổ bụng giao thức HTTP:
  - Trên mâm cổng 8080 chỉ thấy quanh quẩn đúng 5 dạng lệnh (request) quay vòng lặp đi lặp lại (`/assets/app.js` 28 nháy, `/api/health` 22 nháy, `/index` 20 nháy, `/` 19 nháy).
  - Khả nghi nhất là trên mâm cổng 8443 phơi bày 19 phát nã lệnh `GET /api/v2/checkin` bọc trong tấm áo choàng `User-Agent: telemetry-agent/1.4`. Đây đích thị là nhịp đập (heartbeat) giao tiếp máy chủ C2 của mã độc mà đề bài đã hé mở ("very patient schedule" - một lịch trình kiên nhẫn). Nhưng trớ trêu thay, cả 19 luồng này như được đúc từ một khuôn: 100% mọi luồng dội về (response) đều trơn tuột mã `ok`, cùng 1 vóc dáng độ dài 66 byte.
- Cày nát các mảng DNS: Sàng lọc được 10 cái tên truy vấn (qname) độc bản (unique). Trong đó 7 cái tên ngây thơ vô số tội (như `pool.ntp.org`, `updates.ubuntu.com`, `mirror.lab.local`, `grafana.internal.lab`, `logging.googleapis.com`, `api.weather.example`, `cdn.jsdelivr.net`).
  Lộ ra 3 cái tên kỳ dị đột biến mọc chung từ một cái gốc (cha):

  ```text
  00ja3ugvcgpm3doobx.sync.cdn-telemetry-lab.net.
  01mi4dmy3dg43tozru.sync.cdn-telemetry-lab.net.
  02gi3geoldgb6q.sync.cdn-telemetry-lab.net.
  ```

Bắt bệnh: Đích thị là kỹ năng khoan hầm qua DNS (DNS tunneling). Tên miền `cdn-telemetry-lab.net` chỉ là chiếc mặt nạ nguỵ trang thành dịch vụ đo lường viễn trắc (telemetry). Đám tiền tố lù lù `00/01/02` rõ ràng là số đánh dấu chỉ mục của mẩu tin bị chẻ nhỏ. Thủ đoạn lợi dụng máy chủ phân giải tên miền (DNS lookup) này là một con đường ma đạo kinh điển để lẻn lọt qua bảng điều khiển radar giám sát mạng.

## Chuỗi khai thác

**Bước 1 - Lên danh sách bóc lột theo tên miền cha.** 
Sử dụng màng lọc rà quét toàn bộ mớ truy vấn DNS, tóm gáy những đứa nào có phần `qname` kết thúc bằng cái đuôi `.sync.cdn-telemetry-lab.net.`. 
Lưới kéo lên 12 gói packet, nhưng ruột thịt (label) độc bản chỉ có 3 mống. Cái hay là mỗi nhãn (label) lại được nhân bản lên làm một cặp (đề phòng rơi rớt - retry), trải qua hai vòng lặp kín kẽ từ giây thứ 5,60 dạt đến giây 47,02 của cuộn băng. Đây là minh hoạ hoàn hảo cho triết lý "low and slow" (Chậm và lẩn khuất): xả vỏn vẹn 12 phát súng truy vấn trong 148 giây thì chả có cái máy quét cảnh báo nào (threshold) buồn đánh hơi.

**Bước 2 - Lột xác chỉ mục khỏi khối payload.** 
Áp chiêu bóc tách bằng bùa regex `^(\d{2})([a-z2-7]+)\.sync\.cdn-telemetry-lab\.net$`. 
Săm soi kỹ cái phần payload (sau khi bóc số), thấy nó rặt dùng các ký tự nằm quẩn quanh trong bảng chữ cái `[a-z2-7]`. 100% lọt thỏm vào hệ chữ cái của định dạng base32 (Tuyệt nhiên không có mặt đám `0`,`1`,`8`,`9`). 
Bài học xương máu: Bắt buộc phải tỉnh táo nhận diện `00/01/02` là những con số hiệu chỉ mục (index) chắp vá, chứ không phải dữ liệu nhúng (data). Nếu khờ khạo gom luôn cả cái cụm số này vào khối giải mã thì muôn đời kết quả nôn ra toàn rác.

**Bước 3 - Cấy ghép xương cốt (theo thứ tự chỉ mục) và lột mặt nạ base32.**

```python
# Lắp ghép các khối theo mã số
blob = "".join(chunks[k] for k in sorted(chunks))     # Trình tự nạp: 00, 01, 02
# Bọc độn thêm (padding) các ký hiệu = cho đủ phom base32
pad  = blob.upper() + "=" * ((8 - len(blob) % 8) % 8)
# Giải mã
data = base64.b32decode(pad)
```

Quá trình phơi bày:
```text
Khối thô blob (gom 44 ký tự): ja3ugvcgpm3doobxmi4dmy3dg43tozrugi3geoldgb6q
Bản trần decoded (lòi ra 27 byte): H7CTF{6787b86cc777f426b9c0}
```

**Bước 4 - Bồi thẩm (Kiểm chứng tính toàn vẹn).** 
Phép toán `44 % 8 = 4` lý giải rành rành vì sao cái cục (chunk) chót cùng lại có dáng vẻ cụt lủn (chỉ ôm 12 ký tự so với 16). Đây là dấu hiệu nhận diện đặc thù của cái khúc đuôi trong một dòng chảy dữ liệu bị băm vằm. Tuyệt phẩm hơn nữa là dòng kết quả giải mã được chốt sổ vừa khít bằng dấu `}` và mở màn hiên ngang bằng tiền tố `H7CTF{`. 
Hãy nhớ: Nếu bạn xếp hàng các chunk lộn xộn, hay ngớ ngẩn làm rớt mất một chunk nào đó dọc đường, cái lò nôn ra sẽ chỉ toàn là một đống ký tự rác rưởi hỗn loạn. Làm gì có chuyện xếp nhầm mà nó lại tự động ép viền ngoặc thẳng hàng tăm tắp như vậy. Do đó, đây là bằng chứng thép chốt lại quy trình giải mã, chứ không phải là một trò đoán mò (suy đoán) ăn may.

## Flag
Kích hoạt tự động bằng lệnh:

```bash
python _ctf/patient-exfil/exploit.py "C:/Users/Administrator/Downloads/capture (2).pcap"
```

Nhật ký nôn ra:
```text
[+] Gom được 3 khối cục chunks: ['00', '01', '02']
[+] Cục blob thô dạng base32 (ôm 44 ký tự chars): ja3ugvcgpm3doobxmi4dmy3dg43tozrugi3geoldgb6q
[+] Mở khoá ra được 27 bytes -> b'H7CTF{6787b86cc777f426b9c0}'
[+] Cờ lượm được flag: H7CTF{6787b86cc777f426b9c0}
```
