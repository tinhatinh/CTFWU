# Read Me My Fortune - Exploitation

**Điểm:** 200 · **Wave:** 1
**Flag:** `POCTF{127.612.IB2GGFAM2XGX6RDT.TEENFQ3KNWVEA3MCHJNFWFODQI}`

**Files:** `service.py` (`a1421668…`), `Dockerfile`, `runner.sh`, `entrypoint.sh`, `read_my_fortune.xinetd`. SHA256 của các file khớp thông tin trên thẻ đề.

## Đề bài

Dịch vụ tại `read-my-fortune.pointeroverflowctf.com:9000` yêu cầu session token của đội. Token thay đổi khi tải lại trang và hết hạn sau 15 phút. Người chơi nhập tên, cung hoàng đạo và một template cho `.format()`. Dịch vụ render template rồi in kết quả.

## Phân tích ban đầu

Trong `service.py`, template được xử lý như sau:

```python
reading = template.format(
    name=name, sign=sign, date=date, elara=_greet,
)
```


`name`, `sign` và `date` là các chuỗi. `elara` là function object `_greet`. Cú pháp field của `str.format` hỗ trợ truy cập attribute và subscript, chẳng hạn `{a.b[c]}`. Vì vậy, có thể đi từ `_greet` tới `__globals__` và đọc biến `FLAG` trong module.

Chú thích trong source cũng mô tả hướng khai thác này:

```python
# FLAG is a module-level global by design - the intended solve path
# uses Python's format-string attribute walk to reach it via a
# function's __globals__.
```


Payload cần sử dụng đúng cú pháp attribute lookup; không cần thực thi biểu thức Python. Hai giới hạn của dịch vụ không ngăn được payload này:

- `_read()` giới hạn template ở 2048 ký tự.
- `reading[:8000]` giới hạn output ở 8000 ký tự. Nội dung `FLAG` ngắn hơn giới hạn này.

Dịch vụ in loại và thông báo exception. Các lỗi như `KeyError` hoặc `IndexError` có thể dùng để kiểm tra cú pháp payload.

## Chuỗi khai thác

**Bước 1 - Xác định primitive.**

Theo luồng `main()`, `template` được đưa vào `template.format(elara=_greet)` mà không có bộ lọc ngoài giới hạn độ dài. Function object cung cấp đường truy cập tới biến global.

**Bước 2 - Tạo payload.**

```text
{elara.__globals__[FLAG]}
```


Field này tương ứng với `getattr(_greet, "__globals__")["FLAG"]`.

**Bước 3 - Kiểm tra local.**

Chạy `analysis/local_service.py` với `POCTF_DEV_MODE=1` để bỏ qua token và dùng flag thử nghiệm. Payload trả về `POCTF{dev.flag.local.testing.only}`, xác nhận cú pháp hoạt động.

Trên Windows, bản chạy local cần xử lý ba khác biệt:

1. `signal.SIGALRM` không được hỗ trợ.
2. Banner có box-drawing characters; đặt `PYTHONIOENCODING=utf-8` để tránh `UnicodeEncodeError` với cp1252.
3. `os.read()` không đọc được socket; dùng `sock.recv` cho socket và giữ `os.read` cho pipe.

**Bước 4 - Chạy trên instance.**

Kết nối cổng 9000, gửi token còn hạn, nhập hai trường thông tin rồi gửi payload ở trường Template. Phần Reading trả về flag.

## Flag

```text
POCTF{127.612.IB2GGFAM2XGX6RDT.TEENFQ3KNWVEA3MCHJNFWFODQI}
```


Flag khớp định dạng của `_build_marker()`: `<cid>.<team_id>.<nonce>.<sig26>`. Trong kết quả này, `cid=127`, `team_id=612` và `nonce=IB2GGFAM2XGX6RDT`. `sig26` gồm 26 ký tự base32 của HMAC-SHA256, được tính bằng `FLAG_HMAC_SECRET` trên server.

## Reproduce

```bash
cd read-me-my-fortune
python exploit.py --local
python exploit.py read-my-fortune.pointeroverflowctf.com 9000 "<nhập token còn hạn lấy trên trang web>"
```
