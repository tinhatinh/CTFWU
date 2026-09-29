# Read Me My Fortune - log phân tích

Quy ước: mỗi giả thuyết một mục, nhánh sai ghi `result: DEAD - <lý do>`.

## H1 - Primitive là format string với object sống
`template.format(name=..., sign=..., date=..., elara=_greet)`. `elara` là function object.
Python 3 cho phép `{a.b[c]}` trong field name, nên `__globals__` của `_greet` mở ra namespace
module, nơi `FLAG` được định nghĩa ở top level. Đầu file còn ghi đích danh đây là đường đi dự kiến.
`result: ALIVE - payload `{elara.__globals__[FLAG]}`.`

## H2 - Chạy service.py trực tiếp trên Windows
`AttributeError: module 'signal' has no attribute 'SIGALRM'` ngay dòng 58, trước cả banner.
`result: DEAD - nền tảng không có SIGALRM. Hướng xử lý: stub `signal.SIGALRM` và `signal.alarm`,
giữ nguyên phần còn lại (`analysis/local_service.py`), không cần Docker hay WSL.`

## H3 - Child in banner bị chết vì mã hoá
Sau khi stub alarm, service raise `UnicodeEncodeError: 'charmap' codec can't encode characters`
rồi in "Something has disturbed the veil". Banner dùng ký tự box-drawing `╭─╮`.
`result: DEAD ở mặc định - sửa bằng `PYTHONIOENCODING=utf-8` và `PYTHONUTF8=1` cho tiến trình con.`

## H4 - `os.read` trên socket của Windows
`OSError: [Errno 9] Bad file descriptor` khi recv qua `os.read(sock.fileno(), n)`.
Với pipe của subprocess thì `os.read` lại cần thiết, vì `.read(n)` trên pipe block tới khi đủ n byte.
`result: DEAD cho socket - nhánh socket dùng `sock.recv`, nhánh pipe giữ `os.read`.`

## H5 - Bỏ qua bước token khi đánh live
`_verify_token` kiểm tra 6 điều kiện: độ dài <= 512, đúng 6 phần tách bởi `.`, prefix `EXP1`,
`int()` được cho team_id/cid/expires, `cid == CHALLENGE_ID_ENV`, nonce thỏa
`replace('_','').isalnum()` và dài 8..48, `time.time() <= expires`, cuối cùng `hmac.compare_digest`
trên payload 5 phần. Fail thì `sys.exit(1)` với thông báo chung.
`result: DEAD - không có đường vòng, và cũng không cần: token của team có sẵn trên trang đề.`

## H6 - Dump `os.environ` thay vì đọc FLAG
`{elara.__globals__[os].environ}` và các biến thể tương tự chạy được về mặt cú pháp nhưng không
cần thiết, và service đã cắt output ở 8000 ký tự kèm comment nói rõ mục đích chặn dump môi trường.
`result: KHÔNG CẦN - FLAG nằm ngay trong globals.`

## Ghi chú về giao thức hội thoại
Thứ tự đúng: banner -> `Token: ` -> `What is your name? ` -> `What is your star sign? ` ->
`Template: ` -> phần Reading -> `consultation is complete`. Service flush sau mỗi write
(`sys.stdout.reconfigure(line_buffering=True)`), nên đọc theo marker là đủ, không cần timeout
cố định cho từng bước.

## Cấu trúc cờ POCTF (rút ra từ `_build_marker`)
`POCTF{<cid>.<team_id>.<nonce>.<sig26>}` với `sig26 = base32(HMAC-SHA256(secret, "cid:team_id:nonce"))`
bỏ dấu `=` rồi cắt còn 26 ký tự. Cùng khuôn dạng này giải thích luôn cờ của bài
letters-never-sent (`2.612.ORSMSQU6A7IQJGUC.PQ4FI6SPWLYJYQGBQK66AWTILP` = cid 2, team 612,
nonce 16 ký tự, sig 26 ký tự).
