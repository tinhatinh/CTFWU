# notes.md - yummy-rat-toast

Input: `files/hash.txt` (33 B, sha256 `082b5ad8c25c7437967bbb2c0b10c434fb6a95a8529b9d6e7c3fa09aa139f1bb`)
Định dạng cờ đề yêu cầu: `cdctf{...}`

## H1 - Mật khẩu nằm trong bảng md5 công khai
cmd: `browser-use` mở `https://md5.gromweb.com/?md5=3f1ebefc63dc39f3c9b934a30accb221`
evidence: trang báo "Provided MD5 hash could not be reversed into a string: no reverse string was found", DB ghi 832.927.522 tổng
result: DEAD - không có trong rainbow DB lớn nhất thử được, phải tự quét

## H2 - Mật khẩu phổ biến kiểu rockyou
cmd: `hashcat -m 0 -a 0 hc.txt union.txt -r rules/best64.rule` (union = 27.7M dòng: xato-net-10M, Pwdb_top-10M, darkc0de, alleged-gmail, openwall.net-all, rockyou-75)
evidence: `Status: Exhausted`, `Progress: 2138454780/2138454780`; chạy thuần 27.7M và `T0XlC` cũng Exhausted
result: DEAD

## H3 - Tên người hoặc từ điển Anh + rule
cmd: `hashcat -m 0 -a 0 hc.txt base.txt -r rules/dive.rule` (base = 443.026 dòng: names.txt, male/female/family top-1000, words_alpha, rockyou-75)
evidence: Exhausted với `dive` (99.092 rule), `rockyou-30000`, `d3ad0ne`, `Incisive-leetspeak`; riêng `theme.txt × Incisive-leetspeak` đo được `Progress: 22718732085/22718732085`
result: DEAD - các corpus này không chứa tên nhân vật Ratatouille

## H4 - Mọi chuỗi chữ thường và mọi chuỗi số
cmd: `hashcat -m 0 -a 3 -i --increment-min=1 --increment-max=9 -1 ?l hc.txt '?1?1?1?1?1?1?1?1?1'`
evidence: `analysis/mask_lowercase_lengths1-8.txt`, Exhausted tới `208827064576/208827064576` (26^8); `?d^1-12`, `?u^1-7`, `?h^1-8`, `(?l?u)^1-7`, `(?l?d)^1-8` cũng chạy hết
result: PARTIAL - chữ thường độ dài 9 bị cắt giữa chừng khi tắt tiến trình, chỉ 1-8 là có bằng chứng đầy đủ; kết luận đúng hướng vẫn là chữ hoa + số

## H5 - Bảng mã và hash kép
cmd: `python t4.py` và `python t5.py` (scratch)
evidence: 49.566.060 ứng viên qua UTF-8/16/16LE/16BE/32/latin-1/cp1252 có và không có `\n`, `\r\n`; 26.405.190 dạng md5(md5(x)) hex/raw, bọc `cdctf{}`, `flag{}`, prefix/suffix `alex`, `rat`
result: DEAD - đề nói md5 thật, không có mẹo bảng mã

## H6 - Hai batch wordlist lớn "Exhausted" nhưng không quét gì
cmd: `hashcat $CM --session=x -a 0 "$wordlist" -r rules/dive.rule "$H"` (script tự viết, nối hashfile ở cuối)
evidence: hashcat nhận `wordlist` làm hashfile và `hc.txt` làm wordlist; log vẫn in `Status: Exhausted` vì chỉ vài dòng của wordlist trông như digest hợp lệ, phần còn lại bị báo `Token length exception` và bị bỏ
result: FIXED - thứ tự đúng là `hashcat [opts] HASHFILE [wordlist|mask]`; toàn bộ pass `theme2/theme/base2/usernames` phải chạy lại, và mỗi pass sau đều in kèm `Progress: x/y` để đối chiếu `y ≈ |wordlist| × |rules|`

## H7 - John 1.9 với ruleset KoreGel
cmd: `john --format=raw-md5 --wordlist=base.txt --rules=KoreGel h.txt`
evidence: log dừng ở `! No "KoreGel" mode rules found` rồi `Terminating on error, wordlist.c:1107`, thoát trong vài ms; bản này chỉ có `best64 d3ad0ne dive T0XlC T0XlCv1 InsidePro-PasswordsPro rockyou-30000 specific passphrase-rule1/2`
result: DEAD - không phải bằng chứng phủ định; JtR raw-md5 trên máy này cũng chỉ đạt 657k c/s nên chuyển hẳn sang hashcat

## H8 - Danh sách MD5 16 byte khác
cmd: `hashcat -m 3000 -a 0 hc.txt theme.txt`
evidence: MD4 nạp hash bình thường và chạy hết; `-m 6000` (RIPEMD-128), `-m 10` (MD2), `-m 2400` báo `Token length exception` / `Separator unmatched` ngay khi nạp
result: DEAD cho MD4; ba mode kia là phép thử không hợp lệ, không tính là đã loại

## H9 - Tên dàn cast Ratatouille, ghép thành tên đầy đủ, có hoa thường
cmd: `hashcat -m 0 -w 3 --backend-devices=3 -a 0 hc.txt theme3.txt -r rules/dive.rule`
evidence: `Status: Cracked`, `Progress: 4194304/19611893808 (0.02%)`, outfile `3f1ebefc63dc39f3c9b934a30accb221:Alfredo Linguini01`; Python xác nhận `md5("Alfredo Linguini01") == 3f1ebefc63dc39f3c9b934a30accb221`
result: OK - cờ: `cdctf{Alfredo Linguini01}`

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
