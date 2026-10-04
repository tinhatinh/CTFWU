# notes.md - vat-4-what-the-helly

Input: `files/OTP_CODES_VAT.mp3` (448848 B, sha256 `56c3bbfa042f4e6a...897d5e11c`),
74.808 s, MPEG layer III v2, 48 kbps, 24 kHz, mono.
Định dạng cờ đề yêu cầu: `cdctf{password}`. Dữ kiện đề: `n=8`, hash có nap, không seed.

## H1 - Dữ liệu nằm trong container hoặc dưới dạng mode tín hiệu
cmd: `ffprobe -show_entries format=duration,bit_rate -show_entries stream=sample_rate,channels,codec_name files/OTP_CODES_VAT.mp3`
evidence: mp3 trần, không ID3 mang nội dung, 24 kHz mono 48 kbps giống các phần khác của chuỗi
VAT (TTS). Phổ và cấu trúc frame không có gì lạ so với file TTS thông thường.
result: DEAD - payload là lời đọc, không phải byte thừa hay mode số.

## H2 - Whisper `base` cho bản nghe
cmd: `python analysis/asr_whisper.py vat.wav base ./models` (log: `analysis/asr_base_run.log`)
evidence: 48 token OTP, 37/48 nằm trong từ điển S/Key. 11 token lệch (`GOWER`, `GLIN`,
`YALL`, `PUE`, `BOOY`, `GAME`, `BAL`, `IFY`, `WIRM`, `HULT`, `ACER`) và 6 token 5-6 ký tự
trong khi từ điển chỉ có từ 1-4 ký tự.
result: ĐỦ để định dạng scheme (S/Key six-word), chưa đủ để làm bảng chứng 64 bit.

## H3 - Whisper `small` với word timestamps
cmd: `python analysis/asr_whisper.py vat.wav small ./models` (log: `analysis/asr_small_run.log`)
evidence: 59 phân đoạn, mỗi phân đoạn một từ (độ dài 1.0-1.2 s), 42 token OTP, 36/42 trong từ
điển. Hai engine khác nhau đúng ở những ô cần sửa: base `BATE/TACT/NO/HOLD`, small
`BAIT/TACKED/KNOLL/HOLT`.
result: dùng làm nguồn chính cho mask, nhưng vẫn còn 4-6 ô sai.

## H4 - Vosk với grammar giới hạn đúng 2048 từ
cmd: `python analysis/asr_vosk_grammar_probe.py <model-vosk> vat.wav all`
(log: `analysis/asr_vosk_grammar_attempt.txt`)
evidence: 49/49 lan cat (moi lan ~1.1 s, mot tu) tra ve khong co candidate nao. Grammar 2048 tu
bi model bo qua 19 tu khac nhau (931 dong `Ignoring word missing in vocabulary`: `awk`, `amra`,
`bhoy`, `blat`, `bogy`, `ceil`, `geld`, `lesk`, `lura`, `mert`, `oint`, `oldy`, `owly`, `quod`,
`skat`, `teet`, `trag`, `whee`, `yawl`), va khi thu khong grammar thi API báo
`Expecting array of strings, got: 'null'` roi segfault.
result: DEAD - nhân dạng bị ràng buộc từ điển không dùng được trên lát cắt ngắn với model
small-en; chuyển sang Vosk không ràng buộc (H5).

## H5 - Vosk tự do
cmd: `python analysis/asr_vosk.py <model-vosk> vat.wav` (log: `analysis/asr_vosk_run.log`)
evidence: `buoy`, `own`, `know`, `missed`, `word i like`, `los`, `says` - cùng kiểu lệch với
Whisper, xác nhận các ô nghi vấn nằm ở vị trí 1, 2, 5, 6 của một số mã.
result: dùng để merge, không dùng riêng.

## H6 - Đóng gói six-word là chuẩn RFC hay biến thể
cmd: `python analysis/skey_kat.py` (log: `analysis/skey_kat.log`)
evidence: 27/27 vector Appendix C của RFC 2289 khớp cả hex lẫn sáu từ, với điều kiện seed được
chuyển sang chữ thường trước khi nối với pass phrase, MD4/MD5 nap byte-wise nua dau voi nua cuoi,
SHA1 nap theo word va ghi little-endian. Tu dien 2048 tu RFC 1760, tu 1-4 ky tu. Ba bit
duoc dung lam checksum: tong 32 cap bit cua gia tri 64 bit, lay 2 bit thap nhat, nam o 2 bit
cuoi cua tu thu sau.
result: ĐÓNG góp - encoding display là bản chuẩn; sang loc checksum cho 5/8 ma du 6 tu dien,
4 ma (3,4,5,7) hop le, ma 6 lech o tu thu sau (`WAVE` -> `WATS`).

## H7 - Chuoi hash theo RFC: step = fold(MD5(8 byte tho))
cmd: `python analysis/chain_model_scan.py` phan 8-byte-tho (log: `analysis/chain_model_scan.log`)
evidence: 0 kieu khop tren 20 cap co the giua 5 ma du 6 tu dien, voi md4/md5/sha1, k=1..7,
ca hai byte order.
result: DEAD cho chieu dai 1-7 buoc. Ket luan nay gan nhu chac vi truoc do co mot lan tinh sai:
xem H8.

## H8 - Negative bi nhieu boi 2 bit checksum
cmd: (trong phien) so sanh 6 tu nguyen ban cua `step(mask)` voi transcript, cho phep lech 1 tu
evidence: tu thu sau cua moi ma duoc sinh ra deu mang checksum nguyen ban, trong khi ben so sanh
duoc thiet ke lech 1 o. Negat ive o H7 chi co gia tri sau khi doi sang so sanh gia tri 64 bit
(khoi 2 bit checksum), do la cach `chain_model_scan.py` va `exploit.py` dang lam.
result: GHI LẠI - bài học về self-test; probe chưa được cài positive control thì âm tính vô nghĩa.

## H9 - Hàm bước thật
cmd: `python analysis/chain_model_scan.py`
evidence: 65 tổ hợp (4 hash, 4 kiểu nap, 5 dạng input). Chỉ `md5 / xor-nua / chuoi-hex` khớp,
3 kieu khop voi lech=[]: `step(Code4)=Code3`, `step(Code5)=Code4`, `step^2(Code5)=Code3`.
Suy ra Code2 và Code1 từ Code3: `GLEN YAWL PEW RUNG BUOY BODY` và `BAIT GAUR OS TACT TIP DUD`,
khang dinh cac o `GLIN/YALL/RUN` va `BATE/GOWER` la loi ASR.
result: ĐÓNG góp - `step(v) = fold(MD5("%016x" % v))`, ma 8 = fold(MD5(password)) (no seed),
ma 1 = step^7(ma 8) dung voi n=8.

## H10 - Probe cua bo loc
cmd: `python exploit.py --selftest`
evidence: cay mot mat khau gia, sinh 8 ma, bo loc bat dung `planted-secret-1`; ba chuoi sai
(`password`, `letmein`, `planted-secret-2`) bi loai; round-trip 64 bit <-> 6 tu dung.
result: PASS - so bit cua mask lan luot 53, 42, 64, 64, 64, 64, 64, 53; bo loc dung mask >= 45 bit.

## H11 - Quet wordlist
cmd: `python exploit.py --crack C:/Tools/rockyou.txt 14`
evidence: 14 344 391 dong, 14 tien trinh; dung 1 mask hit duy nhat:
`[*] mask hit b'idontcare1': 39/48 o khop, 3/8 ma khop het` (log: `analysis/crack_rockyou.log`).
Xac suat duong ham gia: uoc luong tren so lan thu mask ~ 1.1e8 lan voi cac mask 53-64 bit,
ke ca khi chi dung 53 bit thi ~ 1e-8, nen mot hit la hit that; exploit.py con buoc >=3 ma khop
tuyen doi truoc khi ghi co. Chuoi nam o dong 39260 cua rockyou.
result: CỜ - `cdctf{idontcare1}`.

## H12 - Doi chieu ngoai chuoi OTP
cmd: `gpg --batch --pinentry-mode loopback --passphrase-fd 0 --import <VAT_key>` voi passphrase
`idontcare1`
evidence: `key 9BAAC44EC4B7766A: secret key imported`, `secret keys read: 1`,
`secret keys imported: 1`; S2K la iter+salt SHA1 protect-count 65011712 (algo 7 = AES-256),
nen khong the mo neu passphrase sai.
result: XÁC NHẬN ĐỘC LẬP - vat 4/5 và keyring của b0b dùng chung một mật khẩu.

## Cờ

`cdctf{idontcare1}` (verbatim trong `analysis/crack_rockyou.log`).
