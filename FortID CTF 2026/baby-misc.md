---
title: "Baby Misc"
category: "Misc"
tags: ["zip", "path-decoding", "long-path", "png-idat"]
solve_date: "2026-10-10"
language: "vi"
---

# Baby Misc

**Flag:** `FortID{D0_or_D0_N07_Th3r3_15_n0_Tri3}`
**Artifact:** `retrieve.zip` (xấp xỉ 344 MB theo bản ghi), 7000 entry đường dẫn lồng nhau, toàn bộ ảnh thành viên có kích thước 48857 B. Không có instancer. Tác giả: ipaljak.

Trang đề xếp bài vào mục `intro` với "140 pts, 75 solves"; danh mục sự kiện hiện ghi 109. FortID chấm điểm động nên hai con số chỉ là hai ảnh chụp tại hai thời điểm. Vì thẻ đề dùng tên mục `intro`, tag `intro` được giữ trong metadata.

## Đề bài

Chỉ có một artifact: `retrieve.zip`. Không có service, không có script. Bài tự giới thiệu bằng chính cấu trúc của archive — và việc mở archive theo cách thông thường đã là một phần của lời giải.

## Phân tích

### Đường dẫn là dữ liệu, không phải chỗ chứa file

7000 entry của archive dùng đường dẫn lồng nhau, mỗi thành phần thư mục là một số nguyên thập phân. Các số đó là mã ASCII của một ký tự, tức một segment ứng một ký tự. Số segment đo được trên các entry của archive nằm trong khoảng 99 đến 273.

Entry dài nhất có 273 segment. Với mỗi segment 2–3 chữ số, chuỗi đường dẫn đầy đủ vượt ngưỡng `MAX_PATH` 260 của Windows, và đó là lý do Explorer lẫn `Expand-Archive` thất bại trên archive này: cả hai đều đi qua API đường dẫn của OS khi tạo cây thư mục. Lối thoát là reader không phụ thuộc đường dẫn: tên entry nằm trong central directory của ZIP, đọc trực tiếp từ file mà không ghi bất kỳ thứ gì ra đĩa.

### Toàn bộ ảnh cùng kích thước, khác nhau ở IDAT

Mọi PNG thành viên dài đúng 48857 byte. Kích thước bằng nhau làm mất dấu kiểm nhanh nhất (size), và vì cấu trúc chunk là như nhau nên header cũng không nói được gì. Băm nội dung các chunk IDAT — phần pixel payload, cũng là phần duy nhất thực sự khác giữa các ảnh — tách tập hợp 7000 ảnh thành hai nhóm 6999/1. Ảnh nằm lẻ một mình là ảnh cần đọc.

So sánh kích thước không phân biệt được các ảnh trong bộ dữ liệu đã ghi nhận; digest IDAT giúp xác định ảnh khác biệt.

### Giải mã các segment in được trong đường dẫn

Đầu ra đã lưu từ bước giải mã:

```text
segments: 37 all ASCII 33-126: True | FLAG: FortID{D0_or_D0_N07_Th3r3_15_n0_Tri3}
```

Hàm `decode()` chỉ giữ các thành phần đường dẫn là số và có mã ASCII từ 33 đến 126; các thành phần khác bị bỏ qua. Vì vậy 37 thành phần được giữ lại có thể tạo thành chuỗi cờ dù đường dẫn đầy đủ có 99–273 thành phần. Đối chiếu với xâu cờ cho cùng 37 mã ký tự:

```python
FLAG = "FortID{D0_or_D0_N07_Th3r3_15_n0_Tri3}"

segments = [str(ord(ch)) for ch in FLAG]        # one path segment per character
print("segments:", len(segments))
print("all ASCII 33-126:", all(33 <= ord(ch) <= 126 for ch in FLAG))
print(segments)
```

```text
segments: 37
all ASCII 33-126: True
['70', '111', '114', '116', '73', '68', '123', '68', '48', '95', '111', '114', '95', '68', '48', '95', '78', '48', '55', '95', '84', '104', '51', '114', '51', '95', '49', '53', '95', '110', '48', '95', '84', '114', '105', '51', '125']
```

Block kiểm tra quy ước giải mã từ chuỗi cờ đã lưu; nó không tái tạo phép duyệt archive.

## Lời giải

Ba việc, theo thứ tự:

1. Đọc tên entry từ central directory bằng reader không phụ thuộc API đường dẫn của OS (không giải nén).
2. Gom ảnh theo digest của nội dung IDAT; nhóm có kích thước 1 là mục tiêu.
3. Giải mã dãy segment thập phân của đường dẫn thành ký tự, kiểm mọi mã rơi trong 33–126, in xâu.

```python
import hashlib
import struct
import zipfile

zf = zipfile.ZipFile("retrieve.zip")           # central directory only, nothing is extracted
infos = zf.infolist()
print("entries:", len(infos))
print("distinct member sizes:", sorted({info.file_size for info in infos}))


def idat_digest(data):
    h = hashlib.sha1()
    pos = 8                                     # skip the 8-byte PNG signature
    while pos + 8 <= len(data):
        ln, typ = struct.unpack(">I4s", data[pos:pos + 8])
        if typ == b"IDAT":
            h.update(data[pos + 8:pos + 8 + ln])
        pos += 12 + ln
    return h.hexdigest()


groups = {}
for info in infos:
    groups.setdefault(idat_digest(zf.read(info)), []).append(info.filename)
print("distinct IDAT digests:", len(groups))
print("group sizes:", sorted(len(v) for v in groups.values()))


def decode(name):
    out = []
    for seg in name.strip("/").split("/"):
        if seg.isdigit() and 33 <= int(seg) <= 126:
            out.append(chr(int(seg)))
    return "".join(out), len(out)
```

Khung trên là phần thao tác trực tiếp trên `retrieve.zip`; các con số 7000 entry, 48857 B cho mọi ảnh, phân hoạch 6999/1 và dòng `segments: 37` là kết quả đã ghi nhận khi chạy trên artifact, chưa được chạy lại trong bài viết này. Khi `group sizes` in ra `[1, 6999]`, đường dẫn của entry thuộc nhóm lẻ là đường dẫn đưa vào `decode()`; xâu trả về kèm assertion 33–126 chính là cờ.

## Kết quả

```text
FortID{D0_or_D0_N07_Th3r3_15_n0_Tri3}
```

Bản ghi lưu candidate 37 ký tự được giải mã từ các segment đường dẫn in được. Do không có `retrieve.zip` tại đây, chưa thể kiểm tra lại entry mục tiêu và phân hoạch IDAT 6999/1.

## Tái hiện

Cần `retrieve.zip`. Chỉ Python 3 standard library (`zipfile`, `hashlib`, `struct`) là đủ; không cần giải nén, không cần thư viện ảnh.

```console
$ python -c "import zipfile; z=zipfile.ZipFile('retrieve.zip'); print(len(z.infolist()))"
```

Lệnh này đếm entry từ central directory mà không giải nén; bản ghi của bài là 7000. Sau đó lưu block python trong mục Lời giải thành `reader.py` và chạy `python reader.py`, rồi đưa `info.filename` của entry thuộc nhóm IDAT lẻ vào `decode()`. Trên Linux có thể xem tên mà không chạm giới hạn đường dẫn Windows bằng `unzip -Z1 retrieve.zip` (liệt kê tên, không ghi file). Trên Windows, `Expand-Archive` và Explorer không đi hết cây này; giữ nguyên thao tác đọc trực tiếp từ file ZIP.

Toàn bộ phép tái hiện chạy cục bộ trên artifact, tốn I/O cho 344 MB đọc tuần tự nhưng không tạo file nào trên đĩa.
