# notes.md - epic-rat-encoding

Input: `files/message_encoder.c` (360 B, sha256 `738e4cbaa71cc9a48260ed6130718c04f66d910582a10d4760fc27466deb2734`), `files/nums.txt` (160 B, sha256 `188ff63f2326345e495fffc6b2199384b87c021d92489a027354fe4d4f9085b5`)
Định dạng cờ đề yêu cầu: `cdctf{Place_Place_Place_at_time_time_time_Time}`

## H1 - `+=` là tổng số học của 8 byte
cmd: đọc lại vòng lặp trong `message_encoder.c`
evidence: nếu chỉ cộng thì mỗi `nums[j]` mang ~8 bit, 8 số không dựng lại được một câu mô tả địa điểm + giờ; hơn nữa `<< 8` chen giữa 8 lần cộng là cấu trúc đóng gói byte
result: DEAD - bác bỏ bằng cấu trúc loop, xác nhận ở H2

## H2 - `nums[j]` là 8 byte big-endian
cmd: nhẩm theo loop: `i=0` cộng byte đầu rồi shift 8 (vì `i != 7`), `i=7` cộng byte cuối và không shift
evidence: byte đầu chunk nằm ở bit cao nhất => big-endian; 8 chunk * 8 byte = 64 byte, vừa khuôn độ dài cờ 47-64 byte
result: PENDING -> kiểm chứng bằng self-test ở H3

## H3 - Self-test: dựng encoder với message đã biết, chạy rồi giải mã lại
cmd: `gcc -O0 -D__USE_MINGW_ANSI_STDIO=1 -o enc.exe enc.c && ./enc.exe | python decode.py $(cat out)`
evidence: bản đầu chạy WITHOUT `-D__USE_MINGW_ANSI_STDIO=1` in bang `%lu` cho `uint64_t` -> 8 token 10 chu so (chi 32 bit thap), giai ma ra `\x00\x00\x00\x00f{Wa...` xen ke toan 0. Ban co `%llu` + ANSI stdio cho 8 token 19 chu so va round-trip khop chu
result: OK (ban dau) - DEAD (ban %lu): negative gia do LLP64 (`long` = 4 byte tren Windows), khong phai do decoder sai

## H4 - Giai ma 8 so cua de
cmd: `python exploit.py files/nums.txt`
evidence: `64 byte`, hex `4d656574...546875727364617900256c`, in duoc `Meet me at the Tom Bevill Building at noon next week Thursday.%l`
result: OK - message 61 ky tu + NUL + 2 byte duoi `%l`

## H5 - `00 25 6c` cuoi la gi?
cmd: `python exploit.py files/nums.txt` (in hex + vung in duoc)
evidence: `...day \x00 % l`; chuoi format trong C la `"%lu "`, nam canh `message` trong .rodata; loop doc 64 byte trong khi chuoi chi 61 + NUL
result: OK - khop do dai 61 ky tu va khop chuan bi bien dich cua tac gia; little-endian se day 3 byte nay len dau chunk va pha chu

## H6 - doi chung bang chinh encoder
cmd: `gcc -O0 -D__USE_MINGW_ANSI_STDIO=1 analysis/encoder_reconstructed.c` roi chay
evidence: ra dung 8 số của `files/nums.txt` (`identical: True`, xem `analysis/encoder_reconstructed.log`)
result: OK - cờ: `cdctf{Tom_Bevill_Building_at_noon_next_week_Thursday}`

## Bẫy ghi lại
- `%lu` trên MinGW/LLP64 cắt `uint64_t` còn 32 bit. Bài này tự dựng encoder để đối chứng mà không thêm `-D__USE_MINGW_ANSI_STDIO=1` + `%llu` thì self-test báo sai dù decoder đúng. Dấu hiệu nhận biết: số in ra chỉ 10 chữ số trong khi uint64 phải 19-20.
- `nums[8]` trong file gốc không khởi tạo. Bản dựng lại phải đặt `= {0}` thì mới so được với số của đề.

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
