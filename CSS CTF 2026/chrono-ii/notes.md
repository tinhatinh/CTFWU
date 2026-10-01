# Notes - chrono-ii

## Bối cảnh lấy dữ liệu

`curl` và socket Python đều không tới được `34.116.80.78:8001` (SYN drop, timeout 8/12/30s),
trong khi `example.com:80` và `1.1.1.1:443` mở tức thì. Browser thì tải được trang.
Toàn bộ capture lấy qua `browser-use`: `evaluate_script` đọc biến `capture` mà chính
`app.js` đã fetch từ `/api/feed`. `fetch()` gọi trực tiếp trong page bị CSP chặn
("Failed to fetch"), điều hướng thẳng tới `/capture.json` cũng ERR_FAILED.

Trang có: đồng hồ UTC, `TRANSMISSION RATE 1 Hz`, `CAPTURE WINDOW 60 seconds`,
log 60 dòng `timestamp + ciphertext`, và `/api/feed` trả đúng 60 bản ghi.

## H1 - plaintext có đổi không

Observation: mọi dòng có cùng khuôn `-UUUUUU{lll_lllll_...}` và chữ số xuất hiện ở
đúng những vị trí giống nhau trên cả 120 dòng.
Evidence: `analysis/rows.txt` đối chiếu `analysis/feed2.txt`.
result: PENDING -> sau thành CONFIRMED. Plaintext cố định, chỉ key đổi.

## H2 - Vigenère key lặp, offset quay theo giây

Giả thuyết: `o(T) = (T + c) mod L`, key là một từ cố định độ dài L.
Test 1: nếu đúng thì dòng giây T và T+1 phải chồng nhau đúng 5 ký tự
(`ki[1:] == kj[:5]`). Kết quả chỉ 43/60 cặp có kẻ kế, 17 cặp không có.
Test 2: độ dài 4-gram distinct = 77 > mọi L nhỏ.
result: DEAD - offset không tiến 1 mỗi giây.

## H3 - chu kỳ của keystream

Observation: cùng một ciphertext xuất hiện ở hai thời điểm khác nhau.
Đo trên hai cửa sổ A (06:38:27-06:39:26) và B (07:00:51-07:01:50):
43 ciphertext chung, và delta thời gian của chúng chỉ nhận đúng hai giá trị
1309 = 17 x 77 và 1386 = 18 x 77.
Suy ra: `o(t + 77) = o(t)`, chu kỳ 77 (ước chung lớn nhất của 1309 và 1386 là 77;
L >= 60 vì một cửa sổ 60 giây cho 60 offset phân biệt).
result: CONFIRMED - L = 77.

## H4 - bước nhảy mỗi giây

Test: với mọi cặp dòng phát hiện được độ dịch `d` (1..5) giữa hai cửa sổ,
hồi quy `d == (g * dt) mod 77` cho g chạy hết 1..76.
Kết quả: g = 43 khớp 460/965 cặp, trong khi nền ngẫu nhiên chỉ ~965/77 = 12.5.
result: CONFIRMED - `o(T) = (43 * T) mod 77`.

## H5 - ký tự không bị mã hoá có ăn chỉ số key không

Test: giải mã toàn bộ 120 dòng với hai biến thể.
- `advance_all=True` (`_ { }` cũng tiến chỉ số): 120 dòng ra 77 plaintext khác nhau.
- `advance_all=False` (chỉ tiến ở ký tự bị mã hoá): 120 dòng ra đúng 1 plaintext.
result: CONFIRMED - `advance_all=False`. Đây là mấu chốt; nếu sai bước này thì
kết quả trông như "mỗi giây một thông điệp khác nhau".

## H6 - bảng chữ

Test: chữ số dùng riêng mod 10 hay gộp chung mod 36 với chữ thường.
mod 36 cho ra `C22C3F{21e1e_...}`, vô nghĩa.
result: DEAD - chữ hoa/thường mod 26, chữ số mod 10, tách bảng.

## Kiểm chứng

- Dựng keystream từ 120 dòng: phủ đủ 77/77 residue, 0 conflict.
- Toàn bộ 180 dòng của ba cửa sổ giải mã về đúng một plaintext.
- Held-out: cửa sổ 07:09:46-07:10:45 (60 dòng, lấy sau khi đã chốt mô hình) giải mã
  bằng keystream huấn luyện từ hai cửa sổ đầu -> 60/60 ra cùng cờ.
