# Yummy Rat Toast - Password Cracking (500 points)

**Flag:** `cdctf{Alfredo Linguini01}` · **Điểm:** 500 · **Tác giả:** alex
**Files:** `hash.txt` (33 B, sha256 `082b5ad8c25c7437967bbb2c0b10c434fb6a95a8529b9d6e7c3fa09aa139f1bb`)

## Đề bài

Thẻ cho một chuỗi md5 duy nhất, `3f1ebefc63dc39f3c9b934a30accb221`, và nói mật khẩu "based on the name of
a good friend of his". Nhân vật kể chuyện có bạn là chuột Remy, và Remy dẫn lại câu "Anyone can cook" của
một người bạn thông thái. Hai chi tiết đó chỉ thẳng sang phim Ratatouille: Remy, Alfredo Linguini, đầu bếp
Auguste Gusteau. Cờ theo định dạng `cdctf{...}` của giải.

## Phân tích

Bài không kèm file; đầu vào chỉ là digest 16 byte, nên việc đầu tiên là xác định độ khó thật của nó bằng
oracle ngoài. DB tra ngược md5 của gromweb (832.927.522 tổng đã biết) trả lời không tìm thấy:

```text
Provided MD5 hash could not be reversed into a string: no reverse string was found.
```

Cơ sở dữ liệu đã tra không có kết quả cho hash này. Phép thử local trên RTX 3050 (9,6 GH/s với `-m 0`) cũng không tìm thấy preimage trong hai mask: chữ thường dài 1..8 và chữ số dài 1..12. Các kết quả này chỉ loại trừ những tập ứng viên đã thử:

```text
Exhausted  26/26              Exhausted  308915776/308915776
Exhausted  676/676            Exhausted  8031810176/8031810176
Exhausted  17576/17576        Exhausted  208827064576/208827064576
Exhausted  456976/456976
Exhausted  11881376/11881376
```

Gợi ý Ratatouille định hướng wordlist theo tên nhân vật, gồm cả họ tên có khoảng trắng và hậu tố số. Các mask trước đó chưa loại trừ mọi dạng mật khẩu khác.

## Hướng đã thử

1. **Mật khẩu phổ biến**: 27.7 triệu dòng từ xato-net-10M, Pwdb_top-10M, darkc0de, alleged-gmail,
   openwall.net-all, rockyou-75, chạy thuần và với `best64` (2.138.454.780 candidate, Exhausted) và
   `T0XlC`. Không khớp.
2. **Tên người và từ điển Anh**: 443.026 dòng (names.txt, male/female/family top-1000, words_alpha,
   rockyou-75) nhân `dive.rule` (99.092 rule), `rockyou-30000`, `d3ad0ne`, `Incisive-leetspeak`. Exhausted.
3. **Họ tên ghép từ corpus lớn**: 10 triệu username xato và 2,4 triệu từ Wikipedia en/fr/de cộng tên
   Brazil/India/Danish, cùng các combinator. Loại một phần vì hai batch đầu gọi hashcat sai thứ tự tham
   số nên không quét gì (xem `notes.md` H6), sau đó chạy lại đúng thì vẫn không khớp.
4. **Không phải md5**: đề nói "which is in md5, of course". Các digest 16 byte khác được thử; chỉ MD4
   (`-m 3000`) nhận hashfile 32 hex và chạy hết `theme.txt`, cho Exhausted. `-m 6000`, `-m 10`, `-m 2400`
   từ chối nạp hash nên không phải phép thử hợp lệ.
5. **Bảng mã và hash kép**: 49.566.060 ứng viên qua UTF-8, UTF-16, UTF-16LE/BE, UTF-32, latin-1, cp1252,
   có/không `\n` và `\r\n`; 26.405.190 dạng hash kép (md5(md5(x)) hex và raw), bọc `cdctf{}`/`flag{}`,
   ghép `alex`/`rat` làm prefix và suffix. Không khớp.
6. **Chuỗi chữ thường độ dài 1-8 và chuỗi số 1-12**: Exhausted hoàn toàn, nên mật khẩu buộc phải có chữ
   hoa hoặc ký tự khác. Loại mọi đoán kiểu `linguini`, `ratatouille`, `anyonecancook` ở dạng thuần.

## Lời giải

**Bước 1 - Dựng wordlist đúng bối cảnh.** Lấy dàn nhân vật và ê-kíp phim Ratatouille (tên từ thẻ wiki của
bộ phim: Remy, Alfredo Linguini, Skinner, Django, Émile, Anton Ego, Auguste Gusteau, Colette Tatou, Horst,
Lalo, Mustafà, Talon Labarthe, Ambrister Minion, Brad Bird, Michael Giacchino, Patton Oswalt, Lou Romano,
Ian Holm, Brian Dennehy, Peter Sohn, Peter O'Toole, Janeane Garofalo, Will Arnett, John Ratzenberger),
ghép mỗi tên với mọi tên khác bằng ba dấu nối (không, cách, chấm), rồi nhân ba kiểu hoa thường
(lower, title, upper). Kết quả 197.928 dòng, đã mang sẵn dạng "Alfredo Linguini" mà rule không tự sinh được.

```python
SEPARATORS = ["", " ", "."]
CASES = [str.lower, str.title, str.upper]
for a in names:
    for b in names:
        if a != b:
            for sep in SEPARATORS:
                bases.append(a + sep + b)
```

**Bước 2 - Cho chạy qua `dive.rule` để thử hậu tố số.** Wordlist chỉ cần phủ phần tên; hậu tố
`01`, `!`, leet thuộc `dive.rule` (99.092 rule) sẽ tự thêm. Chạy trên iGPU (Speed 44,98 MH/s vì đây là
wordlist + rule stack dài):

```bash
hashcat -m 0 -w 3 --backend-devices=3 --potfile-path=pot_3 --outfile=out_3.txt \
  -a 0 hc.txt theme3.txt -r rules/dive.rule
```

```text
Session..........: stheme3+dive3603
Status...........: Cracked
Hash.Mode........: 0 (MD5)
Speed.#3.........: 44977.2 kH/s (86.33ms) @ Accel:8 Loops:128 Thr:64 Vec:1
Progress.........: 4194304/19611893808 (0.02%)
Candidates.#3....: Alfredo -> GIACCHINO CHEESE!
```

```text
3f1ebefc63dc39f3c9b934a30accb221:Alfredo Linguini01
```

**Bước 3 - Kiểm chứng.** Tính lại md5 bằng Python độc lập với hashcat, và giới hạn không gian trong
`exploit.py` (không phụ thuộc rule) để lần sau chạy lại vẫn ra:

```bash
python exploit.py files/hash.txt
```

```text
candidates tried : 112500 in 0.2 s
password         : Alfredo Linguini01
FLAG             : cdctf{Alfredo Linguini01}
written          : C:\Users\Administrator\Downloads\CTFWU\CDCTF 2026\yummy-rat-toast\flag.txt
```

## Kết quả

```
cdctf{Alfredo Linguini01}
```

## Tái hiện

```bash
python exploit.py files/hash.txt
```

Script tự sinh dàn tên nhân vật, ghép tên, thử ba kiểu hoa thường và hậu tố số từ `""`, `00`-`99`,
`1900`-`2029`, in mật khẩu và ghi `flag.txt`. Muốn chạy nhanh hơn bằng đúng đường của phiên làm bài, dùng
`theme3.txt` + `rules/dive.rule` như Bước 2; lời giải nằm ở candidate thứ 4.194.304 trong tổng 19,6 tỷ.
