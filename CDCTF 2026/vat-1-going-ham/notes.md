# notes.md - vat-1-going-ham

Input: `files/captured_radio.mp3` (584028 B, sha256 `36a9039cd0dfe841...adca1d07`)
Định dạng cờ đề yêu cầu: `cdctf{...}` (ví dụ trên thẻ: `cdctf{Ex4mpl3_flag}`)

## H1 - Cờ nằm trong container MP3 (appended data / stego byte)
cmd: `node ~/.qoder/skills/ctf-solve/scripts/triage.cjs captured_radio.mp3`
cmd: `python analysis/mp3_frame_walk.py files/captured_radio.mp3`
evidence: entropy 6.494/8, 0 hit với pattern cờ. Đi bộ frame: 2026 frame đều 288 byte,
8 khoảng ngoài frame mỗi khoảng đúng 44 byte, đuôi 144 byte. Dump các khoảng đó: một
khoảng là `49443304 ... TSSE Lavf61.7.103` (ID3v2.4 giữa stream), các khoảng còn lại là
payload frame lỗi header do quá trình re-encode; đuôi file là một frame `FFF3` với payload
toàn `0x55` (frame im lặng được pad).
result: DEAD - không có vùng dữ liệu thừa nào mang nghĩa; mọi byte lạ giải thích được bằng
encoder ffmpeg/LAME.

## H2 - Mode số vô tuyến (RTTY/AFSK, SSTV, FT8)
cmd: `python analysis/spectrogram.py` (scipy STFT, 3 dải 0-12k / 0-1.2k / 0-6k Hz)
evidence: `analysis/spectrogram_0-1200Hz.png` và `analysis/spectrogram_0-6000Hz.png` cho
thấy hài âm trượt liên tục theo thời gian và formant, không có cặp tone đứng yên, không có
chậm điều chế kiểu AFSK 2 tone, không có cấu trúc dòng của SSTV.
result: DEAD - phổ là đặc trưng nguồn giọng nói, không phải tín hiệu điều chế số.

## H3 - DTMF
cmd: `python analysis/dtmf_pitch_probe.py`
evidence: năng lượng trung bình tại 4 tần số thấp `697/770/850/941` là
`0.00066/0.00052/0.00043/0.00047` và 4 tần số cao `1209/1336/1477/1850` là
`0.00043/0.00039/0.00038/0.00027`, tất cả đều dưới mức tham chiếu broadband `500 Hz =
0.00145` và ngang mức `2000 Hz = 0.00023`. Không ô nào nhô lên.
result: DEAD - không có cặp tone, loại hoàn toàn kênh bàn phím điện thoại.

## H4 - Morse / on-off keying
cmd: `python analysis/envelope_profile.log` (RMS 1 s) và autocorrelation 60 ms trong
`analysis/dtmf_pitch_probe.py`
evidence: có khoảng lặng (giây 6-9, 27-33, 38-41) nhưng ranh giới là hơi thở giữa các cụm
từ, không phải nhịp dot/dash. Autocorrelation cho 884/1617 khung hữu thanh với f0 trung vị
103.9 Hz, p10 85.1 Hz: sóng mang bị biến điệu biên độ liên tục, không phải carrier bật/tắt.
result: DEAD - nhịp điệu là của lời nói; không có trường tone để đo dot/dash.

## H5 - Tiếng người, cần speech-to-text
cmd: `python analysis/asr_base.py` (Whisper `base`, beam 5, word_timestamps)
evidence: ra cả cuộc hội thoại: `Delta team ... This is Eagle 2 ... Flag is 636 4637 467
bravo correction flag is ...`. Phần đọc cờ bị model `base` gom thành số (`636`, `4637`) nên
không dùng trực tiếp.
result: PENDING -> cần per-token đáng tin hơn.

## H6 - ASR lại với model lớn hơn và prompt định hướng bảng NATO
cmd: `python analysis/asr_small.py` (Whisper `small`, beam 10, temperature 0, initial_prompt
chứa bảng chữ cái NATO và các từ chỉ chữ số; chạy trên cả file và riêng đoạn 45-83 s)
evidence: 34 token rõ ràng cho bản `Correction`, `word_timestamps` đếm đúng 34 khung từ;
bản `Repeat` đọc cùng chuỗi đó.
result: OK - đủ dữ liệu để giải mã.

## H7 - Ghép token thành hex
cmd: `python exploit.py files/transcript_small_flagpart.txt`
evidence: lần 1 `6364637467B` (11 ký tự, lẻ, không ghép byte); lần 2 và 3 cùng ra
`63646374667B4E3454305F636F6D6D737D` = 17 byte = `cdctf{N4T0_comms}`.
result: OK - cờ: `cdctf{N4T0_comms}` (2 lần đọc độc lập trùng nhau, prefix và `}` khớp
luật đề).

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại
không thử trùng.
