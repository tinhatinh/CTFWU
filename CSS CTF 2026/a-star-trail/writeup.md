# A Star Trail - Misc/OSINT (Beginner)

**Flag:** `CSSCTF{P1JT-21.0}`
**File đính kèm:** `A_Star_Trail.png` (Kích thước: 3780x1890, SHA256: `a3584ca6...c3d33ed`)

## Đề bài

Hệ thống cung cấp một bản đồ với tiêu đề "POLARIS LOGISTICS STAR MAP - NO. CA-S08-R11". Bản đồ này mô tả 13 thiên thể được kết nối với nhau thông qua 20 đường nét đứt, mỗi đường có ghi chú số ngày di chuyển tương ứng. Yêu cầu đặt ra là tìm một lộ trình di chuyển từ thiên thể `EARTH` đến thiên thể `LANCER-RXKRD`, di chuyển theo các đường đã cho sao cho tổng số ngày không vượt quá 25. 
Cấu trúc cờ (flag) được ghép từ chữ cái đầu tiên của từng thiên thể trên lộ trình (chỉ tính các trạm trung gian), nối với tổng số ngày di chuyển (được định dạng với một chữ số thập phân) thông qua dấu gạch ngang `-`.

## Phân tích ban đầu

Kiểm tra cấu trúc tập tin PNG: Tệp được xuất từ phần mềm Inkscape, tuân thủ đúng định dạng với các khối chunk chuẩn (`IHDR`, `pHYs`, `tEXt`, 74 khối `IDAT`, và `IEND`). Không phát hiện bất kỳ dữ liệu dư thừa nào sau khối `IEND` cũng như không có chuỗi văn bản bất thường trong cấu trúc dữ liệu. Do đó, có thể loại trừ khả năng tệp sử dụng kỹ thuật giấu tin (steganography). Bài toán quy về dạng thuần túy: đọc dữ liệu từ đồ thị và tìm đường đi ngắn nhất.

Đồ thị bao gồm 13 đỉnh và 20 cạnh, trọng số là các số thực. Kích thước đồ thị này đủ nhỏ để có thể trích xuất dữ liệu thủ công qua việc đọc trực quan, sau đó sử dụng mã lập trình để tự động hóa quá trình tính toán.

## Chuỗi khai thác

**Bước 1 - Trích xuất toàn bộ 20 cạnh từ bản đồ.** 
Tiến hành phân chia ảnh thành bốn dải (band) có phần chồng lấp lên nhau, đảm bảo mỗi đường nét đứt và nhãn số tương ứng nằm trọn vẹn trong một khung ảnh (các dải này được lưu trữ tại `files/band_*.png`). Từ đó, tiến hành lập bảng và xác nhận thu thập đủ 20 nhãn trọng số.

**Bước 2 - Áp dụng thuật toán Dijkstra.**
Thiết lập đồ thị và chạy thuật toán Dijkstra để tìm đường đi ngắn nhất:

```python
path, cost = dijkstra(g)
# Lộ trình: EARTH -> PALLUS-XA -> 12-PUCK-8 -> JIP-REIA -> TAYLOR-3489 -> LANCER-RXKRD
# Chi phí: 10.7 + 1.8 + 0.4 + 5.5 + 2.6 = 21.0 ngày
```

**Bước 3 - Xác minh tính duy nhất của lộ trình.** 
Sử dụng thuật toán duyệt để liệt kê toàn bộ các đường đi đơn có chi phí dưới 25 ngày. Kết quả cho thấy có tổng cộng 5 đường đi hợp lệ, với các mức chi phí lần lượt là: 21.0, 21.6, 22.7, 22.9, và 24.3 ngày. Lộ trình đạt 21.0 ngày là đường đi ngắn nhất và xuất hiện duy nhất một lần, không yêu cầu bổ sung điều kiện (crib) nào khác để phân loại.

**Bước 4 - Kiểm chứng tính toàn vẹn dữ liệu.** 
Thực hiện phép cộng đối chiếu các trọng số trên đường đi Dijkstra thu được, tổng chính xác bằng 21.0. Mọi cạnh trên lộ trình đều có mặt trong bảng dữ liệu trích xuất từ ảnh ban đầu, và số lượng cạnh được sử dụng khớp với số nhãn trên bản đồ.

**Bước 5 - Trích xuất và ghép Cờ (Flag).** 
Dữ kiện "each planet/oid in your path" được hiểu là các trạm dừng chân trung gian, không bao gồm điểm xuất phát (`EARTH`) và điểm đích (`LANCER-RXKRD`). 
Lộ trình đầy đủ là: `EARTH -> PALLUS-XA -> 12-PUCK-8 -> JIP-REIA -> TAYLOR-3489 -> LANCER-RXKRD`. 
Lấy chữ cái đầu tiên của bốn trạm trung gian, ta có: `P` (PALLUS-XA), `1` (12-PUCK-8), `J` (JIP-REIA), `T` (TAYLOR-3489). Ghép lại ta được chuỗi `P1JT`, kết hợp với tổng số ngày là `-21.0`. (Quá trình thử nghiệm cho thấy nếu bao gồm cả hai đầu thành `EP1JTL-21.0` thì hệ thống không chấp nhận).

Một điểm đáng lưu ý về độ nhạy của dữ liệu: Lộ trình ngắn thứ hai có chi phí là 21.6 ngày, chỉ chênh lệch 0.6 ngày so với lộ trình tối ưu. Nếu có bất kỳ sai sót nào trong quá trình đọc các nhãn trọng số nhỏ (chẳng hạn đọc nhầm 0.4 hoặc 1.8), chuỗi cờ có thể bị thay đổi thành `EPBJTL-21.6`. Kịch bản kiểm tra đã xác thực sự thay đổi này nếu đưa vào thông số sai, chứng tỏ bước đọc dữ liệu từ ảnh là khâu có rủi ro cao nhất, đòi hỏi sự chính xác tuyệt đối.

## Flag

Quá trình thực thi mã kịch bản tự động hóa:
```bash
$ python exploit.py
1) do thi: 13 nut, 20 canh (doc tu anh)
2) Dijkstra: EARTH -> PALLUS-XA -> 12-PUCK-8 -> JIP-REIA -> TAYLOR-3489 -> LANCER-RXKRD = 21.0 ngay
3) cong lai tung canh: 21.0 - khop
4) duong duoi 25 ngay: 5, ngan nhat 21.0, thu nhi 21.6
5) dinh dang CSSCTF{<ky tu dau moi nut>-<ngay>}

FLAG: CSSCTF{P1JT-21.0}
```

Kết quả:
```text
CSSCTF{P1JT-21.0}
```
