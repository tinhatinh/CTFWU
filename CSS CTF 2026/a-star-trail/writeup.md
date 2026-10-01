# A Star Trail — Misc/OSINT (Beginner)

**Flag:** `CSSCTF{P1JT-21.0}` · **Files:** `A_Star_Trail.png` (3780x1890, sha256 `a3584ca6…c3d33ed`)

## Đề bài

Bản đồ "POLARIS LOGISTICS STAR MAP - NO. CA-S08-R11" vẽ 13 thiên thể nối với nhau bằng 20
đường nét đứt, mỗi đường ghi số ngày đi. Phải bay từ EARTH tới LANCER-RXKRD theo đúng
các đường có sẵn, dưới 25 ngày. Cờ ghép từ chữ cái đầu của mỗi thiên thể trên đường đi,
nối với tổng số ngày (một chữ số thập phân) bằng dấu gạch.

## Phân tích ban đầu

File là PNG do Inkscape xuất, chunk chuẩn `IHDR / pHYs / tEXt / 74xIDAT / IEND`, không có byte
nào sau IEND và không có chuỗi đáng ngờ nào trong dữ liệu, nên không có kênh stego: bài thuần
tụ là đọc đồ thị rồi tìm đường ngắn nhất.

13 nút, 20 cạnh, trọng số thực. Nhỏ đến mức đọc bằng mắt và kiểm lại bằng code là đủ.

## Các hướng đã loại

1. **Stego trong PNG**: không có dữ liệu thừa, không có archive nhúng. Loại.
2. **Suy cạnh bằng hình học** (nhãn trọng số nằm giữa cạnh, thử mọi cặp nút): nhiễu, hai nhãn
   `7.5` và `8.5` không khớp cặp nào vì toạ độ chỉ ước lượng. Loại, chuyển sang đọc trực tiếp.
3. **Một nét gãy ở góc Trái Đất**: thoạt nhìn `5.0` và `10.7` như một đường gấp khúc
   BACONITE→PALLUS-XA. Phóng to thấy chúng gặp nhau đúng trên rìa Earth, tức là hai cạnh
   riêng BACONITE-EARTH và EARTH-PALLUS-XA. Đã kiểm tra lại.

## Chuỗi khai thác

**Bước 1 - Đọc hết 20 cạnh.** Cắt ảnh thành bốn dải phủ chồng để mỗi nét đứt và nhãn của nó
nằm gọn trong một khung (các dải lưu trong `files/band_*.png`). Bảng cạnh ra đủ 20 nhãn.

**Bước 2 - Chạy Dijkstra.**

```python
path, cost = dijkstra(g)
# EARTH -> PALLUS-XA -> 12-PUCK-8 -> JIP-REIA -> TAYLOR-3489 -> LANCER-RXKRD
# 10.7   + 1.8         + 0.4          + 5.5         + 2.6            = 21.0 ngay
```

**Bước 3 - Kiểm đỉnh có duy nhất.** Liệt kê mọi đường đơn dưới 25 ngày: có năm đường,
21.0 / 21.6 / 22.7 / 22.9 / 24.3. Đỉnh 21.0 chỉ xuất hiện một lần, nên không cần crib thêm.

**Bước 4 - Kiểm chứng.** Cộng lại từng cạnh của đường Dijkstra được đúng 21.0; mọi cạnh trên
đường đều có thật trong bảng đọc từ ảnh; số cạnh khai thác bằng đúng số nhãn trên bản đồ.

**Bước 5 - Ghép cờ.** "each planet/oid in your path" ở bài này là các chặng trung gian,
không tính nơi xuất phát và nơi đến. Bản đầy đủ là
`EARTH -> PALLUS-XA -> 12-PUCK-8 -> JIP-REIA -> TAYLOR-3489 -> LANCER-RXKRD`, lấy bốn chặng
giữa được P (PALLUS-XA), 1 (12-PUCK-8), J (JIP-REIA), T (TAYLOR-3489) → `P1JT`, thêm `-21.0`.
Bản tính cả hai đầu (`EP1JTL-21.0`) đã nộp và bị từ chối.

Độ nhạy đáng ghi nhớ: á quân chỉ kém 0.6 ngày, nên nếu đọc sai một trọng số nhỏ (0.4 hoặc 1.8)
thì cờ đảo sang `EPBJTL-21.6`. Script đã thử hai biến thể đó và cho thấy nó đổi kết quả thật,
tức phần đọc ảnh mới là chỗ dễ gãy, không phải phần tính toán.

## Flag

```
$ python exploit.py
1) do thi: 13 nut, 20 canh (doc tu anh)
2) Dijkstra: EARTH -> PALLUS-XA -> 12-PUCK-8 -> JIP-REIA -> TAYLOR-3489 -> LANCER-RXKRD = 21.0 ngay
3) cong lai tung canh: 21.0 - khop
4) duong duoi 25 ngay: 5, ngan nhat 21.0, thu nhi 21.6
5) dinh dang CSSCTF{<ky tu dau moi nut>-<ngay>}

FLAG: CSSCTF{P1JT-21.0}
```

## Reproduce

```bash
python exploit.py
```
