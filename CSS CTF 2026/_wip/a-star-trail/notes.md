# notes.md - a-star-trail

Input: `files/A_Star_Trail.png` (597693 B, sha256 `a3584ca6…c3d33ed`, 3780x1890 RGBA)
Định dạng cờ: `CSSCTF{<chữ cái đầu mỗi thiên thể>-<số ngày 1 chữ thập phân>}`

## H1 - Liệu có dữ liệu giấu trong PNG không
cmd: `python - <<'PY' ... struct unpack chunk + tim chuoi ASCII ... PY`
evidence: chunk đúng chuẩn `IHDR, pHYs, tEXt(25B = "Software: www.inkscape.org"), 74xIDAT, IEND`;
EOF hợp lệ, không có byte nào sau IEND, không có `PK\x03\x04`, không có chuỗi `CSSCTF`/`flag`/`days`.
Chuỗi "ctf" duy nhất ở offset 340894 nằm giữa dòng IDAT đã deflate nên là ngẫu nhiên.
result: DEAD - không có stego, bài thuần đồ thị.

## H2 - Suy cạnh bằng hình học (nhãn nằm giữa cạnh)
cmd: `python analysis/edges.py`
evidence: gán toạ độ 11 thiên thể nhỏ + điểm neo trên rìa EARTH/LANCER rồi tìm cặp có đoạn
thẳng đi gần nhãn nhất. Kết quả nhiễu: `7.5` và `8.5` không khớp cặp nào, nhiều nhãn cho 3 ứng
viên gần nhau vì toạ độ chỉ ước lượng bằng mắt từ bản hiển thị 2000x1000.
result: DEAD - thay bằng cách đọc trực tiếp trên ảnh phóng to.

## H3 - Đọc đồ thị trực tiếp
cmd: cắt ảnh thành 4 dải phủ chồng, xem từng dải (`files/band_top.png`, `files/band_mid.png`,
`files/band_right.png`, `files/band_bottom.png`, `files/earth_rim.png`)
evidence: mỗi dải nhìn rõ nét đứt và nhãn của nó. Điểm mù duy nhất là góc dưới trái, nơi hai
nét gặp nhau ngay trên rìa Earth: nét `5.0` từ BACONITE xuống rìa và nét `10.7` từ đúng điểm đó
sang PALLUS-XA, tức hai cạnh BACONITE-EARTH và EARTH-PALLUS-XA chứ không phải một nét gãy.
Đủ 20 nhãn cho 20 cạnh, khớp sĩ số đã đếm trên ảnh.
result: PENDING -> dùng bảng cạnh ở H4.

## H4 - Đường ngắn nhất
cmd: `python analysis/graph.py`
evidence: Dijkstra cho `EARTH -> PALLUS-XA -> 12-PUCK-8 -> JIP-REIA -> TAYLOR-3489 -> LANCER-RXKRD`
= 10.7+1.8+0.4+5.5+2.6 = 21.0 ngày. Liệt kê hết đường đơn dưới 25 ngày: 5 đường, lần lượt
21.0 / 21.6 / 22.7 / 22.9 / 24.3, nên đỉnh 21.0 là duy nhất.
result: OK - cờ: `CSSCTF{EP1JTL-21.0}`

## Độ nhạy của lời giải
cmd: `python exploit.py` với hai trọng số bị sửa
evidence: đổi `JIP-REIA-12-PUCK-8` 0.4 -> 4.0 hoặc `PALLUS-XA-12-PUCK-8` 1.8 -> 8.1 thì đường tốt
nhất đảo sang `… -> BARAT-BARAT -> JIP-REIA -> …` = 21.6, cờ thành `CSSCTF{EPBJTL-21.6}`.
Nghĩa là lời giải không tự kiểm được phần đọc ảnh: khoảng cách tới á quân chỉ 0.6 ngày. Nếu cờ
bị từ chối, việc đầu tiên là đọc lại ba nhãn 10.7, 1.8, 0.4 trên bản gốc.

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
