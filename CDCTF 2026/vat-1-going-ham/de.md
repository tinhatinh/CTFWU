# Đề bài - vat-1-going-ham

## Nguyên văn đề

```text
Verbal Authentication Transmissions 1/5: Going HAM
500
OSINT Crypto
b0b

We intercepted this radio transmission between two Crimson Offense field operatives.
They appear to be passing an encoded flag.

Flag format: cdctf{Ex4mpl3_flag}
```

File đính kèm: `captured_radio.mp3`.

Thẻ bài không được lưu ảnh trong phiên này, nên case không có `files/de.png`. Văn bản
trên là nguyên văn phần đề người dùng dán vào chat.

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/captured_radio.mp3` (copy từ: `C:\Users\Administrator\Downloads\captured_radio.mp3`) |
| Kích thước | 584028 byte |
| SHA-256 | `36a9039cd0dfe8416da8acc64a6cd1d4222da5e0312617cb72aff74cadca1d07` |
| Loại file | MP3 with ID3v2 tag; MPEG ADTS layer III v2, 48 kbps, 24 kHz, monaural |
| Độ dài | 97.08 s (2329920 sample @ 24000 Hz) |
| ID3 | 34 byte, một frame `TSSE = Lavf61.7.103`, không có TIT2/COMM |
| Cấu trúc frame | 2026 frame, tất cả 288 byte; 8 khoảng ngoài frame, mỗi khoảng 44 byte; đuôi 144 byte (`analysis/mp3_frame_walk.log`) |
| Nội dung âm | giọng nói, f0 trung vị 103.9 Hz, 884/1617 khung hữu thanh (`analysis/dtmf_pitch_probe.log`) |
| Mode vô tuyến | không có DTMF, không có AFSK/RTTY shift, không có keying Morse |
| Transcript | `files/transcript_small_full.txt`, `files/transcript_small_flagpart.txt` (Whisper `small`, bản `base` ở `analysis/asr_base_raw.log`) |
| Nội dung nghe được | cuộc gọi giữa `Eagle 2` và `Delta team`, cờ được đọc chính tả 3 lần |
| Định dạng cờ | `cdctf{...}` |

## Hướng giải (tóm tắt)

Artifact là tiếng người chứ không phải mode số, nên bước trích xuất dữ liệu là speech to
text. Transcript cho thấy mỗi ký tự của cờ được đọc theo bảng chữ cái NATO, trong đó các
chữ số là chữ số hex thật và `bravo / echo / foxtrot / delta` là các chữ số hex `B E F D`.
Ghép 34 token thành 17 byte hex giải ra `cdctf{N4T0_comms}`. Lần đọc đầu tiên thiếu một
số `6` nên chuỗi hex lẻ và không ghép được byte; phát sóng tự sửa bằng từ `Correction`,
và lần `Repeat` xác nhận lại bản đúng.

## Chạy lại lời giải

Bước ASR cần model Whisper (không commit vào repo):

```bash
ffmpeg -y -i files/captured_radio.mp3 -acodec pcm_s16le -f wav audio.wav
ffmpeg -y -ss 45 -to 83 -i audio.wav -ar 16000 -ac 1 part_45_83.wav
python analysis/asr_small.py          # in transcript + word timestamps -> files/transcript_small_flagpart.txt
```

Bước giải mã chạy bằng stdlib, đọc transcript đã lưu trong repo:

```bash
python exploit.py files/transcript_small_flagpart.txt
```

Kết quả: `cdctf{N4T0_comms}` (đã lưu trong `flag.txt`).

## Ghi chú về thời điểm solve

`tools/solve_times.json` chỉ ghi ngày `2026-10-04`, không ghi giờ. Đồng hồ máy nhảy ~24 giờ
giữa chừng phiên (file sinh đầu phiên mang mtime `2026-10-03T22:1x`, file sinh cuối phiên mang
`2026-10-04T22:0x` trong khi hai nhóm lệnh cách nhau vài phút), nên giờ cục bộ lúc in ra cờ
không truy vết được. Ngày được chốt theo `currentDate` của phiên và theo `date` sau khi đồng hồ
đã chỉnh lại.

