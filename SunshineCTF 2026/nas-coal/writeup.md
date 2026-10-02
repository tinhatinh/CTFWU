# NAS Coal — Forensics (Medium)

**Flag:** `sun{yup_issa_gem}`
**Files:** `gem_collection.pptm` (2229848 byte, sha256 `929726804037cc9b2e8779814aabf88361a6f4035ca1d93803662bdee543e855`)

## Đề bài

> "someone put coal in my gem collection :'^(" 

Thử thách này chỉ cung cấp duy nhất một tệp `.pptm` (PowerPoint có chứa Macro) mà không đi kèm bất kỳ dịch vụ mạng hay máy chủ (instance) nào. Mục tiêu của người chơi là phải truy tìm bằng được cờ định dạng `sun{...}` bị cất giấu tinh vi bên trong bộ sưu tập "đá quý" này. Điểm thú vị là trong tập tin trình chiếu có chứa rất nhiều hình ảnh các loại đá quý đan xen với ảnh chế (meme), và chỉ duy nhất một bức ảnh JPEG lạc loài được ngầm ám chỉ là cục "than" (coal) như mô tả của đề bài.

## Phân tích ban đầu

Định dạng `.pptm` (Microsoft PowerPoint 2007 Macro-Enabled Presentation) về bản chất chính là một tập tin nén ZIP chứa các tệp XML cấu trúc và mã VBA bên trong. Khi tiến hành giải nén và kiểm tra thủ công, có một vài chi tiết bất thường đáng chú ý:

1. Thư mục `ppt/media/` chứa 6 tập tin hình ảnh phục vụ cho 5 slide, bao gồm năm file `.png` và một file `.jpg` có tên `image1.jpg&w=1920&q=75`. Đây chính là tệp JPEG duy nhất và nó hoàn toàn khớp với hình ảnh "cục than" được đề cập trong đề bài.
2. Tệp cấu hình `docProps/app.xml` khai báo các thông số: `Slides=5, Notes=0, HiddenSlides=0`, cho thấy không hề có slide ẩn nào tồn tại.
3. Trên Slide số 5 có một hộp thoại (textbox) chứa dòng chữ `> mfw olevba oneshot chall`. Đây là một gợi ý cực kỳ rõ ràng từ tác giả hướng người chơi sử dụng công cụ phân tích macro `olevba`.

## Chuỗi khai thác

**Bước 1: Trích xuất mã macro bằng oletools**

Sử dụng công cụ `olevba` để mở tệp tin `ppt/vbaProject.bin` (đây là tệp OLE lưu trữ mã macro nằm ẩn sâu trong tệp ZIP) nhằm phân tích module `MediaCache`:

```bash
pip install --index-url https://pypi.org/simple oletools
olevba gem_collection.pptm
```

Kết quả trích xuất thu được đoạn mã sau:

```vba
Public Sub RefreshCache()
    Dim encoded As String
    Dim commandLine As String
    encoded = "JABjAGEAbQBwAGEAaQBnAG4AIAA9ACAAJwBzAHUAbgB7AHkAdQBwAF8AaQBzAHMAYQBfAGcAZQBtAH0AJwANAAoA..."
    commandLine = "powershell.exe -NoProfile -EncodedCommand " & encoded
    Debug.Print commandLine
End Sub
```

Đoạn macro trên chứa một chuỗi ký tự được mã hoá Base64 khá dài. Nó lợi dụng một tên miền mang đuôi `.invalid` (hoàn toàn không tồn tại trên thực tế) và chỉ in lệnh ra bảng điều khiển (console) thông qua hàm `Debug.Print` thay vì thực thi lệnh PowerShell thực sự. Đây rõ ràng là một mồi nhử tinh vi để đánh lừa các hệ thống phân tích mã độc tĩnh. Dẫu vậy, bản thân chuỗi bị mã hoá lại ẩn chứa thông tin quan trọng nhất của bài.

**Bước 2: Giải mã tham số `-EncodedCommand`**

Một đặc tính cần lưu ý là PowerShell luôn yêu cầu chuỗi truyền vào tham số `-EncodedCommand` phải được mã hoá ở định dạng UTF-16LE. Chính vì sự khác biệt về mã hoá bộ ký tự này, lệnh `grep` thông thường sẽ hoàn toàn bất lực trong việc tìm kiếm chuỗi `sun{` nếu chỉ quét thô trên file. Việc chúng ta cần làm là tự động trích xuất và giải mã đoạn Base64 này để lấy cờ:

```python
import re
import base64

B64_RUN = re.compile(rb"[A-Za-z0-9+/=]{80,}")
FLAG    = re.compile(rb"sun\{[^}\n]{1,120}\}")

for m in B64_RUN.finditer(vba_bin):
    s = m.group(); s = s[: len(s) // 4 * 4]
    for skip in range(4):
        raw = base64.b64decode(s[skip:])
        text = raw.decode("utf-16-le", errors="ignore").encode("latin-1", "ignore")
        if FLAG.search(text):
            yield text
```

**Bước 3: Tổng hợp kết quả giải mã**

Đoạn Base64 thực sự nằm tại offset 4117 của tệp `vbaProject.bin` với tổng chiều dài 584 byte. Khi áp dụng phương pháp giải mã UTF-16LE, nó hiển thị nội dung nguyên bản như sau:

```powershell
$campaign = 'sun{yup_issa_gem}'
$source = 'https://gem-cache.example.invalid/coal.bin'
$destination = 'coal.bin'
[pscustomobject]@{Operation='download'; Campaign=$campaign; Source=$source; Destination=$destination}
```

Quá trình rà soát lại toàn bộ tệp tin đã xác nhận đây là chuỗi cờ duy nhất hợp lệ. Mọi phương pháp tiếp cận khác như cố gắng phân tích giấu tin LSB trên các file PNG hay kiểm tra kỹ thuật giấu dữ liệu qua hệ số DCT của file JPEG "than" đều đi vào ngõ cụt và không trả về bất kỳ kết quả nào.

## Flag
```bash
python exploit.py files/gem_collection.pptm
```

```text
[*] files/gem_collection.pptm -> ppt/vbaProject.bin = 13312 byte
[+] PowerShell -EncodedCommand giai ma duoc:
    $campaign = 'sun{yup_issa_gem}'
    $source = 'https://gem-cache.example.invalid/coal.bin'
    $destination = 'coal.bin'
    [pscustomobject]@{Operation='download'; Campaign=$campaign; Source=$source; Destination=$destination}
[+] CO: sun{yup_issa_gem}
```
