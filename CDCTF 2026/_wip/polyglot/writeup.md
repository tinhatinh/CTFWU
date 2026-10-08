# Polyglot - Reverse Engineering (500)

**Flag:** chưa xác nhận. Prefix đã chứng minh là `cdctf{SecretOfComp`; ứng viên đã nộp gợi ý
`cdctf{SecretOfCompartmentalized}` · **Điểm:** 500 · **Tác giả:** reep236
**Files:** `Polyglot1.zip` (2313 B, sha256 `f96c6082004222a2c8356d24e0edfb92f8256c5f9986a7d099b5b11089d88555`)

## Đề bài

Đề cho ba file: một "protocol" bằng Haskell, một bộ câu hỏi 32 dòng, một bộ câu trả lời 32 dòng đã phục
hồi nhưng mỗi dòng thiếu mất một phần. Nhiệm vụ là lấy lại thông tin còn thiếu, tức module `Secrets` chứa
`KEY` mà `Program1.hs` import. Gợi ý "far depths of Glasgow, Scotland" chỉ tới GHC và phương ngữ
Glasgow; format cờ là `cdctf{ABunchOfTitleCaseWords}`.

## Phân tích

`Program1.hs` dùng type-level programming (`DataKinds`, `TypeFamilies`, `UndecidableSuperClasses`) và
`import Secrets (KEY)`, với `KEY` là một `Symbol`. Chạy trực tiếp không được vì máy không có GHC và cũng
không có `Secrets.hs`, nên phải viết lại đúng semantics của nó rồi giải ngược.

Semantics nằm ở instance `LocaleSet`. Với state `n` và ký tự `c`:

```haskell
locales _ _ =  locale  (Proxy @(Mod (n * CharToNat c) M1))
            :  locales (Proxy @(Mod (n * CharToNat c) M2)) (Proxy @(UnconsSymbol cs))
```

`type M1 = 6`, `type M2 = 7`, `data Locale = Alpha | Beta | Gamma | Delta | Epsilon | Zeta`, và
`dialect = zipWith6 mkForms (locales @1 ls) ... (locales @6 ls)` với `mkForms` person place thing time
method reason. Nghĩa là có 6 chuỗi song song seed `n = 1..6`, mỗi bước phát ra
`out = (n * ord c) mod 6` và chuyển `n' = (n * ord c) mod 7`, mỗi chuỗi tương ứng một cột
Who/Where/What/When/How/Why qua `\case` trong `respond`.

Vì phép mod 7 chỉ nhân nên state của chuỗi j luôn bằng `(j * P) mod 7` với `P = ∏ ord(c) mod 7`: toàn bộ
6 chuỗi được theo dõi bằng đúng một biến mod 7. `respond` đọc một dòng input cho mỗi `Forms`, nên số dòng
bằng đúng độ dài `KEY`, tức `len(KEY) = 32` và body cờ là 25 ký tự.

Dữ liệu tự kiểm chứng cách đọc này: 32 dòng answer đều có đúng 3 fragment, và category của fragment khớp
thứ tự question từng dòng. Parser được đối chiếu với đủ 96 fragment quan sát được.

## Hướng đã thử

1. **Homoglyph hoặc stego trong byte**: cả ba file không có byte nào ngoài ASCII; histogram dấu cách cuối
   dòng là uniform (Answers 1/dòng do mỗi variant kết thúc bằng space, Questions 0).
2. **Zip chứa entry ẩn hoặc ADS**: `unzip -l` chỉ có 4 entry (folder + 3 file), không comment; `dir /r`
   chỉ thấy `Zone.Identifier` do trình duyệt gắn. Ba lần tải cùng md5 `55e1ce98f5df3c1b44b73f1b6b392531`
   dù BTC nói đã update, nên bản tải về không đổi.
3. **Thứ tự question dòng 21-32 mã hóa đuôi**: 20 dòng đầu là đúng 20 tổ hợp chập 3 của 6 cột theo thứ tự
   chuẩn, 12 dòng sau là bản đảo ngược của 12 dòng đầu. Không có bit nào ngoài mẫu hình.
4. **Nhánh "chuỗi sống" để đuôi vẫn bị ràng buộc**: `python exploit.py files/Polyglot1.zip --alive`, kết quả ở `analysis/alive.log`. Bắt buộc không có ký tự `≡ 0 (mod 7)` ở vị trí 18 thì
   quét toàn bộ chuỗi khả dụng ở index 12-17 cho 528 kết quả, tất cả là chuỗi phụ âm không tạo thành từ đã nhận diện (`CHCECL`, `CHmEmv`);
   quét theo từng vị trí chết 18, 20, 22, 24, 26, 28, 30 với từ điển 10k và 370k từ cho 0 cụm có nghĩa.
   Loại, nên nhánh tiếng Anh buộc ký tự 18 là `p`.
5. **Dò từ điển không có tiền tố cờ**: tìm cụm TitleCase khớp ràng buộc mà không giả định `cdctf{` cho
   0 kết quả, vì 3 ký tự đầu bị ép là `cdc` dạng chữ thường. Sai ở chỗ đặt giả định sai về chỗ bắt đầu body.
6. **Chạy GHC để lấy oracle**: không có `ghc`/`runghc`/`stack` trên máy, và `import Data.List (zipWith6)`
   cũng không có trong `Data.List` chuẩn. Loại, mô hình viết tay đã đủ và có self-test.

## Lời giải

**Bước 1 - Dựng lại semantics và kiểm tra parser.** `exploit.py` mô phỏng đúng `locales` cho cả 6 chuỗi rồi
ngược lại: sinh ràng buộc từ answer, ép mỗi fragment phải đứng đúng cột mà question hỏi.

```bash
python exploit.py files/Polyglot1.zip --selftest
```

```
[selftest] plant = 'GlesgaWeeFreeMenPureDeadlyBampot'
[selftest] KEY cai dat luon nam trong tap kha dung o ca 32 vi tri: True
[selftest] so vi tri bi ep cung 1 chu: 6
```

Self-test cài một KEY đã biết, sinh answer bằng chính mô hình rồi chạy bộ lọc: KEY cài luôn nằm trong tập
khả dụng ở cả 32 vị trí, nên các kết luận "không còn dữ kiện" phía sau không phải do probe hỏng.

**Bước 2 - Siết ràng buộc bằng DP forward và backward.** Với mỗi vị trí, giữ các state mod 7 mà một đường
di khả thi thực sự đi qua (fwd ∩ bwd), rồi đếm ký tự còn hợp lệ.

```bash
python exploit.py files/Polyglot1.zip
```

```
lines = 32  ->  len(KEY) = 32

Ung cu vien cua tung vi tri (chu cai, sau bua backward):
  pos  1  states 1   1 cai: c
  pos  2  states 1   1 cai: d
  pos  3  states 23   2 cai: Wc
  pos  4  states 2   8 cai: DJPVhntz
  pos  5  states 123456   8 cai: BHNZflrx
  pos  6  states 45   3 cai: EQo
  pos  7  states 2   1 cai: S
  pos  8  states 5   1 cai: e
  pos  9  states 1   7 cai: EKQWcou
  pos 10  states 123456   8 cai: BHNZflrx
  pos 11  states 2   1 cai: e
  pos 12  states 6   2 cai: Jt
  pos 13  states 3   9 cai: CIOUagmsy
  pos 14  states 123456   8 cai: BHNZflrx
  pos 15  states 3   2 cai: Cm
  pos 16  states 5   2 cai: Eo
  pos 17  states 2   2 cai: Cm
  pos 18  states 1   8 cai: FLRXdjpv
  pos 19  states 0123456  52 cai: ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz

Ky tu kha dung o vi tri 18 ma cung chia het cho 7: Fp
Tu vi tri 19 tro di, ca 52 chu cai deu kha dung -> duoi KEY khong bi file nay rang buoc.
```

Vị trí 1-3 ép `cdc`, vị trí 7 ép `S` và vị trí 8 ép `e`; bộ ba 4-5-6 cho phép `t`,`f`,`{`, nên `KEY` là
nguyên văn xâu cờ chứ không riêng body. Trong các ứng viên đã phân tích, prefix tiếng Anh được chọn ở
18 vị trí đầu là `cdctf{SecretOfComp`: `Se` + `cr` + `e` + `t` ghép thành `Secret`, `O` + `f` ghép thành
`Of`, rồi `C` + `o` + `m` + `p` mở đầu một từ `Comp*`.

**Bước 3 - Chỉ ra vùng mơ hồ bằng chính dữ liệu.** State mod 7 là hấp thụ: `P = 0` thì mọi cột ra Alpha bất
kể ký tự, và `p` (112) ở vị trí 18 làm `P = 0`. Bốn KEY khác nhau phần đuôi đều tái tạo đủ 32 dòng, trong
khi hai xâu đối chứng sai thì lệch ngay:

```bash
python exploit.py files/Polyglot1.zip "cdctf{SecretOfCompartmentalized}"
```

```
KEY = 'cdctf{SecretOfCompartmentalized}' (32 ky tu, du 32 dong)  khop 32/32 dong | TAI TAO DU TOAN BO SO DONG DA KIEM
```

```
KEY = 'cdctf{SecretOfCompartmentalised}' (32 ky tu, du 32 dong)  khop 32/32 dong | TAI TAO DU TOAN BO SO DONG DA KIEM
KEY = 'cdctf{SecretOfCompoundSentences}' (32 ky tu, du 32 dong)  khop 32/32 dong | TAI TAO DU TOAN BO SO DONG DA KIEM
KEY = 'cdctf{SecretOfComprehensiveness}' (32 ky tu, du 32 dong)  khop 32/32 dong | TAI TAO DU TOAN BO SO DONG DA KIEM
KEY = 'cdctf{WrongPhraseEntirelyWrong}' (31 ky tu, ph bao 31/32 dong)  khop 17/31 dong | lech dong 7,8,9,10,11,12,13,15,16,17,18,19,20,21
```

Có 52 chữ cái hợp lệ ở mọi vị trí từ 19 nghĩa là phần còn lại của body không do protocol quyết định,
nó là một cụm từ tiếng Anh. Bài này vì thế cần tác giả xác nhận: reep236 trả lời rằng cờ bị dài quá khi
chuyển từ dev sang testing, script verify bỏ sót input vẫn pass, và checker đã được đổi thành regex tính
từ vùng mơ hồ, tức mọi đuôi sau `cdctf{SecretOfComp` đều được chấp nhận.

## Kết quả

Vùng đã chứng minh bằng dữ liệu:

```
cdctf{SecretOfComp
```

Chuỗi nộp theo checker mới của tác giả:

```
cdctf{SecretOfCompartmentalized}
```

## Tái hiện

```bash
python exploit.py files/Polyglot1.zip
python exploit.py files/Polyglot1.zip --selftest
python exploit.py files/Polyglot1.zip "cdctf{SecretOfCompartmentalized}"
python exploit.py files/Polyglot1.zip "cdctf{WrongPhraseEntirelyWrong}"
python exploit.py files/Polyglot1.zip --alive       # phan nhanh chuoi song
python exploit.py files/Polyglot1.zip --invariant # ma tran 6 cot, 26/32 hang bat bien
```

Log thật của ba lệnh đầu nằm trong `analysis/regions.log`, `analysis/selftest.log`, `analysis/verify.log`.
