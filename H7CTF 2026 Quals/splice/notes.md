# Notes — Splice

## Mục tiêu do platform cung cấp

- Trang challenge: `https://ctf.webverselabs-pro.com/e/YfQq-BkjAX1I9bECP5U9xcsY/c/28`
- Instance (Express + Cloudflare): `https://ced0f13a-5765-splice-5ba63.mystery-challenges.webverselabs-pro.com`
- Nhãn của WebVerse: `MYSTERY CHALLENGE · CMDI`, HARD, 300 pts, tác giả Kakam / Leighlin Ramsay.
- Nộp flag ngay trên trang WebVerse, format `WEBVERSE{...}`, sync ngược về H7TEX theo email.

## Luồng của app (đọc từ HTML tĩnh, không suy đoán)

`/studio` có hai form:

1. `POST /studio/upload`, multipart, field `clip` → server lưu thành
   `/opt/app/media/<workspace16>/source.wav` (đường dẫn lộ trong log ffmpeg).
2. `POST /api/render`, JSON `{"slug": ..., "theme": ...}` → chạy ffmpeg render audiogram,
   trả `{"ok":bool,"outputs":[{"file","url"}],"errors":...}`.
3. Ảnh trả về phục vụ tại `/m/<workspace16>/<file>`.

Ghi chú cố ý trong JS của trang: *"the API also returns an `errors` field on failure. The Studio does not surface it here."* → `errors` là oracle.

## Quan sát dẫn tới primitive

| Thử | Kết quả | Kết luận |
| --- | --- | --- |
| `slug=aa;id` | file `aa;id.png` được tạo thật | không có shell, `;` là ký tự thường |
| `slug=aa$(id)` / `` aa`id` `` / `aa\|id` | vẫn là tên file nguyên văn | không shell expansion |
| `slug=x'` và `x" && id && "y` | ffmpeg báo `Unable to find a suitable output format for 'x''` | dấu nháy không phải cơ chế group |
| `slug=x -h` | **`Unrecognized option 'h.png'.` / `Error splitting the argument list`** | slug được **split theo khoảng trắng thành nhiều argv** → argument injection |
| `theme=0x00ff00:s=200x200`, `theme=nope` | render vẫn `ok`, poster không đổi | `theme` không phải vector |

Suy ra: code kiểu `exec`/`spawn` với `("ffmpeg ... " + slug + ".png").split(" ")`. Tên bài (**Splice**) chính là mô tả lỗi: ghép lệnh bằng cách splice chuỗi rồi tách theo space.

## Oracle đọc file

`-f concat -i <đường-dẫn>` làm ffmpeg parse file đích bằng concat demuxer. Dòng đầu không theo cú pháp `file '...'` bị echo ngược vào stderr:

```
[concat @ 0x...] Line 1: unknown keyword 'WEBVERSE{...}'
/flag.txt: Invalid data found when processing input
```

Và server đưa nguyên stderr vào field `errors`. Đọc được file tuỳ ý mà không cần render ảnh hay OCR.

## Kết quả

- `/flag.txt` tồn tại và chứa flag. `/flag`, `/opt/app/flag.txt`, `/app/flag.txt`, `./flag.txt` đều `No such file or directory`.
- Chạy `exploit.py` với session mới hoàn toàn (workspace `0d6a6fc0562fc2eb`, khác workspace probe `b9f13764512c81b7`) cho cùng một chuỗi flag → tái lập được, không phải giá trị rơi ra từ state cũ.

## Nhánh đã loại (giữ lại để không làm lại)

- Path traversal trên tên file output (`../../etc/passwd`): ffmpeg có thật mở đường dẫn tương đối theo cwd, nhưng fail vì `image2` cần pattern `%03d` hoặc `-update`. Chưa cần tới; route `concat` đã đủ.
- Format string / XSS / IDOR workspace: không có tín hiệu, không cần thiết.
