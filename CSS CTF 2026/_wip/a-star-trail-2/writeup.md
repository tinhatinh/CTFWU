# A Star Trail 2 — Misc/Graph (Intermediate)

**Flag:** `CSSCTF{STARmaPdElAUNaYTriaNGulATioNDIjKStrAVoRonoiGrAPHSdetERmiNaNTcolineaRALGOrITHmSLeEandsCHAcHTERTANgEnTSmErGECirCuMcIrcLEcOnVEXhuLLgeOMeTRy}` · **Files:** `map.zip` (2663657 B, sha256 `31c44f1b…a97525f9`)

## Đề bài

Bản đồ thiên hà lần này không phải ảnh nữa mà là một database 10000 file Markdown, mỗi file
là một hành tinh: ID, toạ độ, và danh sách láng giềng dạng `[[wikilink]]`. Phải bay từ
`S0jRxc` tới `yRJyDb` "trong thời gian hợp lý". Cờ ghép bằng cách lấy chữ cái thứ nhất của
điểm dừng thứ nhất, chữ thứ hai của điểm dừng thứ hai, ..., quay vòng về chữ thứ nhất ở
điểm dừng thứ 7, 13, 19; phân biệt hoa thường.

## Phân tích ban đầu

Quét hết 10000 file thì mỗi file chỉ có đúng ba loại dòng:

```
Counter({'wikilink': 59944, 'title': 10000, 'coords': 10000})
```

Không có trường số ngày nào như phien 1, nên thứ duy nhất đo được là toạ độ. Đồ thị cũng
sạch: 59944 cạnh chiều gộp lại còn đúng 29972 cạnh vô hướng (liên kết đối xứng tuyệt đối),
không link treo, bậc trung bình 5.99.

## Các hướng đã loại

1. **BFS ít chặng nhất**: ra 13 chặng nhưng tổng quãng đường 199.95, tệ hơn hẳn 144.93 của
   đường theo toạ độ; với bậc ~6 thì 13 chặng cũng không đủ để có một đường duy nhất. Loại.
2. **Dùng trọng số có sẵn**: không tồn tại, đã đếm từng dòng một. Loại.

## Chuỗi khai thác

**Bước 1 - Dựng đồ thị từ zip**, không cần giải nén: đọc từng `map/<ID>.md` bằng `zipfile`,
lấy toạ độ và tập láng giềng.

**Bước 2 - Dijkstra với trọng số là khoảng cách Euclid giữa hai toạ độ.**

```
135 chan, tong quang duong 144.9333, so duong toi uu = 1
duong thang noi hai dau 138.6231 -> lo trinh dai hon 4.55%
```

Đếm số đường tối ưu bằng DP trên cây Dijkstra ra đúng 1, nên không cần đoán thêm.

**Bước 3 - Đối chiếu hai cách hiểu.** Đường ít chặng nhất dài 199.95 trong khi đường ngắn
nhất theo toạ độ dài 144.93; nếu đề muốn đếm chặng thì hai cái đã trùng nhau.

**Bước 4 - Kiểm chứng bằng thông điệp ẩn.** Ghép chữ cái theo luật `id[i % 6]` (tính cả
`S0jRxc` và `yRJyDb`) thì xâu 136 ký tự đọc thành:

```
STAR MAP · DELAUNAY TRIANGULATION · DIJKSTRA VORONOI · GRAPHS · DETERMINANT ·
COLINEAR · ALGORITHMS · … TANGENTS · MERGE · CIRCUMCIRCLE · CONVEX HULL · GEOMETRY
```

Một xâu lấy sai đường sẽ là nhiễu chữ cái, không thể tự đọc thành danh sách thuật toán
hình học như vậy. Đây là bằng chứng mạnh nhất rằng đường đã chọn là đường tác giả định.

**Bước 5 - Kiểm luật ghép cờ.** Ví dụ trong đề (ASTART, BCDEFG, hijklm, NOPQRS, tuvwxy,
ZFINAL → `ACjQxL`) được dùng làm test chốt trong `exploit.py`; thử luật sai (luôn lấy chữ
đầu) thì test bắt được ngay.

## Flag

```
$ python exploit.py files/map.zip
1) do thi: 10000 nut, 59944 canh chieu, 29972 canh vo huong
2) Dijkstra theo toa do: 135 chan, tong quang duong 144.9333, so duong toi uu = 1
3) duong thang lien nut dau-cuoi = 138.6231 -> lo trinh 4.55% dai hon
4) ca 135 canh deu la wikilink that trong map
5) cach hieu 'it chan nhat': 13 chan nhung dai 199.9478 (ngan nhat la 144.9333) -> khong trung
6) duong di: S0jRxc -> 1T5eN4 -> hmANsv -> ... -> KTjmKT -> jvRMt3 -> yRJyDb

FLAG: CSSCTF{STARmaPdElAUNaYTriaNGulATioNDIjKStrAVoRonoiGrAPHSdetERmiNaNTcolineaRALGOrITHmSLeEandsCHAcHTERTANgEnTSmErGECirCuMcIrcLEcOnVEXhuLLgeOMeTRy}
```

## Reproduce

```bash
python exploit.py files/map.zip
```
