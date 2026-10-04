# notes.md - polyglot

Input: `files/Polyglot1.zip` (2313 B, sha256 `f96c6082004222a2c8356d24e0edfb92f8256c5f9986a7d099b5b11089d88555`)
Định dạng cờ đề yêu cầu: `cdctf{ABunchOfTitleCaseWords}`

## H1 - Chạy Program1.hs để lấy oracle
cmd: `which ghc runghc stack`
evidence: không có GHC nào trên máy; file thiếu module `Secrets`, và `import Data.List (zipWith6)` không
tồn tại trong base chuẩn
result: DEAD - phải viết lại bán đột của chương trình rồi giải ngược

## H2 - File là polyglot theo nghĩa kỹ thuật (Haskell cộng một định dạng khác)
cmd: `node -e "...đếm byte > 0x7F, tab, CRLF, dấu cách cuối dòng..."`
evidence: `Program1.hs` 4482 B với 0 byte ngoài ASCII, 0 tab, 0 CRLF; `Questions1.txt` và `Answers1.txt`
cũng 0 byte ngoài ASCII; histogram dấu cách cuối dòng của answers là `{"0":1,"1":32}`
result: DEAD - không có second-reading, không có stego whitespace

## H3 - Zip hoặc NTFS cất thêm dữ liệu
cmd: `unzip -l Polyglot1.zip; unzip -z Polyglot1.zip; cmd.exe /c dir /r Polyglot1.zip`
evidence: 4 entry (folder plus 3 file), không comment; ADS duy nhất là `Zone.Identifier` của trình duyệt;
ba lần tải (`Polyglot1.zip`, `Polyglot1 (1).zip`, `Polyglot1 (2).zip`) cùng md5
`55e1ce98f5df3c1b44b73f1b6b392531` dù BTC nói đã update
result: DEAD - attachment chưa thực sự thay đổi

## H4 - KEY là chuỗi ngẫu nhiên, không liên quan xâu cờ
cmd: `python exploit.py files/Polyglot1.zip`
evidence: DP fwd∩bwd ép vị trí 1 = `c`, 2 = `d`, 3 = `Wc`; 4-6 cho phép `t`, `f`, `{`; vị trí 7 ép `S`
(chữ hoa), 8 ép `e`; xem `analysis/regions.log`
result: OK - `KEY` là nguyên văn xâu cờ, `len(KEY) = 32` nên body 25 ký tự

## H5 - Mô hình inverse có đáng tin không
cmd: `python exploit.py files/Polyglot1.zip --selftest`
evidence: cài `GlesgaWeeFreeMenPureDeadlyBampot`, sinh answer bằng chính mô hình forward, chạy lại bộ lọc:
KEY cài nằm trong tập khả dụng ở cả 32 vị trí (`analysis/selftest.log`)
result: OK - probe có khả năng dương, nên các kết luận thiếu dữ kiện phía sau đáng tin

## H6 - Đuôi recover bằng từ điển TitleCase mà không giả định `cdctf{`
cmd: `node phrase.mjs` (DFS trie 370k từ, chỉ nhận chuỗi TitleCase khớp ràng buộc, bản gốc ở scratch)
evidence: 0 kết quả, vì 3 vị trí đầu bị ép là chữ thường `cdc` nên không có từ TitleCase nào bắt đầu ở vị trí 1
result: DEAD - giả định sai chỗ bắt đầu body, phải xét `KEY` gồm cả wrapper

## H7 - Nhánh "chuỗi sống": không có ký tự `≡ 0 (mod 7)`, đuôi vẫn bị ràng buộc
cmd: `python exploit.py files/Polyglot1.zip --alive`
evidence: 528 chuỗi khả dụng ở index 12-17 và toàn bộ là phụ âm rác, 10 chuỗi đầu là
`SecretCHCECL`, `SecretCHCECR`, `SecretCHCECX`, `SecretCHCECd`... (`analysis/alive.log`)
result: DEAD - nhánh tiếng Anh buộc ký tự 18 thuộc `{F, p}`

## H8 - Ký tự 18 bị ép bởi chính ràng buộc
cmd: `python exploit.py files/Polyglot1.zip`
evidence: ở vị trí 18 chỉ state `P_17 = 1` khả dụng, ký tự phải `≡ 4 (mod 6)`; giao với `≡ 0 (mod 7)` còn
đúng `F` (70) và `p` (112). Dòng in ra: `Ky tu kha dung o vi tri 18 ma cung chia het cho 7: Fp`
result: OK - chọn `p` cho ra `P_18 = 0`, từ vị trí 19 cả 52 chữ cái đều khả dụng nên đuôi mang 0 bit

## H9 - Phần answer còn thiếu (3 cột không hỏi) có recover được không
cmd: `python exploit.py files/Polyglot1.zip --invariant`
evidence: 26/32 hàng có duy nhất một vector 6 cột khả dụng; trong vùng 18 hàng đầu chỉ hàng 3 và hàng 6 là
hai vector (`000333`/`300330` và `033003`/`333000`); xem `analysis/invariant.log`
result: OK - phần thiếu suy ra được mà không cần biết KEY chính xác, nhưng nó là hàm của cùng cặp
`(P, ký tự)` nên không thêm dữ kiện nào về đuôi

## H10 - Chứng minh vùng mơ hồ bằng chính file
cmd: `python exploit.py files/Polyglot1.zip "<KEY>"` với 7 xâu, log ở `analysis/verify.log`
evidence: bốn KEY 32 ký tự khác đuôi (`Compartmentalized`, `Compartmentalised`, `CompoundSentences`,
`Comprehensiveness`) đều khop 32/32 dong; `cdctf{SecretOfComp}` khop 19/19; hai xâu đối chứng
`cdctf{WrongPhraseEntirelyWrong}` chỉ khop 17/31 và `GlesgaWeeFreeMenPureDeadlyBampot` khop 15/32
result: OK - bộ kiểm phân biệt đúng sai, nên bốn lần khop 32/32 không phải trùng hợp. 14 ký tự cuối của
KEY không do protocol quyết định

## H11 - Chốt từ phía tác giả
cmd: hỏi trực tiếp reep236 trên Discord
evidence: "I unfortunately made the flag too long from dev -> testing, and for some reason my verification
script just missed some possible inputs that still caused the check to succeed. It's been made regex past
the region of ambiguity!"
result: OK - checker là regex tính từ hết vùng mơ hồ, mọi đuôi sau `cdctf{SecretOfComp` đều pass. Nộp
`cdctf{SecretOfCompartmentalized}`. Chưa có xác nhận accepted nên bài vẫn ở `_wip`

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
