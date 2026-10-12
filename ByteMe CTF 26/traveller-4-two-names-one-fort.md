---
title: "Traveller-4 : Two Names, One Fort"
category: "OSINT"
tags: ["geolocation", "wikipedia", "toponym", "exif-gps"]
solve_date: "2026-10-09"
language: "vi"
---

# Traveller-4 : Two Names, One Fort

**Flag:** `OWASP{vitandgad}`
**Artifact:** `Travellers_dump.zip` (mốc định vị trong EXIF của `img_2.jpg`). Bộ artifact và tọa độ dùng chung cho cả chuỗi được nêu ở mục Phân tích.

## Đề bài

```text
Challenge Description
What is the old name of the fort traveller hiked.
Points 100   Difficulty Medium   Format OWASP{...}
```

Đề hỏi tên cũ của pháo đài mà người du hành đã leo. Tít bài "Two Names, One Fort" chỉ thẳng vào chi tiết cần tìm: cùng một pháo đài có hai tên gọi.

## Phân tích

### Bối cảnh chuỗi bài

Bài thứ tư trong chuỗi Traveller dùng lại đúng một địa điểm mà ba bài đầu đã định vị (ga khởi đầu, trạm dừng, làng chân pháo đài, rồi pháo đài). Chuỗi gắn với nhau bằng bộ artifact giải nén từ `Travellers_dump.zip` và mốc GPS lưu trong EXIF của `img_2.jpg`:

```text
Travellers_dump.zip
  img_1.jpg          3,566,466 B
  img_2.jpg          2,130,878 B
  Traveller Note.txt   1,026 B

img_2.jpg EXIF: 18 deg 37' 55.09" N  73 deg 30' 45.13" E   altitude 762 m
                 direction 261 (ref Magnetic North)  date 2026:10:04 04:02:36Z
```

`img_1.jpg` không có EXIF GPS (các trường kinh/độ vĩ rỗng), nên toàn bộ định vị dựa vào `img_2.jpg`. Tọa độ EXIF trùng với node `Tikona peak` trong OpenStreetMap trong khoảng ~4 m, tức pháo đài của chuỗi là Tikona. Quy ước định dạng cờ đã được học ở Traveller-3 — chấp nhận chữ thường và gạch dưới — nên tên một từ `Vitandgad` ở đây chỉ cần viết thường, không dấu cách:

```text
rejected : OWASP{Tikona Peth}   (Traveller-3, has a space)
accepted : OWASP{tikona_peth}   (Traveller-3, lowercase + underscore)
```

## Lời giải

Đáp án là tên gọi khác của cùng pháo đài Tikona, lấy trực tiếp từ câu mở đầu trang Wikipedia về pháo đài này:

```text
Tikona also known as Vitandgad,  is the dominant hill fort in Maval in western India.
```

Trang `https://en.wikipedia.org/wiki/Tikona` (bản lưu trong hồ sơ làm bài) cho đúng câu đó. Chính tả `Vitandgad` (một từ) được đối chiếu với hai nguồn độc lập khác có trong hồ sơ — "Tikona Fort &#124; Vitandgad Monsoon Special Trek" (maharashtragadkille.com) và "Tikona Fort, also known by the pseudonym Vitandgad" (escape2explore.com) — tất cả đều ghi cùng một dạng. Áp quy ước định dạng học ở Traveller-3, tên viết thường một từ cho cờ:

```text
OWASP{vitandgad}
```

## Kết quả

```text
OWASP{vitandgad}
```

Chưa lưu phản hồi submission cho chính chuỗi này.

## Tái hiện

Phần định vị chạy hoàn toàn trên artifact cục bộ; phần xác minh chính tả tên cần mạng.

```console
$ exiftool img_1.jpg
$ exiftool img_2.jpg
$ for f in img_1.jpg img_2.jpg; do echo "########## $f GPS ##########"; exiftool -GPS* "$f"; done
```

GPS của `img_1.jpg` trả về rỗng; GPS của `img_2.jpg` cho các trường (bản ghi `exiftool -j`, trích các mục liên quan):

```text
GPSVersionID        : 2.2.0.0
GPSLatitudeRef      : North
GPSLongitudeRef     : East
GPSAltitudeRef      : Above Sea Level
GPSDateStamp        : 2026:10:04
GPSTimeStamp        : 04:02:36Z
GPSImgDirectionRef  : Magnetic North
GPSImgDirection     : 261
```

Cặp tọa độ `18°37'55.09"N 73°30'45.13"E` khớp node `Tikona peak` trong OSM trong khoảng ~4 m, nên đối tượng của bài là Tikona. Tên gọi khác cần mạng: đọc câu đầu của `https://en.wikipedia.org/wiki/Tikona` — "Tikona also known as Vitandgad" — rồi đối chiếu một trang lữ hành hoặc escape2explore để chốt chính tả. Kết quả `OWASP{vitandgad}`.
