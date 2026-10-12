---
title: "Traveller-2 : Seven Stops"
category: "OSINT"
tags: ["geolocation", "exif", "osm", "railway"]
solve_date: "2026-10-09"
language: "vi"
---

# Traveller-2 : Seven Stops

**Flag:** `OWASP{Kamshet}`
**Artifact:** `Travellers_dump.zip` chứa `img_1.jpg` (3,566,466 B), `img_2.jpg` (2,130,878 B), `Traveller Note.txt` (1,026 B).

## Đề bài

Trang challenge (CTF7, tạo 08 Oct 2026, Solves 44) ghi mô tả:

```text
Which station traveller got off the train.
```

Points 75, Difficulty Easy. Category trên trang để trống; đây là bài geo-OSINT nên phân loại OSINT. Bài này hỏi ga **xuống tàu** — tức ga thứ 7 trong chuỗi "After 6 stops our destination was on the 7th station", đầu bên kia của hành trình so với Traveller-1.

## Phân tích

Neo định vị của cả series nằm ở `img_2.jpg`: EXIF GPS của nó là

```text
GPS Latitude                    : 18 deg 37' 55.09" N
GPS Longitude                   : 73 deg 30' 45.13" E
GPS Altitude                    : 762 m Above Sea Level
GPS Img Direction               : 261
GPS Img Direction Ref           : Magnetic North
GPS Date Stamp                  : 2026:10:04
```

Toạ độ thập phân `18.631969 / 73.512536` trùng node OSM `natural=peak` "Tikona peak" (id `974330624`, `18.6319782 / 73.5124988`) trong khoảng 4 mét. Vậy pháo đài trong note là Tikona, và ga gần Tikona nhất trên tuyến có local train dừng là Kamshet — điều này biến Kamshet thành ứng viên "ga thứ 7".

Note cung cấp hai cách kiểm chứng cho cùng một ga:

```text
I live in Nigdi, Pradhikaran, so I walked to the station and took a local from there.

After 6 stops our destination was on the 7th station.

Got off there. The fort wasn't exactly near the station — Maps showed something around 20–22 km away.
```

- **Khoảng cách ga→fort**: Kamshet → Tikona khoảng 20 km đường bộ, nằm trong dải "20–22 km" của note. Wikipedia *Tikona* cũng ghi fort "located near Kamshet".
- **Đếm ga**: boarding ở Akurdi (Traveller-1), qua sáu ga trung gian rồi xuống ở ga thứ bảy sau điểm khởi đầu.

## Lời giải

Thứ tự ga trên tuyến Pune Jn → Lonavala (Pune Suburban Railway) ghi nhận trong quá trình giải, đếm từ ga khởi đầu Akurdi:

```text
Akurdi -> Dehu Road -> Begdewadi -> Ghorawadi -> Talegaon -> Vadgaon -> Kanhe -> Kamshet
   (1)        2            3            4             5          6         7   <- 6 stops, 7th station
```

Lên tàu ở Akurdi, qua 6 ga (Dehu Road, Begdewadi, Ghorawadi, Talegaon, Vadgaon, Kanhe), xuống tại ga tiếp theo = Kamshet. Con số này khớp cả hai ràng buộc: đúng "7th station" và Kamshet cách fort Tikona ~20 km như note.

Wikipedia *Kamshet railway station* xác nhận tuyến có local train Pune Jn–Lonavala dừng ở đây, khớp chi tiết "took a local". Ga xuống tàu là:

```text
OWASP{Kamshet}
```

Danh sách ga gồm Akurdi, sáu ga trung gian và Kamshet: tám ga nếu tính cả điểm lên tàu. Câu “7th station” được hiểu là ga thứ bảy sau khi rời Akurdi; không phải thứ bảy khi tính Akurdi là ga 1.

## Kết quả

```text
OWASP{Kamshet}
```

Giá trị là dẫn xuất trong quá trình làm của người chơi: ga thứ 7 khi đếm từ Akurdi trên tuyến Pune Jn → Lonavala, đồng thời là ga gần đỉnh Tikona (neo EXIF) với khoảng cách khớp "20–22 km". Không có dòng chấp nhận submission riêng cho bài này trong bản ghi; bài được liệt kê là đã giải trong bảng solved của sự kiện, và đó là nguồn ghi nhận chấp nhận.

## Tái hiện

Cần `exiftool` và Python 3 stdlib; các bước định vị/tra cứu **cần mạng**.

```console
$ exiftool -GPS* img_2.jpg
```

```text
GPS Latitude                    : 18 deg 37' 55.09" N
GPS Longitude                   : 73 deg 30' 45.13" E
GPS Altitude                    : 762 m Above Sea Level
GPS Img Direction               : 261
GPS Img Direction Ref           : Magnetic North
GPS Date Stamp                  : 2026:10:04
```

Xác nhận đỉnh Tikona bằng reverse-geocode (mạng):

```console
$ curl -s "https://photon.komoot.io/reverse?lat=18.631969&lon=73.512536"
```

Node `natural=peak` "Tikona peak" tại `18.6319782 / 73.5124988` (id `974330624`). Độ lệch ~4 m kiểm bằng haversine, chạy offline:

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

Kiểm chứng ga Kamshet và tuyến dừng local train (mạng):

```console
$ curl -s "https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext&exintro&titles=Kamshet%20railway%20station&format=json"
```

Thứ tự ga Pune Jn → Lonavala trong bảng đếm ga ở mục Lời giải là dữ liệu ghi nhận trong quá trình giải, đối chiếu với vị trí các ga trên cùng tuyến.
