# Chrono II — Crypto (Intermediate)

**Flag:** `CSSCTF{th3_cl0ck_r3m3mb3rs_3very_s3c0nd}` · **Files:** không có artifact, dữ liệu lấy từ service đang chạy

## Đề bài

Đề cho một service `http://34.116.80.78:8001` và nói rằng đoạn chatter đã chặn được
"lần này có vẻ đổi liên tục". Người chơi phải lấy các bản mã từ service rồi suy lại
plaintext gốc. Chrono I (cùng bộ đôi) là bản dễ: key đúng là các chữ số của mốc thời
gian trong message, Vigenère số chu kỳ 14. Bản II giữ nguyên ý đó nhưng để key chạy
theo đồng hồ.

## Phân tích ban đầu

Trang chủ là một "đài thu" liệt kê sẵn endpoint: `/api/feed` trả 60 bản ghi
`{timestamp, ciphertext}`, một bản cho mỗi giây, `/capture.json` là bản 60 giây đã lưu.

Nhìn vào 60 dòng thấy ngay hai điều:

- Mật văn luôn có dạng `UUUUUU{lll_lllll_lllllllll_lllll_llllll}`. Chữ số luôn rơi vào
  cùng một tập vị trí trên mọi dòng. Nếu plaintext đổi thì không có lý gì khuôn lại
  bất biến như vậy, nên plaintext là cố định, chỉ key đổi theo giây.
- `_ { }` xuất hiện y nguyên ở vị trí cố định, tức các ký tự này đi qua không bị mã hoá.

Ba bảng chữ tách rời: chữ hoa mod 26, chữ thường mod 26, chữ số mod 10.

Vì plaintext cố định và format cờ đã biết, sáu ký tự đầu luôn là `CSSCTF`. Đó là crib
sẵn: mỗi dòng lộ ra 6 symbol của keystream.

## Các hướng đã loại

1. **Key là một từ cố định, offset quay theo giây (`o = T + c`)**: nếu đúng thì hai dòng
   ở giây liên tiếp phải chồng khít 5 ký tự (`ki[1:] == kj[:5]`). Chỉ 43/60 cặp có kẻ kế,
   17 cặp không có. Loại.
2. **Dựng keystream bằng cách đặt mỗi dòng tại đúng giây của nó rồi gấp theo chu kỳ**:
   phủ đủ 77 residue nhưng sinh ra 8 chỗ mâu thuẫn value, và giải mã ra 77 plaintext
   khác nhau. Loại vì giả định bước nhảy sai.
3. **Cho `_ { }` cũng tiến chỉ số key**: 120 dòng cho 77 plaintext khác nhau, trông rất
   giống "mỗi giây một thông điệp". Đây là bẫy chính của bài. Loại.
4. **Gộp chữ thường và chữ số vào một bảng mod 36**: ra `C22C3F{21e1e_ee1e101a...}`,
   vô nghĩa. Loại.

## Chuỗi khai thác

**Bước 1 — Lấy nhiều cửa sổ capture.** `curl` và socket Python không tới được host
(SYN bị drop, timeout 8/12/30s, trong khi `example.com:80` mở tức thì). Browser thì
được, nên lấy số liệu từ trong page: `app.js` giữ kết quả fetch ở biến `capture`.

```js
capture.map(r => r.timestamp + ' ' + r.ciphertext).join('\n')
```

Gọi `fetch('/api/feed')` từ trong page thì bị CSP chặn, điều hướng thẳng tới
`/capture.json` cũng ERR_FAILED. Đọc biến `capture` của app là đường sạch nhất.

**Bước 2 — Tìm chu kỳ của keystream.** So hai cửa sổ A (06:38:27-06:39:26) và
B (07:00:51-07:01:50): có 43 ciphertext chung, và delta thời gian của chúng chỉ nhận
đúng hai giá trị, 1309 và 1386 giây.

```
1309 = 17 * 77
1386 = 18 * 77
gcd(1309, 1386) = 77
```

Vậy `o(t + 77) = o(t)`, chu kỳ 77. Con số 77 cũng khớp với việc một cửa sổ 60 giây
có 17 dòng không tìm được kẻ kế: 77 - 60 = 17 offset trống.

**Bước 3 — Tìm bước nhảy mỗi giây.** Với mọi cặp dòng mà cửa sổ 6 ký tự của chúng chồng
lên nhau được một độ dịch `d` nào đó (1..5), hồi quy `d == (g * dt) mod 77` cho `g` chạy
hết 1..76.

```
best step g = (43, 460)   # 460/965 cặp khớp, nền ngẫu nhiên chỉ ~12.5
```

Nên `o(T) = (43 * T) mod 77`.

**Bước 4 — Dựng keystream.** Mỗi dòng cho 6 symbol tại các vị trí `o(T) .. o(T)+5`.
120 dòng từ hai cửa sổ phủ đủ 77 vị trí và không có mâu thuẫn nào.

```python
K = {}
for T, ct in rows:
    base = (43 * T) % 77
    for j, (a, b) in enumerate(zip(ct[:6], "CSSCTF")):
        K[(base + j) % 77] = (ord(a) - 65 - (ord(b) - 65)) % 26
# -> 77/77 symbol, 0 conflict
```

**Bước 5 — Giải mã, và đây mới là chỗ quyết định.** Chỉ số key chỉ tiến khi gặp ký tự
thực sự bị mã hoá; `_ { }` được chép ra mà không ăn symbol nào.

```python
def dec(T, ct):
    i = 0; o = (43 * T) % 77; out = []
    for ch in ct:
        if ch in "_{}":
            out.append(ch); continue          # khong tang i
        base, m = (65,26) if ch.isupper() else (97,26) if ch.islower() else (48,10)
        out.append(chr(base + (ord(ch) - base - K[(o+i) % 77]) % m)); i += 1
    return "".join(out)
```

120 dòng hội tụ về đúng một plaintext.

**Bước 6 — Kiểm chứng trên dữ liệu chưa từng thấy.** Sau khi đã chốt mô hình, lấy thêm
cửa sổ 07:09:46-07:10:45 (60 dòng) rồi giải mã bằng keystream chỉ huấn luyện từ hai cửa sổ
đầu:

```
train rows=120  held-out rows=60
  n= 60/60  CSSCTF{th3_cl0ck_r3m3mb3rs_3very_s3c0nd}
```

Không một dòng nào lệch. Chu kỳ 77 cũng tự kiểm chứng thêm một lần: dòng
`HIWLWH{bp6_...}` ở 06:38:58 xuất hiện y hệt ở 07:09:46, chênh đúng 1848 = 24 x 77 giây.

## Flag

```bash
python exploit.py analysis/rows.txt analysis/feed2.txt
```

```
[*] 120 rows, 1 distinct plaintexts, best has 120
[flag] CSSCTF{th3_cl0ck_r3m3mb3rs_3very_s3c0nd}
```

## Reproduce

```bash
python exploit.py analysis/rows.txt analysis/feed2.txt
python exploit.py analysis/rows.txt analysis/feed2.txt analysis/feed3_clean.txt
```

Script tự assert rằng đủ 77 symbol keystream và rằng mọi dòng phải cho cùng một plaintext,
nên nó exit khác 0 nếu mô hình không còn đúng với capture mới.
