---
title: "Spill the Tea"
category: "Misc"
tags: ["qr-code", "image-recovery", "reed-solomon", "linear-algebra", "gf2"]
solve_date: "2026-10-10"
language: vi
---

# Spill the Tea

## Đề bài

Tác giả: **ipaljak, laragrr**. Category trên đề: **Miscellaneous**; điểm ghi nhận: **500**.

> Oh no! Our recent hire spilled some tea over flag. Hope you can still read it...

Artifact là [flag.jpg](https://platform.ctf.fortid.com/uploads/3dd091c6a6e2a0c4a53c650f6d931ad0a693fbc2d6e200a315d0440e70ef6803/flag.jpg), ảnh JPEG **2304 × 4096**, **4.765.346 byte**. Một mã QR trên giấy bị lá trà che phần lớn vùng data.

![Ảnh gốc](images/spill-the-tea-original.jpg)

SHA-256 của file gốc và bản lưu trong repo:

```text
3dd091c6a6e2a0c4a53c650f6d931ad0a693fbc2d6e200a315d0440e70ef6803
```

## Phân tích

OpenCV không đọc được trực tiếp ảnh gốc. Vẫn nhìn thấy các finder pattern và nhiều ô giấy rời rạc, nên có thể lấy từng bit còn lộ ra thay vì coi mọi vùng tối là module đen. Lá trà cũng tối; threshold toàn ảnh sẽ biến nhiều module trắng bị che thành bit đen sai.

Grid có **41 × 41 module**, tương ứng QR version 6 vì `41 = 17 + 4 × 6`. Dùng homography đưa bốn góc vùng QR về hình vuông; tọa độ pixel theo thứ tự trên trái, trên phải, dưới phải, dưới trái là:

```text
(198, 758), (2107, 750), (2169, 2670), (173, 2698)
```

Mỗi module sau phép biến đổi có kích thước **40 × 40 pixel**. Grid kiểm tra dưới đây được thu nhỏ để dễ đối chiếu:

![Grid sau khi căn chỉnh](images/spill-the-tea-grid.png)

Hai lượt đo tạo được **699 module ban đầu** và **120 module đen bổ sung**:

- Giấy trắng: độ sáng trung bình cao, độ lệch chuẩn thấp, chênh lệch các kênh màu nhỏ.
- Mực đen: vùng tối tương đối trung tính và đồng đều. Lượt bổ sung đo sau Gaussian blur để giảm ảnh hưởng texture của mực in.
- Những ô không đủ bằng chứng giữ là unknown. Ô `(row=19, col=36)`, đánh số từ 0, bị bỏ vì patch tối được lấy mẫu nằm trên một mảnh trà; đây không phải phép đo đáng tin cậy của mặt giấy.

Ngưỡng cụ thể nằm trong `measure()` của code tái hiện. Tọa độ và ngưỡng gắn với đúng file gốc đã kiểm tra hash, không phải bộ đọc QR tổng quát.

## Khôi phục bằng Reed–Solomon

Bộ tham số được dùng là **version 6, ECC Q, mask 3**. Với bộ tham số này, QR có bốn block Reed–Solomon, mỗi block gồm **19 byte data + 24 byte parity = 43 byte**. Tổng cộng có **76 byte data = 608 bit chưa biết** và **172 codeword = 1376 bit** sau khi thêm parity, interleave các block.

Trước hết đánh dấu finder, separator, timing, alignment và format information là các module dành riêng. Các module còn lại được đọc theo đường zigzag hai cột của QR, rồi bỏ mask bằng `qrcode.util.mask_func(3)`. Không đưa các module cấu trúc vào payload.

Reed–Solomon tuyến tính trên GF(256); khi biểu diễn từng byte thành 8 bit, phép encode cũng tuyến tính trên **GF(2)**. Gọi `x` là vector 608 bit data. Để dựng ma trận encoder, lần lượt encode 608 vector cơ sở, mỗi vector chỉ bật một bit, rồi interleave data/parity đúng thứ tự QR. Mỗi bit codeword quan sát được tạo một phương trình:

```text
encoder_row[i] · x = observed_module XOR mask(row, col)
```

Khử Gauss bằng XOR cho hệ có **rank 600/608**, còn **8 biến tự do**. Duyệt `2^8 = 256` nghiệm, đọc segment ở byte mode (`0100`) cùng trường độ dài 8 bit, rồi giữ payload có toàn bộ ký tự thuộc ASCII in được (`32..126`). Chỉ còn một ứng viên trong tập này. Bước tái hiện không hardcode flag, prefix `FortID{` hoặc nội dung câu tiếng Anh.

Một chi tiết cần giữ nguyên: năm byte cuối data là `d0 00 ec 11 ec`; nibble `d` thuộc ký tự đóng `}`. Có thêm một byte `00` trước chuỗi pad `ec 11 ec`. Nếu áp đặt cách pad `ec 11 ec 11` ngay sau terminator/alignment thì hệ không khớp các module nhìn thấy. Vì vậy, code giải trực tiếp các bit data, kể cả phần padding, thay vì dựng padding từ phỏng đoán.

## Code tái hiện

Lưu code sau thành `solve.py`. Chạy từ thư mục cuộc thi với ảnh gốc đi kèm:

```powershell
python -m pip install numpy Pillow opencv-python-headless qrcode reedsolo zxing-cpp
python solve.py "images/spill-the-tea-original.jpg"
```

```python
import hashlib
import sys
from pathlib import Path

import cv2
import numpy as np
import qrcode
import reedsolo
import zxingcpp
from PIL import Image
from qrcode import base, util

N, SCALE, K = 41, 40, 608
ECC, MASK = qrcode.constants.ERROR_CORRECT_Q, 3


def template():
    qr = qrcode.QRCode(version=6, error_correction=ECC, mask_pattern=MASK)
    qr.modules_count = N
    qr.modules = [[None] * N for _ in range(N)]
    for r, c in [(0, 0), (N - 7, 0), (0, N - 7)]:
        qr.setup_position_probe_pattern(r, c)
    qr.setup_position_adjust_pattern()
    qr.setup_timing_pattern()
    qr.setup_type_info(False, MASK)
    return qr


def data_positions():
    qr = template()
    positions, row, step = [], N - 1, -1
    for col in range(N - 1, 0, -2):
        if col <= 6:
            col -= 1
        while True:
            for c in (col, col - 1):
                if qr.modules[row][c] is None:
                    positions.append((row, c))
            row += step
            if row < 0 or row >= N:
                row -= step
                step = -step
                break
    return positions[:172 * 8]


def measure(path):
    image = cv2.imread(str(path))
    corners = np.float32([[198, 758], [2107, 750], [2169, 2670], [173, 2698]])
    target = np.float32([[0, 0], [N*SCALE, 0], [N*SCALE, N*SCALE], [0, N*SCALE]])
    h = cv2.getPerspectiveTransform(corners, target)
    image = cv2.warpPerspective(image, h, (N*SCALE, N*SCALE))
    a = cv2.cvtColor(image, cv2.COLOR_BGR2RGB).astype(np.float32)
    gray = a.mean(2)
    mean7 = cv2.blur(gray, (7, 7))
    std7 = np.sqrt(np.maximum(0, cv2.blur(gray*gray, (7, 7)) - mean7*mean7))
    chroma = a.max(2) - a.min(2)
    white = (mean7 > 160) & (std7 < 12) & (cv2.blur(chroma, (7, 7)) < 20)
    mean15 = cv2.blur(gray, (15, 15))
    std15 = np.sqrt(np.maximum(0, cv2.blur(gray*gray, (15, 15)) - mean15*mean15))
    ch15 = cv2.blur(chroma, (15, 15))
    black = (mean7 < 100) & (std15 < 3.5) & (ch15 < 7)
    bits = np.full((N, N), -1, dtype=int)
    for r in range(N):
        for c in range(N):
            sl = (slice(r*SCALE + 7, r*SCALE + 33), slice(c*SCALE + 7, c*SCALE + 33))
            w, b = int(white[sl].sum()), int(black[sl].sum())
            if max(w, b) > 25 and min(w, b) < max(w, b)*0.1:
                bits[r, c] = int(b > w)
    initial = int((bits >= 0).sum())
    smoothed = cv2.GaussianBlur(gray, (7, 7), 2)
    smooth_mean = cv2.blur(smoothed, (15, 15))
    smooth_std = np.sqrt(np.maximum(0, cv2.blur(smoothed*smoothed, (15, 15)) - smooth_mean**2))
    ink = (mean15 < 100) & (mean15 > 18) & (ch15 < mean15*0.18) & (smooth_std < 5)
    added = 0
    for r in range(N):
        for c in range(N):
            sl = (slice(r*SCALE + 12, r*SCALE + 28), slice(c*SCALE + 12, c*SCALE + 28))
            if bits[r, c] < 0 and ink[sl].sum() > 50:
                bits[r, c] = 1
                added += 1
    # This patch is a tea fragment, not a reliable measurement of the paper.
    bits[19, 36] = -1
    print(f"initial={initial}, additional={added}")
    return bits


def encode(payload):
    blocks = base.rs_blocks(6, ECC)
    dc, ec, offset = [], [], 0
    codec = reedsolo.RSCodec(24)
    for block in blocks:
        part = payload[offset:offset + block.data_count]
        offset += block.data_count
        encoded = codec.encode(part)
        dc.append(part)
        ec.append(encoded[block.data_count:])
    return [v[j] for j in range(19) for v in dc] + [v[j] for j in range(24) for v in ec]


def generator():
    rows = [0] * (172*8)
    for i in range(K):
        payload = [0] * (K//8)
        payload[i//8] = 1 << (7 - i%8)
        for j, byte in enumerate(encode(payload)):
            for b in range(8):
                if byte >> (7 - b) & 1:
                    rows[j*8 + b] |= 1 << i
    return rows


def affine(equations):
    pivots = {}
    for coeff, rhs in equations:
        while coeff:
            p = coeff.bit_length() - 1
            if p not in pivots:
                pivots[p] = (coeff, rhs)
                break
            other, value = pivots[p]
            coeff ^= other
            rhs ^= value
        if not coeff and rhs:
            raise ValueError("Inconsistent image observations")
    free = [i for i in range(K) if i not in pivots]
    expressions = {i: 1 << j for j, i in enumerate(free)}
    constants = {i: 0 for i in free}
    for p, (coeff, rhs) in sorted(pivots.items()):
        expression, value = 0, rhs
        for i in range(p):
            if coeff >> i & 1:
                expression ^= expressions[i]
                value ^= constants[i]
        expressions[p], constants[p] = expression, value
    print(f"rank={len(pivots)}/{K}, free={len(free)}")
    return free, expressions, constants


def main():
    path = Path(sys.argv[1])
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == '3dd091c6a6e2a0c4a53c650f6d931ad0a693fbc2d6e200a315d0440e70ef6803'
    bits, positions, rows = measure(path), data_positions(), generator()
    mask = util.mask_func(MASK)
    equations = [(rows[i], int(bits[r, c]) ^ int(mask(r, c)))
                 for i, (r, c) in enumerate(positions) if bits[r, c] >= 0]
    free, expressions, constants = affine(equations)
    candidates = []
    for choice in range(1 << len(free)):
        values = [constants[i] ^ ((expressions[i] & choice).bit_count() & 1) for i in range(K)]
        payload = bytes(sum(values[j*8 + b] << (7-b) for b in range(8)) for j in range(K//8))
        raw = int.from_bytes(payload, 'big')
        mode, length = raw >> (K-4), (raw >> (K-12)) & 255
        if mode != 4 or length > (K-12)//8:
            continue
        text = bytes((raw >> (K-12-8*(j+1))) & 255 for j in range(length))
        if all(32 <= ch < 127 for ch in text):
            candidates.append((payload, text))
    print(f"printable candidates={len(candidates)}")
    assert len(candidates) == 1
    payload, text = candidates[0]
    print(text.decode('ascii'))
    print(f"tail={payload[-5:].hex()}")
    qr = template()
    qr.map_data(encode(list(payload)), MASK)
    pixels = np.pad(255*(1-np.array(qr.modules, dtype=np.uint8)), 4, constant_values=255)
    image = Image.fromarray(pixels).resize((980, 980), Image.Resampling.NEAREST)
    image.save('recovered_qr.png')
    zx = zxingcpp.read_barcode(image).text
    cv = cv2.QRCodeDetector().detectAndDecode(np.asarray(image))[0]
    assert zx == cv == text.decode('ascii')
    print('ZXing/OpenCV: match')


if __name__ == '__main__':
    main()
```

Output:

```text
initial=699, additional=120
rank=600/608, free=8
printable candidates=1
FortID{1_Sw3ar_70_Sp1ll_7h3_T3a_Th3_Wh0l3_Te3_4nd_N0thin6_Bu7_7h3_T34}
tail=d000ec11ec
ZXing/OpenCV: match
```

Script dựng lại QR từ payload tìm được và kiểm tra bằng ZXing cùng OpenCV. Việc hai decoder khớp là kiểm tra cục bộ của mã đã khôi phục; cơ sở chọn payload vẫn là các phép đo từ ảnh, hệ Reed–Solomon và điều kiện ASCII nêu trên.

![QR đã khôi phục](images/spill-the-tea-recovered.png)

## Kết quả

```text
FortID{1_Sw3ar_70_Sp1ll_7h3_T3a_Th3_Wh0l3_Te3_4nd_N0thin6_Bu7_7h3_T34}
```

Giữ nguyên `Te3`, `N0thin6` và `T34` như dữ liệu giải mã, không chuẩn hóa theo cách viết tiếng Anh. Không lưu phản hồi submission của nền tảng.
