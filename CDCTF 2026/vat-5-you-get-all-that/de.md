# Đề bài - vat-5-you-get-all-that

## Nguyên văn đề

```text
Verbal Authentication Transmissions 5/5: You get all that?
500
OSINT Crypto
b0b

We're trying to hack Crimson Clinic and captured this automated message sent to one of
Jeffery Barrett's employees. It says a credential is being shared, but the encoding is
very weird. (Transcript is provided because half the words are unintelligible LOL)

Flag Format: cdctf{ex4mp13_f14g}
```

File đính kèm: `captured_cred_call.mp3`, `cred_call_transcript.txt`.

Thẻ bài không được lưu ảnh trong phiên này, nên case không có `files/de.png`. Văn bản
trên là nguyên văn phần đề người dùng dán vào chat.

## Transcript đính kèm

```text
Hello User. You have. One. shared credential from. Jeffery. Barrett. Here is your
credential, encoded for ease of verbal transmission: ximok. gemul. ganol. ruvul. hevaf.
murof. felyf. metuf. myvaf. cusih. zynok. sitek. lulol. bemef. hatok. norek. lizyx.
```

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact 1 | `files/captured_cred_call.mp3` (copy từ: `C:\Users\Administrator\Downloads\captured_cred_call.mp3`) |
| Kích thước | 151244 byte |
| SHA-256 | `687fecc9b0868355f0af53b347d8a3a5e918522d936cda0cd46d89504799f803` |
| Loại file | ID3v2.4 + MPEG ADTS layer III v2, 48 kbps, 24 kHz, monaural |
| Độ dài | 25.20 s (decode ra 1209600 sample @ 48000 Hz) |
| ID3 | 34 byte, một frame `TSSE = Lavf61.7.100`, không có TIT2/COMM |
| Container | `44 + 151200 = 151244` byte, đúng bằng `25.20 s * 48000 / 8`; không có appended data (`analysis/mp3_container.log`) |
| Phổ | năng lượng <500 Hz cao hơn dải 4-11 kHz 25.40 dB, dao động 91.05 dB theo frame: giọng nói, không có lưới điểm ảnh (`analysis/spectrogram_probe.log`) |
| Nhịp lời | tiếng người trải toàn bộ 25 s; 50 đoạn vượt ngưỡng, 29 đoạn >=0.25 s, 18 trong số đó bắt đầu từ 9.0 s trở đi, tức phần đọc code word (`analysis/audio_layout.log`) |
| ASR | Whisper `small`: chỉ trả lời đoạn 0.0-9.4 s (câu intro), 0 token cho đoạn code word (`analysis/asr_check.log`) |
| Artifact 2 | `files/cred_call_transcript.txt` (copy từ: `C:\Users\Administrator\Downloads\cred_call_transcript.txt`), 254 byte, SHA-256 `41eb65db34be1d35090b7d694d2bd065d1afbee97d57172f3aa9ead6aab00fea`, ASCII text |
| Payload | 17 word sau dấu `:`, mỗi word 5 ký tự, kiểu hình `CVCVC` |
| Bảng chữ | 6 nguyên âm `a e i o u y` + 15 trong số 17 phụ âm `b c d f g h k l m n p r s t v z x`; `d` và `p` không xuất hiện |
| Neo cấu trúc | `word[0][0] == 'x'` và `word[-1][-1] == 'x'` |
| Số ký tự distinct theo vị trí | pos0 12, pos1 6, pos2 8, pos3 6, pos4 5 (`analysis/structure.log`) |
| Định dạng cờ | `cdctf{...}` |

## Hướng giải (tóm tắt)

Payload là 17 nhóm 5 ký tự `CVCVC` trên đúng bảng chữ của **BubbleBabble**, định dạng
fingerprint "đọc qua điện thoại" mà OpenSSH sinh trong hàm `fingerprint_bubblebabble`
(`sshkey.c`), với `x` đứng đầu và đứng cuối chuỗi. BubbleBabble quy mỗi cặp byte thành 5
chỉ số, trong đó 4 bit giữa của byte chẵn và cả byte lẻ lấy trực tiếp, còn 2+2 bit đầu/cuối
bị cộng theo `seed` mô-đun 6; vì `seed` tiến hoá xác định (`seed = (seed*5 + b*7 + b') % 36`,
khởi tạo 1) nên lần theo chuỗi `seed` là đảo được không mất mát. 17 nhóm cho `rounds = 17`,
và vị trí thứ ba của nhóm cuối là `z` chứ không phải `x` buộc độ dài dữ liệu là lẻ, tức 33
byte. Áp ngược công thức thu được `cdctf{8u88l3_848813_fl4g_pa55ing}`; mã hoá lại toàn bộ
33 byte sinh ra đúng 85 ký tự của transcript, nên transcript không có chữ nào bị nghe sai.

## Chạy lại lời giải

```bash
python exploit.py files/cred_call_transcript.txt
```

Kết quả: `cdctf{8u88l3_848813_fl4g_pa55ing}` (đã lưu trong `flag.txt`).

Các bước loại trừ và dò cấu trúc chạy độc lập bằng stdlib + numpy/scipy:

```bash
python analysis/mp3_container.py
python analysis/audio_layout.py
python analysis/spectrogram_probe.py
python analysis/radix_probe.py
python analysis/structure.py
```

Riêng `analysis/asr_check.py` cần model Whisper `small` (weights tự tải, không commit).
