# Trace Amounts - Hardware (Medium)

**Flag:** `H7CTF{48333086-d56b-41f5-b24b-a1d53fb122ec}`
**Khoá bí mật (AES-128) trích xuất được:** `f937e70cf8f9f6f287a14b0da829ba47`

## Đề bài

Hệ thống sử dụng thuật toán AES-128 để xác thực. Người tấn công đã sử dụng thiết bị đo dòng điện và thu thập được 500 chu kỳ hoạt động phê duyệt. Dữ liệu dòng điện thu thập đi kèm các bản rõ thử thách (plaintext challenge) bị công khai. 
Lưu ý: Khoá bảo mật không rò rỉ, tuy nhiên dấu vết điện tiêu thụ được ghi nhận. 
Tài liệu cung cấp gồm 3 file: `traces.npy` (ma trận 500×700), `plaintexts.npy` (ma trận 500×16) và tệp `secret.enc` (dài 48 B, chuẩn AES-ECB). 
Nhiệm vụ: Trích xuất khóa và giải mã `secret.enc`.

## Phân tích ban đầu

Hệ thống là máy chủ `SimpleHTTP` chứa 3 file, không yêu cầu phân tích cấu trúc web. 
Điểm khai thác: Áp dụng phương pháp Phân tích năng lượng tương quan (Correlation Power Analysis - CPA) áp dụng cho vòng mã hóa đầu tiên của AES.

Nguyên lý: Với plaintext thứ `i`, ứng với mỗi khóa dự đoán `k`, giá trị biến đổi có dạng `S-box[pt_i ^ k]`. 
Nếu cấu trúc chip tiêu thụ điện theo mô hình Hamming, giá trị `HW(S-box[pt_i ^ k])` sẽ tạo ra mức tương quan cao tại mẫu (sample) nơi xử lý tín hiệu. Phép biến đổi này chỉ đúng với `k` chính xác.

Khảo sát dữ liệu:

```text
Ma trận điện traces     (500, 700) định dạng float32   trị số mean 0.06, độ lệch std ~1.0
Ma trận rõ   plaintexts (500, 16)  định dạng uint8
```

Với 500 mẫu, nhiễu tín hiệu trung bình có độ lệch chuẩn `1/sqrt(500) = 0.045`. 
Với phạm vi phân tích (16 byte × 256 khoá × 700 sample), đỉnh nhiễu cao nhất có thể đạt ngưỡng giá trị 0.21. Việc xác định các đỉnh cao hơn 0.21 là cơ sở để phân tích tính chính xác. Điểm đáng lưu ý trong thực tế là tại lần quét ban đầu, kết quả đều dao động quanh 0.21.

## Chuỗi khai thác

**Bước 1 - Phân tích đặc tính thời gian của dòng điện.** 
Phân tích phổ năng lượng theo từng mẫu (`mean trace` và `variance profile`) cho thấy cấu trúc chu kỳ rõ ràng: Các đỉnh xuất hiện tại mẫu 30, 70, 110, ..., 630 - tương ứng với 16 chu kỳ cách nhau 40 mẫu. 
Sự tương quan: 16 chu kỳ = 16 byte. Kiến trúc này cho thấy hệ thống xử lý tuần tự từng byte. Byte thứ `i` nằm tại khung `30 + 40*i`. 
Thông tin này giúp xác định vùng lấy mẫu và loại trừ các giả thuyết sai: Khi có chu kỳ hoạt động rõ ràng nhưng hệ số tương quan vẫn ở mức nhiễu, thuật toán dự đoán không chính xác.

**Bước 2 - Điều chỉnh mô hình và phân tích theo khung thời gian.** 
Sử dụng script `analysis/sweep.py` để quét: 6 mô hình × 16 byte × 256 khoá, tính toán hệ số tương quan Pearson cho mỗi khung. Kết quả trả về rõ ràng:

```text
Slot byte  0 áp dụng HW(S[xor])  tìm được k=0xf9  ngay mẫu  30  đỉnh tương quan |r|=0.731
Slot byte  6 áp dụng HW(S[xor])  tìm được k=0xf6  ngay mẫu 270  đỉnh tương quan |r|=0.740
Slot byte 13 áp dụng HW(S[xor])  tìm được k=0x29  ngay mẫu 550  đỉnh tương quan |r|=0.736
...
```

Kết quả: 15/16 byte còn lại đều đạt mức 0.67-0.74, trong khi khóa có hệ số cao nhì giữ ở mức ~0.20. 
Thời điểm xuất hiện đỉnh tương quan khớp hoàn toàn cấu trúc chu kỳ, chứng minh mô hình phân tích chính xác tuyệt đối.

**Bước 3 - Ghép khóa và giải mã.** 
Xác định 16 byte, ghép thành khóa `f937e70c f8f9f6f2 87a14b0d a829ba47`. 
Sử dụng khoá này tiến hành giải mã `secret.enc` bằng AES-128-ECB:

```text
H7CTF{48333086-d56b-41f5-b24b-a1d53fb122ec}
```

Trích xuất 43 byte cờ + 5 byte padding mang giá trị `0x05` (`pt[-5:] == 5*0x05`). Đây xác định là cấu trúc PKCS#7 chuẩn xác. Đây là minh chứng cho việc tính toán đúng khóa, vì sai lệch 1 byte khóa sẽ tạo ra chuỗi dữ liệu sai định dạng.

**Bước 4 - Kiểm chứng độc lập.** 
Quá trình trích xuất khóa không phụ thuộc vào file `secret.enc`; tệp này đóng vai trò xác nhận cuối cùng. 
Có hai yếu tố chứng minh: (a) Toàn bộ 16 byte đều đạt đỉnh |r| ~0.7 vượt trội so với khóa có điểm cao nhì, và (b) Bản giải mã có định dạng UUID cộng với đuôi đệm chuẩn mực. Khóa sai 1 byte sẽ trả về dữ liệu lỗi, không khớp định dạng chuẩn.

## Flag
```bash
python exploit.py files/traces.npy files/plaintexts.npy files/secret.enc
```

Bảng kết quả:
```text
    Slot byte  0: xác định k=0xf9  đỉnh |r|=0.731  điểm cao nhì |r|=0.199
    ...
    Slot byte 15: xác định k=0x47  đỉnh |r|=0.673  điểm cao nhì |r|=0.197
[+] Chìa khoá AES-128 key: f937e70cf8f9f6f287a14b0da829ba47
[+] Dữ liệu decrypted: 'H7CTF{48333086-d56b-41f5-b24b-a1d53fb122ec}'
[+] cờ thu được: H7CTF{48333086-d56b-41f5-b24b-a1d53fb122ec}
```

Quá trình chạy thời gian thực thi khoảng 0.35 giây.
