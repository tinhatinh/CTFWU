---
title: "Read Me My Fortune - Exploitation"
date: 2026-09-29 23:31:27 +0700
lastmod_at: 2026-09-29 23:31:27 +0700
categories: [EXP]
tags: [pointer-overflow, EXP]
image:
  path: /CTFWU/Pointer%20Overflow%20CTF%202026/read-me-my-fortune/files/de.png
---
**Điểm:** 200 · **Wave:** 1 · **Cờ:** `POCTF{127.612.IB2GGFAM2XGX6RDT.TEENFQ3KNWVEA3MCHJNFWFODQI}`

**File cho trước:** `service.py` (`a1421668…`), `Dockerfile`, `runner.sh`, `entrypoint.sh`, `read_my_fortune.xinetd`, tất cả khớp sha256 in trên thẻ đề.

## Đề bài

Một service netcat tại `read-my-fortune.pointeroverflowctf.com:9000`. Trước khi reading bắt đầu,
service đòi session token phát hành riêng cho team, đổi mỗi lần reload trang và hết hạn sau
15 phút. Người chơi nhập tên, cung hoàng đạo và một template `.format()` tự viết; Madame Elara
render template đó và in kết quả.

## Phân tích ban đầu

Toàn bộ `service.py` là source công khai, và nó tự nói luôn chỗ đánh:

```python
reading = template.format(
    name=name, sign=sign, date=date, elara=_greet,
)
```

`name`, `sign`, `date` là chuỗi. `elara` là **function object** (`_greet`). Trong Python 3,
format string cho phép đi thuộc tính và subscript ngay trong field name
(`{a.b[c]}`), nên một đối tượng hàm mở ra `__globals__`, tức namespace module. Đầu file ghi rõ:

```python
# FLAG is a module-level global by design - the intended solve path
# uses Python's format-string attribute walk to reach it via a
# function's __globals__.
```

Vậy bài này không có bug ẩn: primitive là `.format()` với tham số là object sống, và nhiệm vụ
chỉ là viết đúng field, vượt qua vòng token, rồi đọc lại output.

Hai ràng buộc còn lại đáng chú ý nhưng không chặn được gì:

- `_read()` cắt input theo `max_len`, template được phép dài 2048 ký tự, dư sức chứa payload.
- Kết quả bị cắt `reading[:8000]`, nhưng payload chỉ in ra một field nên nằm gọn trong giới hạn.
- Exception được in kèm loại và message (`print(f"({type(exc).__name__}: {exc})")`), nên nếu đi
  sai bước nào thì service tự báo KeyError hay IndexError, đủ để chỉnh đường đi mà không cần đoán.

## Các giả thuyết đã loại trừ

- **Chạy `service.py` trực tiếp trên Windows để test**: chết ngay ở `signal.signal(signal.SIGALRM, ...)`
  vì `SIGALRM` không tồn tại trên platform này. Không cần WSL hay Docker cho bước này, chỉ cần
  stub đúng hai symbol `SIGALRM` và `alarm`, giữ nguyên mọi đường dẫn code khác
  (`analysis/local_service.py`).
- **Bỏ qua token để test live**: `main()` gọi `sys.exit(1)` nếu `_verify_token` trả `None`,
  và `_verify_token` kiểm tra prefix `EXP1`, đúng 6 phần, `cid` khớp `CHALLENGE_ID_ENV`, nonce
  hợp lệ, còn hạn, rồi mới so HMAC. Không có đường vòng, nên mọi thử nghiệm live đều phải dùng
  token thật của team.
- **Đi đường `os.environ` qua `{elara.__globals__[...]}`**: khả thi về kỹ thuật nhưng không cần
  thiết, vì `FLAG` nằm ngay trong globals của chính `_greet`. Service cũng đã chừa sẵn comment
  về việc cắt output 8000 ký tự để chặn kiểu dump cả dict môi trường.

## Chuỗi khai thác

**Bước 1 - Xác định primitive.** Đọc `main()`, thấy `template.format(elara=_greet)` và ghi nhớ
rằng field name trong `str.format` hỗ trợ cả attribute lookup lẫn subscript. Không có sanitisation
nào trên `template` ngoài giới hạn độ dài.

**Bước 2 - Dựng payload.** `FLAG` là global của module chứa `_greet`, nên:

```text
{elara.__globals__[FLAG]}
```

Field này resolve thành `getattr(_greet, "__globals__")["FLAG"]`, tức đúng chuỗi cờ.

**Bước 3 - Proof trên máy local.** Chạy service qua `analysis/local_service.py` với
`POCTF_DEV_MODE=1` (bỏ bước token, cờ là placeholder), đưa payload vào, nhận về
`POCTF{dev.flag.local.testing.only}`. Bước này xác nhận giao thức hội thoại và cú pháp payload
mà không tiêu tốn token live, đúng như thẻ đề khuyên.

Ba chỗ phải sửa để local chạy được trên Windows, đều là lỗi harness chứ không phải lỗi bài:
`signal.SIGALRM` thiếu (stub), banner chứa ký tự box-drawing làm child chết vì
`UnicodeEncodeError` của cp1252 (set `PYTHONIOENCODING=utf-8` cho child), và `os.read()` không
dùng được với socket trên Windows (dùng `sock.recv` cho socket, `os.read` cho pipe).

**Bước 4 - Đánh live.** Kết nối tới cổng 9000, gửi token còn hạn, trả lời hai câu hỏi bằng chuỗi
bất kỳ, rồi gửi payload ở câu Template. Service in cờ vào phần Reading.

## Cờ

```text
POCTF{127.612.IB2GGFAM2XGX6RDT.TEENFQ3KNWVEA3MCHJNFWFODQI}
```

Cấu trúc cờ khớp chính xác `_build_marker()`: `<cid>.<team_id>.<nonce>.<sig26>` với
`cid=127`, `team_id=612`, `nonce=IB2GGFAM2XGX6RDT` lấy từ token, và 26 ký tự base32 của
HMAC-SHA256. `sig` không tự tính lại được vì cần `FLAG_HMAC_SECRET` phía server.

## Chạy lại

```bash
cd read-me-my-fortune
python exploit.py --local
python exploit.py read-my-fortune.pointeroverflowctf.com 9000 "<token còn hạn trên trang đề>"
```
