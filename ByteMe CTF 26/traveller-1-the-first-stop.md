---
title: "Traveller-1 : The First Stop"
category: "OSINT"
tags: ["geolocation", "exif", "osm", "railway"]
solve_date: "2026-10-09"
language: "vi"
---

# Traveller-1 : The First Stop

**Flag:** `OWASP{Akurdi}`
**Artifact:** `Travellers_dump.zip` chứa `img_1.jpg` (3,566,466 B), `img_2.jpg` (2,130,878 B), `Traveller Note.txt` (1,026 B).

## Đề bài

Trang challenge trên nền tảng (CTF7, tạo ngày 08 Oct 2026, Solves 43) ghi mô tả:

```text
Determine the railway station from which the traveller started.
```

Points 75, Difficulty Easy. Trường Category trên trang để trống; bài thuộc nhóm geo-OSINT nên phân loại là OSINT trong bài này. Ba bài Traveller-1/2/3 dùng chung một bộ artifact và một hành trình; bài này hỏi ga khởi đầu.

## Phân tích

Toàn bộ series xoay quanh một neo định vị: `img_2.jpg` mang EXIF GPS còn `img_1.jpg` thì không. Dòng GPS đọc được từ ảnh:

```text
GPS Latitude                    : 18 deg 37' 55.09" N
GPS Longitude                   : 73 deg 30' 45.13" E
GPS Altitude                    : 762 m Above Sea Level
GPS Img Direction               : 261
GPS Img Direction Ref           : Magnetic North
GPS Date Stamp                  : 2026:10:04
```

Đổi ra thập phân: `18 + 37/60 + 55.09/3600 = 18.631969`, `73 + 30/60 + 45.13/3600 = 73.512536`. Reverse-geocode toạ độ này trả về đúng node OSM `natural=peak` "Tikona peak" (id `974330624`, `18.6319782 / 73.5124988`), lệch điểm GPS khoảng 4 mét. Nghĩa là bức ảnh được chụp từ đỉnh pháo đài Tikona, và đó là neo khiến cả series suy luận được.

`Traveller Note.txt` mô tả hành trình bằng lời:

```text
I live in Nigdi, Pradhikaran, so I walked to the station and took a local from there.

After 6 stops our destination was on the 7th station.

Got off there. The fort wasn't exactly near the station — Maps showed something around 20–22 km away.

The fort was around 3,500 ft high. It looked almost like a pyramid from a distance.
```

Hai chi tiết khớp với Tikona: Wikipedia *Tikona* ghi "The 3500 foot high hill is pyramidal in shape" và "located near Kamshet". Pháo đài 3.500 ft hình kim tự tháp, có hồ nước trên đường về (Pawna/Pavana), nhìn sang các fort khác (Tung, Lohagad, Visapur) — đúng như note.

Câu hỏi của bài này là **ga khởi đầu**, không phải ga đích. Note nói traveller "sống ở Nigdi, Pradhikaran nên đi bộ ra ga". Ga nội ô của Nigdi Pradhikaran là Akurdi; Wikipedia *Akurdi railway station* mô tả ga nằm ở "Sector-26, Nigdi Pradhikaran, Pune" — chuỗi địa chỉ này trùng đúng nơi ở trong note, nên nó là bằng chứng độc lập xác nhận ga boarding.

## Lời giải

Có hai hướng độc lập cùng trỏ về một ga, và chúng khớp nhau:

1. **Từ nơi ở**: Nigdi Pradhikaran → ga Akurdi (mã AKRD), xác nhận bằng chuỗi "Sector-26, Nigdi Pradhikaran".
2. **Đếm ngược 7 ga**: ga đích (nơi xuống tàu, thuộc Traveller-2) là Kamshet — ga gần Tikona nhất và cách fort khoảng 20 km đường bộ, khớp "Maps showed 20–22 km". Trên tuyến Pune Jn → Lonavala (Pune Suburban Railway), thứ tự ga ghi nhận trong quá trình giải là:

```text
Akurdi -> Dehu Road -> Begdewadi -> Ghorawadi -> Talegaon -> Vadgaon -> Kanhe -> Kamshet
   (1)        2            3            4             5          6         7   <- 6 stops, 7th station
```

Lên tàu ở Akurdi, qua sáu ga trung gian rồi xuống Kamshet. Đây là ga thứ bảy sau khi rời Akurdi; điểm lên tàu không được tính vào bảy điểm dừng. Kết quả cũng khớp nơi ở Nigdi Pradhikaran.

Đáp án của Traveller-1 là ga khởi đầu:

```text
OWASP{Akurdi}
```

Danh sách ga gồm Akurdi, sáu ga trung gian và Kamshet: tám ga nếu tính cả điểm lên tàu. Câu “7th station” được hiểu là ga thứ bảy sau khi rời Akurdi; không phải thứ bảy khi tính Akurdi là ga 1.

## Kết quả

```text
OWASP{Akurdi}
```

Giá trị là dẫn xuất trong quá trình làm của người chơi (nơi ở Nigdi Pradhikaran → ga Akurdi, và đếm lùi 7 ga từ Kamshet), khớp chuỗi địa chỉ "Sector-26, Nigdi Pradhikaran". Không có dòng chấp nhận submission riêng cho bài này trong bản ghi; bài được liệt kê là đã giải trong bảng solved của sự kiện, và đó là nguồn ghi nhận chấp nhận.

## Tái hiện

Cần `exiftool` cho phần GPS và Python 3 stdlib cho phần tính khoảng cách; các bước định vị/tra cứu **cần mạng**.

```console
$ exiftool -GPS* img_2.jpg
$ exiftool -GPS* img_1.jpg
```

Đổi DMS sang thập phân và đối chiếu node OSM "Tikona peak" (mạng):

```console
$ curl -s "https://photon.komoot.io/reverse?lat=18.631969&lon=73.512536"
```

Node `natural=peak` trả về tại `18.6319782 / 73.5124988` (id `974330624`). Kiểm tra độ lệch bằng haversine, chạy offline:

```python
from math import radians, sin, cos, asin, sqrt
def hav(a, b, c, d):
    a, b, c, d = map(radians, (a, b, c, d))
    return 2 * 6371000 * asin(sqrt(sin((c-a)/2)**2 + cos(a)*cos(c)*sin((d-b)/2)**2))
print(round(hav(18.631969, 73.512536, 18.6319782, 73.5124988), 1), "m")
```

```text
4.1 m
```

Tra Wikipedia xác nhận ga khởi đầu (mạng):

```console
$ curl -s "https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext&exintro&titles=Akurdi%20railway%20station&format=json"
```

Đoạn trích có "Sector-26, Nigdi Pradhikaran". Thứ tự ga Pune Jn → Lonavala và việc tuyến này có local train dừng ở Kamshet lấy từ Wikipedia *Kamshet railway station*; bảng đếm ga ở mục Lời giải là dữ liệu ghi nhận trong quá trình giải.
