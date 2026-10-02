# Welcome Call - Forensics (Medium)

**Flag:** `sun{thankyouforplaying}`
**Files:** `welcomecall.pcap` (181952 B, sha256 `7e0effd30dbd6fd0…`)

## Đề bài

> "I just got a call from the flag factory, they said they were looking for their favorite CTFer?"

Thử thách cung cấp duy nhất một tệp tin mạng định dạng `.pcap`.

## Phân tích ban đầu

Kiểm tra tệp tin cho thấy đây là luồng bắt gói (capture) của một phiên đàm thoại VoIP qua giao thức SIP. Cuộc gọi bắt đầu bằng bản tin `INVITE` từ địa chỉ `192.0.2.10` gửi tới `sip:board@192.0.2.20`, và lần lượt nhận được các phản hồi tiêu chuẩn như `100 Trying`, `180 Ringing`, `200 OK`, kết thúc bằng `ACK`. Giao thức mô tả phiên (SDP) của hai phía thống nhất thông số như sau:

```
m=audio 4000 RTP/AVP 0        a=rtpmap:0 PCMU/8000   a=ptime:20   a=sendonly   (người gọi)
m=audio 4002 RTP/AVP 0        a=rtpmap:0 PCMU/8000   a=ptime:20   a=recvonly   (tổng đài)
```

Điều này có nghĩa là phiên đàm thoại sử dụng luồng âm thanh chuẩn G.711 mu-law với tần số lấy mẫu 8 kHz, mỗi gói tin chứa 20 ms âm thanh, và tín hiệu chỉ truyền theo một chiều duy nhất (từ người gọi đến tổng đài). 
Do hệ thống phân tích không cài đặt sẵn công cụ `tshark`, giải pháp tối ưu là sử dụng thư viện `scapy` để đọc tệp pcap và tự trích xuất nội dung phần tải trọng (payload).

Sau khi kiểm tra kỹ lưỡng các trường dữ liệu của giao thức RTP và xác nhận không có bất kỳ kỹ thuật giấu tin (steganography) nào được áp dụng ở tầng mạng, bước tiếp theo là phân tích trực tiếp sóng âm thanh.

## Chuỗi khai thác

Tiến hành giải mã payload G.711 mu-law sang chuẩn PCM thô:

```python
pcm = audioop.ulaw2lin(payload, 2)     # Tham số width là độ rộng mẫu ĐẦU RA; truyền số 1 sẽ ra chất lượng 8-bit
```

Việc đối chiếu chéo bằng lệnh `ffmpeg -f mulaw -ar 8000 -i payload.raw` cho ra kết quả trùng khớp hoàn toàn: hệ số tương quan `corr(audioop, ffmpeg) = 1.0000`.
*(Chú ý: Trong các lần thử nghiệm trước, do vô tình truyền `width=1` cho hàm giải mã, độ dài tệp âm thanh đã bị tính nhầm thành 7.78 giây thay vì con số chính xác là 15.56 giây).*

Sau khi trích xuất được âm thanh nguyên bản, biểu đồ phổ âm (spectrogram) hiển thị rõ các dải sóng hài và tần số cộng hưởng (formant) liên tục. Tần số cơ bản dao động trong khoảng ~100-125 Hz, phân bổ thành 32 cụm âm riêng biệt, khẳng định chắc chắn đây là giọng nói của con người. Tuy nhiên, khi sử dụng công cụ whisper (với cấu hình model `base`/`small`, tham số `beam=5`, bật nhận diện ngôn ngữ tự động và thêm prompt CTF) kết hợp quét thử qua nhiều dải tốc độ (từ 0.6x đến 4x), kết quả trả về luôn là những câu văn vô nghĩa nhưng mang tính lặp lại ổn định. Điều này loại trừ khả năng model nhận diện lỗi, và cho thấy tín hiệu âm thanh đã bị cố tình biến đổi.

Phép đo mang tính chất quyết định là phân tích tính bất đối xứng giữa sườn lên (onset) và sườn xuống (offset) của các cụm âm. Theo đặc điểm sinh học, tiếng nói con người (khi phát âm thuận chiều) luôn có sườn lên dốc (cường độ tăng đột ngột) và tắt âm chậm. Vì thế, năng lượng ở phần đầu mỗi cụm âm phải mạnh hơn so với phần cuối. Khi tiến hành đo trên toàn bộ 32 cụm âm, kết quả thu được:

```
năng lượng trung bình ở 1/3 phần đầu cụm = 0.0539
năng lượng trung bình ở 1/3 phần cuối cụm = 0.0649   -> tỉ lệ 0.83
```

Chỉ số nghịch đảo này chứng minh âm thanh đã bị đảo ngược thời gian. Bằng cách đảo chiều mảng âm thanh (`x[::-1]`) rồi mới đưa vào công cụ phiên mã, văn bản thu được là:

```
Welcome to Bsides Orlando. The flag that you are looking for is Sun with a left curly
bracket. Thank you for playing right curly bracket. All lowercase, no spaces.
Thank you and have a good one.
```

Cờ được giấu dưới dạng lời đọc mô tả trực tiếp: bắt đầu bằng tiền tố `sun`, tiếp theo là "left curly bracket" (dấu ngoặc nhọn mở `{`), phần thân "thank you for playing", kết thúc bằng "right curly bracket" (dấu ngoặc nhọn đóng `}`), cùng với ràng buộc định dạng "all lowercase, no spaces" (viết thường toàn bộ, không có khoảng trắng):

```
sun{thankyouforplaying}
```

Khuôn dạng này hoàn toàn nhất quán với một bài tập khác của cùng tác giả trong hệ thống giải (`sun{praisethesun}`), tái khẳng định tính chính xác của tiền tố `sun{`.

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
