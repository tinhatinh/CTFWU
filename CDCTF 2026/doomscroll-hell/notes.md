# notes.md - doomscroll-hell

Input: `C:\Users\Administrator\Downloads\doomscroll.zip` (51.462.800 B, sha256 `5163b4d7...903f79`)
Định dạng cờ đề yêu cầu: `cdctf{word_word_word_word_word}`

## H1 - Nhãn metadata chứa dữ liệu ẩn
cmd: `ffprobe -show_format -show_streams` + `exiftool` trên 15 file
evidence: tag chỉ có `encoder = Lavc libx264`, `handler_name`, `creation_time` 2026-10-03 (khác nhau
giữa các file, không theo quy luật nào); trong `moov` có `udta/meta` 53 B và một `free` 8 B rỗng
result: DEAD - `udta/meta` chỉ là tag encoder, `free` đúng 8 byte không payload

## H2 - Dữ liệu nằm ngoài hai stream chuẩn (box thừa ở mức container)
cmd: `python -c "walk mp4 boxes"` (đọc header 8/16 byte đệ quy)
evidence: cả 15 file có đúng chuỗi box `ftyp, moov, free, mdat, uuid`; box cuối `uuid` 92-93 B nằm
SAU `mdat`, payload 68-69 B, 15 file dùng chung UUID `5f0a6c1e-7b3d-5a8e-9c4f-2d1b6a7e3c90`; dump
payload thấy `%PDF-1.4`, `1 0 obj`, `/Type /Pages`, `xref`, `trailer`, `startxref`, `%%EOF`, `x\xda`
result: OK - mỗi video giấu một lát cắt của cùng một file PDF

## H3 - Lỗi lệch offset khi carve
cmd: `buf[o+16:o+size]`
evidence: `AssertionError` ngay file đầu tiên; box `uuid` = 4 size + 4 type + **16 extended_type**
+ payload, tức payload bắt đầu ở `o+24`
result: FIXED - carve lại với `o+24`, tổng 13*68 + 2*69 = 1022 B

## H4 - Ghép lát cắt theo tên file hoặc theo `mvhd` creation_time
cmd: (không chạy)
evidence: hai khoá sắp xếp này không có quan hệ nhân quả với vị trí byte trong PDF; PDF có sẵn
ràng buộc mạnh hơn nhiều
result: DEAD (bỏ trước khi thử) - chuyển sang suy thứ tự từ cú pháp PDF

## H5 - Suy thứ tự bằng cú pháp, brute-force phần stream
cmd: đọc tay 15 payload
evidence: 6 lát ASCII nối được với nhau theo `%PDF-` -> `2 0 o|bj` -> `/Font << /` + `F1 4 0 R` ->
`/Sub` + `type /Type1` -> `/F` + `ilter /FlateDecode >>\nstream\n`; 3 lát cuối nối theo `endstream`
và các dòng xref 20 byte (`0000000015 00000 n ` + ` \n0000000064 ...`)
result: OK - còn 6 lát binary ở giữa, 6! = 720 hoán vị

## H6 - Oracle zlib xác nhận phần stream
cmd: `zlib.decompress(pdf[head:head+450])` cho từng hoán vị
evidence: đúng một hoán vị (`CU4g7CDhW5q, CDx8NCxzTUA, CtJum68xxwr, CPZGeCCcZfB, Ct9t7nQO6KL,
CYzUFRaPz5o`) inflate ra 946 B content stream; mọi hoán vị khác raise `zlib.error`
result: OK - cờ `cdctf{doomscrolling_is_so_much_fun!}`

## H7 - Kiểm chứng tính đóng của file
cmd: đối chiếu `xref` với vị trí thật trong file dựng lại
evidence: các offset 15/64/121/247/317 trùng khớp vị trí của `1 0 obj`..`5 0 obj`, `startxref` = 839
trùng vị trí `xref`; `%%EOF` kết thúc file; `fitz` render ra đúng 1 trang
result: OK - 1022 B là toàn bộ file, không thiếu lát cắt nào

## H8 - Script tự động hoá: phân loại lát cắt theo tỉ lệ byte in được
cmd: `python exploit.py files/chunks` (bản dùng `plausible()` yếu)
evidence: lát `C1-sQVqsTIu` (chứa `endstream`, `xref`) bị xếp thứ 3 vì predicate chỉ kiểm số thứ tự
object; DFS bùng nổ, chạy 2 m 38 s rồi trả `zlib.error: incomplete or truncated stream`
result: DEAD - bỏ cách phân loại ASCII/binary, đổi sang DFS có oracle inflate

## H9 - Oracle "inflate không lỗi trên tiền tố" là chưa đủ
cmd: `python exploit.py files/chunks` (bản DFS toàn bộ, chỉ kiểm `decompressobj().decompress`)
evidence: DFS nhận cả run `Cks57 > CU4g7 > CDx8 > C9nruRG2aNs > CtJum > C4cE45r8 > CPZGe > C1-sQV`
vì deflate giữa block có thể nuốt byte rác mà không raise; run này không vượt được `zlib.decompress`
+ `xref_ok` ở bước sau, nhưng `inflate_run` chỉ trả về nghiệm đầu tiên
result: FIXED - khi đủ 450 byte bắt buộc `zlib.decompress(body[:450])` chạy hết stream VÀ byte kế
tiếp phải là `\nendstream`; thêm `(?<!end)stream\n` để không nhầm `endstream\n` thành đầu stream
(không có regex này, `next()` chọn lát `C1-sQVqsTIu` làm opener và DFS chết ngay)

## H10 - Kiểm khung hình
cmd: `ffmpeg -vf select=eq(n\,150) -vframes 1` trên `CWBRyIGYAOd.mp4`, `CFH95xUXh5X.mp4`
evidence: frame là reel bình thường (chó kéo quần ông chủ, watermark `@SNOPFEED`), không có chữ
hay mã QR khả nghi
result: DEAD - không cần khai thác kênh frame/audio, PDF đã đóng bằng ràng buộc xref

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
