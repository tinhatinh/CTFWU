---
title: "Traveller-6 : Across the Water"
category: "OSINT"
tags: ["dem-skyline", "lake-constraint", "exif-gps", "osm-water"]
solve_date: "2026-10-09"
language: "vi"
---

# Traveller-6 : Across the Water

**Flag:** `OWASP{tung_pawna}`
**Artifact:** ảnh "quay xuống" (return photograph) đính kèm trên nền tảng, chụp từ cùng vị trí đã định vị ở các bài trước (mốc EXIF của `img_2.jpg`). Bộ artifact và tọa độ dùng chung cho cả chuỗi được nêu ở mục Phân tích.

## Đề bài

```text
Challenge Description
Identify the fort across the water and the lake in the return photograph.
Points 150   Difficulty Medium   Format OWASP{FORT_LAKE}
```

"Solves (26)". Cờ gồm hai vế: một pháo đài và một hồ, với ràng buộc pháo đài phải nằm ở bên kia mặt nước.

## Phân tích

### Bối cảnh chuỗi bài

Bài thứ sáu vẫn đứng ở cùng vị trí các bài trước và dùng chung bộ artifact Traveller:

```text
Travellers_dump.zip
  img_1.jpg          3,566,466 B
  img_2.jpg          2,130,878 B
  Traveller Note.txt   1,026 B

img_2.jpg EXIF: 18 deg 37' 55.09" N  73 deg 30' 45.13" E   altitude 762 m
                 direction 261 (ref Magnetic North)  date 2026:10:04 04:02:36Z
```

Tọa độ EXIF trùng node `Tikona peak` trong OpenStreetMap trong khoảng ~4 m, nên vị trí quan sát là Tikona. Vì định dạng là `FORT_LAKE`, một mặt nước phải được chỉ ra cùng pháo đài, và ràng buộc "across the water" loại mọi ghép cặp mà pháo đài vẫn là chính điểm đặt máy.

### Ràng buộc mặt nước

Hai lần nộp đầu giữ lại pháo đài quan sát Tikona và đều bị từ chối (hồ sơ ghi nhận cả `OWASP{tikona_pavana}` và `OWASP{tikona_pawna}` là sai). Vấn đề không nằm ở hồ mà ở chỗ vế pháo đài phải là một đỉnh khác, nhìn từ phía bên kia mặt nước. Vì nền tảng dùng chữ thường nối bằng `_` (bài Traveller-3 đã loại `OWASP{Tikona Peth}` và chấp nhận `OWASP{tikona_peth}`), cờ đúng phải có dạng `fort_lake`.

## Lời giải

Chạy lại so khớp đường chân trời từ DEM với ràng buộc đỉnh mục tiêu nằm ở bờ bên kia mặt nước. Hai hồ được đưa ra đánh giá là Mulshi và Pawna (các mảng `lake_MULSHI.npy`, `lake_PAWNA.npy` và `lake_mask.npy` lưu trong hồ sơ). Cặp thỏa ràng buộc là hồ Pawna và pháo đài trên đỉnh ở bờ đối diện, Tung (dữ liệu gây nhiễun ghi `cands.json`, mỗi dòng `[tên, loại OSM, lat, lon, cao độ m, giá trị ghi nhận]`):

```text
["Tung", "other", 18.6598, 73.4616, 972, 0.55]
["Pawna", "district", 18.6975, 73.495, 774, null]
```

Ghép fort + lake theo định dạng `FORT_LAKE`, viết thường và nối bằng `_`, cho cờ:

```text
OWASP{tung_pawna}
```

## Kết quả

```text
OWASP{tung_pawna}
```

Cờ được nền tảng chấp nhận; hồ sơ làm bài lưu dòng báo chấp nhận cho đúng chuỗi này, sau hai lần nộp `tikona_pavana` và `tikona_pawna` bị từ chối.

## Tái hiện

Định vị và dựng đường chân trời cần mạng ở hai bước: tải tile độ cao Terrarium và gọi Overpass; phần khớp DEM và dựng mặt nạ hồ chạy cục bộ bằng numpy. exiftool đọc mốc từ artifact:

```console
$ exiftool -GPS* img_2.jpg
$ curl -s --data-urlencode data@q1.txt https://overpass.kumi.systems/api/interpreter
```

Các trường EXIF liên quan (`exiftool -j`, trích các mục liên quan):

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

Truy vấn `q1.txt` liệt kê cả `natural=peak` lẫn `natural=water`/`waterway=dam` quanh vị trí quan sát; DEM lưu ở `dem.npy` (metadata zoom 11, raster 2304×2304 pixel resample `N=2048`), đường chân trời và phép chiếu phân cực ở `horizon_*.npy`/`polar.npz`, mặt nạ hồ ở `lake_mask.npy` và `lake_MULSHI.npy`/`lake_PAWNA.npy`, danh sách ứng viên ở `cands.json`. So khớp dưới ràng buộc "pháo đài ở bên kia mặt nước" chọn cặp Tung (fort) + Pawna (lake). Kết quả `OWASP{tung_pawna}`.

Bài chưa kèm mã tạo DEM, trích skyline và so khớp. Metadata cùng kết quả đã lưu chưa đủ để tái hiện bước so khớp ảnh tự động. Hướng EXIF dùng magnetic north, cần hiệu chỉnh nếu so với phương vị true north của DEM.
