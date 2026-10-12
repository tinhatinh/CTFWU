---
title: "Traveller-3 : The Road Ends Here"
category: "OSINT"
tags: ["geolocation", "exif", "osm", "flag-format"]
solve_date: "2026-10-09"
language: "vi"
---

# Traveller-3 : The Road Ends Here

**Flag:** `OWASP{tikona_peth}`
**Artifact:** `Travellers_dump.zip` chứa `img_1.jpg` (3,566,466 B), `img_2.jpg` (2,130,878 B), `Traveller Note.txt` (1,026 B).

## Đề bài

Trang challenge (CTF7, tạo 08 Oct 2026, Solves 41) ghi mô tả:

```text
Which village traveller got off the bus.
```

Points 100, Difficulty Medium. Category trên trang để trống; bài geo-OSINT nên phân loại OSINT. Sau khi xuống tàu ở Kamshet (Traveller-2), traveller đi bus tới một làng gần chân pháo đài rồi đi bộ tiếp; bài này hỏi tên làng đó.

## Phân tích

Neo định vị của series là EXIF GPS trên `img_2.jpg`:

```text
GPS Latitude                    : 18 deg 37' 55.09" N
GPS Longitude                   : 73 deg 30' 45.13" E
GPS Altitude                    : 762 m Above Sea Level
GPS Img Direction               : 261
GPS Img Direction Ref           : Magnetic North
GPS Date Stamp                  : 2026:10:04
```

Điểm thập phân `18.631969 / 73.512536` trùng node OSM `natural=peak` "Tikona peak" (id `974330624`, `18.6319782 / 73.5124988`) trong khoảng 4 mét, nên pháo đài là Tikona. Note mô tả chặng cuối bằng lời:

```text
From there we took a bus and got down somewhere near the base. Had to walk another 1–2 km after that.
```

"From there" = ga Kamshet. Bus từ Kamshet hướng về Tikona, xuống ở làng gần chân, rồi đi bộ 1–2 km. Wikipedia *Tikona* chỉ thẳng làng đó: "The village nearest to the fort is called Tikona-Peth" và "The base village of the fort is Tikona peth... the trekking path starts from the hillock south of the parking area near Tikonapeth". "Bãi đỗ xe" là điểm đường bộ dừng lại — đúng nghĩa title "The Road Ends Here", phần còn lại đi bộ.

## Lời giải

Đối chiếu khoảng cách đường bộ (OSRM driving, toạ độ OSM) giữa ga, làng và fort với các con số trong note:

```text
Kamshet (KMST) -> Tikona Fort    ~20.8 km   <- note "Maps showed 20-22 km"
Kamshet        -> Tikona Peth    ~19.5 km
Tikona Peth    -> Tikona Fort    ~1.3 km     <- note "walk another 1-2 km"
Tikona Fort    -> Pavana Lake    ~4 km thang / ~18.8 km duong  <- note "stopped beside a lake"
```

POI "Tikona Fort" nằm tại `18.6319 / 73.5126`, trùng điểm GPS EXIF của `img_2.jpg` (đỉnh Tikona). Node OSM/Photon "Tikona Peth" cách POI đó khoảng 1,3 km — khớp đúng "đi bộ 1–2 km" sau khi xuống bus. Tìm làng quanh chân fort qua Overpass (`node["place"~"village|hamlet|locality"](around:7000,18.63198,73.51250)`) không cho làng nào khác vừa là base village, vừa cách fort 1–2 km, vừa có bus từ Kamshet.

Địa danh chốt là **Tikona Peth**. Vấn đề còn lại chỉ là định dạng chuỗi trong `OWASP{...}`. Sau khi dạng Title Case bị từ chối (xem mục dưới), quy ước chấp nhận được xác lập là **chữ thường, dấu cách thay bằng `_`**:

```text
OWASP{tikona_peth}
```

## Kết quả

```text
OWASP{tikona_peth}
```

Làng xuống bus là Tikona Peth (base village của pháo đài Tikona, cách đỉnh ~1,3 km theo OSM/OSRM). Bản ghi lưu rõ hai lần nộp: `OWASP{Tikona Peth}` bị từ chối, sau đó `OWASP{tikona_peth}` được báo đúng — nên quy ước chấp nhận ở đây (chữ thường, `_` thay khoảng trắng) có bằng chứng trực tiếp từ lần nộp, khác với Traveller-1/2.

## Tái hiện

Cần `exiftool` và Python 3 stdlib; các bước reverse-geocode, Overpass, Wikipedia và OSRM **đều cần mạng**.

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

Xác nhận đỉnh Tikona (mạng):

```console
$ curl -s "https://photon.komoot.io/reverse?lat=18.631969&lon=73.512536"
```

Node `natural=peak` "Tikona peak" `18.6319782 / 73.5124988` (id `974330624`). Độ lệch ~4 m kiểm offline:

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

Tìm làng quanh chân fort (mạng; mirror overpass-api.de trả 406, mirror kumi.systems trả kết quả):

```console
$ curl -s "https://overpass.kumi.systems/api/interpreter" --data-urlencode "data=[out:json][timeout:30];node[place~\"village|hamlet|locality\"](around:7000,18.63198,73.51250);out;"
```

Xác nhận base village (mạng):

```console
$ curl -s "https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext&titles=Tikona&format=json"
```

Đoạn trích có "The village nearest to the fort is called Tikona-Peth". Các khoảng cách trong dữ liệu gây nhiễung Lời giải (Kamshet→Fort ~20.8 km, Tikona Peth→Fort ~1.3 km) lấy từ OSRM driving trên cùng bộ toạ độ OSM; chúng là số đo ghi nhận trong quá trình giải, đối chiếu với dải "20–22 km" và "1–2 km" của note.
