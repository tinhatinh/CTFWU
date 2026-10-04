# Ghi chú làm bài - a-rat-by-any-other-name

Log đầy đủ, gồm cả các hướng đã loại. Writeup chỉ giữ chuỗi quyết định.

## Môi trường

- Máy: Windows 11, MSI GF63, NVIDIA GeForce RTX 3050 Laptop 4 GB (driver 617.14, CUDA 13.4).
- hashcat 6.2.6, `C:\Tools\hashcat\hashcat-6.2.6\hashcat.exe`, kernel optimized (`-O`), `-w 3`, `-d 1` (CUDA).
- Python 3.12.10 cho phần đối chiếu MD5.
- hashcat tìm kernel theo `./OpenCL/` (đường dẫn tương đối), nên mọi lời gọi subprocess phải đặt `cwd` = thư mục cài đặt. Lần chạy đầu của `exploit.py` fail với `./OpenCL/: No such file or directory` (rc=-1) vì thiếu chi tiết này.
- `hashcat -D 3 --benchmark` báo `No devices found/left` trên máy này; `-d 1` trực tiếp trong attack mode thì chạy bình thường, nên script không dùng benchmark.

## Chuỗi thời gian

| Mốc | Việc | Kết quả |
| --- | --- | --- |
| T+0 | Đọc đề, ghi nhận 3 ràng buộc hình thức | ứng viên chỉ thuộc lớp `?u?l{0,7}` |
| T+2 | So MD5 với `words_alpha.txt` (từ <= 8 ký tự, capitalize) | 149.189 ứng viên, âm tính |
| T+4 | So MD5 với Moby `NAMES.TXT`, `NAMES-F.TXT`, `NAMES-M.TXT` | 30.829 ứng viên, âm tính |
| T+9 | Tải `name-dataset` v3 `first_names.pkl.gz` (25 MB), so 3 biến thể mỗi tên | 727.556 khóa, âm tính; 359.022 khóa đã khớp regex `^[A-Z][a-z]{1,7}$` |
| T+13 | Benchmark nhanh bằng mask ngắn `?u?l?l` | 4873 kH/s hiển thị (keyspace quá nhỏ để đo đúng), GPU visible |
| T+15 | hashcat `-O -m 0 -a 3 -d 1 --increment 2..8` trên mask 8 vị trí | Cracked sau ~86 s, `Jaqurtis` ở 17.61% mặt cắt độ dài 8, tốc độ 8415 MH/s |
| T+18 | `python -c` đối chiếu md5 | khớp chính xác hash trong đề |
| T+20 | Chạy `exploit.py --selftest` (cắm `md5("Felix")`, mask `?u?l{1,3}`) | thu hồi `Felix` sau 18.6 s |
| T+22 | Chạy `exploit.py` bản ship trong case | `Jaqurtis` sau 41.9 s |
| T+25 | đóng mặt cắt độ dài 1 (`?u`, 26 ứng viên) | Exhausted, 0/1 |

## Những hướng đã loại

1. **Đoán tên theo ngữ nghĩa** (chuột hoạt họa: `Remy`, `Emile`, `Django`, `Alfred`, `Linguini`, `Colette`, `Jerry`, `Stuart`, `Splinter`, `Mortimer`, `Roderick`, cộng họ `Tatouille`, `Chester`...; thử cả chữ thường và chữ hoa toàn bộ): không cái nào khớp. Loại vì chi phí thấp và đã đo.
2. **Wordlist từ điển tiếng Anh**: 149.189 từ <= 8 ký tự viết hoa đầu, âm tính. Loại làm bằng chứng kết luận, không loại làm hướng: nó chỉ nói từ điển không chứa tên đó.
3. **Corpus tên riêng (name-dataset 727k, Moby 30k)**: âm tính, cùng lý do như trên. Đây là chỗ dễ tự đánh lừa nhất - một cái tên "unconventional" được kỳ vọng là vắng mặt trong danh sách tên phổ biến, nên âm tính ở đây nhất quán với mọi giả thuyết, tức không mang thông tin.
4. **Đổi hàm băm (SHA1/SHA256/SHA512) trên cùng chuỗi ứng viên**: hash đề cho là MD5 32 hex và đã nổ ở MD5, không cần mở rộng.
5. **Nghi ngờ đề có file đính kèm / dịch vụ**: thẻ challenge không có link tải, không có netcat. Artifact duy nhất là chuỗi hash.

## Việc còn hở

- `files/de.png` chưa có: ảnh thẻ đề chỉ tồn tại dưới dạng dán trong chat phiên làm bài, không tìm thấy file gốc trên đĩa. Nếu về sau lấy được thẻ từ CTFd của giải, bổ sung vào `files/` và chèn `![de](files/de.png)` vào `de.md`.
- Cờ `cdctf{Jaqurtis}` mới được xác minh bằng MD5 cục bộ; chưa ghi nhận phản hồi từ hệ thống chấm điểm trong phiên này.
- Độ phủ keyspace tính theo mask đúng như ràng buộc đề. Nếu tên thật có dấu, dấu cách, gạch nối hoặc số thì nằm ngoài mask; thực tế preimage đã tìm thấy nên không cần mở rộng charset.
