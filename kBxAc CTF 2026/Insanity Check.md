---
title: "Insanity Check"
category: "Misc"
tags: ["base64", "ascii85", "nested-encoding", "decoy", "stop-condition"]
solve_date: "2026-10-10T21:05:00+07:00"
language: "vi"
points: 100
---

# Insanity Check

**Flag:**

```text
kBxAc{0k"i_?99W..Rc-]1/0&GF?<>U4@M:s:c2Bj;H5>,=Z0>F>ZslJ4^_hF0/Xn\=CF'NC.qAb?>qW#3bCB';_C'j6od1dEH5;@>;J!P6S'T@=%$Uo<A-$^6<meZFXAkd05NjL/jF;#AP=g33GCiB8LZAV/3@QJFYYX"5s[t(2`l"24^;\F2KM>391E#`=&h"'=BRg><%KD94=W`p7R1r?-"&ec5uC--?n5/l}
```

**Input:** một chuỗi Base64 rất dài được đưa trực tiếp trong mô tả bài, không có file đính kèm. Chuỗi bắt đầu bằng `VmpGYVYyRXhXWGxXYkdScVVteEtVMWx0...`, kết thúc bằng `...UmJFcFJWa1JCT1E9PQ==`. Dữ liệu đã chuẩn hóa có 1.400 ký tự ASCII.

## Đề bài

Dữ liệu đầu vào có nhiều lớp Base64. Sau sáu lần decode, marker `here is the flag : ` xác định phần cần dùng làm flag body.

## Phân tích

Chuỗi chỉ sử dụng bảng chữ cái Base64 và có `==` ở cuối. Dùng CyberChef với công thức `From Base64` lặp lại, hoặc Python với `base64.b64decode`, được các độ dài sau:

| Layer | Input bytes | Output bytes |
|---|---:|---:|
| Base64 #1 | 1400 | 1048 |
| Base64 #2 | 1048 | 784 |
| Base64 #3 | 784 | 588 |
| Base64 #4 | 588 | 440 |
| Base64 #5 | 440 | 328 |
| Base64 #6 | 328 | 244 |


Sau **lần giải mã thứ 6**, kết quả không còn là chuỗi Base64 lồng nhau mà xuất hiện dòng:

```text
here is the flag : 0k"i_?99W..Rc-]1/0&GF?<>U4@M:s:c2Bj;H5>,=Z0>F>ZslJ4^_hF0/Xn\=CF'NC.qAb?>qW#3bCB';_C'j6od1dEH5;@>;J!P6S'T@=%$Uo<A-$^6<meZFXAkd05NjL/jF;#AP=g33GCiB8LZAV/3@QJFYYX"5s[t(2`l"24^;\F2KM>391E#`=&h"'=BRg><%KD94=W`p7R1r?-"&ec5uC--?n5/l
```

Đây là dấu mốc quan trọng: **phần nằm sau `here is the flag : ` chính là flag body**, kể cả khi các ký tự trông giống ASCII85. Không cắt bỏ dấu nháy kép, gạch chéo ngược, dấu backtick hoặc các dấu câu khác.

## Bẫy flag giả

Nếu tiếp tục lấy phần sau tiền tố để giải **4 lần ASCII85 rồi thêm 1 lần Base64**, kết quả là:

```text
HeHe_Haa_Hoo_HOO_you_got_the_wrong_flag_maybe_you_misread_something
```

Một ứng viên sai dễ gặp là:

```text
kBxAc{HeHe_Haa_Hoo_HOO_you_got_the_wrong_flag_maybe_you_misread_something}
```

Ứng viên này **đã bị hệ thống từ chối** trong quá trình giải. Câu `you_got_the_wrong_flag_maybe_you_misread_something` là mồi nhử: đường decode sâu hơn vẫn hợp lệ về mặt cú pháp, nhưng không phải điểm dừng mà challenge yêu cầu.

## Lời giải

1. Sao chép nguyên chuỗi Base64 trong mô tả bài vào file `insanity.txt` (một dòng, không thêm tiền tố hoặc dấu ngoặc).
2. Chạy **chính xác 6** bước `From Base64` trong CyberChef hoặc script Python bên dưới. Sử dụng bảng chữ cái Base64 chuẩn.
3. Kiểm tra kết quả bắt đầu bằng `here is the flag : `.
4. Lấy **nguyên văn 225 ký tự ASCII** sau tiền tố, bọc vào `kBxAc{...}`. **Không** áp dụng thêm `From ASCII85`.

Flag đúng:

```text
kBxAc{0k"i_?99W..Rc-]1/0&GF?<>U4@M:s:c2Bj;H5>,=Z0>F>ZslJ4^_hF0/Xn\=CF'NC.qAb?>qW#3bCB';_C'j6od1dEH5;@>;J!P6S'T@=%$Uo<A-$^6<meZFXAkd05NjL/jF;#AP=g33GCiB8LZAV/3@QJFYYX"5s[t(2`l"24^;\F2KM>391E#`=&h"'=BRg><%KD94=W`p7R1r?-"&ec5uC--?n5/l}
```

## Kết quả

Giải mã sâu hơn điểm được marker chỉ định tạo ra một chuỗi decoy, dù các bước decode vẫn hợp lệ. Điểm dừng chính xác là **6 lớp Base64**, không phải lớp plaintext cuối có thể thu được.

## Tái hiện

Cần Python 3.9+. Lưu phần ciphertext ban đầu từ mô tả challenge thành `insanity.txt`, lưu đoạn code dưới đây là `solve_insanity.py` rồi chạy:

```powershell
python solve_insanity.py insanity.txt
```

```python
#!/usr/bin/env python3
"""Stop after exactly six Base64 layers: do NOT decode the ASCII85 flag."""
import base64
from pathlib import Path
import sys

raw = Path(sys.argv[1]).read_text(encoding="ascii").strip().encode("ascii")
for i in range(6):
    decoded = base64.b64decode(raw, validate=True)
    assert base64.b64encode(decoded) == raw, f"Bad Base64 layer {i + 1}"
    raw = decoded
prefix = b"here is the flag : "
assert raw.startswith(prefix), "Unexpected layer-6 plaintext"
flag_body = raw[len(prefix):].decode("ascii")
print("kBxAc{" + flag_body + "}")
```

Kết quả mong đợi:

```text
kBxAc{0k"i_?99W..Rc-]1/0&GF?<>U4@M:s:c2Bj;H5>,=Z0>F>ZslJ4^_hF0/Xn\=CF'NC.qAb?>qW#3bCB';_C'j6od1dEH5;@>;J!P6S'T@=%$Uo<A-$^6<meZFXAkd05NjL/jF;#AP=g33GCiB8LZAV/3@QJFYYX"5s[t(2`l"24^;\F2KM>391E#`=&h"'=BRg><%KD94=W`p7R1r?-"&ec5uC--?n5/l}
```


