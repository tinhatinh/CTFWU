# Read Me My Fortune - Exploitation

**Điểm:** 200 · **Wave:** 1
**Cờ:** `POCTF{127.612.IB2GGFAM2XGX6RDT.TEENFQ3KNWVEA3MCHJNFWFODQI}`

**Files cung cấp:** `service.py` (`a1421668…`), `Dockerfile`, `runner.sh`, `entrypoint.sh`, `read_my_fortune.xinetd` (tất cả đều có mã băm sha256 trùng khớp với thông tin trên thẻ đề).

## Đề bài

Người chơi được cung cấp một dịch vụ netcat tại địa chỉ `read-my-fortune.pointeroverflowctf.com:9000`. Để bắt đầu phiên "coi bói" (reading), hệ thống bắt buộc phải nhận được một mã phiên (session token) phát hành độc quyền cho từng đội. Token này sẽ tự động thay đổi mỗi khi tải lại (reload) trang và có thời hạn sử dụng khắt khe chỉ trong 15 phút.
Trong quá trình tương tác, người chơi sẽ lần lượt nhập tên, cung hoàng đạo và cung cấp một chuỗi mẫu `.format()` tự do. Nhân vật ảo "Madame Elara" sẽ kết xuất (render) chuỗi mẫu đó và in ra lời bói toán.

## Phân tích ban đầu

Toàn bộ mã nguồn `service.py` được công khai trong gói tải về, và nó cũng phơi bày luôn vị trí tử huyệt của chương trình:

```python
reading = template.format(
    name=name, sign=sign, date=date, elara=_greet,
)
```

Ở đây, `name`, `sign`, `date` đều là dữ liệu kiểu chuỗi thuần tuý. Lỗ hổng chết người nằm ở biến `elara` – nó thực chất là một **đối tượng hàm (function object)** tham chiếu tới hàm `_greet`. Theo đặc tả của Python 3, khi sử dụng chuỗi định dạng (format string), ta hoàn toàn có thể trỏ thẳng tới các thuộc tính (attribute) và truy cập theo chỉ số (subscript) ngay trong cấu trúc cặp ngoặc nhọn (ví dụ: `{a.b[c]}`). Lợi dụng cơ chế này, một đối tượng hàm cho phép ta đi sâu vào thuộc tính `__globals__`, mở toang cánh cửa bước vào không gian tên (namespace) của toàn bộ module. 

Ngay trên đầu tệp mã nguồn, tác giả cũng để lại những lời ghi chú chân thành:

```python
# FLAG is a module-level global by design - the intended solve path
# uses Python's format-string attribute walk to reach it via a
# function's __globals__.
```

Tóm lại, bài này không hề có những mánh khoé lỗi (bug) ngầm nào cả: cơ chế khai thác cốt lõi (primitive) chính là kỹ thuật lạm dụng hàm `.format()` khi đối số truyền vào là một đối tượng sống. Nhiệm vụ duy nhất của người chơi là viết đúng cú pháp truy xuất trường dữ liệu, nạp token hợp lệ, và lấy cờ từ dữ liệu xuất ra.

Hai giới hạn bảo vệ được đặt ra nhưng không mảy may ảnh hưởng đến quá trình khai thác:

- Hàm `_read()` cắt cụt chuỗi đầu vào theo `max_len`, cho phép chuỗi khuôn mẫu (template) dài tới 2048 ký tự – thừa sức để nhét vừa bất kỳ payload khai thác nào.
- Kết quả đầu ra bị giới hạn bằng lệnh `reading[:8000]`. Payload khai thác của ta chỉ in ra nội dung một biến dữ liệu nên chắc chắn nằm gọn trong giới hạn an toàn này.
- Bất kỳ ngoại lệ (exception) nào xảy ra cũng sẽ được in kèm theo loại và thông báo chi tiết (`print(f"({type(exc).__name__}: {exc})")`). Điều này vô cùng đáng giá, vì nếu ta có gõ sai cú pháp, hệ thống sẽ ân cần báo lỗi `KeyError` hoặc `IndexError`, giúp người chơi tự tinh chỉnh đường đi mà không cần phải chơi trò đoán mò.

## Chuỗi khai thác

**Bước 1 - Khoanh vùng Primitive.** 
Đọc kỹ luồng hàm `main()`, chú ý dòng `template.format(elara=_greet)`. Phải khắc cốt ghi tâm rằng trường định danh (field name) trong phương thức `str.format` hỗ trợ đồng thời tính năng tra cứu thuộc tính (attribute lookup) và chỉ mục. Hoàn toàn không có màng lọc (sanitisation) nào xử lý biến `template` ngoài việc chặt ngắn độ dài.

**Bước 2 - Lắp ráp Payload.** 
Biến `FLAG` đóng vai trò là biến toàn cục (global) ở cấp module – chính là module chứa hàm `_greet`. Do đó, cú pháp payload sẽ là:

```text
{elara.__globals__[FLAG]}
```

Khi được thực thi, bộ phân giải (resolver) sẽ diễn dịch trường này thành `getattr(_greet, "__globals__")["FLAG"]`, và hệ quả tất yếu là nó kéo toàn bộ chuỗi cờ ra ngoài ánh sáng.

**Bước 3 - Diễn tập trên môi trường nội bộ (Local Proof-of-Concept).** 
Sử dụng script `analysis/local_service.py` kèm theo biến môi trường `POCTF_DEV_MODE=1` (để lách qua bước kiểm tra token, cờ trên môi trường cục bộ chỉ là chuỗi mẫu). Bơm payload vào và ta lập tức thu về `POCTF{dev.flag.local.testing.only}`. 
Giai đoạn này giúp ta kiểm chứng độ tin cậy của giao thức kết nối và cú pháp payload mà không bị lãng phí token trên môi trường live, hoàn toàn tuân thủ theo lời khuyên in trên thẻ đề.

Trong quá trình thiết lập, có ba chỗ nhỏ cần phải sửa lại để môi trường local chạy mượt mà trên hệ điều hành Windows (đều là sự cố tương thích do môi trường giả lập, không phải là lỗi ẩn của đề): 
1. Tín hiệu ngắt `signal.SIGALRM` bị thiếu (cần tạo mã stub giả). 
2. Biểu ngữ (banner) có chứa các ký tự đồ họa đường kẻ (box-drawing) khiến luồng tiến trình con chết đột ngột vì lỗi `UnicodeEncodeError` dưới bảng mã cp1252 (khắc phục bằng cách gắn biến `PYTHONIOENCODING=utf-8` cho luồng con).
3. Lệnh `os.read()` không dùng được cho socket trên môi trường Windows (thay bằng `sock.recv` cho kết nối socket và giữ nguyên `os.read` cho cấu trúc pipe).

**Bước 4 - Khai hoả vào mục tiêu Live.** 
Tạo kết nối ròng đến cổng 9000, nạp token hợp lệ, bịa một câu trả lời bất kỳ cho hai câu hỏi đầu (tên và cung hoàng đạo), và tung đòn quyết định bằng payload vào ô câu hỏi Template. Hệ thống ngoan ngoãn nôn ra cờ ở phần kết quả Reading.

## Flag

```text
POCTF{127.612.IB2GGFAM2XGX6RDT.TEENFQ3KNWVEA3MCHJNFWFODQI}
```

Cấu trúc cờ thu được khớp chính xác đến từng ký tự so với hàm `_build_marker()`: bao gồm định dạng `<cid>.<team_id>.<nonce>.<sig26>`, trong đó `cid=127`, mã đội `team_id=612`, phần nonce ngẫu nhiên `nonce=IB2GGFAM2XGX6RDT` được kéo nguyên vẹn từ cấu trúc token, và kết lại bằng 26 ký tự chữ số hệ base32 của mã băm HMAC-SHA256. Thành phần chữ ký (`sig`) này không thể bị thao túng tự do do cần đến chìa khoá `FLAG_HMAC_SECRET` trên máy chủ.

## Phục dựng (Reproduce)

```bash
cd read-me-my-fortune
python exploit.py --local
python exploit.py read-my-fortune.pointeroverflowctf.com 9000 "<nhập token còn hạn lấy trên trang web>"
```
