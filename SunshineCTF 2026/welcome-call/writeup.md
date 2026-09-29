# Welcome Call — Forensics (Medium)

**Flag:** `sun{thankyouforplaying}`
**Files:** `welcomecall.pcap` (181952 B, sha256 `7e0effd30dbd6fd0…`)

## Đề bài

"I just got a call from the flag factory, they said they were looking for their favorite CTFer?"
Một file pcap duy nhất.

## Phân tích ban đầu

Capture là một phiên VoIP: SIP `INVITE` từ `192.0.2.10` tới `sip:board@192.0.2.20`, trả lời bằng
`100 Trying` / `180 Ringing` / `200 OK` / `ACK`. SDP hai phía thống nhất:

```
m=audio 4000 RTP/AVP 0        a=rtpmap:0 PCMU/8000   a=ptime:20   a=sendonly   (caller)
m=audio 4002 RTP/AVP 0        a=rtpmap:0 PCMU/8000   a=ptime:20   a=recvonly   (board)
```

Tức là một luồng audio G.711 mu-law 8 kHz, 20 ms một packet, chỉ một chiều có tiếng.
Máy không có tshark, nên dùng `scapy` đọc pcap và tự ghép payload.

Trước khi nghe nội dung, loại các chỗ giấu kiểu "dữ liệu giả giọng":

| kiểm tra | kết quả |
| --- | --- |
| sequence number | 778 packet, 0 gap |
| RTP timestamp | delta luôn 160 mẫu |
| SSRC | duy nhất `48271739` |
| telephone-event (PT 101) | không có -> không có DTMF |
| Goertzel 697/770/852/941 x 1209/1336/1477 trên audio | không có cặp tone |
| LSB bit 0/1/7 của payload mu-law | nhiễu |
| chuỗi ASCII trong pcap | `xor`/`rot`/`HINT` chỉ là trùng hợp: byte mu-law lúc im lặng nằm ngay vùng 0x60-0x7E, tạo tới 3733 "ASCII run" giả |

Vậy cờ phải nằm trong nội dung âm thanh.

## Chỗ mình tự đánh lừa mình (quan trọng nhất)

Bản đầu mình tự viết hàm giải mã mu-law. Mãi tới khi đối chiếu với stdlib mới phát hiện nó sai cả 256 mã  -  ví dụ mã `0x00` cho ra `-126943` trong khi giá trị đúng là `-32124` (trượt ~4 lần và tràn int16).

Hậu quả dây chuyền:

- WAV phát ra là rác, nhưng rác này có biên độ và phổ *giống giọng người*, nên spectrogram trông hoàn toàn hợp lý.
- Whisper trên cái rác đó sinh hallucination rất "có vẻ tin": `"I was a dead man"` lặp 7 lần, và một bản khác `"a girl in law"` lặp lại. Mình suýt kết luận "chỉ là cuộc gọi thoại bình thường, không có gì".
- Mọi kết luận về metadata/stego vẫn đúng (chúng chỉ dùng payload gốc), nhưng mọi kết luận về *nội dung audio* trước thời điểm sửa decoder đều vô giá trị.

Sửa bằng cách dùng đúng đồ có sẵn và đối chiếu chéo hai nguồn độc lập:

```python
pcm = audioop.ulaw2lin(payload, 2)     # width là độ rộng mẫu ĐẦU RA; truyền 1 sẽ ra 8-bit
```

`ffmpeg -f mulaw -ar 8000 -i payload.raw` cho kết quả trùng khít: `corr(audioop, ffmpeg) = 1.0000`.
(Also: vì truyền `width=1` lần đầu, mình tính nhầm độ dài audio thành 7.78 s thay vì 15.56 s.)

## Chuỗi khai thác

Với audio đúng, spectrogram hiện hài + formant liên tục, fundamental ~100-125 Hz, 32 cụm âm:
đúng là giọng người. Nhưng whisper `base`/`small`, beam=5, có prompt CTF, auto-detect ngôn ngữ,
quét tốc độ 0.6x-4x đều cho văn bản vô nghĩa ổn định -> tín hiệu đã bị biến đổi, không phải lỗi model.

Phép đo quyết định là bất đối xứng onset/offset của các cụm âm. Tiếng người thuận chiều có khởi
phát dốc và tắt chậm, nên phần đầu cụm phải mạnh hơn phần cuối. Đo trên 32 cụm:

```
năng lượng trung bình 1/3 đầu cụm = 0.0539
năng lượng trung bình 1/3 cuối cụm = 0.0649   -> ratio 0.83
```

Ngược dấu -> audio bị đảo ngược thời gian. `x[::-1]` rồi mới transcribe:

```
Welcome to Bsides Orlando. The flag that you are looking for is Sun with a left curly
bracket. Thank you for playing right curly bracket. All lowercase, no spaces.
Thank you and have a good one.
```

Cờ được *đọc bằng lời mô tả*: prefix `sun`, rồi "left curly bracket", rồi nội dung
"thank you for playing", rồi "right curly bracket", kèm ràng buộc "all lowercase, no spaces":

```
sun{thankyouforplaying}
```

Trùng khuôn với bài cùng tác giả trong chuỗi này (`sun{praisethesun}`), nên tiền tố `sun{` là nhất quán.

## Flag
```
$ python solve_call.py
[2] RTP: 778 packets, 124480 payload bytes, 0 sequence gaps, 0 bad timestamps
[3] mu-law expansion via stdlib audioop
    15.56 s of audio; corr(audioop, ffmpeg) = 1.0000
[5] transcription: Welcome to B-Sides Rolando. The flag ... Sun with a left curly bracket.
    Thank you for playing right curly bracket. All lowercase, no spaces. ...
[+] FLAG: sun{thankyouforplaying}
```
