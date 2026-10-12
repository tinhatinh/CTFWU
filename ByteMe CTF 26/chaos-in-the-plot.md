---
title: "Chaos in the Plot"
category: "Misc"
tags: ["matplotlib", "connected-components", "coordinate-recovery", "affine-cipher", "crib-dragging"]
solve_date: "2026-10-09"
language: "vi"
---

# Chaos in the Plot

**Flag:** `OWASP{CHAOS_IN_THE_PLOT}`
**Artifact:** `the_math_of_plot.zip` (49,003 B, 2 thành viên, tổng dung lượng giải nén 98,583 B).

## Đề bài

Phần mô tả được lưu lại cho bài:

```text
The Soul Stone has distorted a hidden message using a mathematical transformation and scattered the resulting values across a chaotic Matplotlib plot…
```

Medium, 200 điểm.

## Phân tích

### Archive và hai tệp bên trong

Các thành viên của `chaos_artifact.bin` mang extra field `0x9901` của WinZip AE (vendor `AE`, strength 3 = AES-256, method 8 = deflate). Mật khẩu nén là `OWASP`; giá trị này được cung cấp trong quá trình làm bài chứ không phải kết quả khôi phục từ artifact. Toàn bộ lời giải chỉ dùng hai tệp giải nén được:

```console
$ 7z t -pOWASP chaos_artifact.bin
Testing archive: chaos_artifact.bin
--
Path = chaos_artifact.bin
Type = zip
Physical Size = 49003

Everything is Ok

Folders: 1
Files: 2
Size:       98583
Compressed: 49003
```

- `the math of plot/chaos.png` — 4500×2400, 98,191 B: một scatter của matplotlib, không có tick, không có nhãn trục.
- `the math of plot/fragments.dat` — 392 B: 56 dòng `HEX:HEX`.

### Đám marker

Marker của scatter là màu `tab:blue` (31, 119, 180). Ngưỡng khoảng cách Manhattan < 60 trên ảnh RGB tách đúng phần marker khỏi nền trắng; connected component cho ảnh nhị phân này trả về 56 thành phần, mỗi thành phần đúng 777 px, tổng 43,512 px. Toạ độ tâm của mọi marker đều rơi vào toạ độ pixel nguyên, nên việc đọc vị trí không cần nội suy.

### Hai bộ luật trục

Trục dữ liệu phải được suy ra lại vì ảnh không còn tick. Matplotlib cộng thêm 5% margin ở mỗi phía khi autoscale, và khoảng 180 đơn vị dữ liệu trải trên hiệu hai tâm ngoài cùng. Phép đo cho:

```text
x_px = 245.0 + slot * 22.277778      22.277778 = 4010/180,  slot = 0..180
key  = 0x1F4 + slot                                             key range 500..680
y_data = round((2254 - y_px) * 254 / 2026)
```

`245.0` là cột pixel của marker ngoài trái, `2254` là mép trên vùng dữ liệu và `2026` là chiều cao của vùng đó sau khi đã trừ margin; hệ số `254` tương ứng dải giá trị 0..254. Bộ luật này được xác nhận bằng chính dữ liệu: áp dụng cho 56 tâm thì mỗi marker khớp đúng một giá trị trong `fragments.dat`, không marker nào lệch.

### Khoá trùng và luật toạ độ

`fragments.dat` chỉ có 52 khoá khác nhau trên 56 dòng: `0x281`, `0x29D`, `0x29E`, `0x2A6` mỗi khoá xuất hiện hai lần. Vì có 56 marker nhưng chỉ 52 khoá khác nhau, các giá trị lặp phải được phân biệt bằng cao độ, và cao độ không tự do — nó là ảnh của chính giá trị:

```text
y_data = (value XOR 91) - 2 * [value even]
```

Trong công thức, `[value even]` bằng 1 khi `value` chẵn và bằng 0 khi lẻ. Ví dụ đo trực tiếp: marker slot 0 có `y_px = 1783`, suy ra `y_data = 59`; ứng viên duy nhất của khoá `0x1F4` trong `fragments.dat` là `value = 102`, và `102 XOR 91 = 61`, trừ 2 vì 102 chẵn, cho đúng 59. Quan hệ này nhất quán trên toàn bộ 56 điểm, nên nó là luật encode của tác giả chứ không phải khớp ngẫu nhiên ở một điểm.

### Phép biến đổi affine

Đặt dãy `c` gồm 56 giá trị `y_data` sắp theo `x` tăng dần. Dãy này là ảnh affine của chuỗi plaintext trên vành 256:

```text
c = (7*p + 18) mod 256          p = (c - 18) * 7^-1 mod 256,   7^-1 = 183
```

`7 * 183 = 1281 = 5*256 + 1`, nên 183 đúng là nghịch đảo của 7. Crib `OWASP{` quét mọi vị trí và mọi `a` lẻ (điều kiện cần để khả nghịch mod 256) cho đúng một nghiệm `(m, a, b, pos) = (256, 7, 18, 0)`; không có nghiệm khác trong toàn bộ dãy.

Kiểm tra tay một phần tử: `y_px = 1783 → c = 59 → (59 − 18) * 183 mod 256 = 79 = 'O'`.

## Lời giải

```python
"""Chaos in the Plot -- marker detector, axis recovery, inverse affine."""
import numpy as np
from PIL import Image
from scipy import ndimage

PNG = "chaos/the math of plot/chaos.png"
DAT = "chaos/the math of plot/fragments.dat"

a = np.array(Image.open(PNG))[:, :, :3].astype(int)
blue = (np.abs(a - np.array([31, 119, 180])).sum(2) < 60)
lab, n = ndimage.label(blue)
sizes = ndimage.sum(blue, lab, range(1, n + 1))
cen = ndimage.center_of_mass(blue, lab, range(1, n + 1))
pts = np.array([(round(c[1], 4), round(c[0], 4)) for c in cen])
print("png=%s  components=%d  distinct sizes=%s  blue px=%d"
      % (Image.open(PNG).size, n, sorted(set(int(s) for s in sizes)), int(blue.sum())))

pairs = [tuple(int(x, 16) for x in line.strip().split(":"))
         for line in open(DAT) if line.strip()]
kn = [k for k, v in pairs]
print("fragments=%d  duplicate keys=%s"
      % (len(pairs), sorted({hex(k) for k in kn if kn.count(k) > 1})))

xs = np.sort(np.unique(pts[:, 0]))
X0, XSTEP = xs[0], (xs[-1] - xs[0]) / 180
print("x0=%.1f step=%.6f (=4010/180=%.6f)  key = 0x1F4 + slot" % (X0, XSTEP, 4010 / 180))

PX1, SPAN, MOD = 2254, 2026.0, 254.0
y_data = lambda py: int(round((PX1 - py) * MOD / SPAN))
series = [y_data(int(round(y))) for x, y in sorted(pts.tolist())]
print("first c values:", series[:8])

inv = pow(7, -1, 256)
plain = [(c - 18) * inv % 256 for c in series]
print("decrypted     :", "".join(chr(p) if 32 <= p < 127 else "." for p in plain))
print("re-encrypt check:", all((7 * p + 18) % 256 == c for p, c in zip(plain, series)))

CRIB = "OWASP{"
hits = [(256, aa, (series[pos] - aa * ord(CRIB[0])) % 256, pos)
        for pos in range(len(series) - len(CRIB) + 1) for aa in range(1, 256, 2)
        if all((aa * ord(ch) + (series[pos] - aa * ord(CRIB[0]))) % 256
               == series[pos + i] for i, ch in enumerate(CRIB))]
print("crib hits:", len(hits), hits)
print("hand check: y_px=1783 -> c=%d -> (c-18)*183 mod 256 = %d = %r"
      % (y_data(1783), (y_data(1783) - 18) * inv % 256,
         chr(((y_data(1783) - 18) * inv) % 256)))
print("markers in slots 100..180:", len([1 for x, y in pts.tolist()
                                        if round((x - X0) / XSTEP) >= 100]))
```

```text
png=(4500, 2400)  components=56  distinct sizes=[777]  blue px=43512
fragments=56  duplicate keys=['0x281', '0x29d', '0x29e', '0x2a6']
x0=245.0 step=22.277778 (=4010/180=22.277778)  key = 0x1F4 + slot
first c values: [59, 115, 217, 87, 66, 111, 231, 10]
decrypted     : OWASP{CHAOS_IN_THE_PLOT}...s..J].."..)......M....L.....B
re-encrypt check: True
crib hits: 1 [(256, 7, 18, 0)]
hand check: y_px=1783 -> c=59 -> (c-18)*183 mod 256 = 79 = 'O'
markers in slots 100..180: 32
```

Dòng `decrypted` là toàn bộ 56 giá trị đã giải affine: 24 ký tự đầu là `OWASP{CHAOS_IN_THE_PLOT}`, 32 giá trị còn lại không rơi vào vùng in được. `re-encrypt check: True` nghĩa là hàm `(7*p + 18) mod 256` dựng lại đúng dãy `c` đã đo từ ảnh, nên tham số `(7, 18, 256)` không phải nghiệm khớp một chiều.

## Kết quả

```text
OWASP{CHAOS_IN_THE_PLOT}
```

Toàn bộ chuỗi suy ra từ `chaos.png` và `fragments.dat`, được xác nhận lại bằng phép mã hoá thuận `(7*p + 18) mod 256` trên chính dãy đã đo. Bảng các bài đã giải của sự kiện ghi nhận bài này ở trạng thái đã giải.

## Tái hiện

Cần 7-Zip (hoặc một tool WinZip-AE bất kỳ) để mở archive, Python 3 với `numpy`, `Pillow`, `scipy`. Lời giải chạy ngoại tuyến hoàn toàn.

```console
$ 7z x -pOWASP -o./chaos chaos_artifact.bin
$ python chaos_repro.py
```

Lưu đoạn script trong mục Lời giải thành `chaos_repro.py` và đặt cạnh thư mục `chaos/the math of plot/` tạo ra khi giải nén. Hai hằng số `PX1 = 2254` và `SPAN = 2026` là kết quả đo trên ảnh 4500×2400; nếu ảnh bị resize thì phải đo lại trước khi dùng công thức trục.
