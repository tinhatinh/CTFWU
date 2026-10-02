# Read Me My Fortune - Exploitation

**Điểm:** 200 · **Wave:** 1
**Cờ:** `POCTF{127.612.IB2GGFAM2XGX6RDT.TEENFQ3KNWVEA3MCHJNFWFODQI}`

**Files cung cấp:** `service.py` (`a1421668…`), `Dockerfile`, `runner.sh`, `entrypoint.sh`, `read_my_fortune.xinetd` (tất cả đều có mã băm sha256 trùng khớp với thông tin trên thẻ đề).

## Đề bài

Thử thách cung cấp một dịch vụ netcat tại địa chỉ `read-my-fortune.pointeroverflowctf.com:9000`. Để bắt đầu phiên tương tác (reading), hệ thống yêu cầu một mã phiên (session token) cấp phát riêng cho từng đội. Token này sẽ thay đổi mỗi khi tải lại trang và có thời hạn sử dụng 15 phút.
Trong quá trình tương tác, người chơi nhập tên, cung hoàng đạo và một chuỗi mẫu `.format()` tự do. Hệ thống sẽ kết xuất (render) chuỗi mẫu đó và in ra kết quả.

## Phân tích ban đầu

Mã nguồn `service.py` được cung cấp cho thấy rõ vị trí lỗ hổng của chương trình:

```python
reading = template.format(
    name=name, sign=sign, date=date, elara=_greet,
)
```

Các biến `name`, `sign`, `date` là dữ liệu kiểu chuỗi thuần tuý. Điểm yếu bảo mật nằm ở biến `elara` – đây là một **đối tượng hàm (function object)** tham chiếu tới hàm `_greet`. Theo đặc tả của Python 3, khi sử dụng chuỗi định dạng (format string), ta có thể truy cập các thuộc tính (attribute) và chỉ số (subscript) bên trong cặp ngoặc nhọn (ví dụ: `{a.b[c]}`). Dựa vào cơ chế này, đối tượng hàm cho phép truy cập vào thuộc tính `__globals__`, từ đó tiếp cận không gian tên (namespace) của toàn bộ module.

Tác giả cũng đã để lại chú thích trong tệp mã nguồn:

```python
# FLAG is a module-level global by design - the intended solve path
# uses Python's format-string attribute walk to reach it via a
# function's __globals__.
```

Thử thách không chứa các lỗi (bug) tiềm ẩn phức tạp: cơ chế khai thác cốt lõi (primitive) là kỹ thuật lợi dụng hàm `.format()` khi đối số truyền vào là một đối tượng. Nhiệm vụ của người chơi là sử dụng đúng cú pháp truy xuất dữ liệu, cung cấp token hợp lệ, và lấy cờ từ kết quả đầu ra.

Hệ thống có hai giới hạn bảo vệ nhưng không ngăn cản quá trình khai thác:

- Hàm `_read()` giới hạn đầu vào theo `max_len`, cho phép chuỗi khuôn mẫu (template) dài tối đa 2048 ký tự – đủ để chứa các payload khai thác thông thường.
- Kết quả đầu ra bị giới hạn bằng lệnh `reading[:8000]`. Payload khai thác chỉ in ra nội dung một biến dữ liệu nên sẽ nằm gọn trong giới hạn này.
- Mọi ngoại lệ (exception) sẽ được in ra kèm theo loại và thông báo chi tiết (`print(f"({type(exc).__name__}: {exc})")`). Điều này giúp người chơi dễ dàng điều chỉnh cú pháp payload nếu gặp lỗi `KeyError` hoặc `IndexError` mà không cần phỏng đoán.

## Quá trình phân tích

**Bước 1 - Xác định phương thức khai thác (Primitive).** 
Phân tích luồng hàm `main()`, chú ý dòng `template.format(elara=_greet)`. Trường định danh (field name) trong phương thức `str.format` hỗ trợ tính năng tra cứu thuộc tính (attribute lookup) và chỉ mục. Không có cơ chế lọc (sanitisation) nào xử lý biến `template` ngoại trừ việc giới hạn độ dài.

**Bước 2 - Xây dựng Payload.** 
Biến `FLAG` là biến toàn cục (global) ở cấp module – module chứa hàm `_greet`. Do đó, cú pháp payload được xây dựng như sau:

```text
{elara.__globals__[FLAG]}
```

Khi thực thi, bộ phân giải (resolver) sẽ diễn dịch chuỗi này thành `getattr(_greet, "__globals__")["FLAG"]`, từ đó xuất nội dung cờ.

**Bước 3 - Kiểm thử trên môi trường nội bộ (Local Proof-of-Concept).** 
Sử dụng script `analysis/local_service.py` với biến môi trường `POCTF_DEV_MODE=1` (để bỏ qua bước kiểm tra token, cờ trên môi trường cục bộ là chuỗi giả định). Áp dụng payload, hệ thống trả về `POCTF{dev.flag.local.testing.only}`. 
Giai đoạn này giúp xác nhận kết nối và cú pháp payload hoạt động chính xác trước khi thực hiện trên môi trường thật, tiết kiệm thời gian thao tác với token.

Trong quá trình thiết lập môi trường local trên Windows, cần lưu ý ba điểm tương thích: 
1. Tín hiệu ngắt `signal.SIGALRM` không hỗ trợ (cần tạo mã thay thế). 
2. Dữ liệu đầu ra (banner) chứa các ký tự đồ họa (box-drawing) gây lỗi `UnicodeEncodeError` dưới bảng mã cp1252 (khắc phục bằng cách thiết lập biến môi trường `PYTHONIOENCODING=utf-8`).
3. Lệnh `os.read()` không hoạt động với socket trên Windows (thay bằng `sock.recv` cho socket và giữ nguyên `os.read` cho pipe).

**Bước 4 - Khai thác mục tiêu Live.** 
Tạo kết nối đến cổng 9000, cung cấp token hợp lệ, nhập thông tin bất kỳ cho hai câu hỏi đầu tiên, và nhập payload vào phần yêu cầu Template. Hệ thống sẽ trả về nội dung cờ ở phần kết quả Reading.

## Flag

```text
POCTF{127.612.IB2GGFAM2XGX6RDT.TEENFQ3KNWVEA3MCHJNFWFODQI}
```

Cấu trúc cờ thu được khớp chính xác với hàm `_build_marker()`: định dạng `<cid>.<team_id>.<nonce>.<sig26>`, trong đó `cid=127`, mã đội `team_id=612`, phần nonce ngẫu nhiên `nonce=IB2GGFAM2XGX6RDT` lấy từ token, và kết thúc bằng 26 ký tự hệ base32 của mã băm HMAC-SHA256. Thành phần chữ ký (`sig`) này được bảo mật bằng khóa `FLAG_HMAC_SECRET` trên máy chủ.

## Reproduce

```bash
cd read-me-my-fortune
python exploit.py --local
python exploit.py read-my-fortune.pointeroverflowctf.com 9000 "<nhập token còn hạn lấy trên trang web>"
```
