# Welcome Call - Forensics (Medium)

**Flag:** `sun{thankyouforplaying}`
**Files:** `welcomecall.pcap` (181952 B, sha256 `7e0effd30dbd6fd0…`)

## Đề bài

> "I just got a call from the flag factory, they said they were looking for their favorite CTFer?"

Thử thách cung cấp duy nhất một file mạng định dạng `.pcap`.

## Phân tích ban đầu

Kiểm tra file cho thấy đây là luồng bắt gói (capture) của một phiên đàm thoại VoIP qua giao thức SIP. Cuộc gọi bắt đầu bằng bản tin `INVITE` từ địa chỉ `192.0.2.10` gửi tới `sip:board@192.0.2.20`, và lần lượt nhận được các phản hồi tiêu chuẩn như `100 Trying`, `180 Ringing`, `200 OK`, kết thúc bằng `ACK`. Giao thức mô tả phiên (SDP) của hai phía thống nhất thông số như sau:

```
m=audio 4000 RTP/AVP 0        a=rtpmap:0 PCMU/8000   a=ptime:20   a=sendonly   (người gọi)
m=audio 4002 RTP/AVP 0        a=rtpmap:0 PCMU/8000   a=ptime:20   a=recvonly   (tổng đài)
```
Dùng `scapy` để đọc pcap và ghép RTP payload; môi trường đã thử không có `tshark`.

Kiểm tra sequence number và timestamp để ghép các RTP payload theo thứ tự, rồi giải mã âm thanh theo thông số SDP.

## Chuỗi khai thác

Giải mã payload G.711 mu-law sang chuẩn PCM thô:

```python
pcm = audioop.ulaw2lin(payload, 2)     # Tham số width là độ rộng mẫu ĐẦU RA; truyền số 1 sẽ ra chất lượng 8-bit
```

Việc đối chiếu bằng lệnh `ffmpeg -f mulaw -ar 8000 -i payload.raw` cho ra kết quả trùng khớp: hệ số tương quan `corr(audioop, ffmpeg) = 1.0000`.
*(Chú ý: Trong các lần thử nghiệm trước, do vô tình truyền `width=1` cho hàm giải mã, độ dài file âm thanh đã bị tính nhầm thành 7.78 giây thay vì con số chính xác là 15.56 giây).*

Âm thanh giải mã dài 15.56 giây. Bản phát theo chiều ban đầu khó hiểu; đảo thứ tự sample bằng `x[::-1]` để nghe thông điệp. Các lần thử Whisper trước đó không cho nội dung có nghĩa, nhưng điều đó không tự loại trừ lỗi của model nhận dạng.

Nhật ký có phép đo đầu/cuối của 32 cụm âm như bên dưới. Đây là số liệu bổ sung, không phải tiêu chí chứng minh hướng thời gian của lời nói. Thông điệp được kiểm tra bằng bản audio đã đảo chiều:

```
năng lượng trung bình ở 1/3 phần đầu cụm = 0.0539
năng lượng trung bình ở 1/3 phần cuối cụm = 0.0649   -> tỉ lệ 0.83
```
Bản audio sau khi đảo sample đọc thông điệp sau. Có thể nghe trực tiếp; transcript từ công cụ phiên mã được dùng để đối chiếu:

```
Welcome to Bsides Orlando. The flag that you are looking for is Sun with a left curly
bracket. Thank you for playing right curly bracket. All lowercase, no spaces.
Thank you and have a good one.
```

Cờ được giấu dưới dạng lời đọc mô tả trực tiếp: bắt đầu bằng tiền tố `sun`, tiếp theo là "left curly bracket" (dấu ngoặc nhọn mở `{`), phần thân "thank you for playing", kết thúc bằng "right curly bracket" (dấu ngoặc nhọn đóng `}`), cùng với ràng buộc định dạng "all lowercase, no spaces" (viết thường toàn bộ, không có khoảng trắng):

```
sun{thankyouforplaying}
```
Lời đọc yêu cầu chữ thường và bỏ dấu cách, cho `sun{thankyouforplaying}`.

## Flag
```bash
$ python solve_call.py
[2] RTP: 778 packets, 124480 payload bytes, 0 sequence gaps, 0 bad timestamps
[3] mu-law expansion via stdlib audioop
    15.56 s of audio; corr(audioop, ffmpeg) = 1.0000
[5] transcription: Welcome to B-Sides Rolando. The flag ... Sun with a left curly bracket.
    Thank you for playing right curly bracket. All lowercase, no spaces. ...
[+] FLAG: sun{thankyouforplaying}
```
