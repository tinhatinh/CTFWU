> Bản log đầy đủ của phiên giải này (35 giả thuyết, gồm cả phiên 2 trên instance mới).
> Bản `notes.md` trong cùng thư mục là bản rút gọn theo template.

# Log giả thuyết

Ký hiệu: `LIVE` là nhánh còn hy vọng tại thời điểm kiểm tra, `DEAD` là đã dồn hết, `WIN` là ra cờ.
Mọi số liệu dưới đây lấy từ log trong `analysis/`, ghi trong phiên solve ngày 2026-09-26.

## Giai đoạn 1, đọc artifact

H1. Cờ giấu sẵn trong APK hoặc trong zip.
`result: DEAD` grep trực tiếp `H7CTF{`, `WEBVERSE{`, `flag{` trên zip, APK, dex, manifest, arsc, layout: 0 kết quả.

H2. Cờ giấu dạng mã hóa trong APK (XOR một byte, base64, base32, hex, rot13, đảo ngược) hoặc trong chứng chỉ ký.
`result: DEAD` quét XOR một byte trên toàn bộ 8 file, và mọi tổ hợp decode trên các chuỗi in được dài trên 6 ký tự: 0 kết quả. Cert `CN=Android Debug` chỉ có extension `subjectKeyIdentifier`.

H3. Logic của app lộ endpoint hoặc cơ chế gate.
`result: WIN` `de/dexdump.txt` (androguard, không cần JDK) cho ra 15 class. Đọc được: header attestation tĩnh, `promo/public` là trang WebView nạp, `startsWith(baseUrl)` gắn token, `ExportProvider` traversal không lọc `..`, token nằm plaintext trong SharedPreferences.

## Giai đoạn 2, ba cờ đầu

H4. `X-Meridian-Client` chỉ là chuỗi tĩnh, đặt vào là qua.
`result: WIN` `auth/device` trả token `user_id:1001`; `internal/promo` trả cờ v1. Thử 7 biến thể header (sai version, sai nền tảng, thêm `, internal`, bỏ `(attested)`): tất cả `403 restricted`.

H5. `device_id` được dùng để chọn tài khoản.
`result: DEAD` mọi giá trị tùy ý, kể cả injection (`' or 1=1--`, `../../../etc/passwd`, `{{7*7}}`), đều trả `user_id:1001`. Chỉ chuỗi vắng mặt mới `400`.

H6. Có route khác ngoài những route gọi từ app.
`result: WIN` `promo/public` lộ liên kết sang `internal/promo`; fuzz từ vocabulary tìm tiếp ra `profile` (PATCH), `admin/ledger`, `accounts/me`.

H7. `PATCH /profile` lưu mọi khóa gửi lên.
`result: WIN` `{"role":"admin"}` mở `admin/ledger`, lấy cờ v2. Đảo về `customer` thì `403 admin role required`, xác nhận gate.

H8. `updated` trong đáp án `profile` là oracle cho biết schema.
`result: DEAD` thử 84 tên field, tất cả đều xuất hiện trong `updated` kể cả vô nghĩa. Chỉ 4 khóa `name`, `email`, `role`, `tier` thực sự lưu.

H9. `accounts/me` chỉ cần bearer.
`result: WIN` cờ v4, kèm dòng `session verified from device` khớp bug phía điện thoại.

## Giai đoạn 3, săn v3

H10. Còn route chưa tìm thấy.
`result: DEAD` khoảng 90k path, 1 đến 4 segment, 12 prefix, 5 method. `analysis/raft_sweep.log`: 36058 path nhân 2 method, chỉ 3 kết quả đều là route đã biết. `analysis/modes_out.txt`: 10037 path nhân 3 chế độ credential, cũng vậy. Bảng route cuối cùng có 7 rule.

H11. Route tồn tại nhưng gate bằng method lạ.
`result: DEAD` `Allow` trên từng route: `GET, OPTIONS, HEAD` hoặc `OPTIONS, PATCH` hoặc `POST, OPTIONS`. Không có method nghiệp dư nào.

H12. Route ẩn sau virtual host hoặc cổng khác.
`result: DEAD` `Host:` giả mạo (`links.meridianpay.io`, `meridianpay.io`, `localhost`, `127.0.0.1`) trả `404 page not found` của front-end Go, tức không có vhost. Port 80 và 8080 cũng chỉ tới front-end đó. Cert là cert dùng chung `*.web.h7tex.com`.

H13. Bypass định tuyến bằng chuẩn hóa path.
`result: DEAD` `%2e%2e`, `%00`, `;`, hoa thường, `//` (Werkzeug `merge_slashes` bật, `//api/v1//admin//ledger` về đúng route cũ), đường dẫn tuyệt đối dạng proxy. Không mở thêm route nào.

H14. Tham số query đổi hành vi.
`result: DEAD` 4464 cặp tên và giá trị trên 5 route, 0 diff thật (chỉ có timeout do tự bắn quá nhanh).

H15. Header đổi hành vi.
`result: DEAD` 1200 probe header tên và giá trị, 0 diff. `analysis/field_writes.log` cho thấy các diff xuất hiện đều là `403 admin role required` do một script khác đặt `role=customer` song song, không phải dữ liệu mới.

H16. Có chế độ nhìn khác theo nội dung.
`result: DEAD` 1680 probe `format|view|output|render|type` với 23 giá trị, 8 biến thể `Accept`, và `Content-Type` kiểu form, multipart, xml trên route PATCH. Không gì đổi.

H17. Đặc quyền suy ra từ email hoặc tên.
`result: DEAD` 20 địa chỉ staff (`admin@meridianpay.io`, `cfo@...`, `admin@internal.meridianpay.io`, ...) và 14 giá trị `name`, diff cả 3 route cờ: 0 thay đổi.

H18. Gate theo `role` hoặc `tier` ở một giá trị khác `admin`.
`result: DEAD` 63 giá trị `role` và 21 giá trị `tier`, theo dõi độ dài đáp án từng route. Ledger chỉ mở đúng với chuỗi `admin` duy nhất, kể cả `ADMIN`, `Admin`, `system:admin`, dict, `admin,auditor`.

H19. Mass assignment ghi sang object khác (account).
`result: DEAD` 25 tên field của object account viết qua `profile`, cả dạng lồng `{"account":{"number":...}}` và dạng chấm `account.number`: `accounts/me` không đổi một byte.

H20. IDOR đọc tài khoản member khác.
`result: DEAD` `accounts/`, `account/`, `users/`, `receipts/`, `ledger/`, `balances/` ghép với 18 định danh (`MP-0041-8827`, `8827`, `1000`, `1002`, `418233`, ...): toàn bộ 404.

H21. Server nhận credential ở nơi khác ngoài header.
`result: DEAD` `Cookie: session_token=`, `X-Session-Token`, `X-Meridian-Token`, `X-Auth-Token`, `Authorization` không scheme, và 6 tên query param carrying token. Tất cả `401 missing/invalid bearer`.

H22. So khớp bearer là prefix hoặc substring.
`result: DEAD` bearer là prefix độ dài 1, 2, 4, 8, 10, 16, 20, 30, 40, 144 ký tự, thiếu một ký tự cuối, đổi ký tự giữa, nối thêm dữ liệu, hai token ghép lại: `401` hết.

H23. `alg:none` hoặc bỏ qua chữ ký.
`result: DEAD` `none`, `None`, `NONE`, `nOnE`, key rỗng, `kid` trỏ file. `401`. Đã tự kiểm primitive HMAC bằng cặp tự sinh trước khi dùng kết luận này.

H24. Key JWT lấy từ dữ kiện có sẵn.
`result: DEAD` khoảng 5k chuỗi từ dex, manifest, arsc, layout; 899 candidate dựng từ vật liệu gói (cert DER, SPKI, serial, fingerprint, digest từng file và từng entry, digest MANIFEST và SF, chuỗi D8, độ dài file); mật khẩu keystore thông thường.

H25. Key JWT là từ điển.
`result: DEAD` `analysis/jwt_dict_out.txt`: `no hit in 186296544 candidates`, sinh từ 370105 từ `words_alpha.txt` nhân 3 kiểu hoa thường, 14 hậu tố, 12 tiền tố. Kết luận: key ngẫu nhiên theo instance, vì bản thân cờ cũng là UUID theo instance.

H26. Có SSTI hoặc injection qua field do server render.
`result: DEAD` 8 payload (`{{7*7}}`, `${7*7}`, `#{7*7}`, `<%= %>`, `{{config}}`, `{{''.__class__}}`) viết vào `name`, `email`, `tier` rồi đọc lại 4 route. Server render cờ và `member 1001` nhưng không bao giờ render các field đó.

H27. Body của `auth/device` đổi được danh tính hoặc quyền.
`result: DEAD` 16 body có `user_id`, `member`, `sub`, `role`, `admin`, `impersonate`, `token`, `attested`, `platform`, `account_number`, `tier`. Luôn `user_id:1001`.

H28. Có khóa phiên theo thiết bị phải gửi lại ở header.
`result: DEAD` 17 tên header định danh thiết bị hoặc phiên ghép với 6 giá trị gồm đúng `device_id` đã mint token và chính token đó. 0 diff. Token mint từ `device_id` khác vẫn đọc được như thường, tức không có binding.

H29. HTTP method override hoặc kỹ thuật smuggling mức transport.
`result: DEAD` `X-HTTP-Method-Override`, `X-Original-URL`, `X-Rewritten-URL` không đổi route. Absolute-form request line chỉ tới đúng app. `CONNECT` bị từ chối. Không có header `Access-Control-*` và không cookie để đánh race.

## Trạng thái kết thúc

Ba nhánh còn lại đều cần thứ môi trường này không có:

1. Bug `startsWith(baseUrl)` phía WebView. Khai thác thật cần emulator plus một listener công khai, và sản phẩm là token mà mình đã tự mint được, nên không sinh cờ mới.
2. Bug traversal trong `ExportProvider`. Cũng chỉ đọc được file trên máy, và hướng đó đã trả công ở v4.
3. Nếu v3 là một control phía server thì nó keyed bằng giá trị không xuất hiện trong APK hay trong bất kỳ đáp án nào, tức cần source của bài chứ không cần fuzz tiếp.

Đã hỏi người dùng xin hint ghi trên dòng objective `v3` của card (WebVerse thường có tooltip hoặc tag kỹ thuật ở đó), vì đó là dữ kiện duy nhất còn thiếu.

## Phiên 2, instance mới cùng URL

Người dùng mở lại instance cùng địa chỉ. Ba cờ đổi UUID (v1 `1c008911`, v2 `71dc7efd`, v4 `309444f3`), xác nhận cờ sinh theo instance.

H30. Token của instance cũ còn hạn sẽ bị instance mới từ chối nếu server giữ session store hoặc key sinh theo instance.
`result: DEAD nhưng ra phát hiện mới` token cũ (iat của instance đã chết) vẫn được instance mới chấp nhận, `accounts/me` trả 200. Suy ra verify JWT **stateless** và **key HMAC là hằng số trong image**, không sinh theo instance. Hệ quả: mọi nỗ lực crack key đều so được offline trên token của bất kỳ instance nào, và nếu crack được thì token giả sống qua cả restart.

H31. Route thứ tư trả 404 khi chưa admin, nên toàn bộ sweep phiên 1 (chạy với role customer) mù với nó.
`result: DEAD` `analysis/admin_sweep.py`: 16843 path nhân 2 chế độ credential, token đã lên `role=admin`. Chỉ 7 rule cũ hiện ra.

H32. Flow referral mà trang promo nhắc ("Refer a friend and earn 500 points") có endpoint hoặc param riêng.
`result: DEAD` 26 tên param nhân 18 giá trị (`ref`, `code`, `invite`, `coupon`, `voucher`, `redeem`, `friend`, `promo_code`, ...) trên 5 route, cộng POST body cùng tên. 0 diff thật; 471 dòng diff trong log đều là artifact 403 do script khác ghi đè role song song.

H33. Header hoặc param lấy giá trị từ chính artifact Android (`com.meridian.pay.export`, `meridianpay://open`, `MP-0041-8827`, `receipt-8827.txt`, `http://10.0.2.2:8080`, ...).
`result: DEAD` 46 tên nhân 28 giá trị nhân 7 route, 8036 probe, 0 diff.

H34. Server nhận định danh thô làm bearer (`Bearer 1002`, `Bearer MP-0041-8827`, scheme `Token`, `Meridian`).
`result: DEAD` 35 giá trị nhân 5 scheme trên 3 route, toàn bộ 401.

H35. Instance có host chị em trên zone khác của cert (`*.web3.h7tex.com`, `*.pwn.h7tex.com`).
`result: DEAD` bốn biến thể host đều trả `404 page not found` của front-end Go.

H36. Đường Android App Links `/.well-known/assetlinks.json` và họ well-known khác tồn tại trên instance.
`result: DEAD` 15 đường well-known đều 404 Flask.

H37. Method lạ trên route đã biết là cửa ghi vào bản ghi account (các lần `None` ở ma trận phiên 1 là crash thật).
`result: DEAD` bắn lại PATCH, POST, PUT, DELETE trên `accounts/me`, `admin/ledger`, `internal/promo` với 18 body, có retry: toàn bộ 405. Các `None` phiên 1 chỉ là reset kết nối do quá tải.

H38. Đáp án thay đổi theo thời gian hoặc theo race (cờ xoay vòng, đếm số lần enroll, TOCTOU giữa PATCH role và đọc ledger).
`result: DEAD` 40 GET tuần tự mỗi route cho đúng 1 đáp án; 24 request song song `auth/device` cùng device_id đều 1001; 24 `internal/promo` song song trùng nhau; 24 cặp PATCH rồi đọc ledger đều 200.

H39. Đổi danh tính bằng cách ghi `sub`, `user_id`, `email`, `owner` rồi mint lại token.
`result: DEAD` 24 body, token mint lại luôn `sub=1001`, `name` chỉ đổi theo field `name`. Brute `device_id` 1046 giá trị cũng chỉ ra 1001.

H40. LFI hoặc SSTI qua bốn field được lưu (`role`, `tier`, `name`, `email`) nếu server ghép chúng vào đường dẫn template hoặc file.
`result: DEAD` 28 payload traversal và template nhân 4 field, diff cả 5 route: 0 thay đổi thật.

H41. Key HMAC nằm trong từ điển mật khẩu thật.
`result: DEAD` cộng dồn phiên 2: rockyou plain 14.3M, rockyou nhân 46 rule khoảng 660M (`analysis/jwt_rules.py`), xato top 1M và Pwdb top 1M plain cộng tổ hợp tiền tố hậu tố khoảng 20M (`analysis/jwt_big.py`), 90767 cụm từ và n-gram lấy từ lời đề và chuỗi trong app, 206 hằng số nguồn (hex instance, id sự kiện, UUID cờ, sha256 artifact). Tổng cộng dồn hai phiên khoảng 900 triệu candidate, không trúng. Kết hợp H30, key là hằng số ngẫu nhiên trong source, không crack được bằng từ điển.

## Kết luận phiên 2

Mọi lớp mù có thể gọi tên đều đã đóng: route gate theo role, theo header giá trị Android, theo param referral, theo method, theo host, theo well-known, theo trạng thái và race. Thứ duy nhất còn lại là một route gate bằng giá trị không xuất hiện ở bất kỳ artifact nào, hoặc một bước cần emulator. Cả hai đều ngoài tầm black-box từ máy này.

## Phiên 3, chữ ký request của WebView và kiểm kê emulator

H42. Route ẩn gate bằng header điều hướng trình duyệt (`Sec-Fetch-Mode: navigate`, `Sec-Fetch-Dest`, `Sec-Fetch-Site`, `Upgrade-Insecure-Requests`, `X-Requested-With`, UA có `wv`), tức đúng chữ ký mà WebView của app phát ra và mọi sweep trước không gửi.
`result: DEAD` diff 7 route với 6 tổ hợp header: 0 khác biệt; sweep 10037 path mang đầy đủ chữ ký đó kèm role=admin và bearer (`analysis/wv_sweep.py`) chỉ ra 7 rule cũ.

H43. Gate bằng header vận tải của WebView (`Accept-Encoding: gzip`, `Accept-Charset`, `Connection: keep-alive`).
`result: DEAD` 6 tổ hợp trên 5 route, 0 khác biệt.

H44. Chạy emulator và Frida để tìm logic ẩn.
`result: DEAD ở bước kiểm kê` máy không có emulator nào: `C:\Program Files\Netease\MuMuPlayer` chỉ còn `nx_main\adb.exe` và hai dll (phần cài đặt đã bị gỡ), `C:\Program Files (x86)\Nox\bin` rỗng, không tiến trình emulator, không adb trên PATH. Frida client 17.18.0 có sẵn nhưng không có thiết bị để bám. Về mặt kỳ vọng: APK không có thư viện native, không DexClassLoader, không assets, toàn bộ 15 class đã dump, chỉ có hai lời gọi mạng là `auth/device` và tải trang của WebView; thứ duy nhất Frida quan sát thêm được là việc navigation bằng link click có gửi lại extraHeaders hay không, và cả hai đích mà nó với tới đều đã là cờ của mình.

H45. Cài Android SDK emulator rồi bám Frida, theo yêu cầu người dùng.
`result: DEAD ở bước khả thi phần cứng` máy là laptop vật lý i7-12650H nhưng `hypervisorlaunchtype=Auto` và HVCI đang chạy nên VT-x đã bị hypervisor chiếm, trong khi `HypervisorPlatform` (WHPX) và `VirtualMachinePlatform` đều Disabled, còn HAXM/AEHD không thể nạp khi hypervisor đang giữ VT-x. Mọi đường accel đều đòi bật hoặc tắt một tính năng Windows rồi reboot; người dùng chọn không reboot và dừng ở 3/4. Ghi thêm: frida client 17.18.0 có sẵn qua pip nhưng không có thiết bị nào để bám, và kỳ vọng của hướng này vốn gần 0 vì APK không có native lib lẫn tải dex động.

## Phiên 4, vùng file chưa đụng và kết luận về cờ

H46. Cờ hoặc manh mối giấu trong cấu trúc file: APK Signing Block, entry zip ẩn không có trong central directory, dữ liệu dính sau EOCD.
`result: DEAD` APK có đúng 7 local header khớp 7 central directory header, EOCD nằm sát cuối file, không zip64, không byte thừa; outer zip cũng vậy. Signing Block (4088 byte tại offset 12272) chỉ chứa chữ ký v2 và v3 cùng cert `Android Debug`, không có cặp ID-value tự chế nào.

H47. Lộ nguồn qua dotfile hoặc backup (`.git`, `.env`, `app.py`, `backup.zip`, `.sqlite`, log, `server-status`).
`result: DEAD` 78 đường phổ biến đều trả đúng 404 Flask 207 byte.

H48. Oracle lỗi ở tầng JWT: `kid` trỏ file, `alg` lạ, `jku`, `x5u`, `jwk`, `crit`, kid kiểu dict.
`result: DEAD` 38 biến thể, toàn bộ trả cùng một `401 missing/invalid bearer`, không có 500, không khác biệt thời gian. Server verify bằng thư viện chuẩn trong try hoặc except, không để lộ gì.

H49. Gate bằng client hint mà chỉ WebView thật gửi (`Sec-CH-UA`, `Sec-CH-UA-Mobile`, `Sec-CH-UA-Platform`).
`result: DEAD` 4 tổ hợp trên 5 route, 0 khác biệt.

H50. Route ẩn chỉ hiện khi request mang cả chuỗi điều hướng của app (wv UA, Sec-Fetch navigate, Sec-CH-UA, `X-Requested-With`, và `Referer` đúng trang promo, tức bằng chứng vừa bấm link).
`result: DEAD` `analysis/chain_sweep.py`: 10037 path với đầy đủ chữ ký đó, vẫn chỉ 7 rule.

H51. Key JWT ngắn nên có thể vét cạn.
`result: DEAD với chữ số và chữ thường` `analysis/jwt_short.py`: toàn bộ 10^1..10^8 chữ số và 26^1..26^6 chữ thường, không trúng; alnum độ dài tối đa 5 đang chạy.

H52. Cờ cố định theo instance.
`result: SAI, và là phát hiện quan trọng nhất phiên` bộ cờ đổi giữa hai lần đo trên cùng một URL, khoảng 2,5 giờ: ledger `71dc7efd...` rồi `9404f65a...`. Trong vài phút liên tiếp thì ổn định (3 lần chạy exploit.py cho cùng 3 UUID). Vậy cờ sinh lại khi container khởi động lại, còn key JWT thì không đổi (token cũ vẫn verify được, H30). Hệ quả thực chiến: phải lấy cờ và nộp ngay trong cùng lần chạy, không tin vào UUID ghi ở phiên trước.

## Phiên 5, tự kiểm lỗ hổng đo lường của chính mình

Người dùng phản hồi rằng tôi bị tunnel vision. Kiểm lại quy trình, tìm ra ba lỗi trong cách đo của chính tôi, cả ba đều là lỗ hổng thật chứ không phải nghi thức:

L1. Khi vá lỗi `bytes.translate` trong `jwt_rules.py`, tôi đã xóa luôn dòng leet thay vì sửa bảng. Toàn bộ biến thể leet của rockyou vì thế chưa từng được test ở phiên 2 và 3. Đã vá và chạy lại.
L2. Oracle profile chỉ so tập key bên trong object `profile`, chưa từng so tập key ở cấp cao nhất của đáp án PATCH. Một field dạng `rotation` hoặc `confirmation` ở top-level sẽ lọt. Đã đo lại với 399 tên field nhân 13 kiểu giá trị: top-level luôn là `['profile','updated']`.
L3. Tôi chỉ in `name`/`user_id`/`token` của đáp án `auth/device` mà không dump raw body theo từng `role`. Đã dump lại: đúng 3 key, 195 byte, cho cả 8 giá trị role.

Dồn thêm trong phiên:

H53. Route thứ 8 nằm trong vốn từ tên API có thật ngoài đời (không phải do tôi tự nghĩ).
`result: DEAD` `analysis/api_sweep2_out.txt`: 71321 path dựng từ `api-seen-in-wild`, `api-endpoints-res`, `objects`, `actions`, `common-api-endpoints-mazen160`, `raft-medium-directories`, token đã lên admin. Chỉ 2 hit, đều là route đã biết.

H54. Vốn từ mobile-hardening và open-banking mà list tự chế của tôi thiếu.
`result: DEAD` tìm ra 34 từ hoàn toàn vắng (`integrity`, `frida`, `rooted`, `playintegrity`, `otp`, `mfa`, `biometric`, `settlement`, ...), cộng họ open-banking (`consents`, `tpp`, `aspsp`, `psd2`, `payees`, `standing-orders`). 941 path nhân 2 method: không gì.

H55. Có blueprint hoặc error handler riêng giấu route.
`result: DEAD` 10 path mồi ở các nhánh khác nhau trả 404 có md5 giống hệt nhau, 207 byte. Một error handler toàn cục, không có chỗ cho route ẩn kiểu abort(404) phân nhánh.

H56. Giá trị cờ là gate chain cho objective sau.
`result: DEAD` 3 cờ hiện tại, mỗi cờ 2 dạng (có và không có `H7CTF{}`), phát qua 18 header và 10 param trên 7 route: 0 khác biệt.

H57. Server map `device_id` theo tiền tố nền tảng.
`result: DEAD` 335 device_id phủ 49 tiền tố (`web-`, `ios-`, `corp-`, `staff-`, `emulator-`, `attested-`, ...) nhân 7 dạng: chỉ device_id rỗng là 400, còn lại luôn 1001.

H58. Key JWT là giá trị xoay vòng (master key rotation).
`result: DEAD` offline và online với 26 biến thể từ 3 cờ hiện tại và 3 cờ cũ: không. Đáng chú ý là token cũ vẫn verify SAU khi cờ đã đổi, tức key và cờ không cùng nguồn sinh.

H59. Key nằm trong rockyou với rule stack đầy đủ.
`result: đang chạy` `jwt_deep.py`, toàn bộ rockyou nhân khoảng 200 biến thể (case, reverse, leet bảng đúng, reflect, cộng 1 và 2 ký tự, cộng số và năm, tiền tố chủ đề, thay thế đơn). Tổng cộng dồn hai phiên vào khoảng 2.5 tỷ candidate.

Kết luận trung thực của phiên: ba lỗi đo lường của tôi đều cho kết quả âm tính, nên không có cờ nào bị bỏ do chúng. Bề mặt route đã đóng chặt. Nếu v3 là crack key, nó cần khối lượng lớn hơn Python của tôi hoặc một rule nằm ngoài mọi thứ tôi đã nghĩ ra; nếu không, nó là một route gate bằng giá trị không xuất hiện trong bất kỳ artifact nào, tức cần source.

## Ket cuc phien 5

`jwt_deep.py` chay xong: toan bo rockyou nhan khoang 200 bien the (case, reverse, leet bang dung, reflect, duoi 1 va 2 ky tu, so va nam, tien to chu de, thay the don) -> None. Nang tong khoi JWT da thu len khoảng 2.5 ty candidate, van khong trung.

Ba loi do luong cua chinh toi (L1 leet bi xoa oan khi sap bug, L2 khong so key cap cao nhat cua dap an PATCH, L3 khong dump raw body `auth/device` theo role) duoc do lai ca ba: khong co co bi bo sot do chung.

Hai kha nang con lai va bo tiep van chi tiet (lenh hashcat mode 16500, script gia mai token, danh sach sub can thu) nam o `HANDOFF-v3.md`.

## Phien 6: GPU (RTX 3050, hashcat 6.2.6, -m 16500)

Da tai hashcat tu hashcat.net (20.951.515 byte), giai chay duoc ngay, nhan RTX 3050 Laptop qua OpenCL. Toc do do truc tiep: 11,6 MH/s tong (3050 bi gioi han 35W; luc chay full 73-78 do C, 29,9W).

| Dot | Candidate | Ket qua |
|---|---|---|
| rockyou plain | 14.344.384 | Exhausted, 0 |
| rockyou x best64 | 1.104.517.568 | Exhausted, 0 |
| rockyou x leetspeak | 243.854.528 | Exhausted, 0 |
| rockyou x Incisive-leetspeak | ~14 ty | BI ABORT giua chung (timeout 900s cua toi cong voi pipe grep|head lam mat buffer tien do) - khong tinh la da bao phu |
| mask vet can ?a do dai 1..5 | 8.240.319.040 | Exhausted, 0, khong co outfile |

Tong GPU da thu: 9,602 ty candidate.

Ket luan moi tu phien nay:

H60. Key HS256 la chuoi ngan co ky tu dac biet.
`result: DEAD, da chung minh` vet can hoan toan moi key in duoc do dai toi da 5 (8,24 ty) tra ve Exhausted khong recover. Day khong con la "khong tim thay trong wordlist" ma la khong gian da bi loai hoan toan.

H61. Key la mat khau dien hinh kem bien the thong thuong.
`result: RAT CAO LA DEAD` rockyou plain, best64 (1,1 ty) va leetspeak (244 trieu) deu Exhausted.

Sai lam quy trinh trong phien (ghi lai de kh lap lai):
- Toi tung noi GPU dat "hang tram MH/s" trong khi do lai chi 11,6 MH/s, tuc chi nhanh hon Python cua chinh khoang 6 lan. So tuyet doi (7,4 ty key) la nhu nhau giua hai ben; loi the that cua nam o rule stack lon, khong o do dai key.
- Van pipe job dai qua `grep | head` nen mat tien do cua Incisive-leetspeak khi no bi timeout giet. Lenh kiem tra `hashcat --show --session` cung treo vi no attach vao phien dang chay.
- Da tai va chay hashcat muon: dang le day la buoc dau tien khi noi den brute force JWT, khong phai buoc cuoi sau khi da het 4,5 ty candidate bang CPU.
