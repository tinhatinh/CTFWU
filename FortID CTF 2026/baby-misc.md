---
title: "Baby Misc"
category: "Misc"
tags: ["zip", "path-decoding", "long-path", "png-idat"]
solve_date: "2026-10-10"
language: "vi"
---

# Baby Misc

**Flag:** `FortID{D0_or_D0_N07_Th3r3_15_n0_Tri3}`
**Artifact:** `retrieve.zip` (khoảng 344 MB theo bản ghi), 7000 entry có path lồng nhau; mỗi PNG dài 48857 B. Không có instancer. Tác giả: ipaljak.

Trang đề ghi category `intro`; đây là secondary tag, còn category chính là Misc.

## Đề bài

Artifact duy nhất là `retrieve.zip`; không có service hay script.

## Phân tích

### Path chứa data cần giải mã

7000 entry trong archive có path lồng nhau, với các directory segment biểu diễn bằng số thập phân. Mỗi số là mã ASCII của một ký tự. Full path có 99–273 segment.

Entry dài nhất có 273 segment, khiến full path vượt giới hạn `MAX_PATH` 260 của Windows. Vì Explorer và `Expand-Archive` cần tạo directory tree qua OS path API, cả hai đều thất bại. Có thể đọc tên entry trực tiếp từ ZIP central directory mà không extract file.

### Toàn bộ ảnh cùng kích thước, khác nhau ở IDAT

Mọi PNG thành viên dài đúng 48857 byte. Kích thước bằng nhau làm mất dấu kiểm nhanh nhất (size), và vì cấu trúc chunk là như nhau nên header cũng không nói được gì. Băm nội dung các chunk IDAT — phần pixel payload, cũng là phần duy nhất thực sự khác giữa các ảnh — tách tập hợp 7000 ảnh thành hai nhóm 6999/1. Ảnh nằm lẻ một mình là ảnh cần đọc.

File size không phân biệt được các ảnh; IDAT digest xác định ảnh duy nhất khác biệt.

### Decode các segment dạng số trong path

Output đã lưu:

```text
segments: 37 all ASCII 33-126: True | FLAG: FortID{D0_or_D0_N07_Th3r3_15_n0_Tri3}
```

`decode()` chỉ giữ các path segment dạng số có mã ASCII từ 33 đến 126. Các segment khác bị bỏ qua, nên 37 giá trị còn lại tạo thành flag dù full path có 99–273 segment. Đối chiếu 37 mã ASCII với flag:

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

Đoạn code kiểm tra phép chuyển từng ký tự của flag sang mã ASCII; nó không duyệt archive.

## Lời giải

Các bước giải:

1. Đọc tên entry từ ZIP central directory, không extract file.
2. Gom ảnh theo digest của nội dung IDAT; nhóm có kích thước 1 là mục tiêu.
3. Chuyển các segment thập phân trong path thành ký tự; chỉ giữ mã ASCII 33–126 rồi ghép thành flag.

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

Code trên đọc trực tiếp `retrieve.zip`. Theo bản ghi, archive có 7000 entry, mỗi ảnh 48857 B, IDAT group sizes là 6999/1 và output có 37 segment; các kết quả này chưa được tái chạy vì artifact không có trong workspace. Path của entry thuộc group đơn lẻ được truyền vào `decode()` để lấy flag.

## Kết quả

```text
FortID{D0_or_D0_N07_Th3r3_15_n0_Tri3}
```

Bản ghi lưu flag 37 ký tự decode từ các path segment in được. Không có `retrieve.zip` trong workspace để kiểm tra lại entry đích và IDAT group sizes.

## Tái hiện

Cần `retrieve.zip`. Chỉ Python 3 standard library (`zipfile`, `hashlib`, `struct`) là đủ; không cần giải nén, không cần thư viện ảnh.

```console
$ python -c "import zipfile; z=zipfile.ZipFile('retrieve.zip'); print(len(z.infolist()))"
```

Lệnh này đếm entry từ central directory mà không giải nén; bản ghi của bài là 7000. Sau đó lưu block python trong mục Lời giải thành `reader.py` và chạy `python reader.py`, rồi đưa `info.filename` của entry thuộc nhóm IDAT lẻ vào `decode()`. Trên Linux có thể xem tên mà không chạm giới hạn path Windows bằng `unzip -Z1 retrieve.zip` (liệt kê tên, không ghi file). Trên Windows, `Expand-Archive` và Explorer không đi hết cây này; giữ nguyên thao tác đọc trực tiếp từ file ZIP.

Toàn bộ phép tái hiện chạy cục bộ trên artifact, tốn I/O cho 344 MB đọc tuần tự nhưng không tạo file nào trên đĩa.
