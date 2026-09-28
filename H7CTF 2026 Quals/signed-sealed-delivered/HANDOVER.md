# HANDOVER — Signed, Sealed, Delivered (mobile) — đồng đội đã nhận, mình dừng ở đây

## Đã xác định được
- `fleetlink-4.1.0.apk.zip` (10768 B, sha256 `d724d2397d09744c…`) chứa `fleetlink-4.1.0.apk`
  (16885 B, sha256 `04c185a252558ae2…`, 7 entry, classes.dex 10548 B). Package `com.fleetlink`.
- Instance `https://web-198ec1caaeb6fd82.web.h7tex.com` sống: `GET /` -> `{"service":"FleetLink API","version":"4.1.0"}`, `Server: gunicorn` (Flask).
- `GET /api/v1/trips` -> `401 {"error":"missing signature headers"}`. `POST /api/v1/trips` -> 405, nên endpoint là GET.
- Cơ chế là **request signing bằng HMAC-SHA256**, không phải JWT. Từ DEX string table:
  - headers: `X-Device-Id`, `X-Ts`, `X-Sig`
  - class `Lcom/fleetlink/Signer;` (+ nested `Signer$Signed`), file `Signer.java`
  - pepper hardcode: **`fleetlink_signing_pepper_v3`** và mẫu `fleetlink_signing_pepper_v3:`
  - constant name `APP_SECRET`, `HmacSHA256`, `SecretKeySpec`, `MessageDigest`/`SHA-256`, `digest`,
    `%02x` + `hex` (signature là hex), `TreeMap` + `entrySet` + `getKey`/`getValue` + `&` + `=`
    -> canonical string kiểu **params đã sort theo key, nối `k=v` bằng `&`**, rồi bị HMAC với key
    derived từ pepper (nhiều khả năng `SecretKeySpec(SHA256("fleetlink_signing_pepper_v3"), "HmacSHA256")`).
  - biến/param liên quan: `device_id`, `ts`, `scope`, `sig`, `mine`, `path`?, `trips`; device id có dạng `flt-…`;
    `baseUrl` mặc định `http://10.0.2.2:8080`, override qua SharedPreferences (`base_url`).
- Suy hướng: `scope` nằm trong payload được ký -> tự ký `scope=dispatcher` (hoặc `all`) để lấy fleet manifest,
  khớp hint "Sign for it yourself".

## Việc còn dở
Mình đang viết `analysis/dexdis.py` (parser DEX tự đủ: string/type/proto/method/class_data + giải mã bytecode)
để đọc chính xác thứ tự ghép chuỗi trong `Signer.sign()` thay vì đoán. Đã verify: TYPES_N=63,
`Lcom/fleetlink/Signer;` = type[25], `Signer$Signed` = type[24], DEFS_N=13 @0x2916. Bug còn lại của script:
vòng `for t in range(TYPES_N): if desc(t)==TARGET` không in ra gì -> cần kiểm tra lại `methods_of()`
(class_data_off ở `base+0x18`, và `desc()` đang nhận `u32(base)` là type idx — đúng), nhiều khả năng
`yield` trong generator lẫn `return` sớm làm mất output.

## Chạy tiếp (nếu cần)
```
python analysis/dexdis.py files/dex/classes.dex "Lcom/fleetlink/Signer;"
python analysis/dexdis.py files/dex/classes.dex "Lcom/fleetlink/ApiClient;"
```
rồi tái hiện canonical string bằng Python: `hmac.new(key, canon, hashlib.sha256).hexdigest()`,
gửi `GET /api/v1/trips` với `X-Device-Id: flt-<...>`, `X-Ts: <ms>`, `X-Sig: <hex>`.
