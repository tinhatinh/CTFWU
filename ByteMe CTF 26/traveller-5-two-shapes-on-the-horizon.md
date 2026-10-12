---
title: "Traveller-5 : Two Shapes on the Horizon"
category: "OSINT"
tags: ["dem-skyline", "terrarium-tiles", "exif-gps-bearing", "peak-identification"]
solve_date: "2026-10-09"
language: "vi"
---

# Traveller-5 : Two Shapes on the Horizon

**Flag:** `OWASP{lohagad_visapur}`
**Artifact:** ảnh đính kèm trên nền tảng, chụp từ cùng vị trí đã định vị ở các bài trước (mốc EXIF của `img_2.jpg`). Bộ artifact và tọa độ dùng chung cho cả chuỗi được nêu ở mục Phân tích.

## Đề bài

```text
Challenge Description
What are those in the picture.
Points 150   Difficulty Hard   Format OWASP{FORT1_FORT2}
```

"Solves (32)". Bức ảnh cho thấy hai khối núi trên đường chân trời. Định dạng cờ `FORT1_FORT2` yêu cầu hai tên, nên cần chỉ ra đúng hai pháo đài và đúng thứ tự của chúng.

## Phân tích

### Bối cảnh chuỗi bài

Bài thứ năm vẫn đứng ở cùng vị trí mà các bài đầu đã định vị. Chuỗi Traveller gắn với nhau bằng bộ artifact giải nén từ `Travellers_dump.zip` và mốc GPS trong EXIF của `img_2.jpg`:

```text
Travellers_dump.zip
  img_1.jpg          3,566,466 B
  img_2.jpg          2,130,878 B
  Traveller Note.txt   1,026 B

img_2.jpg EXIF: 18 deg 37' 55.09" N  73 deg 30' 45.13" E   altitude 762 m
                 direction 261 (ref Magnetic North)  date 2026:10:04 04:02:36Z
```

Tọa độ EXIF trùng node `Tikona peak` trong OpenStreetMap trong khoảng ~4 m, nên vị trí quan sát là Tikona. Trường `GPSImgDirection` (=261, ref Magnetic North) cho hướng mà ống kính đang quay, dùng để định hướng việc dựng đường chân trời.

### Bài toán

Từ một vị trí đã biết, "hai khối trên đường chân trời" là hai đỉnh mà hình chiếu biên độ của chúng ăn khớp với đường viền trong ảnh. Cách làm được ghi nhận trong hồ sơ là so khớp đường chân trời dựng từ DEM (tile độ cao Terrarium) với profile lấy từ ảnh, theo hướng đọc từ EXIF, để xem cặp đỉnh nào tái tạo đúng hai khối đó.

## Lời giải

### Dựng đường chân trời từ DEM

DEM khu vực được ghép từ tile độ cao Terrarium, lưu thành `dem.npy` kèm metadata:

```json
{"Z": 11, "X0": 1438, "Y0": 912, "W": 2304, "H": 2304, "N": 2048}
```

Metadata ghi zoom 11, tile góc trái trên `(1438,912)`, vùng raster `2304×2304` và `N=2048`. Các trường `W/H` mô tả kích thước raster, không phải 2304×2304 tile. Profile ảnh và DEM được lưu riêng để so khớp.

Định vị và liệt kê các đỉnh/vùng nước quanh vị trí quan sát dựa vào truy vấn Overpass (bản lưu `q1.txt`):

```text
[out:json][timeout:30];
(
  node["place"~"village|hamlet|locality"](around:7000,18.63198,73.51250);
  way["place"~"village|hamlet"](around:7000,18.63198,73.51250);
  node["historic"](around:9000,18.63198,73.51250);
  way["historic"]["name"](around:9000,18.63198,73.51250);
  node["natural"="peak"](around:9000,18.63198,73.51250);
  node["waterway"="dam" ](around:9000,18.63198,73.51250);
  way["natural"="water"]["name"](around:9000,18.63198,73.51250);
);
out center tags;
```

### Cặp đỉnh khớp silhouette

Hồ sơ so khớp cho ra cặp Lohagad và Visapur (bản ghi `cands.json`, mỗi dòng là `[tên, loại OSM, lat, lon, cao độ m, giá trị ghi nhận]`):

```text
["Lohagad", "district", 18.7206, 73.4915, 1051, 1.15]
["Visapur", "other", 18.7218, 73.4928, 1070, 1.25]
```

Hai đỉnh nằm sát nhau về phương vị nên hiện lên thành hai khối nối tiếp trên cùng một phía của đường chân trời. Thứ tự chấp nhận là Lohagad rồi Visapur, khớp chi tiết ghi nhận rằng note "đánh dấu chúng là 1 và 2" theo trái sang phải. Vì nền tảng dùng chữ thường nối bằng `_` (bài Traveller-3 đã loại `OWASP{Tikona Peth}` và chấp nhận `OWASP{tikona_peth}`), cờ là `OWASP{lohagad_visapur}`.

## Kết quả

```text
OWASP{lohagad_visapur}
```

Cờ được nền tảng chấp nhận; hồ sơ làm bài lưu dòng báo chấp nhận cho đúng chuỗi này.

## Tái hiện

Định vị và dựng đường chân trời cần mạng ở hai bước: tải tile độ cao Terrarium và gọi Overpass; phần khớp DEM và ảnh chạy cục bộ bằng numpy. exiftool đọc mốc từ artifact:

```console
$ exiftool -GPS* img_2.jpg
$ curl -s --data-urlencode data@q1.txt https://overpass.kumi.systems/api/interpreter
```

Trường định hướng dùng để xoay đường chân trời (`exiftool -j`, trích các mục liên quan):

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

DEM lưu thành `dem.npy` (metadata `dem_meta.json` ở trên); đường viền và phép chiếu phân cực lưu ở `horizon_*.npy` và `polar.npz`; danh sách đỉnh/vùng nước ứng viên ở `cands.json`. So profile đường chân trời của ảnh với đường chân trời dựng từ DEM theo hướng 261° để chốt cặp Lohagad–Visapur, thứ tự trái→phải. Kết quả `OWASP{lohagad_visapur}`.

Bài chưa kèm mã tạo DEM, trích skyline và so khớp. Metadata cùng kết quả đã lưu chưa đủ để tái hiện bước so khớp ảnh tự động. Hướng EXIF dùng magnetic north, cần hiệu chỉnh nếu so với phương vị true north của DEM.
