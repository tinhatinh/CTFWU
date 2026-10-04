# notes.md - vat-3-pretty-good-passphrase

Input: `files/voicemail.mp3` (3964752 B, sha256 `437d7631ee3ee3aa...0b4e613a`), 660.792 s,
MPEG layer III v2, 48 kbps, 24 kHz, mono; `files/VAT_key` (2096 B, PGP private key block).
Định dạng cờ đề yêu cầu: `cdctf{...}`.

## H1 - Passphrase đề cho là sai, phải tìm passphrase thật
cmd: `gpg --homedir ./gnupg --batch --armor --pinentry-mode loopback --passphrase 'Password123!' --export-secret-keys`
evidence: báo `Bad passphrase`, nhưng hai keyID bị lỗi (`A6BCF90C...`, `71E56BA5...`) không thuộc
keyring của bài. Thử bằng đường khác: `gpg --local-user 9BAAC44EC4B7766A -sb` rồi
`gpg --verify sig.bin` -> `Good signature from "Crimson Offense b0b (baller)"`.
result: DEAD - passphrase đúng. Thông báo "Bad passphrase" là keyring default của máy lẫn vào.

## H2 - Dữ liệu giấu trong container MP3 hoặc ở bit thấp
cmd: quét `PK\x03\x04`, gzip, 7z, ID3, `strings`; rồi tách 8 bit plane của PCM đã giải mã
evidence: không ID3, không magic nào ngoài `LAME` ở header, `RG2` chỉ là trùng hợp trong dữ liệu
nén. Cả 8 bit plane của WAV cho tỉ lệ ký tự in được 8-17% (ngẫu nhiên).
result: DEAD - MP3 lossy, không có stego bit thấp.

## H3 - Tín hiệu số: DTMF, tone, SSTV, phổ hình
cmd: `ffprobe`; FFT từng burst; dựng spectrogram 0-60 s
evidence: mỗi burst có F0 80-140 Hz kèm hài bậc cao tới 12 kHz, phổ có formant rõ. Không có
stable tone nào trên 2.5 kHz, năng lượng trên 7 kHz chỉ là thành phần của tiếng nói.
result: DEAD - đây là tiếng nói, không phải mode số.

## H4 - Audio có từ lặp lại, tức là một bảng chữ cái chính tả
cmd: so trùng lặp bằng correlation có xê dịch trên 432 burst
evidence: các lần lặp của cùng một từ là bản sao gần như bit-đỉnh (corr = 1.000), nhưng chỉ 175/432
burst có bản đôi; gom cụm cho ~351-371 từ phân biệt.
result: DEAD cho giả thuyết "bảng 26/64 ký tự". Audio đọc một danh sách từ dài, không phải đánh
vần.

## H5 - Whisper `base`/`small` bản chuẩn, có điều kiện hoá văn bản
cmd: `whisper.load_model('base.en').transcribe('vm16k.wav', word_timestamps=True)`
evidence: 419 token, 132 từ phân biệt, toàn bộ chữ cái đầu nằm trong a-k và độ dài âm tiết
luân phiên 2-3-2-3 theo vị trí từ. `medium.en` chạy cùng chế độ thì lặp vô hạn
`gossamer german gossamer german ...` từ token 190.
result: ĐÚNG một phần - đủ để nhận diện scheme, nhưng điều kiện hoá văn bản vừa gây lặp vừa làm
độ chính xác giảm.

## H6 - Đối mẫu bằng TTS tại chỗ
cmd: `espeak-ng -w tmp.wav -s 80..180 button` rồi correlation với burst đầu; `pip install edge-tts`
evidence: espeak-ng correlation cao nhất 0.043 (không cùng engine). edge-tts cài được nhưng mọi
voice đều chết ở `ClientConnectorDNSError` cho `speech.platform.bing.com`.
result: DEAD - không dựng được thư viện mẫu âm thanh tham chiếu.

## H7 - Bỏ qua audio, tìm ciphertext ở nguồn khác (OSINT keyserver, packet ẩn)
cmd: `gpg --list-packets VAT_key`
evidence: chỉ có 5 packet: secret key, uid, self-sig, secret subkey, subkey binding-sig. Không có
user attribute, không có signature subpacket loại comment/URI. Fingerprint không cần tra thêm.
result: DEAD - payload chỉ có thể lấy từ audio.

## H8 - Đọc từng từ theo PGP Word List
cmd: tải 256 cặp từ (even 2 âm tiết / odd 3 âm tiết), Viterbi cưỡng bức parity trên 419 token
evidence: 246/419 token khớp chính xác một từ trong đúng danh sách parity; chuỗi byte giải ra
`-----BEGIN PGP MESSAGE-----`. Cưỡng bức 2 ký tự chưa đọc được rồi quét 64x64: CRC24 của armor
(`uQhg`) không thoả cho tổ hợp nào.
result: OK cho scheme, còn 5 ô từ bị nghe sai nằm ở vị trí mà từ sai vẫn là một từ hợp lệ trong
danh sách.

## H9 - Chạy lại whisper với `condition_on_previous_text=False`
cmd: `model.transcribe('vm16k.wav', word_timestamps=True, condition_on_previous_text=False)` cho
`small.en` và `medium.en`
evidence: mỗi bản cho 423 token -> 417 từ (đúng số 417 của armor đầy đủ). Ba bản chỉ bất đồng ở
8 ô, và phần bất đồng bù trừ nhau: base không đọc được ô 86/94 trong khi small đọc được `W`/`P`;
small không đọc được 229/247/329 trong khi medium và base đều cho `i`/`i`/`Y`.
result: OK - hợp nhất theo đa số là đủ.

## H10 - Chốt bằng CRC24 và gpg
cmd: `python exploit.py files/voicemail.mp3` (log: `analysis/decode_run.log`)
evidence: body 340 ký tự base64 -> 253 byte; CRC đọc từ audio `uQhg` = CRC24 tính lại `b90860`;
PKESK `tag=0x84 len=140 ver=3 keyid=c87aff55f4097c91 algo=1 mpi=1020`, SEIP `tag=0xd2 len=109
ver=1`; `gpg: encrypted with rsa1024 key, ID C87AFF55F4097C91` và plaintext
`Good work: cdctf{pr3t7y_g00d_piv4cy_fl4G}`.
result: OK - cờ: `cdctf{pr3t7y_g00d_piv4cy_fl4G}`

## Bẫy công cụ đã gặp (không phải giả thuyết về đề)

1. Gọi `gpg` bản Git-Bash từ Python Windows với `GNUPGHOME=C:\...` (hoặc `--homedir C:\...`) làm
   gpg hiểu sai thành đường dẫn tương đối. Toàn bộ 4096 lượt quét đầu tiên trả
   `Wrong secret key used` giả, trông hệt như "giải mã thất bại". Phải dùng dạng MSYS
   `/c/Users/...`.
2. Nộp nhiều armor vào một file cho `gpg --decrypt`: sau plaintext đầu tiên gpg phát
   `WARNING: multiple plaintexts seen` và ngừng in kết quả, nên không dùng được làm oracle hàng
   loạt.
3. Đặt tên script là `struct.py` trong thư mục làm việc: `base64` và `ctypes` import `struct` của
   stdlib nên mọi tiến trình con đều chết kiểu `ImportError: cannot import name 'calcsize'`.
4. Chuỗi bắt đầu bằng `--` khiến `printf` của bash báo `invalid option`; dùng `printf '%s'` hoặc
   ghi file bằng Python.
5. Thử tự dẫn xuất khoá RSA từ S2K (nhiều công thức decode count, hai cách cắt IV) không cho
   `p*q == n`; hướng này không cần thiết vì `gpg` đã làm phép kiểm PKCS#1 hộ.

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
