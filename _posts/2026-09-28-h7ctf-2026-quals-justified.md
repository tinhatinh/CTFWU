---
title: "Justified — Web (Medium)"
date: 2026-09-28 16:53:17 +0700
lastmod_at: 2026-09-28 16:53:17 +0700
categories: [Web]
tags: [h7ctf-quals, Web]
image:
  path: /CTFWU/H7CTF%202026%20Quals/justified/files/de.png
---
**Flag:** `WEBVERSE{d5f60724dc9f1197140001fa4b24198e}` · Đã nộp trên WebVerse (trang trả về SOLVED)

## Đề bài

Marlowe & Sons là hiệu đóng sách luận văn. Công cụ "Instant Cover Proof" nhận thông tin luận văn
từ form, typeset trang bìa bằng chính máy chữ của cửa hàng, trả về một PDF kèm log của máy chữ
để thợ in đọc trước khi chạy dao. Tag của bài là `CMDI`, và câu chữ "read what the typesetter reports
back" chỉ thẳng vào kênh log.

Không có tài khoản, không có upload: chỉ một form `POST /proof.php`.

## Phân tích ban đầu

Form có 9 field: `title`, `author`, `degree`, `department`, `institution`, `supervisor`, `year`,
`abstract`, `reference`. Mô tả field `reference` là "names your download", còn `title` đi kèm một
gợi ý rất đáng chú ý:

> Tip: type accented characters and symbols using LaTeX, e.g. `M\"uller`, `\'Etienne`, `\OE`.
> Our typesetter renders them for you.

Đó vừa là tính năng vừa là lời thú nhận: chuỗi người dùng nhập được ghép thẳng vào mã nguồn LaTeX.

Gửi một request hợp lệ rồi đọc khối log trong response cho ta biết chính xác thứ đang chạy:

```
This is pdfTeX, Version 3.141592653-2.6-1.40.26 (TeX Live 2025/dev/Debian)
(preloaded format=pdflatex) \write18 enabled.
entering extended mode
(./main.tex
```

Ba chi tiết quyết định:

1. App tự sinh `main.tex` từ input của ta rồi gọi `pdflatex`.
2. `\write18 enabled.` - shell escape bật đầy đủ, không phải chế độ `restricted`.
3. Toàn bộ log (gồm cả stderr) được hiển thị lại cho người gửi.

## Các hướng đã loại

1. Injection shell trực tiếp trên field text (`$(id)`, backtick, `|id`, `;id` trong `title`/`year`):
   log không thay đổi gì. Loại - các field này không đi qua shell.
2. Injection qua `reference` (field "đặt tên file tải về", nơi dễ bị ghép vào `mv`/`-jobname` nhất):
   mọi payload `ref1;id`, `ref1$(id)`, `ref1|id`, `ref1&&id`, `ref1\nid` đều cho ra cùng một jobname
   `ref1id.pdf`. Field này đã được whitelist về `[A-Za-z0-9_-]`. Loại - và đây chính là cái bẫy của đề:
   field có vẻ dễ dính nhất lại là field được làm sạch nhất.
3. Cần `restricted \write18`: nếu restricted thì chỉ lệnh trong danh sách cho phép chạy được.
   Chuỗi `\write18 enabled.` (không có "restricted") trong dòng đầu log đã phủ định điều này.

## Chuỗi khai thác

**Bước 1 - Chứng minh `title` là LaTeX injection.** putting một macro vô hại nhưng quan sát được:

```
A\typeout{ZZMARKERZZ}
```

`ZZMARKERZZ` xuất hiện nguyên văn trong log. Nghĩa là backslash của ta không bị lọc và TeX dịch và thực
hiện macro do người dùng cung cấp.

Bẫy kỹ thuật ở bước này: khi gọi qua `fetch()` trong devtools, chuỗi JS `'A\typeout{...}'` mất backslash
ngay ở tầng escape của JS (`\t` thành tab), khiến probe đầu tiên kết luận sai rằng `title` cũng bị lọc.
Phải dựng payload bằng `String.fromCharCode(92)` rồi mới kết luận.

**Bước 2 - Bật shell escape.** Với `\write18` đầy đủ, một macro duy nhất là đủ để chạy lệnh hệ thống:

```
\immediate\write18{<command>}
```

**Bước 3 - Chọn kênh lấy dữ liệu.** Lệnh chạy xong thì kết quả ở đâu? Ba lựa chọn:
ghi ra file rồi `\input` vào tài liệu (kết quả nằm trong PDF, phải tải và đọc PDF),
hoặc redirect về stderr của pdflatex - thứ mà app đã tự hiển thị cho ta. Chọn kênh cuối:

```
C\immediate\write18{cat /flag.txt 1>&2}
```

`\write18` spawn tiến trình con thừa hưởng file descriptor của pdflatex, nên `1>&2` đưa stdout của
`cat` vào stream mà app gom vào log. Không cần chạm tới PDF, không cần ghi file.

Kết quả trả về ngay trong log:

```
WEBVERSE{d5f60724dc9f1197140001fa4b24198e}
```

**Bước 4 - Đóng gói và chạy lại độc lập.** `exploit.py` dùng `requests`, không cần cookie hay tài khoản;
nó probe `id` để xác nhận shell escape còn hoạt động rồi chạy lệnh. Hai lỗi nhỏ khi đóng gói đã sửa:
log nằm trong `<pre class=...>` nên regex phải là `<pre[^>]*>`, và server trả trang khác nếu thiếu
`User-Agent` dạng trình duyệt.

## Flag
```bash
python exploit.py https://978870f9-5765-justified-06d98.mystery-challenges.webverselabs-pro.com
```

```
[*] shell escape works: uid=33(www-data) gid=33(www-data) groups=33(www-data)
[+] flag: WEBVERSE{d5f60724dc9f1197140001fa4b24198e}
```
