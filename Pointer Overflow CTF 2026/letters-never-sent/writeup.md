# Letters Never Sent - Crypto

**Điểm:** 95 · **Lượt giải (Solves):** 248 
**Cờ:** `POCTF{2.612.ORSMSQU6A7IQJGUC.PQ4FI6SPWLYJYQGBQK66AWTILP}`

**File cung cấp:** `files/letter.png` (kích thước 1.150.873 byte, mã băm sha256 `907275df295c975e...`)

## Đề bài

Nhiệm vụ của người chơi là phân tích một bức thư viết tay của nhân vật giả định H. Aldous Whitmore để xác định chìa khóa (key) giải mã đoạn thông điệp kèm theo.

Chuỗi mã hoá (ciphertext) được cung cấp:

```text
PXYWN{2.612.QNTOXCK6E7DKGMKC.WK4KK6MPPPRJGOFZZI66EISSED}
```

## Phân tích ban đầu

Bức thư được gửi tới "Admiral Sir Francis Beaufort, K.C.B., Hydrographer to the Navy" và được ký tên Whitmore thuộc Liminal Society for Spectral Fellowship. 
Câu cuối của bức thư đề cập đến phương pháp mã hóa của người nhận: "that reciprocal tableau which bears your name and which I have employed these many years in matters requiring discretion". Gợi ý này chỉ ra hệ mật mã Beaufort - hệ mã tự nghịch đảo (reciprocal), sử dụng chung công thức giải mã và mã hóa: `c = k - p (mod 26)`.

Có thể xác minh giả thuyết này dựa vào định dạng cờ yêu cầu bắt đầu bằng `POCTF{`. Khi kiểm tra ba hệ mã tương tự:

| Phương pháp | Khoá (Key) suy ngược từ `PXYWN` -> `POCTF` |
| --- | --- |
| Beaufort (`p = k - c`) | `ELAPS` |
| Vigenère (`p = c - k`) | `AJWDI` |
| Variant Beaufort (`p = c + k`) | `AREXS` |

Khoá thu được từ phương pháp Beaufort (`ELAPS`) tương tự khởi đầu của một từ tiếng Anh có nghĩa, và khớp với dữ liệu phân tích từ khung viền hình ảnh (chi tiết tại Bước 2). Hệ mã Porta không phù hợp vì nguyên tắc mã hóa của nó không thể tạo kết quả `P` -> `P`.

Đường viền bức ảnh có 24 nhãn dán (6 nhãn mỗi cạnh) chứa từ vựng tiếng Anh. Sáu nhãn được đánh dấu bằng ngôi sao màu đỏ sẫm.

## Quá trình phân tích

**Bước 1 - Xác định hệ mật mã.** 
Từ tiền tố `POCTF{`, áp dụng mã Beaufort để suy ngược 5 ký tự đầu của khóa là `ELAPS`. Sự trùng khớp giữa khóa suy ngược và dữ liệu trên khung ảnh cung cấp cơ sở để chọn phương pháp Beaufort.

**Bước 2 - Phân tích dữ liệu hình ảnh (Pixel Analysis).** 
Việc trích xuất thông tin khóa có thể được tự động hóa. Bằng cách thiết lập bộ lọc màu theo công thức `R - (G+B)/2 >= 45`, các vùng màu đỏ sẫm (ngôi sao và nhãn) được phân tách khỏi nền giấy màu kem (đạt điểm 39). Kết hợp hàm phân nhóm `scipy.ndimage.label`, các cụm diện tích >= 40 pixel được xác định và ánh xạ vào 6 vị trí trên khung dựa trên tọa độ tâm. 
Dữ liệu cho thấy các nhãn thông thường cao 6-10 pixel, trong khi nhãn có sao cao 11-22 pixel. Kết quả xác định 6 vị trí được đánh dấu: top 1, top 4, right 1, bottom 4, bottom 0, và left 1.

**Bước 3 - Trích xuất khóa.** 
Đọc dữ liệu theo chiều kim đồng hồ bắt đầu từ góc trên bên trái, thứ tự 6 nhãn được đánh dấu là: **E**lder, **L**ily, **A**nchor, **P**oppy, **S**wan, **E**lder. Ghép các chữ cái đầu tiên lại, khóa giải mã là: `ELAPSE`.

**Bước 4 - Giải mã đoạn thân cờ (Token Decode).** 
Áp dụng mã Beaufort với khóa `ELAPSE` (khóa chỉ dịch chuyển vị trí trên chữ cái), đoạn ciphertext trả về:
`POCTF{2.612.ORSMSQU6A7IQJGUC.PQ4FI6SPWLYJYQGBQK66AWTILP}`

Phần thân cờ không cấu thành chuỗi từ tiếng Anh có nghĩa. Dựa trên cơ chế cấp phát cờ được tiết lộ trong thử thách `read-me-my-fortune` sau đó, định dạng chuẩn của máy chủ là `POCTF{<cid>.<team_id>.<nonce>.<sig26>}`.
Phân tích kết quả: `cid=2`, `team_id=612`, `nonce` gồm 16 ký tự, và phần còn lại là 26 ký tự base32 của mã băm HMAC.
Do đó, thân cờ là một token cấp phát riêng biệt, không phải thông điệp văn bản tiếng Anh. Việc duy trì quy tắc "khóa chỉ tịnh tiến trên chữ cái" là điều kiện để giữ nguyên tiền tố `POCTF{`.

## Flag

```text
POCTF{2.612.ORSMSQU6A7IQJGUC.PQ4FI6SPWLYJYQGBQK66AWTILP}
```

Kết quả đã được nộp thành công trên hệ thống.

## Reproduce

```bash
cd letters-never-sent
python exploit.py
```

Công cụ tự động đánh giá kích thước pixel để trích xuất khóa, thông báo `key from border: ELAPSE` và in các kết quả giải mã dự tuyển (candidate). Phiên bản dùng mã Beaufort kết hợp khóa `ELAPSE` sẽ tạo tiền tố `POCTF{`. Để giải mã chuỗi từ các tập dữ liệu khác, chạy lệnh:

```bash
python exploit.py files/letter.png "PXYWN{...}"
```
