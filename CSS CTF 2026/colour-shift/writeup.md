# Colour Shift - Forensics (Beginner)

**Flag:** `CSSCTF{SHINE ON}`
**File đính kèm:** `colorshiftctf.bmp` (Kích thước: 1.083.738 B, SHA256: `689f33baf1acdef5c58b61a493977a44384694ef87f07a1f0606f1f34035ef92`)

## Đề bài

Nội dung cung cấp bao gồm một file định dạng BMP và một mô tả văn bản liên quan đến định luật phân tích ánh sáng của Isaac Newton. File đính kèm duy nhất là `colorshiftctf.bmp`, và mô tả đề cập tới nguyên lý tách ánh sáng thành các thành phần quang phổ màu cơ bản. Định dạng cờ được quy định là `CSSCTF{...}`.

## Phân tích ban đầu

Ảnh BMP có kích thước 599×602, 24 bit/pixel, dùng `BI_RGB`. `bfOffBits=138` và `biSizeImage=1083600`; tổng hai giá trị bằng kích thước file, nên không có dữ liệu nối thêm sau pixel array. Header là `BITMAPV5HEADER` dài 124 byte, bitmask `ff/ff00/ff0000`, `biClrUsed=0`; ảnh không có palette.

Ảnh nền là *The Dark Side of the Moon*, khá tối và có nhiễu. Giá trị trung bình R/G/B lần lượt là 15.4, 32.1 và 38.1. Kênh R có dải 0–255, trong khi G đạt tối đa 240 và B đạt 215; do đó kiểm tra riêng từng kênh màu.

## Chuỗi khai thác

**Bước 1 - Phân tách cấu trúc thành phần màu.** 
Tăng contrast của cả ảnh cũng làm nhiễu rõ hơn. Thay vào đó, ước lượng nền bằng median filter rồi lấy hiệu giữa ảnh và nền:

```python
def residual(chan):
    bg = np.asarray(Image.fromarray(chan).filter(ImageFilter.MedianFilter(41)))
    return chan.astype(np.float32) - bg.astype(np.float32)
```

Kernel 41 pixel lớn hơn độ dày nét chữ, nên có thể dùng để ước lượng nền. Trong thử nghiệm này, median filter tạo ít halo quanh nét chữ hơn Gaussian filter.

**Bước 2 - Phân tích đối chiếu trên từng kênh.** 
Sau khi normalize bằng median absolute deviation (MAD) và phóng lớn, dòng chữ hiện rõ ở kênh R và ảnh hiệu `R - B`. Trong cùng vùng, G và B không cho thấy dòng chữ tương ứng. `R - B` giảm phần nhiễu nền chung và làm chữ dễ đọc hơn.

*(Hình ảnh minh họa kết quả phân tích ba kênh màu: `analysis/channels.png`)*

**Bước 3 - Giải mã nội dung văn bản.** 
Vùng dải tín hiệu chứa văn bản định vị tại trục tung y từ dòng 404 đến dòng 436, trải dài qua toàn bộ trục hoành (bề ngang) của ảnh.

```text
C S S C T F { S H I N E   O N }
```

Dòng chữ có khoảng trắng giữa `E` và `O`. Khoảng này rộng khoảng 47 pixel, so với khoảng cách ký tự trung bình 33 pixel. Bản dùng Gaussian filter từng xuất hiện một nét giống `/`; nét đó không còn ở bản median filter.

**Bước 4 - Xác thực quy trình (Kiểm chứng).** 
Dòng chữ được đọc trực tiếp từ vùng y=404–436 của ảnh đã xử lý. Kiểm tra ảnh ba kênh và ảnh hiệu để đối chiếu các ký tự, đặc biệt khoảng trắng trong `SHINE ON`.

## Flag

Chạy script:

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

Nội dung kết quả xuất ra file `analysis/flag_line.png` hiển thị dòng chữ được khôi phục thành công.

Kết quả:
```text
CSSCTF{SHINE ON}
```
