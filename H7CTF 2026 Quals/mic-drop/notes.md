# notes.md - mic-drop

Input: target `https://web-021fc06a681e8dca.web.h7tex.com` (Server: mediamtx), live HLS.
Định dạng cờ `H7CTF{...}`. Capture dùng để phân tích: 7 segment TS = 47.85 s audio.

## H0 - Đi dò API MediaMTX
cmd: `curl /v3/paths/list`, `/v3/rpcconfig`, `/hls/`, `/whep`, `/api/`...
evidence: mọi route API trả 301 → `/v3/paths/list/` → 404; chỉ 404 thuần. Đi theo hướng route theo tên
  path thì `/boardroom/index.m3u8` trả **200** `application/vnd.apple.mpegurl`
result: OK - không cần API, đã có tên path `boardroom`; media playlist là `main_stream.m3u8`

## H1 - Dữ liệu giấu trong container MPEG-TS
cmd: `python analysis/tsparse.py *_main_seg*.ts`
evidence: PID histogram chỉ có `0x0100` (audio, 4515 pkt) + PAT/PMT (`0x0000`, `0x1000`);
  0 packet có adaptation field; **0 ID3 tag**; không có `stream_type` private/subtitle;
  không có chuỗi `H7CTF`/`flag`/`{` nào có nghĩa trong raw TS
result: DEAD - container sạch, phải vào tín hiệu âm thanh

## H2 - Carrier siêu thanh (ultrasonic FSK)
cmd: `python analysis/spectrum.py room.wav`
evidence: năng lượng dải >17 kHz chỉ ngang noise floor (các đỉnh 17-20 kHz đều ~1900, không có đỉnh nào
  nhích hơn); toàn bộ năng lượng tập trung 1-3 kHz. Dải 2000-3000 Hz rms 0.051 trong khi 18-22 kHz rms 0.0005
result: DEAD - không có sóng cao tần ẩn; "không ai nghe thấy gì" không phải vì ngoài tầm nghe

## H3 - LSB của PCM
cmd: kiểm tra nhanh `triage` + `astats` trên WAV
evidence: audio là AAC lossy được giải mã ra PCM; mọi bit thấp đã bị quantiser phá. Ngoài ra phổ cho thấy
  tín hiệu là tổ hợp tone rõ ràng, không phải noise-like payload
result: DEAD - loại vì sai tính chất kênh (lossy codec)

## H4 - Chuỗi burst và bảng tần số
cmd: `python analysis/bursts.py room.wav`
evidence: 9 burst, mỗi burst ~1.68-1.70 s, cách nhau ~5.68 s. Đầu mỗi burst là **1200 Hz thuần ~160 ms**
  (carrier/mark), sau đó xuất hiện đồng thời hai nhóm ~1200 Hz và ~2200 Hz kèm sideband do khoá liên tục.
  Bảng tần số: 2150/2250/1250/1100/1200/2300... tức hai "đỉnh" quanh 1200 và 2200
result: PENDING - đây chính là cặp mark/space của Bell 202, cần xác định baud

## H5 - Đo baud qua mật độ transition
cmd: `python analysis/afsk.py room.wav`
evidence: với cặp 1200/2200 Hz, tỉ lệ transition/bit: 300 baud = 0.528, 600 = 0.267, 1200 = 0.134.
  300 baud cho xấp xỉ 0.5 (mỗi bit đổi trạng thái) và decode 8N1 ở 300 baud cho chuỗi ASCII 100% in được
result: OK - 300 baud, không phải 1200

## H6 - Giải điều chế và xác minh chéo
cmd: `python exploit.py <target>/boardroom 60`
evidence: cả 8 burst trọn vẹn decodes ra **chuỗi giống hệt nhau**
  `H7CTF{7f0cb1b6-34ee-46c0-945b-1f069dff2a29}`; burst thứ 9 bị cắt vì hết cửa sổ capture
  (đọc tới `...dff` thì dừng) -> đúng hành vi một message phát lặp trên live feed
result: OK - CỜ: `H7CTF{7f0cb1b6-34ee-46c0-945b-1f069dff2a29}`

## Ghi chú môi trường
- Không cài gì thêm: ffmpeg 8.1.1 (TS→PCM + `showspectrumpic`), numpy 2.5.3, `curl` có sẵn.
- `spectrogram.png` trong `analysis/` là ảnh render bằng ffmpeg, nhìn trực tiếp thấy 9 burst.
- Target là instance CTF do user cung cấp, chỉ GET tài nguyên công khai của nó; không quét cổng, không đụng host khác.
