# Đề bài - Where the Light Fails to Fall

Chưa có ảnh thẻ đề. Mô tả chép từ text của thẻ và từ trang challenge đang mở.

## Nguyên văn đề

```text
OSINT 400 · Wave 1
Where the Light Fails to Fall

This summer I had an opportunity to go travelling. I took my pet pigeon, Sir Marcus
Skuttlebanks, as well. I was sure to get a picture of him in literally every major city
we visited. Can YOU determine which city I was in based only on the clues I've given you?

How am I supposed to know? Give it a try!

[ảnh: caption] The red line marks true north.

TIME OF OBSERVATION (YOUR TEAM)
2026-06-20 · 19:55 · UTC+02:00

NOTES            (khối này rỗng trên trang của team mình)
YOUR ANSWER (CITY NAME)   [ input#city-input ]  Submit city
SUBMIT FLAG               [ input#flag-input ]  Submit flag
```

## Thông tin đã xác minh từ file và trang

| Mục | Giá trị |
| --- | --- |
| Artifact hiển thị | `GET /challenges/where-light-falls/photo`, cần cookie phiên (curl không cookie nhận 401) |
| File gốc server trả về | `files/PXL_20260621_181159681.jpg`, 3.940.516 B, `content-type: image/jpeg` |
| SHA-256 ảnh gốc | `42b362b6872685571c84bbd96651794c6dd5aa582d55778ca8673f03e520a14a` |
| Bản PNG đã phân tích | `files/photo.png`, 20.518.520 B, 3000x4000, SHA-256 `2a25a57663a8a3b9f7c47b749452b1608bc312ef310bebf3b86ebbcf5ea40339` |
| Quan hệ PNG và JPEG | giải mã ra pixel giống hệt (mean abs diff = 0.0), cả hai đều đã chứa nét đỏ |
| `content-disposition` | `inline; filename=PXL_20260621_181159681.jpg`, lộ tên file gốc kiểu Google Pixel |
| Metadata ảnh gốc | chỉ còn JFIF, XMP container + HDR gainmap, ICC sRGB của Google, MPF. Không ExifIFD, không GPSInfo, không DateTimeOriginal |
| Cấu trúc JPEG | một EOI duy nhất ở cuối file, 0 byte sau EOI, không có dữ liệu nối thêm |
| Thuộc tính `alt` của ảnh | "A photograph, taken looking down at a bird on grey paving stones. A red N indicates true north. Shadows extend from the bird and other small objects." |
| Nét đỏ true north | đi qua (544, 3103) tới (2386, 3864), hướng đơn vị y-up `(-0.92429, +0.38169)`, góc 157,561° |
| Endpoint thành phố | `POST /challenges/where-light-falls/answer` body `{"city": "..."}` → `{correct, message, flag?}` |
| Endpoint cờ | `POST /challenges/where-light-falls/submit` body `{"flag": "..."}` → `{correct, message}` |
| Hành vi endpoint | so khớp chuỗi chính xác, không phân biệt tên lạ và tên sai; chuỗi rỗng trả 400 `Enter a city name.`; `{"city":true}` trả 500 vì server gọi `.strip()` |
| Cờ | server chỉ trả trong field `flag` khi nộp đúng tên thành phố, và tự đổ vào `#flag-input` |
| Định dạng cờ | `POCTF{<cid>.<team_id>.<nonce>.<sig26>}`, bài này cid 99, team 612 |

## Hướng giải (tóm tắt)

Đo mặt trời từ ảnh không đi tới đáp án: bóng chỉ dài 1,3-1,45 lần chiều cao con chim nên ảnh
này ứng với mặt trời cao 30-50°, trái ngược với "19:55 giờ địa phương ngày hạ chí" ở mọi thành
phố châu Âu, và phối cảnh của ảnh không hiệu chuẩn được vì mặt lát đá không phải lưới vuông đều.
Chi tiết các nhánh đã loại nằm ở `notes.md`. Đường thực dụng là lợi dụng việc endpoint chỉ so
chuỗi: liệt kê tên thành phố theo dân số rồi nộp có kiểm soát tốc độ, và dừng ngay khi `correct`
là `true`. Amsterdam là tên thứ 480 trong danh sách.

## Chạy lại

```bash
python exploit.py            # in đoạn JS worker để chạy trong tab đang đăng nhập, kèm danh sách cần nạp
```

Xem `writeup.md` để biết trình tự và cách xác nhận cờ.
