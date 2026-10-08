# Verbal Authentication Transmissions 1/5: Going HAM - OSINT + Crypto (500 pts)

**Flag:** `cdctf{N4T0_comms}`
**Files:** `captured_radio.mp3`, 584028 B, sha256 `36a9039cd0dfe8416da8acc64a6cd1d4222da5e0312617cb72aff74cadca1d07`

## Đề bài

Đề cho một file audio duy nhất, `captured_radio.mp3`, nói là bản thu lại cuộc truyền giữa
hai operative của Crimson Offense, trong đó họ "đưa cho nhau một lá cờ đã mã hoá". Thẻ bài
ghi 500 điểm, hạng OSINT + Crypto, tác giả `b0b`, định dạng cờ `cdctf{Ex4mpl3_flag}`. Không
có service từ xa, không có hint kèm theo; toàn bộ dữ kiện nằm trong 97 giây âm thanh.

## Phân tích

`file` báo MP3 có ID3v2.4, MPEG-2 layer III, 48 kbps, 24 kHz, đơn kênh. `exiftool` chỉ ra ID3
dài 34 byte với duy nhất frame `TSSE = Lavf61.7.103`, tức file được sinh ra bằng ffmpeg và
không có metadata mô tả. Duyệt các frame MP3 (`analysis/mp3_frame_walk.py`) cho 2026 khung, tất
cả 288 byte, kèm 8 khoảng ngoài khung mỗi khoảng đúng 44 byte và phần đuôi 144 byte. Dump
các vùng đó: một khoảng là ID3v2.4 khác chèn giữa stream, các khoảng còn lại là payload của
khung bị mất header sau lần re-encode, đuôi file là một khung `FFF3` với dữ liệu toàn `0x55`
(khung im lặng được pad). Không tìm thấy cờ trong các vùng này; lời giải tiếp tục từ nội dung lời đọc.

Phổ tín hiệu mới là thứ định hướng bài. Ba dải phổ (`analysis/spectrogram_0-1200Hz.png`,
`analysis/spectrogram_0-6000Hz.png`) cho thấy một chuỗi hài âm cách nhau ~100 Hz trượt theo
thời gian cùng formant chuyển động, tức nguồn phát là giọng người. Autocorrelation trên khung
60 ms đo được f0 trung vị 103.9 Hz với 884/1617 khung hữu thanh. Bài không phải mode số, bài
là một cuộc gọi radio nói.

## Hướng đã thử

Trước khi chốt đã kiểm tra và loại các kênh sau (log đầy đủ ở `notes.md`):

1. **Stego container**: mọi vùng byte lạ đều giải thích được bằng encoder ffmpeg, entropy
   6.494/8, 0 hit mẫu cờ.
2. **RTTY/AFSK, SSTV, FT8**: không có cặp tone đứng yên, không có cấu trúc dòng.
3. **DTMF**: năng lượng tại 4 tần số thấp và 4 tần số cao của bàn phím đều dưới mức tham
   chiếu broadband, không ô nào nhô lên.
4. **Morse/on-off keying**: các khoảng lặng là ranh giới cụm từ, sóng mang bị biến điệu biên
   độ liên tục chứ không bật/tắt.

## Lời giải

**Bước 1 - Chuyển audio thành văn bản.** Decode sang WAV rồi chạy Whisper trên CPU. Bản
`base` (beam 5) nghe đúng nội dung nhưng gom chuỗi số thành cụm:

```bash
ffmpeg -y -i files/captured_radio.mp3 -acodec pcm_s16le -f wav audio.wav
python analysis/asr_base.py
```

```text
copy wilco eagle 2 flag is 636 4637 467 bravo correction flag is 636 4637 4667 bravo
4-0-3-4-5-4-3-0-5 Foxtrot 6-36 Foxtrot 6- delta 6- delta 7-3-7- delta. Repeat.
```

Chạy lại với `small`, `beam_size=10`, `temperature=0.0`, `word_timestamps=True` và
`initial_prompt` chứa sẵn bảng chữ cái NATO cùng các từ chỉ chữ số, chỉ trên đoạn 45-83 s.
Lần này mỗi ký tự là một token riêng (`files/transcript_small_flagpart.txt`):

```text
[  4.64- 10.72] Copy Wilco. Eagle two. Flag is six three six four six three seven four six seven bravo.
[ 11.16- 16.80] Correction. Flag is six three six four six three seven four six six seven bravo four echo three
[ 16.80- 22.82] four five four three zero five foxtrot six three six foxtrot six delta six delta seven three seven
[ 22.82- 34.42] Delta. Repeat. Flag is 63646374667 Bravo for Echo 3454305 Foxtrot 636 Foxtrot 6 Delta 6 Delta
```

**Bước 2 - Nhận ra bảng chữ cái đang dùng.** Cờ được đánh vần theo bảng NATO, nhưng chỉ với
bốn chữ cái là chữ số hex: `bravo`, `echo`, `foxtrot`, `delta` tương ứng `B E F D`. Các từ
`six three four...` là chữ số hex đọc thẳng. Ghép 34 token thành 17 byte.

Điểm mấu chốt nằm ở từ `Correction`. Lần đọc đầu bị thiếu một số `6` (`...four six seven
bravo`), cho chuỗi hex 11 ký tự, lẻ nên không ghép thành byte nào. Lần đọc thứ hai chèn thêm
số `6` (`...four six six seven bravo`) thành 12 ký tự, và `63 64 63 74 66 7B` chính là
`cdctf{`. Dùng bản `Correction` và đối chiếu với lần `Repeat` thứ ba để khôi phục chuỗi hex đã sửa.

**Bước 3 - Giải mã và đối chiếu hai lần đọc.**

```python
DIGITS = {"zero":"0","one":"1","two":"2","three":"3","four":"4",
          "five":"5","six":"6","seven":"7","eight":"8","nine":"9"}
LETTERS = {w: w[0].upper() for w in ("alpha bravo charlie delta echo foxtrot golf hotel "
           "india juliett kilo lima mike november oscar papa quebec romeo sierra tango "
           "uniform victor whiskey xray yankee zulu").split()}

hexs = "".join(DIGITS.get(w, LETTERS.get(w, w)) for w in tokens)
flag = bytes.fromhex(hexs).decode("ascii")
```

**Kiểm chứng:** `exploit.py` tách cả ba lần đọc trong transcript bằng một regex, và chỉ exit
0 khi có từ hai lần đọc độc lập cho cùng một chuỗi khớp `^cdctf\{[A-Za-z0-9_]+\}$`. Bản
`Correction` và bản `Repeat` trùng nhau từng byte; bản đầu tiên bị từ chối đúng vì lẻ hex.
Độ dài 34 ký tự chẵn, toàn bộ 17 byte là ASCII in được, prefix và dấu `}` khớp luật đề.

## Kết quả

```bash
python exploit.py files/transcript_small_flagpart.txt
```

```text
[*] transcript_small_flagpart.txt: 3 lan doc co duoc phat song
[1] 11 ky tu hex (le) -> khong ghep duoc thanh byte: 6364637467B
[2] 17 byte -> 'cdctf{N4T0_comms}'  <- co hop le
[3] 17 byte -> 'cdctf{N4T0_comms}'  <- co hop le
[*] lan doc dau tien thieu mot chu so '6' nen hex le: do la loi ma phat song tu sua bang tu 'Correction'
[+] 2 lan doc doc lap (Correction + Repeat) trung nhau: cdctf{N4T0_comms}
[+] da luu flag.txt
```

## Tái hiện

```bash
python exploit.py files/transcript_small_flagpart.txt
```

Muốn chạy lại từ file âm thanh gốc thì làm theo `de.md`: decode WAV, chạy
`analysis/asr_small.py` để sinh transcript, rồi chạy lệnh trên. Bước ASR cần model Whisper
`small` (tự tải weights, không commit trong repo); bước giải mã chỉ dùng stdlib.
