---
title: "Flag from the Future"
category: "Misc"
tags: ["cellular-automaton", "reverse-game-of-life", "dejavu-font", "glyph-metrics", "screenshot-parsing"]
solve_date: "2026-10-10"
language: "vi"
---

# Flag from the Future

**Flag:** `FortID{R3al_L1f3_H45_N0_R3w1nd_Bu7t0n}`
**Artifact:** một screenshot duy nhất, không có file nguồn, không có instancer; kích thước byte của ảnh không được lưu trong bản ghi. Tác giả: ipaljak.

## Đề bài

Đề cho một screenshot hiển thị một dòng ký tự dạng điểm (bitmapped) và nói hai điều: dòng chữ đó được render từ một trong các file TTF của DejaVu 2.37, và mỗi ô có cường độ từ 50% trở lên trở thành ô sống. Không có service, không có script, không có mã nguồn.

Ảnh là lưới tiến hoá của Game of Life, tức thứ đang hiển thị là *hậu duệ*. Cờ nằm ở phía ngược lại, tại cấu hình đã sinh ra nó.

## Phân tích

### Hình học của lưới

Từ screenshot thu được lưới 27 hàng × 371 cột với 909 ô sống, mỗi ô 6×6 px với pitch 8 px, gốc lưới tại `x = 55 + 8c`, `y = 32 + 8r`.

```python
R, C = 27, 371                      # grid extracted from the screenshot


def top_left(r, c):                 # cell origin and pitch, as recorded
    return 55 + 8 * c, 32 + 8 * r


print("grid", R, "x", C, "=", R * C, "cells")
print("live", 909, "density", round(909 / (R * C), 4))
print("last cell top-left", top_left(R - 1, C - 1))
print("raster size", 55 + 8 * (C - 1) + 6, "x", 32 + 8 * (R - 1) + 6)


def pen(i):                         # pen column after i glyphs, recorded formula
    return 1 + round(i * 617 / 64)


print([pen(i) for i in range(13)])
print("pen(38) =", pen(38), " grid width =", C, " cols/glyph =", 617 / 64)
```

```text
grid 27 x 371 = 10017 cells
live 909 density 0.0907
last cell top-left (3015, 240)
raster size 3021 x 246
[1, 11, 20, 30, 40, 49, 59, 68, 78, 88, 97, 107, 117]
pen(38) = 367  grid width = 371  cols/glyph = 9.640625
```

Mật độ ô sống 9.07% — thấp, phù hợp một ảnh đang ở nhiều thế hệ sau khi chữ đã bị cấu hình lại, không phải ảnh render trực tiếp của một dòng chữ.

### Luật

Đếm các still life trong lưới cho: 7 block, 2 beehive, 2 loaf, 2 boat. Bốn loại cấu hình này đều là điểm bất động của B3/S23:

```python
def step(g, rule):
    birth, survive = rule
    r, c = len(g), len(g[0])
    out = [[0] * c for _ in range(r)]
    for i in range(r):
        for j in range(c):
            n = sum(g[i + di][j + dj]
                    for di in (-1, 0, 1) for dj in (-1, 0, 1)
                    if (di, dj) != (0, 0) and 0 <= i + di < r and 0 <= j + dj < c)
            out[i][j] = 1 if (n in birth) or (g[i][j] and n in survive) else 0
    return out


BLOCK = [[1, 1], [1, 1]]
BEEHIVE = [[0, 1, 1, 0], [1, 0, 0, 1], [0, 1, 1, 0]]
LOAF = [[0, 1, 1, 0], [1, 0, 0, 1], [0, 1, 0, 1], [0, 0, 1, 0]]
BOAT = [[1, 1, 0], [1, 0, 1], [0, 1, 0]]

for name, obj in [("block", BLOCK), ("beehive", BEEHIVE), ("loaf", LOAF), ("boat", BOAT)]:
    print(name, "stable under B3/S23:", step(obj, ((3,), (2, 3))) == obj)
```

```text
block stable under B3/S23: True
beehive stable under B3/S23: True
loaf stable under B3/S23: True
boat stable under B3/S23: True
```

Block, beehive, loaf và boat cùng bền dưới B3/S23 nhưng không cùng bền dưới các luật khác, nên chúng là bộ lọc đủ mạnh: theo bản ghi, 16 luật khác bị loại trên chính các cấu trúc đó. Bản ghi không nói toàn bộ không gian luật kiểu Life đã được duyệt, nên kết luận ở phạm vi "luật phù hợp với mọi cấu hình đếm được trong lưới, và loại được 16 ứng viên".

### Cờ là tổ tiên, không phải hậu duệ

Forward Life mất thông tin, nên không "đọc" được cờ từ lưới. Bài toán là tìm predecessors: dãy ô ở thế hệ 0 sao cho sau 18 thế hệ B3/S23 cho ra đúng lưới trích từ screenshot. Nếu chỉ có ràng buộc đó thì không gian predecessor rất lớn nhưng hữu hạn trên lưới cố định — reverse Life vốn là bài toán under-determined.

Ràng buộc thứ hai đến từ chính đề: thế hệ 0 phải là kết quả render một dòng chữ bằng TTF của DejaVu 2.37. Tức predecessor không phải một cấu hình tuỳ ý mà là ảnh điểm của một xâu ký tự, với các cột glyph bị định vị bởi pen advance. Bản ghi dùng công thức:

```text
pen(i) = 1 + round(i * 617 / 64)
```

`617/64 = 9.640625` cột mỗi ký tự; `pen(38) = 367` nằm trong lưới 371 cột, tức hình học này chứa vừa một xâu 38 ký tự — đúng độ dài của cờ. Hai hệ quả: không gian tìm kiếm co lại thành không gian xâu ký tự, và mỗi ứng viên có cách kiểm định rẻ (render rồi mô phỏng tới).

## Lời giải

Tìm kiếm chạy trên các xâu ứng viên: render xâu bằng metrics DejaVu đã ghi nhận để có predecessor, tiến hoá thuận 18 thế hệ dưới B3/S23, rồi so từng ô với lưới trích từ screenshot. Ứng viên đạt sai lệch 0 là lời giải.

Hai dòng cuối của bản ghi, chép nguyên văn (dòng thứ hai là câu tiếng Việt trong bản ghi; dấu `…` ở dòng đầu là phần bị lược của chính bản ghi):

```text
mism= 0 len=40 'FortID{R3al_L1f3_H45_N0_R3w1nd_Bu7t0n}…'
khớp từng ô với lưới trích từ screenshot: 909/909 ô, sai lệch 0
```

Bản ghi báo `mism=0` và `909/909` ô sống khớp. Không có script hay mảng grid để kiểm lại rằng cả các ô chết cũng khớp; đây chưa phải phép tái hiện độc lập.

 bản ghi in `len=40` cho xâu decode được nhưng chỉ lưu 38 ký tự đầu rồi cắt bằng `…`. Flag đã lưu dài 38 ký tự. Dòng `len=40` trong bản ghi solver không khớp với giá trị này; thiếu screenshot và renderer nên chưa thể đối chiếu nguyên nhân. Giữ nguyên flag đã lưu, nhưng chưa thể tái hiện phép dựng ảnh ra chuỗi cờ từ các tệp hiện có.

## Kết quả

```text
FortID{R3al_L1f3_H45_N0_R3w1nd_Bu7t0n}
```

Flag được giữ nguyên từ bản ghi giải. Screenshot và solver dựng/render bị thiếu nên chưa tái hiện được bước từ ảnh sang flag.

## Tái hiện

Đầu vào: screenshot của đề, bộ font DejaVu 2.37 (các file TTF), Python 3 với `pillow`/`numpy` để lấy mẫu điểm ảnh và render glyph, `fonttools` nếu muốn đọc metrics trực tiếp từ TTF.

1. Lấy mẫu lưới theo thông số đã ghi nhận: 27×371, ô 6×6 px, pitch 8 px, gốc `x = 55 + 8c`, `y = 32 + 8r`; cường độ ô ≥ 50% là ô sống. Block hình học trong mục Phân tích chạy lại toàn bộ thông số đó và in mật độ 0.0907 cùng cỡ raster 3021×246 px suy ra từ thông số.
2. Đếm still life để định luật; block `step()` kiểm chứng block/beehive/loaf/boat đều là điểm bất động của B3/S23.
3. Với mỗi xâu ứng viên: render predecessor bằng pen advance `pen(i) = 1 + round(i * 617 / 64)`, tiến hoá thuận 18 thế hệ theo B3/S23, đếm ô lệch với lưới ở bước 1.
4. Dừng ở ứng viên có `mism= 0`; xâu render ra predecessor đó là cờ.

Bước 3 là phần tốn thời gian nhất và chạy cục bộ hoàn toàn. Bản ghi của bài lưu thông số hình học, luật, công thức pen advance, số thế hệ và output kiểm định, nhưng không lưu script tìm kiếm, nên bước 3 phải dựng lại từ các thông số trên.
