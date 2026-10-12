---
title: "Sacrifice"
category: "Forensics"
tags: ["pcap", "ftp-data", "jpeg-stego", "file-carving", "layered-compression"]
solve_date: "2026-10-09"
language: "vi"
---

# Sacrifice

**Flag:** `OWASP{4_50u1_f0r_4_50u1_v0rm1r}`
**Artifact:** `s0ul.pcap` (227,553 B, sha256 `d08f3d1e01ddd3dea611653b2d1fcc1fd10f6e9db2577386ac983c71a27bb76c`, 669 packet). Tác giả: Urvish Bharde.

## Đề bài

Tên bài lấy từ dữ liệu gây nhiễung các bài đã giải của nền tảng; phần mô tả được lưu lại là:

```text
Exfiltrated communication was captured in a packet trace. Retrieve the hidden payload.
```

Easy, 100 điểm. Dòng mở đầu trong README của bundle đi kèm:

```text
Two went down. Only one came back. Find the one who didn't.
```

## Phân tích

### Định dạng và phạm vi trace

`capinfos` đọc từ file cho thấy trace gói gọn trong 669 packet và toàn bộ traffic là loopback — mọi endpoint đều thuộc địa chỉ vòng lại, không có host ngoài. Trace không đi qua mạng nào, nó là dữ liệu gây nhiễun ghi lại một phiên truyền tệp trên máy.

### Phân tầng giao thức

```console
$ tshark -r s0ul.pcap -q -z io,phs
```

Cây phân tầng được ghi lại theo dạng tóm tắt (số liệu giữ nguyên như dữ liệu gây nhiễun ghi, không phải output đầy đủ của `io,phs`):

```text
FTP      : 138 packet
FTP-DATA : ~160 kB payload
```

Toàn bộ khối dữ liệu của trace nằm trong FTP và FTP-DATA: 138 packet điều khiển nhưng xấp xỉ 160 kB payload, tức phần lớn byte trong pcap là nội dung tệp được truyền, không phải header. Hướng phân tích do đó là trích các luồng FTP-DATA và dựng lại tệp, thay vì tìm một payload đơn lẻ trong packet.

### Phiên FTP

Lệnh trích được dùng thực tế:

```console
$ tshark -r s0ul.pcap -Y "tcp.len>0" -T fields -e tcp.stream -e ip.src -e tcp.srcport -e tcp.payload
```

Luồng điều khiển FTP số 3 chứa cặp đăng nhập và danh sách lệnh `STOR`:

```text
USER vormirkeeper
PASS S0ulK33per2014
```

theo sau 22 lệnh `STOR` — 22 tệp được đẩy lên server trong phiên. Danh sách tên tệp lấy từ 22 lệnh này gồm `manifest_*.txt`, `fuel_request*.txt`, `sensor_dump*.bin` và `manifest_final_047.jpg`. `comms.bin` không nằm trong danh sách tên được `STOR`: nó là thành viên của tệp ZIP nối sau ảnh, không phải một tệp truyền riêng. Phần FTP-DATA tương ứng mang nội dung của các tệp này, mỗi tệp là một luồng dữ liệu riêng; payload ở cột `tcp.payload` là hex, cần `binascii.unhexlify` trước khi ghi ra file.

Toàn bộ số liệu dùng ở trên (669 packet, 138 packet FTP, 22 lệnh `STOR`, 290 packet ICMP, một khối `PK\x03\x04` nối sau ảnh, chuỗi trong marker `FFFE` xuất hiện đúng một lần) đã được đo lại trực tiếp trên file `s0ul.pcap` tại thời điểm viết bài. Tên các thành viên bên trong tar thì không đo lại được từ trace: chúng nằm sau các lớp nén nên không xuất hiện dưới dạng chuỗi thô trong pcap.

## Lời giải

### Ảnh JPEG và marker nhúng mật khẩu

Trong số các tệp được `STOR` có `manifest_final_047.jpg`. Ảnh JPEG cho phép các marker nằm ngoài phần dữ liệu ảnh; marker `FFFE` (COM, comment) trong tệp chứa một dòng văn dữ liệu gây nhiễun rõ:

```text
This password might be useful XD : th3_ult1m4t3_s4cr1f1s3
```

`th3_ult1m4t3_s4cr1f1s3` là ứng viên mật khẩu duy nhất xuất hiện trong trace.

Cũng trong tệp này, ngay sau marker kết thúc ảnh `FFD9`, còn dữ liệu nối thêm tại offset 150649. `binwalk` xác nhận:

```text
Zip archive data, encrypted
```

Tệp là một ảnh hợp lệ có một ZIP được append phía sau, và ZIP ở trạng thái mã hoá — khớp đúng với mật khẩu đọc từ marker COM.

### Mở ZIP và bóc các lớp nén

```python
import binascii, bz2, gzip, io, pathlib, tarfile, zipfile

jpg = pathlib.Path("manifest_final_047.jpg").read_bytes()
blob = jpg[150649:]                       # ZIP appended after FFD9
print("carved magic:", blob[:4])

zf = zipfile.ZipFile(io.BytesIO(blob))
zf.set_password(b"th3_ult1m4t3_s4cr1f1s3")
name = zf.namelist()[0]
data = zf.read(name)
print("member:", name, "bytes:", len(data), "magic:", data[:4])

layer = gzip.decompress(data)             # gzip
print("after gzip  :", layer[:4])
layer = bz2.decompress(layer)             # BZh9 -> bzip2
print("after bzip2 :", layer[:4])
layer = gzip.decompress(layer)            # gzip again
print("after gzip2 :", layer[:4])

tf = tarfile.open(fileobj=io.BytesIO(layer))
for m in tf.getmembers():
    if m.isfile():
        print("%9d  %s" % (m.size, m.name))
```

Chuỗi lớp được ghi nhận trong phiên, theo đúng thứ tự bóc:

```text
ZIP (encrypted)  -> comms.bin
comms.bin        -> gzip
gzip output      -> bzip2 (BZh9)
bzip2 output     -> gzip
gzip output      -> tar
tar members      -> comms/<hero>/comm.log
```

Bốn lớp này không tự lộ ra nếu chỉ nhìn `file` trên blob gốc: mỗi lớp chỉ được nhận ra sau khi lớp trước giải nén xong và magic của lớp kế tiếp xuất hiện (`1f 8b` cho gzip, `BZh9` cho bzip2, `ustar` cho tar).

### Chọn comm.log thật và giải mã dòng base64

Tar chứa nhiều thư mục `comms/<hero>/`, mỗi thư mục một `comm.log`. Điểm phân biệt là kích thước: dữ liệu gây nhiễuy tệp `comm.log` có độ dài đúng 300 B và nội dung là dữ liệu ngẫu nhiên, không đọc được; tệp của Natasha dài 3.015 B và là một đoạn hội thoại văn dữ liệu gây nhiễun. Dòng "Find the one who didn't" trong README chỉ ra bước lọc này, và log 3.015 B là log thật.

Bên trong đoạn hội thoại giữa Red Skull và Natasha có một dòng base64:

```console
$ python -c "import base64; print(base64.b64decode('T1dBU1B7NF81MHUxX2Ywcl80XzUwdTFfdjBybTFyfQ=='))"
```

```text
b'OWASP{4_50u1_f0r_4_50u1_v0rm1r}'
```

Câu base64 nằm lồng trong lời thoại nên không tách ra bằng mắt dễ; cách làm trong phiên là quét mọi tệp `comm.log` trong tar, tìm mọi chuỗi có dạng base64 và thử giải mã, nên việc chọn log không phụ thuộc vào tên thư mục:

```python
import base64, glob, pathlib, re

for path in sorted(glob.glob("comms/*/comm.log")):
    raw = pathlib.Path(path).read_bytes()
    hits = []
    for cand in re.findall(r"[A-Za-z0-9+/]{40,}={0,2}", raw.decode("latin-1")):
        try:
            dec = base64.b64decode(cand, validate=True)
        except Exception:
            continue
        if all(32 <= b < 127 for b in dec):
            hits.append(dec)
    print("%6d B  %-28s printable_decodes=%d  %s" % (len(raw), path, len(hits), hits))
```

Tệp được chọn là log 3.015 B của Natasha; các log 300 B không cho chuỗi giải mã in được nào.

## Kết quả

```text
OWASP{4_50u1_f0r_4_50u1_v0rm1r}
```

Cờ được giải mã từ dòng base64 trong `comm.log` của Natasha (tệp 3.015 B lấy ra từ tar), tệp mà chuỗi lớp ZIP -> gzip -> bzip2 -> gzip -> tar cho ra sau khi mở ZIP bằng mật khẩu đọc từ marker COM của ảnh JPEG carve từ FTP-DATA. Toàn bộ chuỗi suy ra từ artifact pcap; không có dịch vụ remote. Chưa lưu phản hồi submission.

## Tái hiện

Cần `tshark`/`capinfos` và `binwalk` (Wireshark CLI), cộng Python 3 stdlib cho phần bóc lớp nén.

```console
$ capinfos s0ul.pcap
$ tshark -r s0ul.pcap -q -z io,phs
$ tshark -r s0ul.pcap -Y "tcp.len>0" -T fields -e tcp.stream -e ip.src -e tcp.srcport -e tcp.payload
$ tshark -r s0ul.pcap -Y "ftp" -T fields -e tcp.stream -e frame.number -e ftp-request -e ftp-request-arg
$ binwalk manifest_final_047.jpg
```

Sau khi dựng lại `manifest_final_047.jpg` từ luồng FTP-DATA, lưu đoạn script trong mục Lời giải thành `solve.py` cùng thư mục và chạy `python solve.py`. Phần ghi tệp từ hex payload dùng `binascii.unhexlify` trên cột `tcp.payload`, ghép theo thứ tự packet của từng `tcp.stream`.

Đường dẫn bên trong tar (`comms/<hero>/comm.log`) phụ thuộc tên thư mục do tác giả đặt; script liệt kê toàn bộ thành viên kèm kích thước để việc chọn tệp 3.015 B không dựa vào tên.
