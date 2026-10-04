# notes.md - vat-5-you-get-all-that

Input: `files/cred_call_transcript.txt` (254 B, sha256 `41eb65db34be1d35...aab00fea`) và
`files/captured_cred_call.mp3` (151244 B, sha256 `687fecc9b0868355...4799f803`)
Định dạng cờ đề yêu cầu: `cdctf{...}` (ví dụ trên thẻ: `cdctf{ex4mp13_f14g}`)

## H1 - Cờ nằm trong chính file MP3 (appended data / tag ẩn)
cmd: `python analysis/mp3_container.py`
evidence: ID3v2.4 dài 34 byte, chỉ một frame `TSSE = Lavf61.7.100`. Thân file 151200 byte,
bằng đúng `25.20 s * 48000 bit/s / 8`; `44 + 151200 = 151244` = kích thước file. Đuôi file
là `55555555...` (frame im lặng đã pad, giống VAT 1/5). Chuỗi `PK` tại 44887/96286/120669
nằm giữa dữ liệu nén, không có header zip hoàn chỉnh.
result: DEAD - mọi byte được giải thích bởi encoder, không có vùng dư nào mang dữ liệu.

## H2 - Payload điều chế trong âm thanh (DTMF/AFSK/Morse/spectrogram stego)
cmd: `python analysis/audio_layout.py`
cmd: `python analysis/spectrogram_probe.py`
evidence: 50 đoạn vượt ngưỡng năng lượng, 29 đoạn dài >=0.25 s, 18 trong số đó bắt đầu từ
9.0 s trở đi (tổng 7.21 s, mỗi đoạn 0.27-0.60 s): đúng nhịp 17 word được đọc liên tiếp. STFT
1183 frame: dải <500 Hz trung bình -95.96 dB so với -121.36 dB ở 4-11 kHz (chênh 25.40 dB) và
dao động 91.05 dB theo frame; dải 1-4 kHz có 0/1183 frame gần trắng toàn phần.
result: DEAD - đây là giọng người, không có tone rời, không có lưới điểm ảnh.

## H3 - Audio là nguồn dữ liệu, cần ASR lấy 17 word
cmd: `python analysis/asr_check.py` (Whisper `small`, `word_timestamps=True`)
evidence: log `analysis/asr_check.log` - đúng một segment `[0.00 9.40] Hello user. You have
one shared credential from Jeffrey Barrett. Here is your credential encoded for ease of verbal
transmission.`, `tokens = 20`, và `token tu 9 s tro di: []`, tức 17 word không được nhận dạng
thành ký tự nào.
result: DEAD như một kênh nhập liệu - transcript của tác giả là nguồn duy nhất. Chuyển sang
H4 với giả thuyết transcript đúng từng chữ cái.

## H4 - Classical cipher trên 85 ký tự (mỗi word một ký tự, Polybius homophonic)
cmd: `python analysis/structure.py`
cmd: `python analysis/radix_probe.py`
evidence: mỗi vị trí chỉ dùng một bảng chữ nhỏ: pos1 và pos3 chỉ 6 nguyên âm
(`aeiouy`), pos0/pos2/pos4 là phụ âm (12, 8, 5 ký tự). Đã quét 654 bộ tham số (tập vị trí
mang tin, `obs_rank`/`full_rank`, endian, 3 bảng a-z0-9 và 8 offset ASCII).
Không bộ nào sinh chuỗi chứa `cdctf|ctf{|flag|pass|jeff|barrett|crimson`.
positive control: cùng bộ máy, đưa 5 word tổng hợp mã hoá `cdctf` bằng sơ đồ 6x6 đó thì máy
bắt được (`1158 hit`), nên negative trên dữ liệu thật có giá trị.
result: DEAD - không tồn tại lời giải "word = 1 ký tự" trong họ sơ đồ số học vị trí thuần.

## H5 - Nhận diện BubbleBabble từ cấu trúc
cmd: `python analysis/structure.py`
evidence: neo `word[0][0] == 'x'` và `word[-1][-1] == 'x'`; bảng chữ đúng 6 nguyên âm
`a e i o u y` và 15/17 phụ âm `bcdfghklmnprstvzx` (thiếu `d`, `p`, và `j q w` vốn không thuộc
bảng nào của BubbleBabble); pattern `CVCVC` mọi word; số nhóm 17. Bộ ba tính chất này trùng
hàm `fingerprint_bubblebabble` trong `sshkey.c` (OpenSSH), định dạng sinh ra để đọc fingerprint
qua điện thoại, tức đúng tinh thần "ease of verbal transmission" của series.
result: PENDING -> xác nhận ở H6 bằng vòng mã hoá.

## H6 - Đảo BubbleBabble theo chuỗi seed
cmd: `python exploit.py files/cred_call_transcript.txt`
evidence: `rounds = len(data)//2 + 1 = 17` nên data dài 32 hoặc 33 byte. Nhánh chẵn ép ký tự
thứ 3 của nhóm cuối thành `x` (idx1 = 16); thực tế nhóm cuối `lizyx` có ký tự thứ 3 là `z` =
chỉ số phụ âm 15, buộc độ dài lẻ = 33. Hai chỉ số nguyên âm là `(bit + seed) mod 6` với
`seed` tiến hoá xác định từ các cặp byte trước (`seed = (seed*5 + b*7 + b') % 36`, khởi tạo 1),
và 2 bit chỉ nhận 0..3 nên phép cộng có nghịch đảo duy nhất. Kết quả trung gian
`63646374667b3875...70613535696e677d` -> `cdctf{8u88l3_848813_fl4g_pa55ing}`. Vòng lại: mã
hoá 33 byte sinh đúng `ximok-gemul-...-lizyx`, khớp 85/85 ký tự và 16 dấu `-`.
result: OK - cờ: `cdctf{8u88l3_848813_fl4g_pa55ing}`

---

## Ghi chú dụng cụ (để lần sau không tái phạm)

- Bản dò nhịp đầu tiên chia file thành `f = 25` bucket bằng `x[i*sr//f:(i+1)*sr//f]`, tức mỗi
  bucket 0.04 s chứ không phải 1 s, nên kết luận "im lặng tuyệt đối sau 17 s" là sai. Bản sửa
  (`analysis/audio_layout.py`, bucket `sr` sample) cho thấy tiếng người trải hết 25 s. Không
  ảnh hưởng lời giải, nhưng là ví dụ điển hình của việc đọc số đo từ một dụng cụ chưa kiểm
  tra đơn vị.
- Đoán đầu tiên "`z` là `x` bị nghe sai" đã bị chính vòng mã hoá bác bỏ. Với các mã có tính
  toàn vẹn như BubbleBabble, hãy kiểm tra transcript bằng round-trip trước khi sửa nó.

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
