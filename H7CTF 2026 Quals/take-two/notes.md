# notes.md - take-two

Target: `https://web-18955a87eb148fa7.web.h7tex.com` (BaseHTTP/0.6 Python/3.11.16).
Artifact: `files/lms.py` - WOTS+ (N=32, W=16, LEN=67) dưới cây Merkle TREE_H=4.
Cờ dạng `H7CTF{...}`.

## H0 - Đọc scheme trước khi đụng server
cmd: `cat lms.py`
evidence: `wots_sign` = `chain(sk[i], d_i)` với `d_i` là nibble của `sha256(msg)` + 3 nibble checksum;
  `verify` dựng lại public key từ chính chữ ký rồi so root. Comment đầu file nói lỗi nằm ở vận hành
  (leaf reuse qua reset counter), không nằm trong code.
result: OK - bài toán là forging qua lá dùng lại, không phải tấn công hash

## H1 - Rollback có cho ký lại không?
cmd: `POST /sign benign-one` rồi `POST /rollback` rồi `POST /sign benign-two`
evidence: chữ ký đầu `leaf=1` (leaf 0 đã tiêu hao từ trước), sau rollback chữ ký kế `leaf=0`
result: PENDING - rollback không "đứng nguyên chỗ cũ" mà **rewind về 0**; phải gom theo lá, không so với lá đầu

## H2 - Vòng lặp đầu tiên của exploit fail
cmd: `python exploit.py <host>` (bản đầu, điều kiện `s["leaf"] != first_leaf -> break`)
evidence: dừng ngay ở vòng 1 vì lá đổi từ 1 sang 0; `no reachable target after 20000 tries`
  (vì mới có 1 chữ ký, `max(mins)=15` nên không với tới message đích nào)
result: DEAD - sửa thành: lặp `rollback -> sign` 260 lần, **nhóm chữ ký theo leaf**, chọn nhóm đông nhất

## H3 - Thu thập trên leaf 0
cmd: 260 x (`POST /rollback` + `POST /sign benign-<i>`)
evidence: 260/260 chữ ký đều `leaf=0`; theo dõi `mins[j] = min digit đã gặp` và `base[j] = sig[j]` tại min đó.
  Kết quả `max(mins)=1`, `sum(mins)=1` -> 66/67 toạ độ có gốc tại chữ số 0
result: OK - đúng dự đoán xác suất `1-(15/16)^k` với k=260

## H4 - Dựng chữ ký giả
cmd: `forged[j] = chain(base[j], t[j]-mins[j])`, path lấy nguyên từ một chữ ký thật của lá 0
evidence: message đích `HELIOS-OTA-BACKDOOR-1` thoả `t[j] >= mins[j]` ngay lần thử đầu (không phải grind)
result: OK

## H5 - Kiểm chứng cục bộ trước khi deploy
cmd: chạy lại `wots_pk_from_sig` + `merkle_root_from_leaf` của chính lms.py
evidence: root tính từ chữ ký giả **khớp** root công bố `4fdc04c2...d34687`
result: OK - chữ ký hợp lệ thật, không phải server bỏ qua kiểm tra

## H6 - Deploy
cmd: `POST /deploy {firmware, sig}`
evidence: `{"ok": true, "booted": true, "flag": "H7CTF{63b0dde3-3edd-4a95-92d3-4e8c26e38483}"}`
result: OK - CỜ: `H7CTF{63b0dde3-3edd-4a95-92d3-4e8c26e38483}`

## Ghi chú
- Không cài gì thêm (requests có sẵn). Toàn bộ exploit chạy trong ~2 phút chủ yếu vì 260 lượt HTTP.
- Điều kiện chặn của `/sign` là "chứa BACKDOOR"; `/deploy` chỉ kiểm root -> forging là hướng duy nhất.
- Instance này có hạn ngắn (21 phút lúc nhận đề); may là chuỗi ký nhanh hơn giới hạn.
