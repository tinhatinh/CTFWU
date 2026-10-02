# Hear No Evil — Hardware (Medium)

**Flag:** 2/2 cờ
`v1 = H7CTF{38b0e71c-6126-49f7-8692-3f0bf6bf31b0}` · `v2 = H7CTF{11945790-f241-4644-9e45-e19819bdc996}`
**Mục tiêu:** `https://web-2c53753bcbf2c207.web.h7tex.com` 
**File cung cấp:** `/capture.pcap` (2220 B, 50 gói tin packet)

## Đề bài

Hệ thống ghi lại luồng giao tiếp sóng Bluetooth (BLE) giữa cặp tai nghe NoiseGate và ứng dụng điện thoại. Thử thách đặt ra là: Bản ghi sóng vô tuyến này không chỉ chứa thiết bị mục tiêu mà còn nhiễu rất nhiều thiết bị rác khác. 
Sẽ có hai báu vật bị chôn giấu trong file capture: một chiếc chìa khoá hớ hênh lọt ra trong lần đọc cấu hình hệ thống, và chiếc còn lại kiêu kỳ hơn, chỉ bị nhả ra sau khi ứng dụng hoàn tất bước xác thực (authenticate). Yêu cầu là phải lấy trọn vẹn cả hai.

## Phân tích ban đầu

Mặt tiền trang web chĩa thẳng về một thông điệp gợi ý:

```text
Tải file capture.pcap (Hãy mở nó trong Wireshark: công cụ này có khả năng tự động giải phẫu cấu trúc btle / btatt).
Bầu không khí này khá hỗn tạp, có nhiều hơn một thiết bị đang phát sóng. Hai bí mật nằm rải rác: một cái tai nghe tự khai khi đọc cấu hình (config read), và một cái chỉ được trả về sau khi ứng dụng vượt rào xác thực.
```

Ngặt nỗi, môi trường máy tính hiện tại không được trang bị các vũ khí hạng nặng như `tshark`, `capinfos`, hay `btlejack`. Khi buộc phải lột xác từng gói tin bằng phương pháp thủ công, một sự thật phũ phàng lộ diện: capture này hoàn toàn không tuân theo chuẩn btle thông thường:

- 4 gói tin đầu tiên vẫy cờ bằng dải địa chỉ truy cập (access address) `D6BE898E`. Wireshark bóc trần đây là các gói tin quảng bá (advertising) BLE thật sự của các nhãn hiệu: `Mi Smart Band 6`, `JBUL TUNE 230NC`, `Galaxy Fit3` và `NoiseGate Buds`. Ba cái tên đầu chỉ là rác rưởi (nhiễu) làm mù mắt người chơi.
- 46 gói tin còn lại đồng loạt khởi đầu bằng mã ma thuật `C3 B2 A1 50`, nối gót là 6 byte header, rồi đến payload và chốt đuôi bằng 3 byte mã sửa lỗi CRC. Dù DLT (Data Link Type) trong header của pcap rêu rao là 251, ruột gan của nó lại sử dụng một giao thức vận tải ATT tự xào nấu (custom).

Không thể ỷ lại vào công cụ tự động, ta buộc phải dùng xẻng xúc bằng tay (parse): trích xuất payload chuẩn bằng lát cắt `payload = packet[11:-3]`.

## Chuỗi khai thác

**Bước 1 - Tái định dạng và phân loại luồng vận tải (Transport).** Dựa vào độ dài (length) và bối cảnh (context), ta chia cắt các payload thành 4 khối hình thái rõ rệt:

| Kiểu dáng | Ví dụ mẫu | Diễn giải |
| --- | --- | --- |
| 2 byte | `21 00` | Yêu cầu kết nối vào thẻ (handle), mốc đọc offset 0. |
| 4 byte | `21 00 14 00` | Yêu cầu kết nối handle + chỉ điểm offset. |
| Khối 20 byte (hoặc khối cắt dư) | `83 3c f9 ...` | Luồng dữ liệu (data) dội về đắp vào cho các request đang há mỏ chờ. |
| >= 11 byte | `31 00 <16 byte data>` | Gói tin báo hiệu (notify) nhồi sẵn dữ liệu. |

**Bước 2 - Lột xác tài liệu đặc tả (Spec) từ chính file capture.** 
Quét gom các mảng dữ liệu phân mảnh (chunk) trả về từ thẻ handle `0x0041`, ta chắp vá lại được 322 byte văn bản ASCII thuần khiết, kể rành mạch mọi thứ:

```text
NoiseGate fw1.4.2 [dbg]
provkey = adv mfg data (company 0x0f39) after the 0x01 type byte, 16 bytes
config@0x0021: plaintext = value XOR provkey (provkey repeated cyclically)
vault@0x0033: released after auth; plaintext = ct XOR ks,
  ks = sha256(provkey || nonce || byte(i)) for i=0,1,.. concatenated;
  nonce = notify@0x0031
```

Thật ngông cuồng: Thiết bị nhả luôn cả bộ cẩm nang thiết kế lược đồ mã hoá (scheme) của nó. 
- Chuỗi `config` là phép XOR thô sơ giữa `value` và mã gốc `provkey`. 
- Két sắt `vault` sử dụng phép XOR giữa văn bản mã (ct) và chuỗi khoá phái sinh `ks`. Trong đó, `ks` được sinh ra từ hàm băm của `provkey` và `nonce` (lấy từ gói tin notify) - tóm lại, hệ thống không hề chứa bất kỳ thủ tục phản biện (challenge-response) xác thực nào, miễn là phép XOR được giải với số liệu khớp.

**Bước 3 - Trộm chìa khoá mã gốc (Provkey).** 
Soi xét gói tin quảng bá (advertising) của thiết bị NoiseGate, tại khối cấu trúc AD `14 FF 39 0F 01 ...` chính là mảng Dữ liệu Đặc quyền Nhà sản xuất (Manufacturer Specific Data). Khối này mở đầu với mã định danh công ty `0x0F39`, nối tiếp là 1 byte định kiểu `0x01`, và phơi bày tơ hơ trọn vẹn 16 byte khoá gốc:

```text
provkey lượm được = cb0bba6665a4fc08131cd624f22869ca
nonce lượm được   = ca2458f360ade373f6d055aeb0304501     (Rút từ gói notify tại handle @ 0x0031)
```

**Bước 4 - Phá vỡ hai két sắt dữ liệu.**
Triển khai thuật toán giải mã bằng Python:

```python
# Bẻ khoá cờ số 1 bằng phép XOR tuần hoàn provkey
v1 = bytes(c ^ provkey[i % 16] for i, c in enumerate(ct_0x21))

# Nhào nặn luồng ks bằng sha256 và bẻ khoá cờ số 2
ks = b"".join(hashlib.sha256(provkey + nonce + bytes([i])).digest() for i in range(8))
v2 = bytes(c ^ ks[i] for i, c in enumerate(ct_0x33))
```

Toàn bộ hai khối văn bản mã (ciphertext) này đều có chiều dài đo được là 43 byte, và con số 43 đó cũng vừa vặn chính là số đo 3 vòng của một chuỗi flag hợp lệ.

**Bước 5 - Niêm phong chứng cứ (Cross-check).** 
322 byte của cục blob `0x0041` khi ráp lại là một đoạn văn bản ASCII mượt mà như suối chảy từ đầu tới cuối. Bất kỳ một trình ráp nối (reassemble) nào đặt lệch con trỏ (offset), hoặc chắp nhầm râu ông nọ (request) cắm cằm bà kia (data) đều sẽ khiến đoạn văn bản biến thành mớ ký tự rác rưởi. Do đó, việc văn bản đọc được trôi chảy là bảo chứng tuyệt đối cho thấy thuật toán sắp xếp thứ tự chunk và các mốc offset hoàn toàn chính xác, loại bỏ nguy cơ phụ thuộc vào trò "ăn may" (guess).

## Flag
```bash
python solve.py analysis/capture.pcap
```

Dòng lệnh tuôn trào:
```text
[*] provkey          : cb0bba6665a4fc08131cd624f22869ca
[*] Nhồi 0x0041 (322 byte) b'NoiseGate fw1.4.2 [dbg]\nprovkey = adv mfg data (company 0x0f'
[*] Giải config@0x0021 -> b'H7CTF{38b0e71c-6126-49f7-8692-3f0bf6bf31b0}'
[*] Giải két vault @0x0033 -> b'H7CTF{11945790-f241-4644-9e45-e19819bdc996}'
```

```text
Cờ 1 (v1): H7CTF{38b0e71c-6126-49f7-8692-3f0bf6bf31b0}
Cờ 2 (v2): H7CTF{11945790-f241-4644-9e45-e19819bdc996}
```
