# Verbal Authentication Transmissions 4/5: What the helly - OSINT + Crypto + Password Cracking (500 pts)

**Flag:** `cdctf{idontcare1}`
**Files:** `OTP_CODES_VAT.mp3` (448848 B, sha256 `56c3bbfa042f4e6ae46e577152260d9f1414ae199f09c0c0c3dcba7897d5e11c`)

## Đề bài

Audio 74.808 s được cho là lời đọc các mã S/Key OTP của một operative bên Crimson Offense.
Mã đã hết hạn sử dụng, nhưng từ đó phải recovery lại được mật khẩu gốc, vì mật khẩu này còn
dùng ở chỗ khác. Đề cho ba tham số: `n=8`, hash có nap (folded), không dùng seed. Thẻ bài ghi
500 điểm, hạng OSINT + Crypto + Password Cracking, tác giả `b0b`, format `cdctf{password}`.

## Phân tích ban đầu

`ffprobe` báo MPEG layer III v2, 48 kbps, 24 kHz, đơn kênh, không có ID3 mang nội dung. Cùng
kiểu container với các phần khác của chuỗi VAT, tức file do TTS sinh ra; payload nằm ở lời đọc,
không phải byte thừa hay mode tín hiệu.

Whisper `base` và `small` (một từ một phân đoạn, `analysis/asr_base_run.log`,
`analysis/asr_small_run.log`) cho 8 khối `CODE n`, mỗi khối sáu từ: 48 token. Đối chiếu với từ
điển 2048 từ của RFC 1760 (1-4 ký tự, `files/skey_dictionary.txt`) thì 44/48 token của bản merge
nằm trong từ điển, các token còn lại dài 5-6 ký tự nên chắc chắn là lỗi nghe. Sáu từ một mã là
đúng signature của định dạng six-word S/Key: 6 x 11 bit cho 64 bit giá trị cộng 2 bit dự phòng.

Bài toán còn lại là tìm đúng ba thứ: cách đóng gói 64 bit thành sáu từ, hàm bước của chuỗi hash,
và mật khẩu. Hai thứ đầu có thể kiểm chứng bằng dữ liệu, không cần đoán.

## Các hướng đã loại

1. **Dữ liệu ngoài lời đọc**: frame MP3 đều, không ID3, không kênh phụ. Loại.
2. **Nhận dạng bị ràng buộc từ điển**: Vosk grammar 2048 từ trên từng lát cắt 1.1 s trả về rỗng
   49/49 lát cắt (`analysis/asr_vosk_grammar_attempt.txt`), kèm 931 dòng
   `Ignoring word missing in vocabulary` cho 19 từ khác nhau trong từ điển bị model bỏ qua.
   Loại, quay về ba bản nghe không ràng buộc.
3. **Chuỗi RFC 1760/2289 đúng nghĩa**: `step(v) = fold(MD5(8 byte thô))`. Kiểm trên mọi cặp mã
   đọc được, `k = 1..7`, cả MD4, MD5, SHA1 và cả hai thứ tự byte: 0 khớp. Loại.
4. **Kết quả âm tính ở hướng 3 từng bị sai một lần**: khi so sáu từ nguyên bản thì hai bit checksum
   của từ thứ sáu luôn luôn lệch, nên mỗi cặp đều "lệch đúng một ô" và bị loại bởi cùng một ngưỡng
   chịu lỗi. Chỉ khi chuyển sang so giá trị 64 bit (bỏ 2 bit checksum) thì phép thử mới có nghĩa.
   Ghi lại vì đây là chỗ âm tính dễ đọc sai nhất của bài.

## Chuỗi khai thác

**Bước 1 - Chốt cách đóng gói bằng vector của RFC.** Phân tích Appendix C của RFC 2289
(27 vector pass phrase + seed + count -> hex -> sáu từ, lưu nguyên văn ở
`analysis/rfc2289_test_vectors.txt`) và đối chiếu implementation:

```python
def fold_md5(data):                      # 128 bit -> 64 bit: XOR nua dau voi nua cuoi
    d = hashlib.md5(data).digest()
    return int.from_bytes(d[:8], "big") ^ int.from_bytes(d[8:16], "big")

def parity(v):                           # tong 32 cap bit, lay 2 bit thap nhat
    return sum((v >> (2 * i)) & 3 for i in range(32)) & 3

def to_words(v):                         # 64 bit + checksum -> 6 index 11 bit
    x = (v << 2) | parity(v)
    return [WORDS[(x >> (55 - 11 * i)) & 0x7FF] for i in range(6)]
```

`python analysis/skey_kat.py` in ra `27/27 vector khop ca hex lan sau tu`, với điều kiện seed
được hạ chữ thường trước khi nối với pass phrase. Cùng script chạy tiếp phép thử checksum trên
từng mã nghe được: 5 mã đủ 6 từ trong từ điển (3, 4, 5, 6, 7) và 4 mã trong số đó hợp lệ
(3, 4, 5, 7); mã 6 đòi từ thứ sáu là `WATS` thay vì `WAVE`. Từ đây có hai kết luận: encoding là
bản chuẩn RFC, và transcript vẫn còn lỗi nên không được dùng nó làm bằng chứng tuyệt đối.

**Bước 2 - Tìm hàm bước thật.** Quét 65 tổ hợp (4 hash, 4 kiểu nap, 5 dạng input) và kiểm xem
`step^k(mã A)` có cho `mã B` hay không, cho phép lệch một ô:

```text
ma dung duoc 6 tu (lam bang chung): [3, 4, 5, 6, 7]
so ket hop hash/nap/input da thu: 65
  KHOP  step^1(Code4) ~ Code3  lech=[]   [md5 / xor-nua / chuoi-hex]
  KHOP  step^2(Code5) ~ Code3  lech=[]   [md5 / xor-nua / chuoi-hex]
  KHOP  step^1(Code5) ~ Code4  lech=[]   [md5 / xor-nua / chuoi-hex]
mo hinh RFC (8 byte tho): khong co
```

Tức là `step(v) = fold(MD5("%016x" % v))`: dữ liệu đưa vào MD5 là chuỗi hex 16 ký tự của giá trị
bước trước, không phải 8 byte thô. Script cũng suy ngược được mã 2 và mã 1 từ mã 3
(`GLEN YAWL PEW RUNG BUOY BODY`, `BAIT GAUR OS TACT TIP DUD`), chỉ rõ các ô `GLIN/YALL/RUN` và
`BATE/GOWER` là lỗi ASR chứ không phải mã thật. Với `n=8` và không seed, chuỗi đi từ
`ma8 = fold(MD5(password))` đến `ma1 = step^7(ma8)`.

**Bước 3 - Quét wordlist bằng mask.** Mỗi mã cho biết trước một phần của giá trị 64 bit: ô 1-5
mang 11 bit, ô 6 mang 9 bit (2 bit cuối là checksum). Số bit chắc chắn của tám mã là
`[53, 42, 64, 64, 64, 64, 64, 53]`. Với ứng viên `P`, tính `v = fold(MD5(P))` rồi đi 8 bước, mỗi
bước so `(v & mask) == value` cho các mask từ 53 bit trở lên. Một mask 53 bit đã cho xác suất va
chạm giả ~ 1e-8 trên toàn bộ 14.3 triệu ứng viên, nên mọi hit đều được dựng lại thành 8 mã và đòi
khớp tuyệt đối ít nhất 3 mã trước khi được nhận.

```text
[*] wordlist C:/Tools/rockyou.txt: 14344391 dong, 14 tien trinh, so bit chac cua tung ma: [53, 42, 64, 64, 64, 64, 64, 53]
[*] mask hit b'idontcare1': 39/48 o khop, 3/8 ma khop het
Code 3    GRUB TRY BABY MUFF GRIM ACME             GRUB TRY BABY MUFF GRIM ACME             == KHOP
Code 4    CUB CUTS GAIN SLUM MUST ELM              CUB CUTS GAIN SLUM MUST ELM              == KHOP
Code 5    RUST HERB BAIL SAVE IFFY DO              RUST HERB BAIL SAVE IFFY DO              == KHOP
[*] 39/48 o tu khop voi transcript, 3/8 ma khop tuyen doi
[+] cdctf{idontcare1}
```

Toàn bộ quét mất 2 phút 47 giây với 14 tiến trình (`real 2m46.994s` trong
`analysis/crack_rockyou.log`). Chuỗi nằm ở dòng 39260 của rockyou. Tám mã dựng từ mật khẩu trùng
với audio ở 39/48 ô; 9 ô còn lại đều là cặp từ gần âm (`BATE/BAIT`, `GOWER/GAUR`, `GLIN/GLEN`,
`YALL/YAWL`, `RUN/RUNG`, `NO/NOLL`, `HOLD/HOLT`, `WORT/WERT`, `LOSE/LOS`), tức là lỗi nghe chứ
không phải lỗi chuỗi.

**Bước 4 - Đối chứng ngoài bài.** Đề nói mật khẩu "would help us gain access elsewhere". Cùng
chuỗi đó mở keyring PGP của operative. File `VAT_key` tải về cùng đợt với audio, nhiều khả năng là
artifact của phần 3/5 (S2K iter+salt SHA1, protect-count 65011712, AES-256): `gpg --import` với
passphrase này báo `secret key imported`, `secret keys imported: 1`. Không có pass phrase nào khác
được thử.

## Flag

```text
cdctf{idontcare1}
```

## Reproduce

```bash
python analysis/skey_kat.py           # 27/27 vector RFC 2289 + sang loc checksum
python analysis/chain_model_scan.py   # 65 to hop, chi md5/xor-nua/chuoi-hex khop
python exploit.py --selftest          # cay chuoi gia: probe bat duong duoi that
python exploit.py --crack C:/Tools/rockyou.txt 14
python exploit.py --verify idontcare1 # dung lai 8 ma tu mot chuoi
```

`--selftest` in ra `planted duoc bat = True, ba mat khau sai duoc loai = True, round-trip 6-tu = True`,
tức bộ lọc đã được chứng minh là bắt được dương tính trước khi tin vào kết quả quét. Bước ASR
không nằm trong đường chạy của cờ: `files/transcript_asr.txt` đã lưu sẵn lời đọc, còn lệnh sinh
nó ghi trong `de.md` (cần model Whisper và Vosk, không commit). Wordlist 140 MB cũng không commit;
thay wordlist khác vào `--crack` là chạy tiếp được.
