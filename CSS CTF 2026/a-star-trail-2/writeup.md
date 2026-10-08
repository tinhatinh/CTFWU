# A Star Trail 2 - Misc/Graph (Intermediate)

**Flag:** `CSSCTF{STARmaPdElAUNaYTriaNGulATioNDIjKStrAVoRonoiGrAPHSdetERmiNaNTcolineaRALGOrITHmSLeEandsCHAcHTERTANgEnTSmErGECirCuMcIrcLEcOnVEXhuLLgeOMeTRy}`
**File đính kèm:** `map.zip` (Kích thước: 2.663.657 B, SHA256: `31c44f1b...a97525f9`)

## Đề bài

Đề cung cấp một cơ sở dữ liệu gồm 10.000 file định dạng Markdown đại diện cho một bản đồ thiên hà. Mỗi file tương ứng với một hành tinh, chứa các thông tin bao gồm: ID, tọa độ, và danh sách các hành tinh lân cận được trình bày dưới định dạng thẻ liên kết wiki (`[[wikilink]]`). Mục tiêu là tìm một lộ trình từ hành tinh `S0jRxc` đến hành tinh `yRJyDb` "trong khoảng thời gian hợp lý".
Quy tắc ghép cờ: Bắt đầu bằng việc lấy chữ cái thứ nhất của điểm dừng đầu tiên, chữ cái thứ hai của điểm dừng thứ hai, tiếp tục tịnh tiến và quay vòng lại (modulo) thành chữ cái thứ nhất ở các điểm dừng thứ 7, 13, 19, v.v. Quá trình ghép này có phân biệt chữ hoa và chữ thường.

## Phân tích

Quét toàn bộ 10.000 file, dữ liệu chỉ hiển thị chính xác ba loại trường thông tin:

```python
Counter({'wikilink': 59944, 'title': 10000, 'coords': 10000})
```
Các file không có trường số ngày hoặc tốc độ. Dùng khoảng cách giữa các tọa độ làm trọng số cạnh. Script kiểm tra 59.944 cạnh có hướng, tương ứng 29.972 cạnh vô hướng, không có cạnh lệch chiều hoặc link tới ID không tồn tại. Bậc trung bình của đỉnh khoảng 5.99.

## Lời giải

**Bước 1 - Xây dựng đồ thị trực tiếp từ file nén.**
Không cần giải nén thủ công, Python script sử dụng thư viện `zipfile` để đọc tuần tự từng file `map/<ID>.md`, từ đó trích xuất các trường tọa độ và danh sách hành tinh lân cận để hình thành đồ thị.

**Bước 2 - Áp dụng thuật toán Dijkstra với trọng số khoảng cách Euclid.**
Sử dụng công thức khoảng cách Euclid giữa hai tọa độ làm trọng số cho các cạnh, sau đó áp dụng thuật toán Dijkstra:

```text
Kết quả: 135 chặng, tổng quãng đường 144.9333, số đường tối ưu = 1
Khoảng cách đường thẳng nối hai điểm đầu cuối là 138.6231 -> Lộ trình tối ưu dài hơn 4.55%
```
Đếm đường đi ngắn nhất bằng dynamic programming trên kết quả Dijkstra cho đúng một đường đi tối ưu theo trọng số đã chọn.

BFS cho đường đi 13 chặng với tổng khoảng cách 199.95; Dijkstra theo khoảng cách tọa độ cho tổng 144.93. Hai tiêu chí cho kết quả khác nhau. Đường Dijkstra được kiểm tra tiếp bằng thông điệp ghép từ các ID ở bước sau.

**Bước 4 - Xác thực thông qua thông điệp ẩn.**
Áp dụng quy tắc ghép chữ cái `id[i % 6]` (bao gồm cả hai đỉnh đầu và cuối là `S0jRxc` và `yRJyDb`), hệ thống thu được chuỗi kết quả dài 136 ký tự. Khi đọc chuỗi này, nội dung hình thành một thông điệp có ngữ nghĩa rõ ràng:

```text
STAR MAP · DELAUNAY TRIANGULATION · DIJKSTRA VORONOI · GRAPHS · DETERMINANT · COLINEAR · ALGORITHMS · … TANGENTS · MERGE · CIRCUMCIRCLE · CONVEX HULL · GEOMETRY
```

Nếu lựa chọn sai lộ trình, kết quả sẽ là một chuỗi ký tự ngẫu nhiên không mang ý nghĩa (nhiễu). Việc chuỗi ký tự hình thành một danh sách các thuật toán hình học tính toán là bằng chứng xác thực mạnh mẽ nhất cho thấy lộ trình Dijkstra theo tọa độ chính là thiết kế dự kiến của tác giả.

Ví dụ của đề (ASTART, BCDEFG, hijklm, NOPQRS, tuvwxy, ZFINAL → `ACjQxL`) được dùng làm unit test cho quy tắc `id[i % 6]` trong `exploit.py`. Phép thử lấy chữ đầu của mọi ID không khớp ví dụ này.

## Kết quả

Chạy script:

```bash
$ python exploit.py files/map.zip
1) do thi: 10000 nut, 59944 canh chieu, 29972 canh vo huong
2) Dijkstra theo toa do: 135 chan, tong quang duong 144.9333, so duong toi uu = 1
3) duong thang lien nut dau-cuoi = 138.6231 -> lo trinh 4.55% dai hon
4) ca 135 canh deu la wikilink that trong map
5) cach hieu 'it chan nhat': 13 chan nhung dai 199.9478 (ngan nhat la 144.9333) -> khong trung
6) duong di (136 nut):
   S0jRxc -> 1T5eN4 -> hmANsv -> XGnRvX -> CZqgmf -> HFtEqa -> PNHmEq -> zdQEDJ -> PqE5LH -> 7GwlrF ->
   s4clAO -> BZBIfU -> Nr4nCb -> caVoaa -> iQYvOf -> PzNTZG -> 1M0urD -> QMPisi -> amu7Wo -> iNCLPy ->
   QpG6f5 -> MR8uJc -> Bj68lj -> HETuLA -> TrGMSs -> JiPYRV -> PpowW7 -> tVsNxK -> 9luvD5 -> BwCBhI ->
   jctq4E -> BK2t5a -> aMS8lF -> 0y8tTE -> Nnb8rI -> gpo1OA -> VIJCJC -> ootqYn -> YGRffF -> oqWomB ->
   gBq3nj -> 9RXg8o -> idn8MR -> 3Ge1Ze -> wDrRGY -> KgxAJF -> Au7JPZ -> sfamMH -> SZeex7 -> 5dB0SL ->
   YHeChf -> AoHtOq -> h8A8Eq -> DcGFsR -> mNypTS -> nikTvk -> QsNinN -> fJSa8c -> UI6ZN7 -> LMdJ5T ->
   cnUGJr -> So0gII -> f9ltmH -> 7Ckib9 -> 96O7nm -> GwZvTe -> aULZyG -> dRrW9E -> AcA4vb -> KQ5LGq ->
   nyeoGv -> K77Q2O -> rM0kaj -> nI3TNd -> JoT8Lw -> 4eMHte -> iOvkmn -> YNz5nS -> LZgaSg -> BepSSx ->
   aXE4nS -> 77Nab2 -> qGHln3 -> hf47ld -> sAFynQ -> lChcQn -> 8fHQzd -> XXpAa6 -> oOyVcu -> FzP1DH ->
   TMtjsI -> HEtwSC -> QFRV2e -> LAVTJQ -> Gl2ZAI -> 0QfLJN -> gjKpSu -> PEsjS8 -> r8nrfI -> RGXT2a ->
   exrjS0 -> K3oT0m -> EGoU5L -> Yrggxs -> 25GB9o -> ssqEuY -> UelHC3 -> EISTKi -> rZhn2k -> 5CXPOK ->
   9buFn2 -> Ug9MqQ -> 4cWCct -> DlIidI -> rm6bAP -> wcxQ5o -> p7LRWQ -> qLnEKN -> ZJNscx -> gymzEO ->
   np5olu -> pVWtdw -> sTEnG2 -> Ws6XnB -> Sawmhz -> KXOShu -> LrO3VY -> PLYS2Q -> GWgqRX -> clzegJ ->
   fm4gOr -> ScLSwM -> etckNZ -> KTjmKT -> jvRMt3 -> yRJyDb

FLAG: CSSCTF{STARmaPdElAUNaYTriaNGulATioNDIjKStrAVoRonoiGrAPHSdetERmiNaNTcolineaRALGOrITHmSLeEandsCHAcHTERTANgEnTSmErGECirCuMcIrcLEcOnVEXhuLLgeOMeTRy}
```

Kết quả:
```text
CSSCTF{STARmaPdElAUNaYTriaNGulATioNDIjKStrAVoRonoiGrAPHSdetERmiNaNTcolineaRALGOrITHmSLeEandsCHAcHTERTANgEnTSmErGECirCuMcIrcLEcOnVEXhuLLgeOMeTRy}
```
