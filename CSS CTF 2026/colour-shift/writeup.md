# Colour Shift - Forensics (Beginner)

**Flag:** `CSSCTF{SHINE ON}`
**File đính kèm:** `colorshiftctf.bmp` (Kích thước: 1.083.738 B, SHA256: `689f33baf1acdef5c58b61a493977a44384694ef87f07a1f0606f1f34035ef92`)

## Đề bài

Nội dung cung cấp bao gồm một tệp tin định dạng BMP và một mô tả văn bản liên quan đến định luật phân tích ánh sáng của Isaac Newton. Tệp đính kèm duy nhất là `colorshiftctf.bmp`, và mô tả đề cập tới nguyên lý tách ánh sáng thành các thành phần quang phổ màu cơ bản. Định dạng cờ được quy định là `CSSCTF{...}`.

## Phân tích ban đầu

Đánh giá tính toàn vẹn của tệp tin ảnh định dạng BMP: Kích thước ảnh 599x602 pixel, độ sâu màu 24 bit/pixel, sử dụng phương thức nén `BI_RGB`. Các thông số tiêu chuẩn như `bfOffBits=138` (địa chỉ bắt đầu của mảng pixel) và kích thước khối dữ liệu `biSizeImage=1083600` là hợp lệ. Tổng `138 + 1083600` khớp chính xác tuyệt đối với kích thước tệp, chứng tỏ hệ thống không chèn thêm khối dữ liệu dị thường (appended data) nào ở cuối tệp. Header sử dụng cấu trúc `BITMAPV5HEADER` với độ dài 124 byte, mặt nạ bit màu chuẩn là `ff/ff00/ff0000`, chỉ số `biClrUsed=0` (ảnh chuẩn dải màu thật - truecolor). Không phát hiện cấu trúc bảng màu (palette) ẩn giấu dữ liệu.

Quan sát thị giác: Hình ảnh mang hình nền của album *The Dark Side of the Moon*, sắc độ trung bình rất thấp (giá trị trung bình ba kênh R/G/B lần lượt là 15.4, 32.1 và 38.1). Bề mặt ảnh tồn tại hiện tượng nhiễu hạt (noise). Tiến hành khảo sát dữ liệu cường độ màu, phát hiện điểm bất thường: Kênh phân tách Đỏ (R) bao phủ toàn bộ dải động từ 0 đến 255. Trong khi đó, kênh Xanh lục (G) chỉ đạt dải đỉnh ở 240, và kênh Xanh dương (B) ở mức 215. Điều này cho thấy dải phổ Đỏ đang mang mức độ động (biến thiên tín hiệu) lớn hơn hai kênh còn lại.

## Chuỗi khai thác

**Bước 1 - Phân tách cấu trúc thành phần màu.** 
Theo đúng định hướng kỹ thuật mà mô tả đã đề cập, việc khuếch đại toàn bộ bức ảnh là không khả thi (việc nâng độ tương phản sẽ đồng thời khuếch đại mức độ nhiễu). Kỹ thuật xử lý yêu cầu loại bỏ lớp nền (tần số thấp) của ảnh, chỉ giữ lại tín hiệu của văn bản (tần số trung bình).

```python
def residual(chan):
    bg = np.asarray(Image.fromarray(chan).filter(ImageFilter.MedianFilter(41)))
    return chan.astype(np.float32) - bg.astype(np.float32)
```

Việc sử dụng bộ lọc không gian trung vị (Median Filter) với kích thước kernel 41 pixel có chủ đích: vì kích thước kernel này lớn hơn độ dày nét chữ, nên nó giúp ước tính chính xác bức xạ nền (background estimation). Trái với phép trừ sử dụng bộ lọc Gaussian, phương pháp này hạn chế tối đa hiện tượng tạo viền sáng/tối (halo effect) bao quanh tín hiệu nét chữ.

**Bước 2 - Phân tích đối chiếu trên từng kênh.** 
Sau khi chuẩn hóa theo độ lệch tuyệt đối trung vị (MAD) và phóng đại kích thước, một dòng tín hiệu văn bản xuất hiện rõ ràng trên kênh R và tại biểu thức hiệu tuyến tính `R - B`. Các kênh G và B ở vùng ảnh đó không mang tín hiệu khả kiến (phẳng). Lớp tín hiệu đè lên chỉ can thiệp vào cường độ của kênh Đỏ. Sự kết hợp hiệu tuyến tính `R - B` đem lại độ tương phản tối ưu, vì hai kênh này dùng chung lớp cấu trúc nhiễu nền; do đó, khi thực hiện phép trừ tín hiệu, bức xạ nền sẽ bị triệt tiêu hoàn toàn.

*(Hình ảnh minh họa kết quả phân tích ba kênh màu: `analysis/channels.png`)*

**Bước 3 - Giải mã nội dung văn bản.** 
Vùng dải tín hiệu chứa văn bản định vị tại trục tung y từ dòng 404 đến dòng 436, trải dài qua toàn bộ trục hoành (bề ngang) của ảnh.

```text
C S S C T F { S H I N E   O N }
```

Phân tích định lượng khẳng định ký tự ngăn cách giữa `E` và `O` là một khoảng trắng (space) chuẩn. Khoảng cách đo được xấp xỉ 47 pixel, so với bước nhảy (nhịp) ký tự trung bình là 33 pixel. Đặc biệt, không phát hiện bất kỳ điểm ảnh nào trong vùng khoảng trống đó đạt ngưỡng tín hiệu trên bất kỳ kênh màu nào. Kịch bản phân tích tín hiệu dải thông (band-pass) bằng hiệu ứng Gaussian trước đó có hiển thị một vệt xéo trông tựa như ký tự `/` tại vùng này, tuy nhiên kết luận cuối cùng đây chỉ là dao động nhân tạo sinh ra bởi bộ lọc Gaussian; việc thay đổi cơ chế lọc sang hệ số trung vị đã loại bỏ hoàn toàn yếu tố này.

**Bước 4 - Xác thực quy trình (Kiểm chứng).** 
Thực hiện rà soát toàn bộ vùng không gian ảnh, kết quả xác nhận không có dòng tín hiệu văn bản bổ sung nào khác ngoại trừ dải 404-436. Các dải năng lượng mật độ cao khác xuất hiện trên ảnh thực chất là các vệt phổ sắc cạnh (cạnh tam giác) và dải cấu trúc cầu vồng thuộc hình nền nguyên bản của bức ảnh. Tiền tố `CSSCTF{` đồng nhất hoàn toàn với định dạng chuẩn do đề bài yêu cầu. Toàn bộ phần nội dung trong cấu trúc cờ nằm trọn trong một dải liên tục, có tính tường minh cao, không chứa các ký tự cần phải áp dụng logic suy đoán.

## Flag

Quá trình thực thi mã kịch bản:

```bash
python exploit.py files/colorshiftctf.bmp -o analysis
```

```text
file      : files/colorshiftctf.bmp  599x602
  residual R  : min  -78.0 max +245.0  p99.9 +208.0
  residual G  : min  -86.0 max +214.0  p99.9 +172.0
  residual B  : min  -65.0 max +182.0  p99.9 +142.0

kenh do = R - B (tru nen median 41, hop thu 2x2)
vuong goc hoa: med 0.080  MAD-sd 1.186  z[min] -7.4
da ghi analysis\flag_line.png

so pixel net chu: 2774 (>=1500 de coi like co dong chu)
```

Nội dung kết quả xuất ra tệp `analysis/flag_line.png` hiển thị dòng chữ được khôi phục thành công.

Kết quả:
```text
CSSCTF{SHINE ON}
```
