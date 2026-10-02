# Mic Drop — Hardware (Medium)

**Flag:** `H7CTF{7f0cb1b6-34ee-46c0-945b-1f069dff2a29}`

## Đề bài

Kịch bản: Hệ thống cầu truyền hình AV trong phòng họp đã bị chiếm quyền điều khiển, và đang phát trực tiếp (live stream) quang cảnh phòng họp. Đáng chú ý, luồng tín hiệu bị lợi dụng để truyền tải dữ liệu mật ra ngoài, mà không tạo ra âm thanh bất thường nào trong phòng. 
Mục tiêu là một máy chủ chạy dịch vụ `mediamtx` (MediaMTX) qua giao thức HTTPS. Yêu cầu: Phân tích luồng stream và giải mã dữ liệu đang được truyền tải.

## Phân tích ban đầu

Lệnh kiểm tra `curl -I /` trả về thông tin `Server: mediamtx`. Xác nhận đây là máy chủ streaming đa phương tiện. 
Cấu trúc của MediaMTX phát luồng hình ảnh HLS qua đường dẫn `<tên-phân-vùng-path>/index.m3u8`, trong khi API `/v3/...` bị chặn (chuyển hướng 301 sang 404). Thông qua thử nghiệm các đường dẫn phổ biến liên quan đến "phòng họp", đường dẫn `/boardroom/index.m3u8` trả về mã 200 kèm cấu trúc `application/vnd.apple.mpegurl`:

```text
#EXT-X-STREAM-INF:BANDWIDTH=186669,...,CODECS="mp4a.40.2"
main_stream.m3u8
```

File `main_stream.m3u8` là danh sách phát trực tiếp. Luồng dữ liệu được chia thành các phân đoạn (segment) `*_main_segN.ts` với thời lượng khoảng ~6.9 giây/phân đoạn, sử dụng cửa sổ trượt (sliding window) lưu trữ 7 phân đoạn mới nhất. 
Thu thập 7 segment, hệ thống thu được 47.85 giây âm thanh chuẩn AAC mono tần số 48 kHz.

Hai câu hỏi quan trọng cần phân tích: 
1. Dữ liệu mật được đính kèm vào cấu trúc file (container) hay mã hóa trực tiếp vào tín hiệu âm thanh? 
2. Nếu mã hóa vào tín hiệu, chuẩn điều chế (modulation) nào được sử dụng?

## Quá trình khai thác

**Bước 1 - Phân tích phổ âm thanh.** 
Sử dụng lệnh `ffmpeg -lavfi showspectrumpic` để tạo ảnh phổ (lưu tại `analysis/spectrogram.png`). 
Trên ảnh hiển thị 9 khối năng lượng (burst), mỗi khối kéo dài đồng đều ~1.7 giây, ngăn cách bởi các khoảng nghỉ ~5.68 giây, nằm trong dải tần 0.8-2.5 kHz. 
Cấu trúc lặp lại chính xác này chứng minh: Đây là dữ liệu được phát lặp lại liên tục trên luồng live, không phải âm thanh môi trường.

**Bước 2 - Phân tích cấu trúc Burst** (`analysis/bursts.py`). 
Mỗi khối burst bắt đầu bằng tín hiệu âm tần 1200 Hz kéo dài ~160 mili-giây. Sau đó, phổ âm chia thành hai dải tần số luân phiên ở 1200 Hz và 2200 Hz, kèm theo dải biên nhiễu (sideband) sinh ra từ việc chuyển đổi trạng thái tần số. 
Cặp tần số 1200/2200 Hz là tín hiệu mark/space đặc trưng của chuẩn truyền tin Bell 202 - thuộc phương thức điều chế AFSK bán song công (half-duplex). Đoạn tín hiệu 1200 Hz dài 160 ms ban đầu là tín hiệu đồng bộ (carrier mark/preamble) trước khi truyền tải dữ liệu.

**Bước 3 - Phân tích tốc độ Baud.** 
Tính toán năng lượng hai dải tần ở các khung thời gian khác nhau, ghi nhận mật độ chuyển mạch (transition) qua công cụ phân tích `analysis/afsk.py`:

```text
Tốc độ baud  300: Lấy 508 bit, ghi nhận 268 lần chuyển mạch, tỷ lệ trans/bit = 0.528
Tốc độ baud  600: Lấy 1018 bit, ghi nhận 272 lần chuyển mạch, tỷ lệ trans/bit = 0.267
Tốc độ baud 1200: Lấy 2038 bit, ghi nhận 274 lần chuyển mạch, tỷ lệ trans/bit = 0.134
```

Kết luận: Ở tốc độ 300 baud, tín hiệu chuyển trạng thái ổn định với tỷ lệ phù hợp (mỗi bit có khả năng lặp khoảng 1 transition nếu bit xen kẽ). **300 baud là tốc độ cấu hình thực của hệ thống** (tham số 1200 thường được gọi là tên chuẩn Bell 202). 
Kiểm chứng tính toán: 
43 ký tự × 10 bit (cấu trúc 8N1) = 430 bit = 1.43 giây, cộng thêm 160 ms tín hiệu preamble ≈ 1.6 giây, khớp chính xác với độ dài 1.7 giây của khối burst.

**Bước 4 - Giải mã tín hiệu điều chế.** 
Xử lý qua bộ lọc dải thông (bandpass filter) ±120 Hz quanh tần số 1200 Hz và 2200 Hz, so sánh biên độ hai tần số: nếu `mark > space` ghi nhận bit 1. Phân tách chuỗi bit qua các bit đồng bộ (start-bit), nhóm 8 bit theo thứ tự LSB-first và chuyển thành ký tự ASCII:

```text
H7CTF{7f0cb1b6-34ee-46c0-945b-1f069dff2a29}
```

**Bước 5 - Xác minh kết quả.** 
Thực hiện giải mã toàn bộ 9 khối burst: 8 khối trả về chuỗi ký tự đồng nhất, không sai lệch. Khối thứ 9 bị ngắt ở phần đuôi (`...dff`) do giới hạn thu thập của khung mẫu (capture window). Sự đồng nhất của 8 khối khẳng định dữ liệu được lặp lại liên tục (loop) và giảm trừ hoàn toàn các yếu tố nhiễu môi trường.

## Flag
```bash
python exploit.py https://web-021fc06a681e8dca.web.h7tex.com/boardroom 60   # Trích xuất dữ liệu trực tiếp từ máy chủ đang hoạt động
python exploit.py files/352f5b477507_main_seg15.ts                          # Trích xuất dữ liệu từ tệp phân đoạn offline
```

Kết xuất thực thi đối với lệnh thứ 2 (trên file TS 159.048 B lưu trữ tại `files/`):

```text
[*] Soi luồng offline TS từ files/352f5b477507_main_seg15.ts: 159048 B
[*] Bốc được 6.85 s luồng PCM tần số 48000 Hz
[*] Bắt được 1 mảng burst(s)
      Từ 0.98-  2.68s  trả về 'H7CTF{7f0cb1b6-34ee-46c0-945b-1f069dff2a29}'
[+] flag: H7CTF{7f0cb1b6-34ee-46c0-945b-1f069dff2a29}   (Xác nhận bởi 1/1 mảng bursts)
```

Qá trình thu thập hoàn thành trên máy chủ live với 7 phân đoạn (47.85 giây audio, chứa 9 khối burst). Sau khi máy chủ ngừng hoạt động, mã script được thiết kế để xử lý tệp dữ liệu đã lưu trữ. Báo cáo phân tích (8/9 burst khớp nhau) được lưu trong `notes.md` (mục H6) qua việc chạy phân tích `analysis/afsk.py` đối với file gốc 47.85s.
