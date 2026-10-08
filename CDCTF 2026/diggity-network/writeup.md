# Diggity Network - Forensics (500 điểm)

**Flag:** `cdctf{file_over_http}` · **Files:** `network_traffic_with_a_flag_in_there.pcapng`, 104320 byte, sha256 `2b77a67c14d61cbabd48ca338cbe86188f5bd5c5ff700e00546fe9b6bbd67fa3`

## Đề bài

Đề cho một capture mạng và mô tả người bạn đã dùng `cat` để gửi file chứa cờ vào netcat. Mục tiêu là khôi phục dữ liệu được truyền và tìm cờ dạng `cdctf{...}`. Bài thuộc Forensics, trị giá 500 điểm.

## Phân tích

File là PCAPNG. Thống kê bằng tshark cho thấy 59 frame, tổng 101971 byte ở tầng frame, chỉ gồm Ethernet/IP/TCP. Có một kết nối: `172.21.0.3:34012 → 172.21.0.2:8080`, tương ứng TCP stream 0.

Frame 4 có payload đầu tiên, sequence number tương đối 1, dài 2048 byte. Tám byte đầu là `89 50 4e 47 0d 0a 1a 0a`, chữ ký PNG. Vì netcat gửi byte của file trực tiếp qua TCP, hướng giải là ghép payload phía gửi theo sequence number rồi mở ảnh.

## Hướng đã thử

1. **Tìm cờ dạng chuỗi ASCII trong capture:** quét chuỗi in được chứa `flag`, `cdctf`, `cat` hoặc `net` không có kết quả. Cách tìm trực tiếp này không cho ra cờ; payload PNG giải thích vì sao cờ viết tay không xuất hiện dưới dạng plaintext.
2. **Phân tích như HTTP hoặc TLS:** không có lớp HTTP/TLS trong thống kê giao thức, và payload bắt đầu ngay bằng chữ ký PNG. Khôi phục file từ TCP là đủ; không cần giải mã hay export đối tượng HTTP.

Lệnh và bằng chứng của từng hướng được lưu trong `notes.md`.

## Lời giải

**Bước 1 - Xác định kết nối và chữ ký file.** Chạy từ thư mục bài:

```powershell
tshark -n -r files/network_traffic_with_a_flag_in_there.pcapng -q -z io,phs -z conv,tcp
tshark -n -r files/network_traffic_with_a_flag_in_there.pcapng -Y "tcp.len > 0" -T fields -e frame.number -e tcp.stream -e ip.src -e tcp.srcport -e tcp.seq -e tcp.len -e tcp.payload
```

Output đầy đủ của thống kê được lưu tại `analysis/triage.txt`. Kết quả xác định phía gửi là `172.21.0.3`, stream 0.

**Bước 2 - Ghép payload.** `exploit.py` dùng tshark lấy sequence number và payload của chiều gửi. Script sắp theo sequence, phát hiện khoảng trống, kiểm tra phần chồng lặp của retransmission rồi ghi dữ liệu thành `analysis/recovered_flag.png`. Đoạn ghép quyết định:

```python
base = parts[0][0]
data = bytearray()
for seq, payload in parts:
    offset = seq - base
    if offset > len(data):
        raise SystemExit(f"Missing TCP bytes at offset {len(data)}.")
    overlap = min(len(data) - offset, len(payload))
    if data[offset:offset + overlap] != payload[:overlap]:
        raise SystemExit("Conflicting retransmission.")
    data.extend(payload[overlap:])
```

**Bước 3 - Kiểm chứng và đọc ảnh.** Khôi phục được 98061 byte từ 30 payload. PNG có kích thước 724×390, gồm 14 chunk: IHDR, 12 IDAT và IEND. CRC của tất cả chunk hợp lệ, không có byte thừa sau IEND.

![Ảnh chứa cờ khôi phục từ TCP](analysis/recovered_flag.png)

Cờ được đọc trực tiếp từ chữ viết tay trong ảnh. Script chỉ khôi phục và kiểm tra PNG, sau đó nhận bản chép cờ bằng tay. Chuỗi cờ chứa `http`, nhưng dữ liệu trong capture được gửi trực tiếp qua TCP.

## Kết quả

```powershell
python exploit.py files/network_traffic_with_a_flag_in_there.pcapng
```

Sau khi mở ảnh và nhập cờ đã đọc, output thực tế là:

```text
TCP stream 0: 30 payloads, 98061 bytes
PNG: 724x390, 14 chunks, all CRCs valid
Saved: analysis/recovered_flag.png
Manual visual step: open the PNG and transcribe its handwritten flag.
[+] flag (manual transcription): cdctf{file_over_http}
```

Cờ đã lưu trong `flag.txt`. Chưa có bằng chứng submission được hệ thống chấp nhận trong bản ghi.

## Tái hiện

Cần Python 3 và Wireshark/tshark trong PATH. Chạy từ thư mục `diggity-network`, mở `analysis/recovered_flag.png` rồi nhập cờ vào prompt của script. Trên Windows có thể dùng `--open-image` để mở ảnh bằng ứng dụng mặc định.

```powershell
python exploit.py files/network_traffic_with_a_flag_in_there.pcapng --open-image
```

Có thể khôi phục thủ công trong Wireshark: lọc `tcp.stream == 0`, chọn **Follow → TCP Stream**, chọn chiều `172.21.0.3:34012 → 172.21.0.2:8080`, chọn **Raw** và lưu thành PNG.
