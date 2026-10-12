---
title: "Don't fill me"
category: "Misc"
tags: ["google-form", "fb_public_load_data", "language-parameter", "plaintext-reading"]
solve_date: "2026-10-09"
language: "vi"
---

# Don't fill me

**Flag:** `OWASP{Thank_you_for_participating!!}`
**Target:** `https://docs.google.com/forms/d/e/1FAIpQLSdm3ndV0ZckRmnABXjalIcRu6Dc46dowK5q0OY1EG-cjT1mGQ/viewform` — Google Form "ByteMe CTF FeedBack Form", 31 câu hỏi.

## Đề bài

Dòng mô tả trên thẻ bài:

```text
fill this we need to submit it to our faculty :(
```

Expert, 500 điểm, tác giả Suyog Jadhav. Thẻ bài ghi số lượt giải là 0 tại thời điểm làm bài.

## Phân tích

### Đối tượng

Trang là một Google Form công khai, tiêu đề `ByteMe CTF FeedBack Form`, 31 câu hỏi, không yêu cầu đăng nhập để xem. Không có response nào được gửi trong quá trình làm bài: cờ nằm trong trang, không cần tương tác với form.

Mọi trang viewform của Google đều nhúng mảng `FB_PUBLIC_LOAD_DATA_`. Cấu trúc liên quan:

```text
FB_PUBLIC_LOAD_DATA_[1][1]    item list (questions)
FB_PUBLIC_LOAD_DATA_[1][2][0] post-submission message slot
```

### Quan sát về tham số hl

Form này do một người tạo Việt Nam dựng, nên render mặc định là `vi`. Khi request thêm `?hl=en`, cùng một ô `[1][2][0]` hiển thị một chuỗi khác:

```text
default render (vi) : "Your response has been recorded"
render with hl=en   : "OWASP{Thank_you_for_participating!!}"
```

Hai bản render cùng một trang, cùng một vị trí trong cấu trúc dữ liệu, chỉ khác nhau ở giá trị của ô đó. Các bản lưu trong workspace đếm được sự khác biệt này:

```console
$ for f in viewform.html viewform_en.html v2.html fbld.json fbld_en.json; do
>   printf "%-18s OWASP{=%d  recorded=%d\n" "$f" \
>     "$(grep -o 'OWASP{' $f | wc -l)" "$(grep -o 'Your response has been recorded' $f | wc -l)"
> done
viewform.html      OWASP{=0  recorded=1
viewform_en.html   OWASP{=1  recorded=0
v2.html            OWASP{=1  recorded=0
fbld.json          OWASP{=0  recorded=1
fbld_en.json       OWASP{=1  recorded=0
```

`viewform.html` là bản render `vi`, `viewform_en.html` và `v2.html` là hai lần fetch với `hl=en`, còn `fbld.json`/`fbld_en.json` là mảng `FB_PUBLIC_LOAD_DATA_` tách từ hai render tương ứng. Giá trị `recorded` đếm chuỗi `Your response has been recorded`.

Trong các buổi làm bài, nhiều giá trị `hl` khác nhau cũng được thử — `en`, `en-US`, `hi`, `fr`, `es`, `de`, `ja`, `pt-BR` — và tất cả đều trả về cùng một chuỗi `OWASP{...}`; chỉ render `vi` gốc là khác.

## Lời giải

Không cần gửi response, chỉ cần đọc trường xác nhận từ bản render tiếng Anh:

```console
$ curl -s "https://docs.google.com/forms/d/e/1FAIpQLSdm3ndV0ZckRmnABXjalIcRu6Dc46dowK5q0OY1EG-cjT1mGQ/viewform?hl=en" -o viewform_en.html
$ grep -o 'OWASP{[^}]*}' viewform_en.html
OWASP{Thank_you_for_participating!!}
```

Đọc đúng vị trí trong cấu trúc dữ liệu, trên hai bản `FB_PUBLIC_LOAD_DATA_` đã tách:

```console
$ python -c "
import json
for f in ('fbld.json','fbld_en.json'):
    d=json.load(open(f,encoding='utf8')); print(f,'items=%d'%len(d[1][1]),'slot[1][2][0]=',repr(d[1][2][0]))"
fbld.json items=31 slot[1][2][0]= 'Your response has been recorded'
fbld_en.json items=31 slot[1][2][0]= 'OWASP{Thank_you_for_participating!!}'
```

Hai mảng có cùng số item (31), xác nhận rằng đây là cùng một form ở hai render khác nhau chứ không phải hai phiên bản nội dung.

## Kết quả

```text
OWASP{Thank_you_for_participating!!}
```

Cờ đọc từ trang remote, từ ô `FB_PUBLIC_LOAD_DATA_[1][2][0]` của render `hl=en`; không có response nào được gửi và không có bước đăng nhập nào. Bảng các bài đã giải của sự kiện ghi nhận bài này ở trạng thái đã giải.

## Tái hiện

Cần `curl` hoặc `requests`, và URL của form còn truy cập được — lời giải phụ thuộc vào trạng thái online của trang, không phải vào artifact lưu local.

```console
$ curl -s ".../viewform"       -o viewform.html
$ curl -s ".../viewform?hl=en" -o viewform_en.html
$ grep -o 'OWASP{[^}]*}' viewform_en.html
```

Nếu nội dung form đổi hoặc trang ngừng hoạt động, cần bản HTML đã lưu để kiểm tra lại.
