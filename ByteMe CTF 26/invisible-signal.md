---
title: "Invisible Signal"
category: "Steg"
tags: ["matplotlib", "plot-marker-recovery", "blob-detection", "axis-calibration"]
solve_date: "2026-10-09"
language: "vi"
---

# Invisible Signal

**Flag:** `OWASP{Sou15_c4nt_b3_533n_bY_n0rm41_3y3s}`
**Artifact:** `soul_stone_graph.png` (414,443 B) — PNG 4475×2474 RGBA, 0 byte sau `IEND`. Tác giả: Suyog Jadhav.

## Đề bài

Medium, 200 điểm, chỉ phát kèm một ảnh PNG. Ảnh là một đồ thị kiểu Matplotlib: hệ trục có lưới, ba đường sine chồng lên nhau và một họ điểm đánh dấu nhỏ chìm gần với nền. Cờ không nằm trong metadata hay trong bít thấp của pixel; nó nằm ở **toạ độ dữ liệu** của các điểm đánh dấu.

## Phân tích

### Loại stego truyền thống

`IEND` kết thúc file, không có dữ liệu append. `zsteg -a` và `strings` không tìm thấy payload trong các phép thử đã chạy. Các kết quả này hướng việc phân tích sang toạ độ marker, không loại trừ mọi phương pháp steganography khác.

### Đọc trục

Đồ thị không ghi nhãn trục số học, nhưng lưới kẻ của nó cho phép định chuẩn. Theo chiều ngang, cột pixel 372 đến 4351 tương ứng x = 0 đến 40; theo chiều dọc, hàng pixel 445 đến 2036 tương ứng y = 40 đến 120:

```text
x : pixel  372 -> 4351  map to  data x =   0 .. 40
y : pixel  445 -> 2036  map to  data y =  40 .. 120
```

Với hai ánh xạ tuyến tính này, mỗi cụm pixel trên ảnh quy được về một cặp toạ độ dữ liệu.

### Bộ lọc điểm dạng đĩa

Các marker là hình tròn đặc, đường kính khoảng 11 px. Điểm ảnh đơn lẻ trên đường sine hoặc trên dòng lưới không thoả hình dạng này, nên một score đo độ "đặc" của cụm (số pixel chia cho diện tích bao) tách được ba lớp:

```text
disc score, solid marker   : 103 - 117
disc score, plain image    :   8
disc score, curve crossing :  40 -  60
```

Chạy bộ lọc trên toàn ảnh cho **đúng 40 điểm**: mỗi điểm rơi vào một giá trị x nguyên trong 0..39, không trùng và không hụt, và giá trị y tương ứng đều là số nguyên nằm trong dải ASCII in được. x là chỉ số, y là mã ký tự:

```text
decoded: / OWASP{Sou15_c4nt_b3_533n_bY_n0rm41_3y3s} / len 40
```

`len 40` khớp số lượng điểm tìm thấy, nên cờ được dựng đủ 40 ký tự từ 40 marker, không phải một phần.

## Lời giải

Toàn bộ lời giải là phân tích ảnh ngoại tuyến:

1. Đọc PNG thành mảng RGB, loại các pixel nền/lưới bằng ngưỡng tổng kênh.
2. Định chuẩn từ dòng lưới: pixel 372→4351 cho x = 0→40, pixel 445→2036 cho y = 40→120.
3. Gom cụm connected-component, tính score độ đặc và giữ cụm có kích thước ~11 px với score trong dải 103–117.
4. Quy tâm mỗi cụm về toạ độ dữ liệu, làm tròn, kiểm tra tập x thu được đúng bằng {0..39}.
5. `chr(y)` theo thứ tự x → 40 ký tự cờ.

Hai detector độc lập trên cùng ảnh — một quét theo ô lưới, một đo độ đầy của hình đĩa — cho cùng tập 40 điểm, đây là cơ sở để tin các toạ độ không phải sản phẩm của ngưỡng lọc.

## Kết quả

```text
OWASP{Sou15_c4nt_b3_533n_bY_n0rm41_3y3s}
```

Cờ được giải từ chính artifact bằng phân tích ảnh ngoại tuyến, và được kiểm chứng chéo bởi hai detector độc lập (quét ô lưới và đo độ đầy hình đĩa) trên cùng tập 40 marker. Chưa lưu phản hồi submission.

## Tái hiện

Cần Python 3 với `numpy` + `PIL`, và `scipy` cho bước gom cụm (hoặc tự viết flood-fill). Bài không cần mạng hay dịch vụ nào.

```console
$ file soul_stone_graph.png
$ zsteg -a soul_stone_graph.png
$ strings soul_stone_graph.png | grep -i matplot
```

Khung dò marker:

```python
import numpy as np
from PIL import Image
from scipy import ndimage

img = np.asarray(Image.open("soul_stone_graph.png").convert("RGB")).astype(int)
mask = img.sum(axis=2) < 240                      # dark pixels on the plot
lab, n = ndimage.label(mask)
pts = []
for i in range(1, n + 1):
    ys, xs = np.where(lab == i)
    h = ys.max() - ys.min() + 1
    w = xs.max() - xs.min() + 1
    fill = len(ys) / (h * w)                      # filled circle ~ 1.0
    if 9 <= h <= 13 and 9 <= w <= 13 and fill > 0.85:
        pts.append((xs.mean(), ys.mean(), h, w, fill))

# grid calibration: col 372->4351 = x 0..40 ; row 445->2036 = y 40..120
def to_data(x_px, y_px):
    gx = (x_px - 372) / (4351 - 372) * 40
    gy = 40 + (y_px - 445) / (2036 - 445) * (120 - 40)
    return gx, gy

out = {}
for x_px, y_px, h, w, fill in pts:
    gx, gy = to_data(x_px, y_px)
    out[int(round(gx))] = chr(int(round(gy)))
print(len(out), "".join(out[k] for k in sorted(out)))
```

Ngưỡng `fill` cần chỉnh theo điểm ảnh thực tế của ảnh: marker thật cho score 103–117, giao điểm đường sine 40–60, nền trống 8. Dải giữ lại phải loại được năm điểm giả liệt kê ở mục trên; nếu một điểm giả lọt qua, tập x sẽ không còn đúng bằng {0..39}.
