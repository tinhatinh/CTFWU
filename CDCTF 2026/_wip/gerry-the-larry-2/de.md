# Đề bài - gerry-the-larry-2

## Nguyên văn đề

```text
Gerry the Larry (2/2)
500
Web Exploitation
reep236, adlee7

Now that you know the political scape of Cat County, help the legitimate hier to the throne of Chief
Mouser - Larry, of the Domestic Loafs - take the throne! It's perfect timing, since Cat County is
implementing a new district system.

If you can use that to help Larry win the election, he might just provide you a purrrfect little flag,
in the format of cdctf{Fl4gGo3sH3re!}

Disclaimer: CDCTF and any of its parent organizations do NOT endorse hacktivism. This is a fictional
scenario created for illustrative purposes, always obey laws and regulations regarding computer use.

Your instance is running

https://njpwkhrj.i.cdctf.net
```

## Metadata đã xác minh

- Không có file đính kèm. Artifact là web app trên instance.
- `index.html` 1.698 B; asset: `/assets/index.501b4b7d.js` (152.592 B, PureScript→JS),
  `/assets/index.63d2b32b.css` (4.883 B); ảnh `img/{Larry,Garry,Harry,Sherry}.jpg` → **4 ứng viên**.
- Backend là **FastAPI** (lỗi 422 đúng định dạng pydantic `{"detail":[{"type":..,"loc":[..],..}]}`),
  chạy sau nginx/1.31.6 + Cloudflare. `/openapi.json`, `/docs`, `/redoc` đều 404 → không có schema công khai.
- Endpoint duy nhất tìm thấy trong bundle: `POST /vote`, body JSON, response `{result, flag}`.
- Danh sách 36 block trong `info.csv` của bài 1/2 trùng đúng danh sách precinct mà client bài này dựng
  (bảng 6×6, ví dụ `Tuna Terrace`, `Whisker Row`, `Biscuit Bend`) → hai bài dùng chung bản đồ.
- **Trạng thái:** đang mở, chưa có cờ. Những gì bên dưới là các sự kiện đã đo được.
