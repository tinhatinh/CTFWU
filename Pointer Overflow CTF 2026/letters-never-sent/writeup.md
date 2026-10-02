# Letters Never Sent - Crypto

**Điểm:** 95 · **Lượt giải (Solves):** 248 
**Cờ:** `POCTF{2.612.ORSMSQU6A7IQJGUC.PQ4FI6SPWLYJYQGBQK66AWTILP}`

**File cung cấp:** `files/letter.png` (kích thước 1.150.873 byte, mã băm sha256 `907275df295c975e...`)

## Đề bài

Người chơi được cung cấp một bức thư viết tay thuộc về di sản của Tiến sĩ H. Aldous Whitmore, bức thư này được cho là chưa từng được gửi đi. Đi kèm với nó là một thông điệp vô cùng bí ẩn. Nhiệm vụ của bạn: Tìm ra chìa khoá (key) đang bị ẩn giấu trong bức thư, từ đó giải mã và đọc được những nội dung thầm kín mà Whitmore không bao giờ muốn gửi. 
Chuỗi mã hoá (ciphertext) hiển thị trên hệ thống là:

```text
PXYWN{2.612.QNTOXCK6E7DKGMKC.WK4KK6MPPPRJGOFZZI66EISSED}
```

## Phân tích ban đầu

Bức thư viết tay được gửi tới "Admiral Sir Francis Beaufort, K.C.B., Hydrographer to the Navy" và được ký tên Whitmore dưới danh nghĩa thành viên (Fellow) của hội Liminal Society for Spectral Fellowship, đề ngày tháng 11 năm 1887. 
Điểm mấu chốt nằm ở câu chốt hạ của bức thư, trực tiếp nhắc đến phương pháp mật mã của chính người nhận: "that reciprocal tableau which bears your name and which I have employed these many years in matters requiring discretion" (tạm dịch: *bức bình phong nghịch đảo mang tên ngài mà tôi đã dùng ngần ấy năm trong những vấn đề cần sự kín kẽ*). "Bức bình phong mang tên Beaufort" chính là hệ mật mã Beaufort - một hệ mã tự nghịch đảo nổi tiếng, nơi mà cả hai quá trình mã hoá và giải mã đều sử dụng chung một công thức duy nhất: `c = k - p (mod 26)`.

Có thể kiểm chứng ngay lập tức giả thuyết này bằng cách dựa vào một chân lý: cờ bắt buộc phải bắt đầu bằng chuỗi `POCTF{`. Nếu thử đảo ngược ba hệ mật mã phổ biến cùng dùng bảng chữ cái 26 ký tự:

| Phép toán | Khoá (Key) suy ngược từ `PXYWN` -> `POCTF` |
| --- | --- |
| Beaufort (`p = k - c`) | `ELAPS` |
| Vigenère (`p = c - k`) | `AJWDI` |
| Variant Beaufort (`p = c + k`) | `AREXS` |

Trong số đó, chỉ có chuỗi `ELAPS` mới trông giống như khởi đầu của một từ tiếng Anh có nghĩa, và tuyệt vời thay, nó trùng khớp hoàn hảo với chìa khoá lấy được từ đường viền khung tranh (sẽ phân tích ở Bước 2). Hệ mã Porta bị loại ngay từ vòng gửi xe, bởi theo luật của Porta, nếu ký tự gốc là `P` thì ký tự mã hoá ở nửa trên bảng không thể nào trả về đúng chữ `P` được.

Quan sát đường viền khung tranh, ta thấy nó được trang trí bởi 24 nhãn dán (chia đều 6 nhãn mỗi cạnh) mang từ vựng tiếng Anh chủ đề tên loài hoa, tên loài chim và một số vật dụng. Nổi bật nhất là 6 nhãn dán được in màu đỏ sẫm, đi kèm với một biểu tượng ngôi sao màu đỏ.

## Chuỗi khai thác

**Bước 1 - Chốt chặn hệ mật mã.** 
Sử dụng phần tiền tố `POCTF{` đã biết chắc chắn, ta dễ dàng suy ngược ra đoạn đầu của khoá là `key[0..4] = ELAPS` nhờ vào thuật toán Beaufort (trên hệ 26 chữ cái). Sự trùng khớp của 5 ký tự này từ hai nguồn dữ kiện hoàn toàn độc lập (phần tiền tố cờ và nhãn dán ở khung viền) là bằng chứng đanh thép loại bỏ mọi nghi ngờ về các hệ mật mã khác.

**Bước 2 - Lục tìm chìa khoá qua phân tích điểm ảnh (Pixel Analysis).** 
Thay vì căng mắt dò bằng tay, ta có thể tự động hoá việc đọc key. Bằng cách áp dụng bộ lọc độ lệch màu sắc theo công thức `R - (G+B)/2 >= 45`, ta tách được chính xác các vùng màu đỏ sẫm (gồm các ngôi sao và các nhãn được đánh dấu), đồng thời loại bỏ thành công phần nền giấy màu kem (chỉ đạt điểm 39). Kế tiếp, sử dụng hàm gom cụm `scipy.ndimage.label`, ta sàng lọc những cụm có diện tích >= 40 pixel và gán chúng vào 6 khe vị trí (slot) trên các cạnh dựa vào toạ độ tâm. 
Một phát hiện thú vị là: các nhãn thường (không sao) chỉ cao từ 6 đến 10 pixel; trong khi nhãn có sao cao từ 11 đến 22 pixel do bị ngôi sao chiếm thêm không gian chiều dọc. Kết quả phân tích trả về 6 vị trí đắc địa: top 1, top 4, right 1, bottom 4, bottom 0, và left 1.

**Bước 3 - Quét theo chiều kim đồng hồ.** 
Bắt đầu từ góc trên cùng bên trái: cạnh trên (top) quét từ trái sang phải, cạnh phải (right) quét từ trên xuống dưới, cạnh dưới (bottom) quét từ phải sang trái, và cạnh trái (left) quét từ dưới lên trên. Sáu nhãn được đánh dấu màu đỏ xuất hiện theo đúng trình tự là: **E**lder, **L**ily, **A**nchor, **P**oppy, **S**wan, **E**lder. Ráp các chữ cái đầu tiên lại, ta có chìa khoá hoàn chỉnh: `ELAPSE`.

**Bước 4 - Giải mã đoạn thân cờ (Token Decode).** 
Chạy thuật toán Beaufort kết hợp khoá `ELAPSE` (lưu ý khoá chỉ dịch chuyển vị trí khi gặp chữ cái), đoạn mã hoá sẽ bung ra thành:
`POCTF{2.612.ORSMSQU6A7IQJGUC.PQ4FI6SPWLYJYQGBQK66AWTILP}`

Phần thân cờ trông chẳng khác nào một mớ ký tự lộn xộn, hoàn toàn không phải là tiếng Anh. Mọi nỗ lực ép buộc nó thành một câu chữ có ý nghĩa (dựa trên các giả thuyết bị loại) đều chìm vào bế tắc. Mãi đến khi giải nghiệm bài tập `read-me-my-fortune` sau đó, bức màn bí ẩn mới được vén lên: hàm sinh cờ `_build_marker()` trong mã nguồn của hệ thống máy chủ đã ép cờ theo khuôn dạng tiêu chuẩn `POCTF{<cid>.<team_id>.<nonce>.<sig26>}`.
Đối chiếu với kết quả thu được: `2.612.ORSMSQU6A7IQJGUC.PQ4FI6SPWLYJYQGBQK66AWTILP`, ta thấy nó khớp từng milimet: `cid=2`, `team_id=612`, theo sau là chuỗi ngẫu nhiên (nonce) 16 ký tự, và cuối cùng là 26 ký tự mã băm HMAC định dạng base32. 
Hệ quả tất yếu: thân cờ thực chất là một chuỗi token cấp phát riêng cho từng đội chơi chứ không phải là một thông điệp ẩn. Việc ta "không thể đọc hiểu" nó không phải là do dùng sai khoá, mà đó chính là bản chất thực sự của lá cờ. Khớp với bộ quy tắc tịnh tiến khoá (advance key), chỉ có quy tắc "chữ cái mới đếm" mới bảo toàn được phần tiền tố `POCTF{`.

## Flag

```text
POCTF{2.612.ORSMSQU6A7IQJGUC.PQ4FI6SPWLYJYQGBQK66AWTILP}
```

Kết quả đã nộp và được hệ thống ghi nhận. Không cần thiết phải thử lại phiên bản chữ thường.

## Phục dựng (Reproduce)

```bash
cd letters-never-sent
python exploit.py
```

Đoạn kịch bản (script) sẽ tự động đo đạc hình ảnh để dựng lại chìa khoá, hiển thị dòng thông báo `key from border: ELAPSE` và in ra danh sách các ứng viên được giải bằng mã Beaufort, trong đó phiên bản dùng `ELAPSE` sẽ mang tiền tố chuẩn `POCTF{`. Nếu muốn giải mã một đoạn ciphertext của đội khác, chỉ cần chạy:

```bash
python exploit.py files/letter.png "PXYWN{...}"
```
