# notes.md - a-star-trail-2

Input: `files/map.zip` (2663657 B, sha256 `31c44f1b…a97525f9`, 10000 file markdown)
Định dạng cờ: `CSSCTF{<chữ cái thứ i vòng 6 của từng điểm dừng>}`

## H1 - Co trong so ngay an trong file khong
cmd: `python - <<'PY' ... dem theo loai dong trong 10000 file ... PY`
evidence: tổng cộng đúng ba loại dòng: `title` 10000, `coords` 10000, `wikilink` 59944.
Không có dòng nào khác, không có trường ngày/giờ/tốc độ.
result: DEAD - không có trọng số cho sẵn; thước đo duy nhất là toạ độ.

## H2 - "Hop ly" = it chan nhat (BFS)
cmd: `python analysis/graph.py`
evidence: BFS cho 13 chan (14 điểm dừng) nhưng tổng quãng đường 199.9478, trong khi
đường theo toạ độ chỉ 144.9333. Ngoài ra với bậc trung bình ~6 thì 13 chan là cận
dưới hiển nhiên và sẽ có rất nhiều đường 13 chan, không đủ điều kiện để ra một xâu cờ.
result: DEAD - để làm nhánh đối chứng trong exploit.py (bước 5).

## H3 - Do thi co lien ket doi xung va link treo khong
cmd: `python analysis/graph.py`
evidence: 59944 cạnh chiều gom lại còn 29972 cạnh vô hướng, đúng bằng một nửa -> đối
xưng tuyệt đối, 0 cạnh lệch chiều; 0 link trỏ tới ID không có file.
result: OK - dùng được làm đồ thị vô hướng lẫn có hướng, kết quả như nhau.

## H4 - Dijkstra trong so = khoang cach toa do
cmd: `python exploit.py files/map.zip`
evidence: 135 chan, tong 144.9333; duong thang noi S0jRxc va yRJyDb dai 138.6231 nen lo trinh
chi dai hon 4.55%%; dem so duong toi uu bang DP tren cay Dijkstra ra dung 1; ca 135 canh
duoc doi chieu lai la wikilink that trong file markdown tuong ung.
result: PENDING -> xac nhan o H5.

## H5 - Thong an trong xau co
cmd: `python exploit.py files/map.zip` (in xau bay chu)
evidence: `STAR maP DeLAUNaYTriaNGulATioN DIjKStrAVoRonoi GrAPHS deTeRmiNaNT colineaR
ALGOrITHmS ... TANgEnTS mErGE CirCuMcIrcLE cOnVEX huLL geOMeTRy` -> đọc thành
"STAR MAP, DELAUNAY TRIANGULATION, DIJKSTRA, VORONOI, GRAPHS, DETERMINANT, COLINEAR,
ALGORITHMS, … TANGENTS, MERGE, CIRCUMCIRCLE, CONVEX HULL, GEOMETRY". Một xâu ngẫu nhiên
136 ký tự không thể tự đọc thành danh sách thuật toán hình học như vậy.
result: OK - cờ: `CSSCTF{STARmaPdElAUNaYTriaNGulATioNDIjKStrAVoRonoiGrAPHSdetERmiNaNTcolineaRALGOrITHmSLeEandsCHAcHTERTANgEnTSmErGECirCuMcIrcLEcOnVEXhuLLgeOMeTRy}`

## luat ghep chu
cmd: `python - <<'PY' ... goi selftest() ... PY`
evidence: ví dụ của đề (ASTART, BCDEFG, hijklm, NOPQRS, tuvwxy, ZFINAL -> ACjQxL) khớp
công thức `id[i % 6]` với i đếm từ 0 và tính cả hai điểm đầu/cuối; thử đặt luật sai
(lấy chữ đầu mọi ID) thì selftest báo `ra ABhNtZ, de bao ACjQxL`.
result: OK - luật đã chốt, có test giữ.

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
