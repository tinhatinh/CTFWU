---
title: "Human RNG"
category: "Crypto"
tags: ["human-randomness", "qr-code", "keystream-recovery", "statistical-analysis", "opencv"]
solve_date: "2026-10-10"
language: "vi"
---

# Human RNG

**Flag:** `FortID{humans_are_not_good_random_number_generators}`
**Artifact:** `handout.zip` (2.5 KB) và một video trên Google Drive (`https://drive.google.com/file/d/1Tsh7dtCGCfWhUliPvIkmd0bUo9f5XCvo/view`). Không có instancer. Tác giả: ipaljak, laragrr.

## Đề bài

Bài chỉ phát artifact, không có service. `handout.zip` (2.5 KB) đi kèm một video trên Google Drive ghi lại cách mảng mô-đun QR được tạo; video là nguồn duy nhất cho phần dữ liệu người.

Điểm cốt lõi của đề: pattern mô-đun của mã QR không do một thư viện QR sinh ra mà do người thật đánh ra. Dãy bit dẫn xuất từ pattern đó vì vậy không phải mẫu của một PRNG, và có thể bị đảo ngược bằng thống kê hành vi. Bài này không công bố mô hình sinh; mọi ràng buộc bên dưới lấy từ phép đo trên artifact.

## Phân tích

### Hai thống kê định hình bài toán

Với một dãy bit, bản ghi dùng hai đại lượng: tần suất bit `1`, và tần suất giá trị đổi giữa hai vị trí kề nhau (`flip`).

```python
def stats(bits):
    """P(1) and the rate of flips between adjacent positions."""
    p1 = sum(bits) / len(bits)
    flip = sum(a != b for a, b in zip(bits, bits[1:])) / (len(bits) - 1)
    return p1, flip


recovered = (0.4848, 0.7238)   # statistics of the recovered keystream
human = (0.4747, 0.7017)       # statistics measured for human-produced bits

print("dP(1) :", round(recovered[0] - human[0], 4))
print("dflip :", round(recovered[1] - human[1], 4))
print("flip expectation for independent fair bits: 0.5")
```

```text
dP(1) : 0.0101
dflip : 0.0221
flip expectation for independent fair bits: 0.5
```

Keystream khôi phục được đo có `P(1) = 0.4848` và `flip = 0.7238`; hai giá trị hành vi người đo được để so sánh là `0.4747` và `0.7017`. Khoảng cách lần lượt là 0.0101 và 0.0221, tức cặp số liệu khôi phục nằm sát mô hình người.

Phần số học của `flip` mới là chỗ bài mở ra: nếu các bit độc lập và cân bằng thì xác suất lật giá trị giữa hai vị trí kề nhau là `2pq = 0.5`. Giá trị 0.7238 (và 0.7017 của mẫu người) lệch rất xa 0.5, nghĩa là dãy bit lật giá trị quá thường xuyên — đúng thiên kiến phổ biến khi người được yêu cầu "đánh ngẫu nhiên". Chuỗi nguồn là sản phẩm của người, nên phần còn lại của bài là bài toán ước lượng thống kê trên một không gian ứng viên hữu hạn, không phải bài toán giải mã dưới khoá bí mật.

### Quét không gian ứng viên

Phần bit không bị các điểm neo khoá lại (các vị trí giữa token) được vét cạn: 45.8M ứng viên. Mỗi ứng viên được chấm bằng hai thống kê trên, chuẩn hoá thành z-score theo phân bố của mẫu hành vi người.

Kết quả của phép quét là một ứng viên cực tách rõ: `z = +14.77`, trong khi ứng viên kế tiếp dừng ở `+13.01` (khoảng cách 1.76). Đây là căn cứ để chọn, không phải căn cứ để kết luận.

## Lời giải

Ứng viên thắng được dùng để dựng lại ma trận và ciphertext; pipeline xác minh in ra các trường đánh số. Dòng verify được ghi nguyên văn như sau, trong đó dấu `…` là phần bị lược của chính bản ghi và các trường `1)`, `3)` không có trong bản ghi:

```text
2) anchors : 522/522 … 4) reconstruct ct : True | 5) OpenCV QR read : 'FortID{humans_are_not_good_random_number_generators}' | FLAG = FortID{humans_are_not_good_random_number_generators}
```

Ba trường đã lưu mang ý nghĩa:

- `anchors : 522/522` — toàn bộ 522 điểm neo của ma trận dựng lại khớp với ràng buộc lấy từ artifact.
- `reconstruct ct : True` — ciphertext tái dựng đạt ràng buộc tự kiểm của nó.
- `OpenCV QR read` — một bộ giải mã QR đọc ma trận vừa dựng và trả về đúng xâu cờ. Đây là bước quan trọng nhất về mặt bằng chứng: nó không dùng z-score, nhưng đầu vào QR vẫn được dựng từ ứng viên đã chọn bằng mô hình hành vi.

Dạng gọi API của bước `5)`:

```python
import cv2

det = cv2.QRCodeDetector()
text, points, straight = det.detectAndDecode(matrix)   # matrix: uint8 ndarray of the rebuilt pattern
print(text)
```

## Kết quả

```text
FortID{humans_are_not_good_random_number_generators}
```

Cờ được chép từ output QR đã lưu. Thiếu ma trận, ciphertext và solver quét nên chưa thể tái hiện phép suy luận thống kê từ thư mục này; không có phản hồi submission được lưu.

## Tái hiện

Cần `handout.zip`, video đề dẫn, Python 3 với `numpy` và `opencv-python` (API `cv2.QRCodeDetector`).

1. Lấy dãy bit nguồn từ artifact/video.
2. Tính hai thống kê và khoảng cách tới mẫu người — block `python` trong mục Phân tích chạy độc lập trên các hằng số đã ghi nhận và in ra đúng ba dòng output kèm theo.
3. Vét cạn các vị trí giữa token (45.8M ứng viên), chuẩn hoá điểm thành z-score theo phân bố hành vi người, chọn ứng viên cực trị (`+14.77`).
4. Dựng lại ma trận và ciphertext từ ứng viên đã chọn; kiểm 522 điểm neo và ràng buộc tái dựng.
5. Đọc ma trận bằng block `python` của bước `5)`; xâu in ra là cờ.

Các bước 1, 3, 4 thao tác trực tiếp trên `handout.zip` và video; bản ghi của bài chỉ lưu các con số đo được (0.4848 / 0.7238, 0.4747 / 0.7017, 45.8M ứng viên, +14.77 / +13.01, 522/522) và dòng verify, không lưu script của phép quét, nên phần tái hiện đầy đủ các bước này phải dựng lại từ chính artifact. Phép quét 45.8M ứng viên là phần tốn thời gian nhất; nó chạy cục bộ và không chạm vào dịch vụ nào.
