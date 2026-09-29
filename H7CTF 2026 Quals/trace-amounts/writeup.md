# Trace Amounts — Hardware (Medium)

**Flag:** `H7CTF{48333086-d56b-41f5-b24b-a1d53fb122ec}` · Khoá AES-128 của card: `f937e70cf8f9f6f287a14b0da829ba47`

## Đề bài

Một thẻ không tiếp xúc chạy AES-128 để phê duyệt mỗi lần quẹt. Người ta kẹp probe dòng vào đường nguồn
và ghi lại 500 lần phê duyệt, kèm plaintext challenge biết trước của từng lần. Khoá không bao giờ rời
chip - nhưng dấu vết điện của nó thì có. Cho ba file: `traces.npy` (500×700), `plaintexts.npy` (500×16)
và `secret.enc` (48 B, đúng 3 block AES-ECB). Việc cần làm: recovery khoá, rồigiải mã `secret.enc`.

## Phân tích ban đầu

Trang challenge là một `SimpleHTTP` của Python, liệt kê thẳng ba tài nguyên, nên không có gì phải dò route.
Vào việc chính: Correlation Power Analysis (CPA) trên vòng đầu của AES.

Với byte plaintext thứ `i`, mỗi khoá thử `k` cho một giá trị trung gian dự đoán `S-box[pt_i ^ k]`.
Nếu chip rò rỉ theo mô hình Hamming, mẫu ứng dụng `HW(S-box[pt_i ^ k])` sẽ tương quan mạnh với đúng
sample nơi phép biến đổi đó diễn ra, và chỉ với `k` đúng.

Chuẩn hoá dữ liệu:

```
traces     (500, 700) float32   mean 0.06, std ~1.0
plaintexts (500, 16)  uint8
```

Với 500 trace, hệ số tương quan của nhiễu thuần có độ lệch chuẩn `1/sqrt(500) = 0.045`;
chiếu theo số lần thử (16 byte × 256 khoá × 700 sample) thì đỉnh ngẫu nhiên lớn nhất rơi vào khoảng 0.21.
Con số này là thước để biết khi nào có tín hiệu thật - và nó chính là thứ làm bài này thú vị,
bởi lần chạy đầu tiên của mình cho đúng 0.21 ở mọi nơi.

## Các hướng đã loại

1. Trace lệch pha (jitter) - giả thuyết phổ biến nhất khi CPA không ra gì. Kiểm chứng bằng cách
   cross-correlate từng trace với trace trung bình: shift tối ưu bằng 0 cho cả 500 trace, std 0.0.
2. Chip có masking bậc 1 - khi đó không có rò rỉ bậc 1 mà phải tổ hợp hai sample. Probe bằng tương quan
   của trace với `HW(pt_i ^ pt_j)` cho mọi cặp byte: tối đa 0.195, vẫn là nền noise.
3. Sai điểm thời gian - có thật, nhưng không phải do lệch pha; xem Bước 2.
4. Sai mô hình rò rỉ - thử `HW(pt^k)`, `pt^k`, `S[pt^k]`, `LSB`: tất cả bám nền 0.19-0.22.

Hoá ra nguyên nhân sâu hơn: code của mình sai, không phải dữ liệu. Bảng trọng số Hamming được dựng dạng
`hw = popcount(sbox[v])` rồi lại tra `hw[S-box[pt^k]]`, tức tính `popcount(S-box[S-box[pt^k]])` - hai lần S-box.
Mô hình dự đoán khi đó không tương quan với bất kỳ thứ gì, nên mọi byte đều trả đúng mức nền noise.
Đây là bẫy rất dễ gặp: |r| ~0.2 nhìn giống "tín hiệu yếu, cần thêm trace", trong khi thực chất là "mô hình vô nghĩa".

## Chuỗi khai thác

**Bước 1 - Đọc cấu trúc thời gian của trace.** Phổ năng lượng theo sample (`mean trace` và `variance profile`)
lộ một mẫu tuần tự rất sạch: các đỉnh tại sample 30, 70, 110, ..., 630 - 16 đỉnh cách đều 40 sample.
16 đỉnh = 16 byte, tức chip xử lý tuần tự từng byte của state, byte `i` nằm trong slot `30 + 40*i`.
Thông tin này nói cho ta biết phải nhìn sample nào, và cũng là cách phát hiện mô hình sai: nếu có 16 khe
hoạt động rõ ràng mà tương quan vẫn bằng nền thì vấn đề nằm ở hàm dự đoán.

**Bước 2 - Sửa mô hình, quét lại theo slot.** `analysis/sweep.py` thử 6 mô hình × 16 byte × 256 khoá,
tính tương quan Pearson vector hoá trong từng slot. Kết quả phân tách dứt khoát:

```
byte  0 HW(S[xor])  k=0xf9  sample  30  |r|=0.731
byte  6 HW(S[xor])  k=0xf6  sample 270  |r|=0.740
byte 13 HW(S[xor])  k=0x29  sample 550  |r|=0.736
...
```

Mọi byte khác (15/16) cùng đạt 0.67-0.74, trong khi á quân của từng byte rơi về ~0.20.
Đỉnh thời gian trùng chính xác công thức slot - bằng chứng mô hình đã đúng chứ không phải ăn may thống kê.

**Bước 3 - Ghép khoá và giải mã.** 16 byte thu được `f937e70c f8f9f6f2 87a14b0d a829ba47`.
giải mã `secret.enc` bằng AES-128-ECB với khoá đó:

```
H7CTF{48333086-d56b-41f5-b24b-a1d53fb122ec}
```

48 B giải ra 43 B cờ + 5 byte `0x05` cuối (`pt[-5:] == 5*0x05`), tức PKCS#7 hợp lệ - thêm một lớp
xác nhận khoá đúng, vì chỉ cần sai một byte là 48 byte đầu ra thành rác không có padding.

**Bước 4 - Xác minh chéo.** Khoá được recover không cần `secret.enc`; nó chỉ là bài kiểm tra cuối.
Vì vậy mình giữ hai dấu hiệu độc lập: (a) 16/16 byte có |r| ~0.7 cách biệt tuyệt đối với á quân,
và (b) plaintextgiải mã ra chuỗi ASCII có khuôn UUID + padding hợp lệ. Một khoá sai lệch một byte sẽ cho
48 byte rác, không thể ra cấu trúc đó.

## Flag
```bash
python exploit.py files/traces.npy files/plaintexts.npy files/secret.enc
```

```
    byte  0: k=0xf9  |r|=0.731  runner-up |r|=0.199
    ...
    byte 15: k=0x47  |r|=0.673  runner-up |r|=0.197
[+] AES-128 key: f937e70cf8f9f6f287a14b0da829ba47
[+] decrypted: 'H7CTF{48333086-d56b-41f5-b24b-a1d53fb122ec}'
[+] flag: H7CTF{48333086-d56b-41f5-b24b-a1d53fb122ec}
```

Toàn trình chạy trong 0.35 s.
