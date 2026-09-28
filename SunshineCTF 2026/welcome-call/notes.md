# notes.md — Welcome Call (VoIP forensics)

## H1 — định hướng: đây là cuộc gọi VoIP
evidence: pcap có SIP INVITE/100/180/200/ACK, SDP `m=audio 4000 RTP/AVP 0`, `PCMU/8000`, `ptime:20`
result: CONFIRMED — một luồng RTP mu-law 8 kHz, 778 packet, 15.56 s, không có telephone-event

## H2 — loại các hướng "cờ giấu trong metadata/stego"
did: kiểm tra sequence continuity, timestamp delta, SSRC, marker bit, LSB của payload mu-law, LSB bit 1 và bit 7, và quét ASCII trong toàn file
evidence:
- 0 sequence gap, delta timestamp luôn 160, một SSRC -> không có packet nào bị giấu/tráo thứ tự
- DTMF Goertzel trên 697/770/852/941 x 1209/1336/1477: không có cặp tone nào
- các bit-plane LSB là nhiễu; chuỗi ASCII 'xor'/'rot'/'HINT' trong pcap chỉ là trùng hợp
  (byte mu-law vùng im lặng rơi đúng 0x60-0x7E, nên có tới 3733 "ASCII run" giả)
result: DEAD — cờ không nằm trong metadata, phải lấy từ **nội dung audio**

## H3 — SAI LẦM CỦA CHÍNH MÌNH: tự viết bảng giải mã mu-law
did: viết `ulaw2lin()` tay trong `analysis/extract_rtp.py`
evidence: đối chiếu với stdlib `audioop.ulaw2lin` trên cả 256 mã -> **sai cả 256**,
    ví dụ mã 0x00: của mình ra -126943, stdlib ra -32124 (trượt ~4x và tràn int16)
hậu quả thật sự:
- WAV đầu ra là rác có biên độ và phổ *giống* tiếng người, nên spectrogram "hợp lý" giả
- ffmpeg `showspectrumpic` + whisper `base` trên rác đó sinh hallucination có vẻ tin cậy
  ("I was a dead man" lặp lại), và mình suýt kết luận "chỉ là cuộc gọi thoại bình thường,
  không có gì trong audio"
- toàn bộ kết luận H2 vẫn đúng (nó chỉ dùng payload gốc), nhưng mọi kết luận về *nội dung*
  audio trước thời điểm này đều vô giá trị
result: DEAD branch — sửa bằng cách dùng `audioop.ulaw2lin(payload, 2)` và đối chiếu chéo
    với `ffmpeg -f mulaw`: `corr(audioop, ffmpeg) = 1.0000`
bài học: chú ý `audioop.ulaw2lin(data, width)` — width là độ rộng mẫu ĐẦU RA (2 = int16);
    truyền 1 sẽ trả mẫu 8-bit và khiến mình tính nhầm độ dài thành 7.78 s

## H4 — audio là giọng người nhưng STT không nhận ra
evidence: spectrogram đúng cho thấy hài + formant liên tục, fundamental ~100-125 Hz, 32 cụm âm
did: whisper `base` (prompt Mĩ, prompt CTF, auto-lang), `small`, beam=5, tắt condition_on_previous_text,
     quét tốc độ 0.6x/0.8x/1.2x/2x/3x/4x
result: vẫn ra văn bản vô nghĩa nhưng *ổn định* -> không phải lỗi model, mà là tín hiệu đã bị biến đổi

## H5 — phép đo quyết định: bất đối xứng onset/offset
evidence: năng lượng trung bình 1/3 đầu mỗi cụm âm = 0.0539, 1/3 cuối = 0.0649, ratio 0.83
         (tiếng người thuận chiều: khởi phát dốc, tắt chậm -> đầu cụm phải mạnh hơn)
         -> dấu hiệu audio bị ĐẢO NGƯỢC thời gian
did: `x[::-1]` rồi transcribe bằng whisper `small`
result: CONFIRMED — ra câu hoàn chỉnh có nghĩa:
    "Welcome to Bsides Orlando. The flag that you are looking for is Sun with a left curly
     bracket. Thank you for playing right curly bracket. All lowercase, no spaces."

## H6 — ghép cờ từ câu đọc
did: cờ được *đọc* bằng lời: "<prefix> [left curly bracket] <body> [right curly bracket],
     all lowercase, no spaces" -> prefix `sun`, body `thank you for playing` -> bỏ khoảng trắng
result: `sun{thankyouforplaying}` (trùng format với bài cùng tác giả: `sun{praisethesun}`)
bug nhỏ đã sửa: regex đầu tiên greedy nuốt cả câu thành `theflagthatyouarelookingforissun{...}`;
    phải bắt từ ngay trước "left curly bracket" trên bản còn dấu cách.

## Chạy lại
`python solve_call.py`  (cần `openai-whisper` + model `small`, đã cài trong phiên này;
 `--no-transcribe` để chỉ xuất WAV đảo ngược)
