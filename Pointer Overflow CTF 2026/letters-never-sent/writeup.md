# Letters Never Sent - Crypto

**Điểm:** 95 · **Solves khi làm:** 248 · **Cờ:** `POCTF{2.612.ORSMSQU6A7IQJGUC.PQ4FI6SPWLYJYQGBQK66AWTILP}`

**File cho trước:** `files/letter.png` 1.150.873 byte, sha256 `907275df295c975e...`

## Đề bài

Thư thu được từ di sản của Dr. H. Aldous Whitmore, chưa từng được gửi. Kèm theo thư là
một thông điệp lạ. Nhiệm vụ: tìm key mà bức thư giấu, rồi đọc nội dung Whitmore không
dự định gửi. Ciphertext trên thẻ đề:

```text
PXYWN{2.612.QNTOXCK6E7DKGMKC.WK4KK6MPPPRJGOFZZI66EISSED}
```

## Phân tích ban đầu

Bức thư viết tay gửi "Admiral Sir Francis Beaufort, K.C.B., Hydrographer to the Navy",
ký tên Whitmore với chức danh Fellow của Liminal Society for Spectral Fellowship, đề
November 1887. Câu chốt là đoạn nói về phương pháp của người nhận: "that reciprocal
tableau which bears your name and which I have employed these many years in matters
requiring discretion". Beaufort cipher đúng là một bảng tra tự nghịch đảo: mã hoá và
giải mã dùng cùng một công thức `c = k - p (mod 26)`.

Kiểm chứng ngay bằng dữ liệu đã biết: cờ phải bắt đầu bằng `POCTF{`. Thử ba họ cipher
dùng bảng tra trên alphabet 26 chữ:

| Phép | Key suy ra từ `PXYWN` -> `POCTF` |
| --- | --- |
| Beaufort `p = k - c` | `ELAPS` |
| Vigenère `p = c - k` | `AJWDI` |
| Variant Beaufort `p = c + k` | `AREXS` |

Chỉ `ELAPS` là mở đầu của một thứ có nghĩa, và nó trùng với key lấy từ khung viền (Bước 2).
Porta bị loại sớm: với Porta, chữ mã ở nửa trên bảng không thể là `P` nếu chữ gốc cũng là `P`.

Khung viền của ảnh có 24 nhãn (6 mỗi cạnh) bằng tiếng Anh: tên hoa, tên chim và vật dụng.
Sáu nhãn in màu đỏ sẫm và có ngôi sao đỏ kèm theo.

## Các giả thuyết đã loại trừ

- Ảnh chứa dữ liệu ẩn: không có byte sau IEND, không có chunk tEXt/zTXt/iTXt, IDAT giải
  nén hết không dư byte nào, tỉ lệ bit thấp ba kênh 0.4933 / 0.5036 / 0.4921 tức nhiễu
  chuẩn, `stegano.lsb.reveal` báo không thấy gì.
- Running key là chính bức thư: Beaufort running key đòi hỏi chuỗi key bắt đầu bằng
  `ELAPS`, mà văn bản thư (607 chữ cái, đã bỏ ký tự không phải chữ) không chứa `ELA`.
- Autokey và progressive Beaufort với key `ELAPSE`: cả ba biến thể đều ra rác.
- Lớp hoán vị sau khi giải mã: thân có đúng 36 chữ cái nên đã quét 720 hoán vị cột của
  lưới 6x6 theo cả hai thứ tự, rail fence độ sâu 2 đến 12 cả encode lẫn decode, spiral
  bốn biến thể, transpose lưới. Không ứng viên nào nhô lên về điểm quadgram.
- Key từ các nhãn không có sao: 18 nhãn không sao bằng đúng 36 chữ cái thân chia đôi,
  nhưng `RFSTPHWMDOVYCRLFST` không khớp prefix đã buộc ở trên.
- Key Beaufort tuần hoàn dài hơn: quét exhaust toàn bộ key độ dài 6, 7, 8, 9 với 5 chữ
  đầu cố định `ELAPS` (tổng 475k khoá, chấm điểm bằng quadgram dựng từ 370k từ tiếng
  Anh) và hill-climb cho 10 đến 16. Không khoá nào cho ra tiếng Anh.

Điểm cuối cùng này hoá ra không phải tín hiệu xấu, xem Bước 4.

## Chuỗi khai thác

**Bước 1 - Cố định cipher.** Dùng prefix `POCTF{` đã biết để suy ra `key[0..4] = ELAPS`
với Beaufort alphabet 26. Năm chữ cái khớp nhau giữa hai nguồn độc lập (prefix đã biết và
khung viền) loại mọi họ cipher khác.

**Bước 2 - Đọc key từ ảnh bằng pixel, không đọc bằng mắt.** Lọc theo độ lệch màu
`R - (G+B)/2 >= 45` tách được đúng các thành phần đỏ (sao và nhãn được đánh dấu), còn
màu giấy kem có điểm 39 nên bị loại. Gom cụm bằng `scipy.ndimage.label`, giữ cụm có
diện tích >= 40 px, gán mỗi cụm vào một trong 6 slot của cạnh dựa trên tâm cụm. Nhãn
không sao cao 6 đến 10 px; nhãn có sao cao 11 đến 22 px vì ngôi sao cộng thêm một khoảng
đứng. Sáu slot vượt ngưỡng: top 1, top 4, right 1, bottom 4, bottom 0, left 1.

**Bước 3 - Sắp theo chiều kim đồng hồ.** Đi từ góc trên-trái: top trái sang phải, right
trên xuống dưới, bottom phải sang trái, left dưới lên trên. Sáu nhãn gặp được theo thứ tự
đó là Elder, Lily, Anchor, Poppy, Swan, Elder, lấy chữ cái đầu cho `ELAPSE`.

**Bước 4 - Chấp nhận thân cờ không đọc được.** Beaufort với `ELAPSE` và key chỉ tiến khi
gặp chữ cái cho `POCTF{2.612.ORSMSQU6A7IQJGUC.PQ4FI6SPWLYJYQGBQK66AWTILP}`. Phần thân
không phải tiếng Anh, và mọi cố gắng làm nó thành tiếng Anh (các giả thuyết đã loại trừ)
đều thất bại. Bài read-me-my-fortune sau đó cho thấy lý do: `_build_marker()` trong source
của service sinh cờ theo khuôn `POCTF{<cid>.<team_id>.<nonce>.<sig26>}`. Đối chiếu lại thì
`2.612.ORSMSQU6A7IQJGUC.PQ4FI6SPWLYJYQGBQK66AWTILP` đúng là `cid=2`, `team_id=612`,
nonce 16 ký tự, và 26 ký tự base32 của HMAC. Thân cờ vì thế là token theo team chứ không
phải câu chữ, nên "không đọc được" là kết quả đúng chứ không phải bằng chứng sai key.
Trong số các quy tắc advance key, chỉ quy tắc "chữ cái mới đếm" giữ được prefix `POCTF{`.

## Cờ

```text
POCTF{2.612.ORSMSQU6A7IQJGUC.PQ4FI6SPWLYJYQGBQK66AWTILP}
```

Đã nộp và được chấp nhận. Bản chữ thường không cần thử lại.

## Chạy lại

```bash
cd letters-never-sent
python exploit.py
```

Script tự đo ảnh để dựng lại key, in ra `key from border: ELAPSE` rồi in các ứng viên
Beaufort, trong đó dòng `ELAPSE` mang prefix `POCTF{`. Muốn chạy với thẻ đề của team khác:

```bash
python exploit.py files/letter.png "PXYWN{...}"
```
