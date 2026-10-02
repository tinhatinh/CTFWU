# Trace Amounts — Hardware (Medium)

**Flag:** `H7CTF{48333086-d56b-41f5-b24b-a1d53fb122ec}`
**Khoá bí mật (AES-128) đào được:** `f937e70cf8f9f6f287a14b0da829ba47`

## Đề bài

Trò chơi xoay quanh một chiếc thẻ từ (thẻ không tiếp xúc) được nhúng bộ mã AES-128 để xét duyệt thao tác quẹt thẻ. Kẻ gian đã lén lút kẹp một thiết bị chọc (probe) đo dòng điện vào đường dây nguồn và thu lén được 500 lần thẻ nháy điện phê duyệt. Đi kèm với đống dữ liệu điện đó là các bản rõ thử thách (plaintext challenge) đã bị lộ của từng lần quẹt. 
Lưu ý: Khoá bảo mật chưa bao giờ lọt ra khỏi con chip - nhưng cái bóng (dấu vết điện) của nó thì đã phơi bày. 
Vũ khí được cấp gồm 3 file: `traces.npy` (chứa ma trận điện 500×700), `plaintexts.npy` (ma trận bản rõ 500×16) và tệp `secret.enc` (dài 48 B, khớp khít 3 khối AES-ECB). 
Sứ mệnh: Vét sạch (recovery) cái khoá đó, rồiquay sang mở toang (giải mã) cái `secret.enc`.

## Phân tích ban đầu

Mặt tiền chướng ngại vật thực chất chỉ là một máy chủ `SimpleHTTP` thuần túy bằng Python, liệt kê thẳng thừng 3 cục tài nguyên, nên chả cần tốn chất xám đi cày đường dẫn (route) làm gì. 
Điểm huyệt chí mạng: Triển khai ngón đòn Correlation Power Analysis (CPA - Phân tích năng lượng tương quan) phang thẳng vào vòng mã hoá đầu tiên của cỗ máy AES.

Nguyên lý: Với cái byte plaintext thứ `i`, ứng với mỗi cái khoá nháp `k`, ta sẽ tính ra được một mốc trung gian dự đoán `S-box[pt_i ^ k]`. 
Nếu cấu trúc con chip rò rỉ điện theo mô hình kinh điển Hamming, thì cái khuôn áp dụng `HW(S-box[pt_i ^ k])` sẽ tạo ra sức tương quan cực kỳ mãnh liệt đập thẳng vào đúng cái mẫu (sample) nơi phép biến đổi đó vừa lóe sáng. Và điều này CHỈ XẢY RA với cái `k` chuẩn xác.

Kiểm đếm quân số (Chuẩn hoá dữ liệu):

```text
Ma trận điện traces     (500, 700) định dạng float32   trị số mean 0.06, độ lệch std ~1.0
Ma trận rõ   plaintexts (500, 16)  định dạng uint8
```

Với vốn liếng 500 vết điện (trace), hệ số tương quan của mớ nhiễu tạp (nhiễu thuần) sẽ sở hữu độ lệch chuẩn `1/sqrt(500) = 0.045`. 
Áp vào bài toán tính số nhịp đập (16 byte × 256 khoá × 700 sample), cái đỉnh nhiễu ngẫu nhiên bự nhất sẽ loanh quanh ở mốc 0.21. Cái mốc 0.21 này chính là cây thước ngắm sinh tử để ta phân định rạch ròi đâu là nhiễu, đâu là tín hiệu xịn. Và đây cũng chính là cú sốc (thú vị) của bài này, vì ngay ở cái lần quét móng đầu tiên, mọi ngóc ngách đều trổ ra đúng con số 0.21 nhạt nhẽo đó.

## Chuỗi khai thác

**Bước 1 - Lột trần phả hệ thời gian của dòng điện (trace).** 
Vác phổ năng lượng theo từng mẫu (`mean trace` và `variance profile`) ra soi, lòi ra ngay một cấu trúc nhịp điệu (mẫu tuần tự) sạch bóng: Các chóp đỉnh cắm sừng sững tại mẫu 30, 70, 110, ..., 630 - đếm tròn 16 cái chóp cách đều đặn 40 mẫu. 
Sự trùng hợp hoàn hảo: 16 chóp đỉnh = 16 byte. Tức là, con chip này xài chiêu chạy bộ (xử lý tuần tự) từng byte của trạng thái (state). Cái byte số `i` sẽ ngoan ngoãn nằm ở cái chuồng số `30 + 40*i`. 
Kho báu thông tin này không chỉ rọi đèn báo cho ta biết cần phải soi kính lúp vào cái mẫu (sample) nào, mà nó còn là công cụ để tát vỡ mặt những mô hình rởm: Nếu rõ ràng có 16 cái chuồng cựa quậy sống động, mà sức tương quan vẫn xịt ngóm bằng đúng mức nền, thì chắc chắn thủ phạm nằm ở hàm dự đoán đang tính sai bét.

**Bước 2 - Vá mô hình, mở máy quét dọc các chuồng (slot).** 
Quăng công cụ `analysis/sweep.py` vào cày với công suất: 6 mô hình × 16 byte × 256 khoá, đo đếm tương quan Pearson vector hoá kẹp chặt trong từng slot. Kết quả bung ra tách bạch sắc lẹm:

```text
Slot byte  0 phang HW(S[xor])  chốt k=0xf9  ngay mẫu  30  nhảy đỉnh |r|=0.731
Slot byte  6 phang HW(S[xor])  chốt k=0xf6  ngay mẫu 270  nhảy đỉnh |r|=0.740
Slot byte 13 phang HW(S[xor])  chốt k=0x29  ngay mẫu 550  nhảy đỉnh |r|=0.736
...
```

Tàn sát: Toàn bộ 15/16 byte còn lại đều đồng loạt chạm đỉnh 0.67-0.74, trong khi những kẻ bám đuôi (á quân) của từng byte tụt dốc thê thảm về rãnh ~0.20. 
Toạ độ đỉnh thời gian ghim cứng xác tuyệt đối vào công thức slot - bằng chứng thép cho thấy mô hình rập khuôn đã chạy hoàn hảo chứ không phải ăn may nhờ thủ thuật thống kê.

**Bước 3 - Vá khoá và lột mặt nạ (giải mã).** 
Hốt đủ 16 byte, ta đúc ra con khoá `f937e70c f8f9f6f2 87a14b0d a829ba47`. 
Đem con khoá này nhét vào lò giải mã `secret.enc` chạy hệ AES-128-ECB:

```text
H7CTF{48333086-d56b-41f5-b24b-a1d53fb122ec}
```

Từ 48 byte lột ra 43 byte cờ + phần đuôi cặn bã 5 byte mang số `0x05` (`pt[-5:] == 5*0x05`). Đây đích thị là định dạng PKCS#7 cực chuẩn - Lại thêm một tấm huy chương bảo chứng cho việc đào khoá đúng. Bởi lẽ, nếu chỉ cần rớt hoặc lệch 1 byte thôi, toàn bộ 48 byte đầu ra sẽ biến thành đống rác mà không hề có miếng padding vuông vức nào.

**Bước 4 - Xác minh rập khuôn (chéo).** 
Quá trình moi khoá (recover) hoàn toàn tự chủ mà chả thèm đếm xỉa đến tệp `secret.enc`; cái tệp đó chỉ dùng cho nghi thức bế mạc (bài kiểm tra cuối). 
Do đó, hai tấm bia bảo chứng được dựng lên hoàn toàn độc lập: (a) Toàn bộ 16/16 byte đều đạt đỉnh |r| ~0.7 tạo ra một hố sâu ngăn cách tuyệt đối với kẻ đứng thứ hai (á quân), và (b) Bản rõ giải mã nôn ra một chuỗi chữ ASCII mang dáng dấp đúng khuôn UUID cộng với đuôi đệm (padding) chuẩn mực. Một con khoá đi lạc 1 byte sẽ chỉ nhả ra 48 byte rác rưởi, không đời nào đẻ ra nổi một cấu trúc như thế.

## Flag
```bash
python exploit.py files/traces.npy files/plaintexts.npy files/secret.enc
```

Bảng kết xuất:
```text
    Slot byte  0: túm được k=0xf9  đỉnh |r|=0.731  kẻ xếp sau runner-up |r|=0.199
    ...
    Slot byte 15: túm được k=0x47  đỉnh |r|=0.673  kẻ xếp sau runner-up |r|=0.197
[+] Chìa khoá AES-128 key: f937e70cf8f9f6f287a14b0da829ba47
[+] Lột xác decrypted: 'H7CTF{48333086-d56b-41f5-b24b-a1d53fb122ec}'
[+] flag lấy được: H7CTF{48333086-d56b-41f5-b24b-a1d53fb122ec}
```

Toàn bộ cuộc đi săn diễn ra chớp nhoáng vỏn vẹn trong 0.35 giây.
