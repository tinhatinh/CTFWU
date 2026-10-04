# notes.md - diggity-network

Input: `files/network_traffic_with_a_flag_in_there.pcapng` (104320 B, sha256 `2b77a67c14d61cbabd48ca338cbe86188f5bd5c5ff700e00546fe9b6bbd67fa3`)
Định dạng cờ đề yêu cầu: `cdctf{...}`
Ngày solve có bằng chứng trong chat: 2026-10-04. Không có bằng chứng giờ/phút để ghi timestamp chi tiết.

## H1 - Cờ nằm trong chuỗi ASCII của capture

cmd: `python analysis/scan_strings.py`; Python đọc bytes của file và dùng `re.findall(rb'[\x20-\x7e]{6,}', b)`, lọc chuỗi chứa flag/cdctf/cat/net (không phân biệt hoa thường).

evidence: `analysis/strings.txt`: `Matching printable strings: 0`.

result: DEAD - quét ASCII trực tiếp không tìm ra cờ; ảnh khôi phục sau đó cho thấy chữ viết tay là nội dung ảnh.

## H2 - HTTP/TLS cần export hoặc giải mã

cmd: `tshark -n -r files/network_traffic_with_a_flag_in_there.pcapng -q -z io,phs -z conv,tcp`

evidence: `analysis/triage.txt`: 59 frame, 101971 byte, Ethernet/IP/TCP; một kết nối 172.21.0.3:34012 ↔ 172.21.0.2:8080. Không có HTTP/TLS được nhận diện. Frame 4 bắt đầu ngay bằng PNG magic.

result: DEAD - dữ liệu có thể khôi phục trực tiếp từ TCP payload.

## H3 - Payload là file PNG gửi qua netcat

cmd: `tshark -n -r files/network_traffic_with_a_flag_in_there.pcapng -Y "tcp.len > 0" -T fields -e frame.number -e tcp.stream -e ip.src -e tcp.srcport -e tcp.seq -e tcp.len -e tcp.payload`

evidence: `analysis/payload_headers.tsv` lưu metadata và 8 byte đầu payload. Frame 4, stream 0, 172.21.0.3:34012, seq 1, 2048 byte; đầu payload là 89504e470d0a1a0a. Script chọn chiều gửi trong stream 0 và ghép theo sequence number.

result: OK - 30 payload tạo PNG 98061 byte.

## H4 - Kiểm chứng file và đọc cờ

cmd: `python exploit.py files/network_traffic_with_a_flag_in_there.pcapng`

evidence: `analysis/verification.txt`: PNG 724x390, 14 chunk có CRC hợp lệ, không gap, không retransmission mâu thuẫn, không byte thừa sau IEND. Cấu trúc gồm IHDR, 12 IDAT, IEND. Công cụ xem ảnh trong chat hiển thị cờ viết tay `cdctf{file_over_http}`.

result: OK - cờ đã đọc trực tiếp từ ảnh và lưu vào flag.txt. Khi tái chạy, nhập lại bản chép cờ đã quan sát vào stdin; script in rõ manual transcription. Không dùng OCR, không hardcode cờ trong exploit.py, không coi nhập cờ là kiểm chứng tự động nội dung ảnh.

## Output tái chạy

```text
TCP stream 0: 30 payloads, 98061 bytes
PNG: 724x390, 14 chunks, all CRCs valid
Saved: analysis/recovered_flag.png
Manual visual step: open the PNG and transcribe its handwritten flag.
[+] flag (manual transcription): cdctf{file_over_http}
```

Chưa quan sát được submission được hệ thống chấp nhận. Không ghi độ khó hay tên tác giả khi đề không cung cấp.
