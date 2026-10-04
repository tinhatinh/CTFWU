# Verbal Authentication Transmissions 3/5: Pretty Good Passphrase - OSINT + Crypto (500 pts)

**Flag:** `cdctf{pr3t7y_g00d_piv4cy_fl4G}`
**Files:** `voicemail.mp3` (3964752 B, sha256 `437d7631ee3ee3aaf15ddb54383609b3f550c4feb5bbd08814c87ccd0b4e613a`), `VAT_key` (2096 B, sha256 `28715250c107ef4a3b2bbe611df4a457256c865c091087a0eaf3a6e0875fd03a`)

## Đề bài

Bạn của tác giả định gửi một thông điệp mã hoá PGP nhưng để lại voicemail tự động. Đề cho
`voicemail.mp3` dài 660.792 s và `VAT_key` là private key PGP, kèm passphrase
`Password123!`. Phải dựng lại thông điệp đã được đọc thành tiếng rồi giải mã nó.

## Phân tích ban đầu

`ffprobe` báo MPEG layer III v2, 48 kbps, 24 kHz, đơn kênh, `duration=660.792000`, không có ID3
mang nội dung. Container giống hệt các phần khác của chuỗi VAT, tức file do TTS sinh ra.

Cắt theo năng lượng cho 432 burst tiếng nói, cách đều nhau 1.585 s, độ dài 0.36-0.88 s. Mỗi burst
có F0 80-140 Hz cùng formant tới 12 kHz, nên đây là tiếng nói chứ không phải mode số. Các lần lặp
của cùng một từ là bản sao gần như bit-đỉnh (correlation 1.000), đúng tính chất của TTS ghép
theo từ.

Whisper `base.en` cho 419 token với hai đặc trưng nổi bật: toàn bộ chữ cái đầu nằm trong khoảng
`a`-`k`, và **số âm tiết luân phiên 2 - 3 - 2 - 3 theo đúng vị trí từ**. Chữ cái đầu bị giới hạn
loại trừ bảng chữ cái chính tả NATO, còn nhịp âm tiết chẵn/lẻ là signature của **PGP Word List**:
danh sách 256 từ hai âm tiết dùng cho byte ở vị trí chẵn và 256 từ ba âm tiết cho vị trí lẻ, được
thiết kế để đọc byte qua kênh giọng nói.

Suy ra: mỗi từ là một byte, và chỉ số của từ trong danh sách theo đúng parity chính là giá trị
byte. Chuỗi byte đó là toàn bộ văn bản ASCII armor, kể cả CR, LF và dòng CRC.

## Các hướng đã loại

1. **Passphrase đề cho bị sai**: `--export-secret-keys` báo `Bad passphrase` nhưng hai keyID bị
   lỗi không thuộc keyring của bài. Thử ký rồi verify cho `Good signature`. Loại.
2. **Stego trong container hoặc bit thấp của PCM**: không magic nào ngoài `LAME`, tám bit plane
   cho 8-17% ký tự in được. Loại.
3. **DTMF, tone ổn định, dữ liệu trong phổ**: không có stable tone nào trên 2.5 kHz. Loại.
4. **Bảng chữ cái chính tả**: gom cụm cho ~351 từ phân biệt trên 413 lát cắt, quá lớn cho một
   bảng 16/26/64 ký tự. Loại.
5. **Đối mẫu bằng TTS tại chỗ**: `espeak-ng` correlation tốt nhất 0.043 (khác engine), `edge-tts`
   cài được nhưng mọi voice chết ở `ClientConnectorDNSError` với `speech.platform.bing.com`. Loại.
6. **Bỏ audio, tìm ciphertext ở chỗ khác**: `gpg --list-packets VAT_key` chỉ có 5 packet, không
   user attribute, không subpacket comment/URI. Loại.

## Chuỗi khai thác

**Bước 1 - Cưỡng bức parity bằng Viterbi.** Với mỗi token, trạng thái là parity hiện tại; một từ
hợp lệ ở đúng danh sách cho điểm 3, từ gần đúng (edit distance nhỏ) cho điểm 1, cho phép gộp hai
token thành một từ để sửa các ca `dogs led`, `eight ball`. Trên 419 token của `base.en`, Viterbi
khớp chính xác 246 ô và giải ra:

```text
-----BEGIN PGP MESSAGE-----

hIwDyHr/VfQJfJEBA/wLRYGn0HpRTthSYqEDJICRMtgAMmeEVkQVzYpzk1gvL9zk
0tfMYkBYFE8txo9+qk7EKJ?T2lBnRL?3oRcdcYswYe6gt+hkRzUKUu8y73woSZoh
...
xmJMn57j6YcQOO5bzw==
=uQhg
-----END PGP MESSAGE---
```

Dấu xuống dòng rơi đúng mỗi 64 ký tự base64, tức số từ và vị trí đã chuẩn; chỉ còn hai ô `?` mà
whisper nghe thành `escamo` và `imbecile`.

**Bước 2 - Định vị lỗi còn lại bằng ba oracle độc lập.** Kiểm cấu trúc packet của 253 byte giải
được: `PKESK tag=0x84 len=140 ver=3 keyid=c87aff55f4097c91 algo=1 mpi=1020 bit` rồi
`SEIP tag=0xd2 len=109 ver=1`. keyID khớp chính xác subkey mã hoá của đề, và `len=109` đúng bằng
`253 - 142 - 2`, nên phần head tới byte 144 là sạch. Quét trọn 64x64 tổ hợp cho hai ô `?` bằng
`gpg`: cả 4096 đều trả `Wrong secret key used`, tức còn lỗi nằm trong vùng RSA.

Oracle thứ hai là CRC24 của armor. Hàm CRC được kiểm trước bằng cách ký một file nháp với chính
key này rồi so dòng `=` do `gpg` sinh với hàm tự viết: `gpg crc: X+0T mine: X+0T MATCH`. Với CRC
đúng, phép thử "một ô sai bổ sung" chỉ còn 4 ứng viên và cả bốn vẫn fail RSA.

Oracle thứ ba là chính bộ nhận dạng: chạy lại whisper với `condition_on_previous_text=False`.
Mặc định của thư viện điều kiện hoá vào văn bản đã sinh ra trước đó, vừa gây lặp vô hạn
(`gossamer german gossamer german ...` ở `medium.en`) vừa làm giảm độ chính xác. Tắt nó đi thì
`small.en` và `medium.en` đều cho đúng 417 từ.

**Bước 3 - Hợp nhất ba bản nghe.** Ba bản bất đồng ở 8 ô và phần thiếu bù trừ nhau: `base` không
đọc được ô 86 và 94 trong khi hai bản kia cùng cho `W` và `P` (tức `Eskimo` và `embezzle`, hai từ
mà `base` nghe thành `escamo` và `imbecile`); `small` trắng ở 229, 247, 329 trong khi `base` và
`medium` cùng cho `i`, `i`, `Y`. Lấy đa số là đủ:

```output
[*] asr_base: 419 token -> 415 tu, body 340, o chua doc duoc [86, 94]
[*] asr_medium: 423 token -> 417 tu, body 340, o chua doc duoc [227]
[*] asr_small: 423 token -> 417 tu, body 340, o chua doc duoc [229, 247, 329]
[*] hop nhat 3 ban nghe: 340 ky tu base64, 8 o co bat dong
      pos 41: tXX -> X
      pos 65: tXX -> X
      pos 86: ?WW -> W
      pos 94: ?PP -> P
      pos 227: W?W -> W
      pos 229: ii? -> i
      pos 247: ii? -> i
      pos 329: YY? -> Y
```

**Bước 4 - Kiểm chứng.** CRC24 đọc từ audio khớp CRC24 tính lại trên 253 byte, tức 24 bit kiểm
tra độc lập đi qua, rồi `gpg` giải mã với MDC hợp lệ:

```output
[*] 253 byte, CRC doc tu audio = uQhg (b90860), CRC24 tinh lai tu body = b90860 KHOP
[*] kiem cau truc packet:
      PKESK tag=0x84 len=140 ver=3 keyid=c87aff55f4097c91 algo=1 mpi=1020 bit
      SEIP  tag=0xd2 len=109 ver=1
[*] gpg:
gpg: encrypted with rsa1024 key, ID C87AFF55F4097C91, created 2026-10-03
      "Crimson Offense b0b (baller) <b0b@crimson.offense>"
[+] plaintext: 'Good work: cdctf{pr3t7y_g00d_piv4cy_fl4G}\n'
```

## Flag

```bash
python exploit.py files/voicemail.mp3
```

```
[*] 253 byte, CRC doc tu audio = uQhg (b90860), CRC24 tinh lai tu body = b90860 KHOP
[*] kiem cau truc packet:
      PKESK tag=0x84 len=140 ver=3 keyid=c87aff55f4097c91 algo=1 mpi=1020 bit
      SEIP  tag=0xd2 len=109 ver=1
[*] gpg:
gpg: encrypted with rsa1024 key, ID C87AFF55F4097C91, created 2026-10-03
      "Crimson Offense b0b (baller) <b0b@crimson.offense>"
[+] plaintext: 'Good work: cdctf{pr3t7y_g00d_piv4cy_fl4G}\n'

FLAG: cdctf{pr3t7y_g00d_piv4cy_fl4G}
```

## Reproduce

```bash
python exploit.py files/voicemail.mp3
```

`exploit.py` chỉ cần stdlib và `gpg` trên PATH. Nó đọc ba bản nghe trong `analysis/`, tự chạy
Viterbi theo parity trên `files/pgp_wordlist.txt`, hợp nhất, kiểm CRC24 rồi giải mã bằng
`files/VAT_key`. Muốn tự sinh lại bản nghe:

```bash
python -c "import whisper,json;w=whisper.load_model('small.en').transcribe('voicemail.mp3',language='en',fp16=False,word_timestamps=True,condition_on_previous_text=False);json.dump([[round(x['start'],3),round(x['end'],3),x['word']] for s in w['segments'] for x in s['words']],open('analysis/asr_small.json','w'))"
```

Lưu ý khi gọi `gpg` bản Git-Bash từ Python trên Windows: `GNUPGHOME` và `--homedir` phải ở dạng
MSYS (`/c/Users/...`). Dạng `C:\Users\...` bị hiểu thành đường dẫn tương đối và trả
`Wrong secret key used` giả, trông hệt như giải mã thất bại.
