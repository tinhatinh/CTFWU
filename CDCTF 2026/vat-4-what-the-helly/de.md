# Đề bài - vat-4-what-the-helly

## Nguyên văn đề

```text
Verbal Authentication Transmissions 4/5: What the helly
500
OSINT Crypto Password Cracking
b0b

The following audio is believed to be the S/Key OTP Codes for a Crimson Offense operative.
The codes are stale, but you should be able to recover the original password used to generate
these codes, which would help us gain access elsewhere. A little clarification: n=8, hashes
are folded, no seed used.

Flag format: cdctf{password}
```

File đính kèm: `OTP_CODES_VAT.mp3`.

Thẻ bài không được lưu ảnh trong phiên này nên case không có `files/de.png`; văn bản trên là
nguyên văn phần đề người dùng dán vào chat.

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/OTP_CODES_VAT.mp3` (copy từ: `C:/Users/Administrator/Downloads/OTP_CODES_VAT.mp3`) |
| Kích thước | 448848 byte |
| SHA-256 | `56c3bbfa042f4e6ae46e577152260d9f1414ae199f09c0c0c3dcba7897d5e11c` |
| Loại file | MPEG ADTS, layer III, v2, 48 kbps, 24 kHz, monaural |
| Độ dài | 74.808 s (`ffprobe -show_entries format=duration`) |
| Metadata | không có ID3 mang nội dung; file sinh bằng TTS (cùng kiểu 24 kHz/mono/48 kbps với các phần khác của chuỗi VAT) |
| Cấu trúc lời đọc | mở đầu "Hello user. Your one-time passcodes are as follows", 8 khối `CODE n` sáu từ, kết "please say these to a secure location, thank you" |
| Số token OTP | 48 (8 mã x 6 từ), `files/transcript_asr.txt` |
| Token khớp từ điển S/Key | 44/48 ở bản merge, 37/48 ở Whisper `base`, 36/42 ở Whisper `small` |
| Từ điển six-word | 2048 từ, độ dài 1-4 ký tự, `files/skey_dictionary.txt` (lấy từ RFC 1760 Appendix) |
| Mã đủ 6 từ trong từ điển | Code 3, 4, 5, 6, 7 |
| Mã thỏa checksum RFC 2289 | Code 3, 4, 5, 7; Code 6 lệch ở từ thứ 6 (`analysis/skey_kat.log`) |
| Thông số đề cho | n=8, hash có nap (folded), không seed |
| Định dạng cờ | `cdctf{password}` |

## Hướng giải (tóm tắt)

Mỗi mã là một giá trị 64 bit đóng gói thành sáu từ 11 bit theo RFC 2289, hai bit cuối của từ thứ
sáu là checksum. Kiểm 27 vector của RFC 2289 thì thấy cách đóng gói và từ điển là bản chuẩn, nên
còn lại đúng một ẩn số: hàm buoc của chuỗi hash. Quét 65 tổ hợp (hash, kiểu nap, dạng input) cho
thấy chuỗi này đi `fold(MD5(chuoi-hex-16-ky-tu))`, không phải `fold(MD5(8-byte-tho))` như RFC.
Với hàm bước đó, các mã 3/4/5/7 cho mask 64 bit; quét rockyou (14 344 391 dòng) bằng mask 53-64
bit cho một ứng viên duy nhất, và ứng viên đó dựng lại đủ tám mã trong audio.

## Chạy lại lời giải

Bước ASR cần Whisper (`base`, `small`) và Vosk small-en; model và WAV 16 kHz không commit vào repo:

```bash
ffmpeg -y -i files/OTP_CODES_VAT.mp3 -ar 16000 -ac 1 vat.wav
python analysis/asr_whisper.py vat.wav base ./models   # -> analysis/asr_base_run.log
python analysis/asr_whisper.py vat.wav small ./models  # -> analysis/asr_small_run.log
python analysis/asr_vosk.py <model-vosk> vat.wav       # -> analysis/asr_vosk_run.log
```

Ba bước còn lại chỉ dùng stdlib (kèm `pycryptodome` cho MD4 ở script quét mô hình):

```bash
python analysis/skey_kat.py            # doi chieu RFC 2289 + sang loc checksum -> analysis/skey_kat.log
python analysis/chain_model_scan.py    # tim ham buoc cua chuoi             -> analysis/chain_model_scan.log
python exploit.py --selftest           # cay chuoi gia kiem probe
python exploit.py --crack C:/Tools/rockyou.txt 14    # -> flag.txt
python exploit.py --verify <mat-khau>  # kiem chung lai toan bo 8 ma
```

Wordlist không commit (140 MB). `files/transcript_asr.txt` là bản merge ba engine ASR; đổi bản
khác vào file đó thì mask tự thay đổi theo.

## Đối chứng độc lập

Cùng chuỗi này mở được keyring PGP của operative. File `VAT_key` (userid
"Crimson Offense b0b (baller) <b0b@crimson.offense>", keyid `9BAAC44EC4B7766A`) tải về cùng đợt với
audio của bài này, nhiều khả năng là artifact của phần 3/5; S2K của nó là iter+salt SHA1 với
protect-count 65011712, algo 7 (AES-256):

```text
gpg: key 9BAAC44EC4B7766A: public key "Crimson Offense b0b (baller) <b0b@crimson.offense>" imported
gpg: key 9BAAC44EC4B7766A: secret key imported
gpg:       secret keys read: 1
gpg:   secret keys imported: 1
```

Câu "which would help us gain access elsewhere" trong đề là chỉ đúng vào chi tiết này: mat khau
duoc tai su dung o noi khac trong chuoi VAT.

## Ghi chú về thời điểm solve

`tools/solve_times.json` ghi `2026-10-04` (không ghi giờ) cho case này. Đồng hồ máy trong phiên
nhảy khoảng 24 giờ giữa hai lượt lệnh cách nhau vài phút (file đầu phiên mang mtime
`2026-10-03T22:4x`, file cuối phiên mang `2026-10-04T22:2x`), nên giờ cục bộ lúc in cờ không truy
vết được; ngày chốt theo `currentDate` của phiên.
