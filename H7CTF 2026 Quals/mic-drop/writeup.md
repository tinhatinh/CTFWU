# Mic Drop — Hardware (Medium)

**Flag:** `H7CTF{7f0cb1b6-34ee-46c0-945b-1f069dff2a29}`

## Đề bài

Vở kịch diễn ra trong một phòng họp trực tuyến: Hệ thống cầu truyền hình AV đã bị tin tặc nẫng tay trên, và nó vẫn đang hồn nhiên phát trực tiếp (live stream) quang cảnh căn phòng. Quái đản ở chỗ, gã tin tặc lại vắt vẻo đi nhờ chính cái luồng live feed đó để bơm dữ liệu mật tống ra ngoài, mà tuyệt nhiên "không một ai ngồi trong phòng họp nghe thấy bất kỳ âm thanh lạ nào". 
Mục tiêu là một máy chủ (instance) chạy công cụ `mediamtx` (MediaMTX) thông qua một URL HTTPS. Nhiệm vụ của ta là: Giải mã và đọc xem gã tin tặc đang tuồn thứ gì ra ngoài.

## Phân tích ban đầu

Đòn thử `curl -I /` dội lại tín hiệu `Server: mediamtx`. Xác nhận đây là một máy chủ streaming đa phương tiện (media streamer) chứ không phải là một ứng dụng web thông thường. 
Kiến trúc của MediaMTX là phục vụ luồng hình ảnh HLS thông qua đường dẫn `<tên-phân-vùng-path>/index.m3u8`, trong khi cái cổng API `/v3/...` của nền tảng này đã bị khóa chặt (bị chặn 301 rồi ném thẳng ra 404). Đem một bộ từ điển đường dẫn đặc sệt mùi "phòng họp" ra nã thử, may mắn thay, đường dẫn `/boardroom/index.m3u8` hào phóng nhả mã 200 kèm định dạng chuẩn `application/vnd.apple.mpegurl`:

```text
#EXT-X-STREAM-INF:BANDWIDTH=186669,...,CODECS="mp4a.40.2"
main_stream.m3u8
```

File `main_stream.m3u8` chính là danh sách phát sóng trực tiếp (live playlist). Nó chẻ luồng ra thành các khúc (segment) `*_main_segN.ts` với thời lượng lác đác cỡ ~6.9 giây/khúc, sử dụng một cửa sổ trượt (sliding window) chỉ lưu luyến giữ lại khoảng 7 khúc mới nhất. 
Quơ gọn mẻ lưới 7 segment đó, ta hốt về được 47.85 giây âm thanh chuẩn AAC mono tần số 48 kHz.

Hai câu hỏi hóc búa cần lột trần theo thứ tự: 
1. Khối dữ liệu bị đánh cắp được nhét trong vỏ của cấu trúc file (container) hay nó hoà quyện thẳng vào tín hiệu âm thanh? 
2. Nếu nó bám vào tín hiệu, thì nó được cải trang dưới vỏ bọc điều chế (modulation) dạng gì?

## Chuỗi khai thác

**Bước 1 - Dùng mắt trần đọc phổ âm thanh.** 
Quật lệnh `ffmpeg -lavfi showspectrumpic` để nặn ra ảnh phổ (được lưu tại `analysis/spectrogram.png`). 
Trên ảnh hiện nguyên hình 9 khối năng lượng rực sáng (burst), mỗi khối kéo dài đều tăm tắp ~1.7 giây, cách nhau những khoảng nghỉ chết chóc đều đặn ~5.68 giây, nằm lọt thỏm trong dải tần hẹp 0.8-2.5 kHz. 
Sự lặp lại mang tính máy móc hoàn hảo này là bảo chứng đanh thép: Đây là tín hiệu thông điệp được máy móc phát lại thành vòng lặp trên luồng live, chứ tuyệt đối không phải tiếng ồn sinh hoạt trong phòng.

**Bước 2 - Giải phẫu thân xác Burst** (`analysis/bursts.py`). 
Mỗi khối burst mở màn bằng một nhịp âm thuần khiết 1200 Hz kéo dài ~160 mili-giây. Kế tiếp, phổ âm chẻ ra làm hai cột năng lượng nháy song song xoay quanh ngưỡng 1200 Hz và 2200 Hz, bọc kèm theo là đám dải biên nhiễu (sideband) văng ra do hiện tượng lật trạng thái chuyển mạch liên tục. 
Ghim cặp tần số 1200/2200 Hz lên bảng: Chân tướng của nó chính là cặp đỉnh mark/space kinh điển của chuẩn truyền tin Bell 202 - thuộc họ điều chế AFSK bán song công (half-duplex) từ thời tiền sử. Cái đoạn 160 mili-giây âm thuần mở đầu thực chất chỉ là một tín hiệu đánh tiếng (carrier mark/preamble) dọn đường trước khi nôn dữ liệu thịt ra.

**Bước 3 - Đo nhịp Baud chứ không đoán bừa.** 
Cân đo đong đếm năng lượng của hai dải tần trong từng ô cửa sổ thời gian (bit) với các tốc độ baud khác nhau, rồi ngồi đếm mật độ chuyển mạch (transition) thông qua công cụ tự viết `analysis/afsk.py`:

```text
Tốc độ baud  300: Vét 508 bit, chẻ ra 268 lần chuyển mạch, tỷ lệ trans/bit = 0.528
Tốc độ baud  600: Vét 1018 bit, chẻ ra 272 lần chuyển mạch, tỷ lệ trans/bit = 0.267
Tốc độ baud 1200: Vét 2038 bit, chẻ ra 274 lần chuyển mạch, tỷ lệ trans/bit = 0.134
```

Nhận xét: Ở tốc độ 300 baud, tín hiệu lật mặt (chuyển trạng thái) gần như cứ đụng mỗi bit là lật một lần. Ở các tốc độ cao hơn, số lần lật mặt tụt giảm tỷ lệ thuận. Chốt hạ: **300 baud chính là tốc độ thực của hệ thống**. Con số 1200 vốn dĩ chỉ là cái vỏ mặc định của chuẩn Bell 202. 
Tính toán đối chiếu thấy khớp đến đáng sợ: 
43 ký tự × 10 bit (cấu hình chuẩn 8N1) = 430 bit = 1.43 giây, đắp thêm 160 mili-giây mào đầu (preamble) ≈ vút lên 1.6 giây, vừa vặn khít khịt với độ dài một khối burst.

**Bước 4 - Giải mã điều chế.** 
Với mỗi bit lấy được, sau khi tống qua bộ lọc dải (bandpass) ±120 Hz rải quanh ranh giới 1200 Hz và 2200 Hz, đem biên độ ra đấu tố: nếu cường độ `mark > space` thì gán là số 1. Cứ thế lôi chuỗi bit ra chặt khúc theo các bit mào đầu (start-bit), gom từng cụm 8 bit theo thứ tự LSB-first rồi nặn thành chữ ASCII:

```text
H7CTF{7f0cb1b6-34ee-46c0-945b-1f069dff2a29}
```

**Bước 5 - Niêm phong chứng cứ (Xác minh chéo).** 
Cắm máy giải mã chạy thục mạng qua cả 9 khối burst: 8 khối burst nguyên vẹn ói ra chuỗi ký tự khớp nhau đến từng dấu chấm phẩy. Khối thứ 9 bị chém lìa đứt đoạn ở phần đuôi (`...dff`) - nguyên do là khung lấy mẫu (capture window) của ta sập cửa chém ngang chừng. Một kết quả giải mã mang tính tình cờ thì không thể nào sao chép y đúc nguyên văn tới 8 lần. Đây cũng là bằng chứng thép chốt lại việc: thông điệp đã được chạy vòng lặp (loop) liên hồi trên luồng live feed.

## Flag
```bash
python exploit.py https://web-021fc06a681e8dca.web.h7tex.com/boardroom 60   # Dùng lệnh này khi đánh trực tiếp máy chủ đang sống
python exploit.py files/352f5b477507_main_seg15.ts                          # Dùng lệnh này khi chạy vét lại từ file segment đã thâu tóm
```

Kết xuất thực tế của câu lệnh thứ 2 (chạy trên 1 file TS dung lượng 159.048 B đã cất trong `files/`):

```text
[*] Soi luồng offline TS từ files/352f5b477507_main_seg15.ts: 159048 B
[*] Bốc được 6.85 s luồng PCM tần số 48000 Hz
[*] Bắt được 1 mảng burst(s)
      Từ 0.98-  2.68s  nôn ra 'H7CTF{7f0cb1b6-34ee-46c0-945b-1f069dff2a29}'
[+] flag: H7CTF{7f0cb1b6-34ee-46c0-945b-1f069dff2a29}   (Chốt bảo chứng bởi 1/1 mảng bursts)
```

Quá trình săn cờ diễn ra khi máy chủ còn phập phồng nhịp thở, thông qua việc hút máu trực tiếp 7 đoạn segment (đo được 47.85 giây audio, mang theo 9 khối burst). Đến lúc đóng gói mã script để nghiệm thu thì máy chủ đã bị rút ống thở (stop), nên thao tác chạy lại chỉ làm được trên khối tài sản đã tàng trữ (artifact). Đoạn khẳng định 8/9 khối burst giống đúc nhau được trích lục từ việc chạy kịch bản `analysis/afsk.py` nã vào đoạn 47.85 giây audio lịch sử đó (Mời xem chi tiết tại `notes.md` phần H6).
