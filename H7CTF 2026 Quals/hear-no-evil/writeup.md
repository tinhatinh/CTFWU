# Hear No Evil - Hardware (Medium)

**Flag:** 2/2 cờ
`v1 = H7CTF{38b0e71c-6126-49f7-8692-3f0bf6bf31b0}` · `v2 = H7CTF{11945790-f241-4644-9e45-e19819bdc996}`
**Mục tiêu:** `https://web-2c53753bcbf2c207.web.h7tex.com` 
**File cung cấp:** `/capture.pcap` (2220 B, 50 gói tin packet)

## Đề bài

Hệ thống ghi lại luồng giao tiếp sóng Bluetooth (BLE) giữa tai nghe NoiseGate và ứng dụng điện thoại. Thử thách yêu cầu phân tích bản ghi sóng vô tuyến, loại bỏ các thiết bị gây nhiễu và trích xuất hai flag: một cờ lộ ra trong quá trình đọc cấu hình hệ thống, và cờ còn lại được trả về sau khi ứng dụng hoàn tất bước xác thực (authenticate). Yêu cầu là lấy trọn vẹn cả hai cờ.

## Phân tích ban đầu

Giao diện đề cung cấp một thông điệp:

```text
Tải file capture.pcap (Hãy mở nó trong Wireshark: công cụ này có khả năng tự động phân tích cấu trúc btle / btatt).
Môi trường này khá hỗn tạp, có nhiều hơn một thiết bị đang phát sóng. Hai bí mật nằm rải rác: một thiết bị tự trả về khi đọc cấu hình (config read), và một thông tin được trả về sau khi ứng dụng hoàn tất xác thực.
```

Khi không sử dụng các công cụ phân tích tự động như `tshark`, `capinfos`, hay `btlejack`, quá trình phân tích thủ công chỉ ra rằng bản ghi không tuân theo chuẩn btle thông thường:

- 4 gói tin đầu tiên phát tín hiệu bằng dải địa chỉ truy cập (access address) `D6BE898E`. Wireshark xác nhận đây là các gói tin quảng bá (advertising) BLE của các thiết bị: `Mi Smart Band 6`, `JBUL TUNE 230NC`, `Galaxy Fit3` và `NoiseGate Buds`. Ba thiết bị đầu là tín hiệu nhiễu.
- 46 gói tin còn lại đều bắt đầu bằng mã `C3 B2 A1 50`, tiếp theo là 6 byte header, phần payload và kết thúc bằng 3 byte mã sửa lỗi CRC. Dù DLT (Data Link Type) trong header của pcap khai báo là 251, cấu trúc bên trong lại sử dụng một giao thức vận tải ATT tùy chỉnh.

Do không thể phụ thuộc vào công cụ tự động, việc trích xuất payload phải thực hiện thủ công bằng cấu trúc: `payload = packet[11:-3]`.

## Quá trình khai thác

**Bước 1 - Tái định dạng và phân loại luồng vận tải.** Dựa vào kích thước và ngữ cảnh, payload được phân thành 4 nhóm:

| Kiểu dáng | Ví dụ mẫu | Diễn giải |
| --- | --- | --- |
| 2 byte | `21 00` | Yêu cầu kết nối vào thẻ (handle), mốc đọc offset 0. |
| 4 byte | `21 00 14 00` | Yêu cầu kết nối handle + chỉ điểm offset. |
| Khối 20 byte | `83 3c f9 ...` | Luồng dữ liệu phản hồi cho các request. |
| >= 11 byte | `31 00 <16 byte data>` | Gói tin báo hiệu (notify) mang dữ liệu. |

**Bước 2 - Trích xuất tài liệu đặc tả (Spec) từ file capture.** 
Tổng hợp các mảng dữ liệu trả về từ thẻ handle `0x0041`, hệ thống thu được 322 byte văn bản ASCII thuần, giải thích cơ chế hoạt động:

```text
NoiseGate fw1.4.2 [dbg]
provkey = adv mfg data (company 0x0f39) after the 0x01 type byte, 16 bytes
config@0x0021: plaintext = value XOR provkey (provkey repeated cyclically)
vault@0x0033: released after auth; plaintext = ct XOR ks,
  ks = sha256(provkey || nonce || byte(i)) for i=0,1,.. concatenated;
  nonce = notify@0x0031
```

Đề cung cấp cơ chế mã hóa (scheme) chi tiết:
- Chuỗi `config` là phép XOR giữa `value` và mã gốc `provkey`. 
- Dữ liệu `vault` sử dụng phép XOR giữa văn bản mã (ct) và chuỗi khoá phái sinh `ks`. Trong đó, `ks` được sinh ra từ hàm băm của `provkey` và `nonce` (lấy từ gói tin notify). Hệ thống không yêu cầu thủ tục challenge-response, chỉ cần phép XOR hợp lệ.

**Bước 3 - Trích xuất mã gốc (Provkey).** 
Kiểm tra gói tin quảng bá của thiết bị NoiseGate, tại khối cấu trúc AD `14 FF 39 0F 01 ...` chứa mảng Dữ liệu Đặc quyền Nhà sản xuất (Manufacturer Specific Data). Khối này mở đầu với mã công ty `0x0F39`, nối tiếp là 1 byte định dạng `0x01`, và chứa nguyên vẹn 16 byte khoá gốc:

```text
provkey trích xuất được = cb0bba6665a4fc08131cd624f22869ca
nonce trích xuất được   = ca2458f360ade373f6d055aeb0304501     (Từ gói notify tại handle @ 0x0031)
```

**Bước 4 - Giải mã dữ liệu.**
Triển khai thuật toán giải mã bằng Python:

```python
# Giải mã cờ số 1 bằng phép XOR tuần hoàn provkey
v1 = bytes(c ^ provkey[i % 16] for i, c in enumerate(ct_0x21))

# Khởi tạo luồng ks bằng sha256 và giải mã cờ số 2
ks = b"".join(hashlib.sha256(provkey + nonce + bytes([i])).digest() for i in range(8))
v2 = bytes(c ^ ks[i] for i, c in enumerate(ct_0x33))
```

Hai khối văn ciphertext này đều có chiều dài 43 byte, phù hợp với kích thước chuỗi flag hợp lệ.

**Bước 5 - Xác thực chéo.** 
Đoạn dữ liệu 322 byte của thẻ `0x0041` tạo thành một đoạn văn bản ASCII liền mạch. Việc ghép sai thứ tự hoặc lỗi trong trình ráp nối (reassemble) sẽ làm đoạn văn bản biến thành chuỗi ký tự lỗi. Văn bản đọc được hoàn chỉnh là bằng chứng xác thực thuật toán xử lý dữ liệu và offset hoàn toàn chính xác.

## Flag
```bash
python solve.py analysis/capture.pcap
```

Kết quả hiển thị:
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
