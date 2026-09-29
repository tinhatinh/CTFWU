# Mic Drop — Hardware (Medium)

**Flag:** `H7CTF{7f0cb1b6-34ee-46c0-945b-1f069dff2a29}`

## Đề bài

Cầu truyền hình AV trong phòng họp trực tuyến bị chiếm quyền, và nó vẫn đang phát trực tiếp căn phòng.
Kẻ tấn công đi nhờ chính luồng live feed đó để tống bí mật ra ngoài, mà "không ai trong phòng họp nghe thấy
điều gì bất thường". Target là một instance chạy `mediamtx` (MediaMTX), cho một URL HTTPS.

Nhiệm vụ: đọc được dữ liệu kẻ tấn công gửi ra.

## Phân tích ban đầu

`curl -I /` trả `Server: mediamtx`, nên đây là một media streamer chứ không phải web app. MediaMTX phục vụ
HLS theo route `<tên-path>/index.m3u8`, còn API `/v3/...` ở đây bị đóng (301 rồi 404). Thử một danh sách
tên path theo ngữ cảnh phòng họp thì `/boardroom/index.m3u8` trả 200 với `application/vnd.apple.mpegurl`:

```
#EXT-X-STREAM-INF:BANDWIDTH=186669,...,CODECS="mp4a.40.2"
main_stream.m3u8
```

`main_stream.m3u8` là playlist live, các segment `*_main_segN.ts` dài ~6.9 s, cửa sổ trượt giữ ~7 segment.
Tải 7 segment được 47.85 s audio AAC mono 48 kHz.

Hai câu hỏi cần trả lời theo thứ tự: dữ liệu nằm trong container hay trong tín hiệu? và nếu trong tín
hiệu thì ở dạng điều chế nào?

## Các hướng đã loại

1. Dữ liệu nhét trong MPEG-TS (`analysis/tsparse.py`): PID histogram chỉ có `0x0100` audio và PAT/PMT;
   0 packet có adaptation field nên không có kênh stuffing; 0 ID3 tag trong ADTS; không có
   `stream_type` private/subtitle; không có chuỗi khả nghi nào trong raw TS.
2. Carrier siêu thanh (`analysis/spectrum.py`): năng lượng dải 17-24 kHz chỉ ngang noise floor
   (rms 0.0005 so với 0.051 của dải 2-3 kHz), không có đỉnh đơn nào nhích lên. Vậy "không ai nghe thấy gì"
   không phải vì ngoài tầm nghe.
3. LSB của PCM: nguồn là AAC lossy, quantiser đã phá bit thấp trước khi tới ta; phổ lại là tổ hợp tone
   rõ ràng chứ không phải noise-like payload.
4. Sai baud khi giải điều chế (xem Bước 3): 1200 baud là mặc định của Bell 202 nên rất dễ đoán ẩu.

## Chuỗi khai thác

**Bước 1 - Nhìn phổ bằng mắt.** `ffmpeg -lavfi showspectrumpic` cho ảnh phổ (đã lưu `analysis/spectrogram.png`).
Thấy ngay 9 burst năng lượng, mỗi burst ~1.7 s, lặp lại đều đặn cách ~5.68 s, nằm gọn trong 0.8-2.5 kHz.
Định kỳ hoàn hảo như vậy là chữ ký của một message được phát lại liên tục trên live feed, không phải tiếng phòng.

**Bước 2 - Đọc cấu trúc burst** (`analysis/bursts.py`). Mỗi burst mở đầu bằng 1200 Hz thuần ~160 ms,
rồi xuất hiện đồng thời hai nhóm năng lượng quanh 1200 Hz và 2200 Hz kèm sideband do chuyển mạch liên tục.
1200/2200 Hz chính là cặp mark/space của chuẩn Bell 202 - AFSK half-duplex cổ điển, và 160 ms âm thuần
đầu burst chính là carrier mark (preamble) trước khi có dữ liệu.

**Bước 3 - Đo baud thay vì đoán.** So sánh năng lượng hai dải theo từng cửa sổ bit ở các baud khác nhau,
đếm mật độ transition (`analysis/afsk.py`):

```
baud  300: 508 bits, 268 transitions, trans/bit=0.528
baud  600: 1018 bits, 272 transitions, trans/bit=0.267
baud 1200: 2038 bits, 274 transitions, trans/bit=0.134
```

Tín hiệu chuyển trạng thái gần như mỗi bit ở 300 baud và giảm đúng theo hệ số ở các baud cao hơn, tức
**300 baud là tốc độ thật**; 1200 chỉ là mặc định của chuẩn Bell 202. Kiểm tra số học cũng khớp:
43 ký tự × 10 bit (8N1) = 430 bit = 1.43 s, cộng 160 ms preamble ≈ 1.6 s, đúng độ dài burst.

**Bước 4 - Giải điều chế.** Với mỗi bit, so sánh biên độ sau bandpass ±120 Hz quanh 1200 Hz và 2200 Hz,
`mark > space` là 1; cắt chuỗi bit theo start-bit, gom 8 bit LSB-first thành ASCII:

```
H7CTF{7f0cb1b6-34ee-46c0-945b-1f069dff2a29}
```

**Bước 5 - Xác minh chéo.** Chạy decode cho cả 9 burst: 8 burst trọn vẹn cho ra chuỗi giống hệt nhau,
burst thứ 9 bị cắt giữa chừng (`...dff`) đúng vì cửa sổ capture kết thúc giữa chừng. Một decode tình cờ
không thể lặp lại nguyên văn 8 lần; đây cũng là bằng chứng message được phát loop trên live feed.

## Flag
```bash
python exploit.py https://web-021fc06a681e8dca.web.h7tex.com/boardroom 60   # khi instance còn chạy
python exploit.py files/352f5b477507_main_seg15.ts                          # chạy lại từ segment đã lưu
```

Output thật của lệnh thứ hai (một segment TS 159.048 B đã lưu trong `files/`):

```
[*] offline TS files/352f5b477507_main_seg15.ts: 159048 B
[*] 6.85 s of PCM at 48000 Hz
[*] 1 burst(s)
      0.98-  2.68s  'H7CTF{7f0cb1b6-34ee-46c0-945b-1f069dff2a29}'
[+] flag: H7CTF{7f0cb1b6-34ee-46c0-945b-1f069dff2a29}   (agreed by 1/1 bursts)
```

Cờ được capture lúc instance còn sống, từ 7 segment tải trực tiếp (47.85 s audio, 9 burst);
khi đóng gói lại script để kiểm tra thì instance đã bị stop nên chỉ chạy được trên artifact đã lưu.
Phần xác minh 8/9 burst giống hệt nhau lấy từ `analysis/afsk.py` chạy trên 47.85 s audio đó (xem `notes.md` H6).
