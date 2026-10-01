# Đề bài - a-star-trail-2

## Nguyên văn đề

```text
A Star Trail 2
187
Intermediate
Noxellar

Congrats on your first, successful delivery cadet! Now that you've got a small
taste of logistics and routing, take a gander at this larger galactic map. You've
got quite a few more stops this time but thankfully, you won't have to be put to
cryosleep now that you've gained your lightspeed vehicle licence. Today, your task
is to make it from planetary body S0jRxc to planetary body yRJyDb. Chart out a
path and don't be late; we expect you to make it there in a reasonable time.
You'll have to do a bit of work to make sense of everything since our database is
stored as Markdown files where each planet links to its neighbours with a wikilink
but it should be easy work once you get used to it.

Report to command your flightpath by taking the first letter of the ID of your
first stop (S0jRxc), the second letter of your second stop, the third letter of
your third stop, and so on, wrapping back around to the first letter on your 7th,
13th, 19th, etc. stop. Your flightpath flag is case sensitive. For example: if
your path from ASTART to ZFINAL was BCDEFG, hijklm, NOPQRS, tuvwxy, ZFINAL the
flag would be CSSCTF{ACjQxL}

- Polaris Logistics.
```

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/map.zip` (copy từ: `/c/Users/Administrator/Downloads/map.zip`) |
| Kích thước | 2663657 byte |
| SHA-256 | `31c44f1ba6aa250952f2c03e9235984106b277d230a548666c2b6a31a97525f9` |
| Loại file | Zip archive, 10001 entry: `map/` + 10000 file `map/<ID>.md` |
| Nội dung mỗi file | `# <ID>`, `Coords: x, y`, rồi các `[[lang-gieng]]`; không có dòng nào khác |
| Đồ thị | 10000 nút, 59944 cạnh chiều = 29972 cạnh vô hướng, liên kết đối xứng hoàn toàn, không link treo, bậc 3..14 trung bình 5.99 |
| Nhiệm vụ | Đường S0jRxc -> yRJyDb "trong thời gian hợp lý", ghép cờ theo luật chữ thứ i quay vòng 6 |
| Định dạng cờ | `CSSCTF{...}` |
| Điểm / độ khó / tác giả | 187 / Intermediate / Noxellar (ngay trên thẻ đề) |
| Trạng thái nộp | cờ kiểm chứng cục bộ (xâu ghép đọc thành danh sách thuật toán hình học, đường tối ưu duy nhất); chưa có xác nhận đã được chấm chấp nhận |

## Hướng giải (tóm tắt)

Đề không cho số ngày như bản trước, và dữ kiện duy nhất có thể đo được là toạ độ, nên
"reasonable time" là tổng quãng đường Euclid giữa các hành tinh liên tiếp: chạy
Dijkstra với trọng số = khoảng cách toạ độ. Đường tối ưu duy nhất, và xâu chữ cái
ghép ra chứa một thông điệp ẩn liệt kê các thuật toán hình học, xác nhận đã đúng đường.

## Chạy lại lời giải

```bash
python exploit.py files/map.zip
```

Kết quả: `CSSCTF{STARmaPdElAUNaYTriaNGulATioNDIjKStrAVoRonoiGrAPHSdetERmiNaNTcolineaRALGOrITHmSLeEandsCHAcHTERTANgEnTSmErGECirCuMcIrcLEcOnVEXhuLLgeOMeTRy}` (đã lưu trong `flag.txt`).
