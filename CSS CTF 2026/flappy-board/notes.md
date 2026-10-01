# notes.md - flappy-board

Input: `files/flappy_board` (43736 B, sha256 `c07bd4504d3e1d9c495aa552acbb4c10266f966c9f47a073c4707c66caf74ded`)
Định dạng cờ đề yêu cầu: `CSSCTF{...}`
Thẻ đề không ghi URL instance nào.

## H1 - Cần hỏi người ra đề lấy URL
cmd: `rabin2 -z files/flappy_board | grep -iE "http|server|api"`
evidence: `.rodata` có `--server`, `Usage: %s [--server https://host] [--snapshot file.ppm]`, `http://34.116.80.78:8765`, và help text của chính client gọi đó là "the configured event server"; `.data` `0xb060` chứa đúng chuỗi đó làm giá trị mặc định.
result: DEAD - target nằm trong artifact, không cần hỏi. Probe `GET /` trả `error=Start+a+new+attempt+first.` nên endpoint còn sống.

## H2 - Cờ bị giấu trong binary dạng khối entropy cao
cmd: `node triage.cjs files/flappy_board`
evidence: entropy 4.700, `.rodata` chỉ 2696 byte toàn chuỗi đọc được, `.data` 608 byte gần toàn số 0.
result: DEAD - cờ do server trả (`flag` là một key được parse khi `round == 4`).

## H3 - Response của API là JSON
cmd: `curl -s -d '' http://34.116.80.78:8765/api/attempt`
evidence: `token=4b76...&round=1&seed=255350293&remaining_seconds=1200&limit_seconds=1200&target=10&wait_seconds=180`; parser JSON trả `{}` nên request kế tiếp bị thiếu Bearer token.
result: DEAD - phải parse urlencoded.

## H4 - Vào practice trước để lấy seed
cmd: `POST /api/practice` (không kèm token)
evidence: `401 error=Start+a+game+session+before+practice.`
result: DEAD - phải `POST /api/attempt` trước để mở session, practice dùng lại token đó.

## H5 - Nối danh sách flap bằng `&`
cmd: `POST /api/practice/check` với `...&flaps=12&45&...`
evidence: `400 error=Malformed+request.`; trong binary xâu phân cách ở `0x874a` là `,` (0x2c), không phải `&`.
result: DEAD - đổi sang phân cách dấu phẩy, body đã parse được.

## H6 - `ticks` là số phần tử của danh sách flap
cmd: gửi `sequence=0&ticks=2&final=1&score=0&flaps=0,2`
evidence: `400 error=Invalid+flap+tick.`; thử `[0]` với `ticks=1` thì 200, `[0,1]` với `ticks=2` thì 200, tức mọi flap tick phải nhỏ hơn `ticks`.
result: DEAD - `ticks` là số tick của chuyến bay (`uVar6 = min(remaining_ticks, 6000)` trong client); gửi `ticks=715` cho chuyến 715 tick thì `verified_score=5` khớp với mô phỏng local.

## H7 - Gọi `/api/attempt` sau mỗi lần complete để lấy round kế
cmd: `python -u run.py` (lần chạy đầu)
evidence: round 1 complete 200 trả `round=2&seed=...&target=20&wait_seconds=360`; sau đó gọi `/api/attempt` thì server quay về `round=1&target=10&remaining_seconds=1200` với seed mới, và complete round 2 bị `422 Virtual waiting timer has not completed` rồi `409 Round order mismatch`.
result: DEAD - tham số round kế đã nằm sẵn trong response của `/api/complete`; `/api/attempt` chỉ dùng để mở session.

## H8 - Chờ đủ cả departure timer lẫn thời gian bay
cmd: `python -u run2.py`
evidence: 180+19.9 + 360+36.0 + 600+52.1 = 1248 s > 1200 s; round 1 và 2 200, round 3 nhận `410 The session deadline has expired, including practice time.`
result: DEAD - server chỉ bắt chờ departure timer; `run3.py` chờ đúng 180/360/600 s thì cả ba round đều 200.

## H9 - Chốt
cmd: `python -u run3.py` rồi `python -u exploit.py`
evidence: `complete r1/r2/r3 -> 200`, response cuối `round=4&...&flag=CSSCTF%7Bbirdddd%7D`; practice oracle trước đó báo `verified_score` khớp tuyệt đối (`cheated=0`).
result: OK - cờ: `CSSCTF{birdddd}`

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
