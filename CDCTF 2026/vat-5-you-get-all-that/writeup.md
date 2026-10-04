# Verbal Authentication Transmissions 5/5: You get all that? - OSINT + Crypto (500 pts)

**Flag:** `cdctf{8u88l3_848813_fl4g_pa55ing}`
**Files:** `captured_cred_call.mp3` (151244 B, sha256 `687fecc9b0868355...4799f803`), `cred_call_transcript.txt` (254 B, sha256 `41eb65db34be1d35...aab00fea`)

## Đề bài

Đề cho một tin nhắn tự động gọi cho nhân viên của Jeffery Barrett, kèm transcript của nó.
Tin nói là một credential đang được chia sẻ và "đã được mã hoá để tiện truyền bằng lời".
Phần code gồm 17 word đọc vô nghĩa, cách nhau bởi dấu chấm. Thẻ bài 500 điểm, hạng OSINT +
Crypto, tác giả `b0b`, định dạng cờ `cdctf{ex4mp13_f14g}`. Không có service từ xa.

## Phân tích ban đầu

Audio là file 24 kHz đơn kênh sinh bằng ffmpeg (`TSSE = Lavf61.7.100`). Container sạch: ID3
dài 34 byte, thân 151200 byte, cộng lại đúng bằng `25.20 s * 48000 / 8`, nên không có byte
dính thêm cuối file. Phổ tín hiệu là giọng nói (năng lượng dưới 500 Hz cao hơn dải 4-11 kHz
25.40 dB và dao động 91.05 dB theo frame), không có lưới điểm ảnh của stego spectrogram.
Whisper `small` chỉ lấy được câu intro trong 9.4 giây đầu và trả về 0 token cho đoạn code,
xác nhận đúng lời than trong đề: máy cũng không nghe ra. Kết luận làm việc: payload nằm
trong transcript, audio chỉ là bản tường thuật lại.

Cấu trúc 17 word tự khai báo thuật toán. Mọi word đều `CVCVC`. Bảng chữ dùng được gói gọn
trong 21 ký tự: đúng 6 nguyên âm `a e i o u y`, và 15 trong số 17 phụ âm
`b c d f g h k l m n p r s t v z x` (thiếu `d`, `p`). Nhóm đầu tiên bắt đầu bằng `x`, nhóm
cuối cùng kết thúc bằng `x`. Bộ ba dấu hiệu "6 nguyên âm + 17 phụ âm + `x` kẹp hai đầu" là
chữ ký của **BubbleBabble**, định dạng fingerprint OpenSSH sinh ra để đọc qua điện thoại,
hàm `fingerprint_bubblebabble` trong `sshkey.c`.

## Các hướng đã loại

Trước khi chốt đã kiểm tra và loại các kênh sau (log đầy đủ ở `notes.md`):

1. **Stego trong MP3**: ID3 chỉ có `TSSE`, thông số bitrate nhân ra đúng số byte thân file,
   các chuỗi `PK` xuất hiện ở offset 44887/96286/120669 là trùng hợp nội dung nén. Loại.
2. **Stego spectrogram**: không có frame nào ở dải 1-4 kHz gần trắng toàn phần, không plateau
   dài; dải thấp liên tục biến điệu theo hài âm. Loại.
3. **DTMF / AFSK / Morse**: chỉ 18 utterance lời người từ 9 s trở đi, không ô tone nào nhô lên. Loại.
4. **Sinh transcript từ audio**: Whisper `small` trả 0 token cho 17 word, nên audio không
   thêm dữ kiện; transcript là nguồn duy nhất. Loại (nhưng vẫn dùng để xác minh transcript
   bằng chính vòng mã hoá).
5. **Mật độ classical trên 85 ký tự** (Polybius homophonic, mỗi word một ký tự): 654 bộ tham
   số (tập vị trí, cách quy đổi, endian, bảng ký tự, offset ASCII) cho 0 kết quả chứa manh
   roi cờ, trong khi cùng bộ máy đó tìm thấy `cdctf` trên dữ liệu tổng hợp có cùng sơ đồ. Loại.

## Chuỗi khai thác

**Bước 1 - Đọc cấu trúc thành tham số của BubbleBabble.** hàm này phát `x`, rồi mỗi vòng
tròn in 5 ký tự từ một cặp byte, xen kẽ dấu `-`:

```python
rounds = len(data) // 2 + 1
idx0 = (((data[2*i] >> 6) & 3) + seed) % 6      # nguyen am
idx1 = (data[2*i] >> 2) & 15                    # phu am
idx2 = ((data[2*i] & 3) + seed // 6) % 6        # nguyen am
idx3 = (data[2*i+1] >> 4) & 15                  # phu am truoc dau '-'
idx4 = data[2*i+1] & 15                         # phu am sau dau '-', = ky tu dau nhom ke tiep
seed = (seed * 5 + data[2*i] * 7 + data[2*i+1]) % 36
```

17 nhóm nghĩa là `rounds = 17`, tức dữ liệu dài 32 hoặc 33 byte. Nhánh độ dài chẵn ép ký tự
thứ ba của nhóm cuối thành `x` (idx1 = 16); nhóm cuối thực tế là `lizyx` với ký tự thứ ba `z`
(chỉ số phụ âm 15), nên độ dài bắt buộc là lẻ: **33 byte**, và byte cuối được lấy từ chính
nhóm đó.

**Bước 2 - Lần theo seed để đảo.** Hai chỉ số nguyên âm không cho bit trực tiếp mà cho
`(2 bit + seed) mod 6` và `(2 bit + seed//6) mod 6`. Vì 2 bit chỉ nhận giá trị 0..3 nên phép
cộng mod 6 có nghịch đảo duy nhất khi `seed` đã biết, và `seed` chỉ phụ thuộc các byte đã
giải ở vòng trước. Điều đó cho một lời giải duy nhất chạy tuần tự từ `seed = 1`:

```bash
python exploit.py files/cred_call_transcript.txt
```

```text
[*] cred_call_transcript.txt: 17 word 5 chu cai
[*] word dau tien bat dau bang 'x' = True, word cuoi ket thuc bang 'x' = True
[*] so byte = (rounds-1)*2 + 1 = 33, rounds = len/2 + 1 = 17
[*] hex stage-1 : 63646374667b387538386c335f3834383831335f666c34675f70613535696e677d
[+] giai ma    : cdctf{8u88l3_848813_fl4g_pa55ing}
```

**Bước 3 - Kiểm chứng bằng vòng mã hoá.** `exploit.py` mã hoá lại 33 byte vừa tìm bằng chính
hàm forward của BubbleBabble và so từng ký tự với transcript:

```text
[*] BubbleBabble re-encode : ximok-gemul-ganol-ruvul-hevaf-murof-felyf-metuf-myvaf-cusih-zynok-sitek-lulol-bemef-hatok-norek-lizyx
[+] vong lap khop 85/85 ky tu: True
```

85/85 ký tự chữ cái khớp nhau, và chuỗi re-encode in ra có đúng 16 dấu `-`, tức vẫn là 17
nhóm như transcript. Không có chữ nào trong transcript bị nghe sai (đoán ban đầu rằng `z` là
`x` bị đọc lệch là sai). Chuỗi ra còn tự giải thích: `8u88l3_848813` là
`bubble_babble`, phần đuôi `fl4g_pa55ing` là `flag_passing`, prefix `cdctf{` và dấu `}` đúng
luật đề. Một tính chất phụ của mã cũng được dùng làm van an toàn: nếu một ký tự bị sửa sai,
phép cộng mod 6 sẽ sinh chỉ số không nằm trong 0..3 ở vòng kế tiếp và lời giải gãy ngay tại
đó.

## Flag

```bash
python exploit.py files/cred_call_transcript.txt
```

```text
[*] cred_call_transcript.txt: 17 word 5 chu cai
[*] word dau tien bat dau bang 'x' = True, word cuoi ket thuc bang 'x' = True
[*] so byte = (rounds-1)*2 + 1 = 33, rounds = len/2 + 1 = 17
[*] hex stage-1 : 63646374667b387538386c335f3834383831335f666c34675f70613535696e677d
[+] giai ma    : cdctf{8u88l3_848813_fl4g_pa55ing}
[*] BubbleBabble re-encode : ximok-gemul-ganol-ruvul-hevaf-murof-felyf-metuf-myvaf-cusih-zynok-sitek-lulol-bemef-hatok-norek-lizyx
[+] vong lap khop 85/85 ky tu: True
[+] da luu flag.txt
```

## Reproduce

```bash
python exploit.py files/cred_call_transcript.txt
```

Script chỉ dùng stdlib và đọc transcript đã lưu trong `files/`, không cần audio. Muốn kiểm
lại phần audio (container, phổ, nhịp lời, ASR) thì chạy bốn script trong `analysis/` như
`de.md`; `analysis/asr_check.py` cần weights Whisper `small` tải lần đầu.
