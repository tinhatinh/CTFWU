# notes.md - tacocat

Input: `files/fat_tacocat.png` (578053 B, sha256 `11fe22d62e5f8a1fee9cb0d9cdc04efd6d66b20ea860aeb58351bf5b69e1f07f`)
Định dạng cờ đề yêu cầu: `cdctf{...}`

## H1 - Appended data sau IEND
cmd: `python -c "d=open('fat_tacocat.png','rb').read(); print(len(d))"` + đi bộ chunk
evidence: `IEND` kết thúc tại 459177, file 578053 B, đuôi 118876 B. Trước `IEND` có chunk private `deBG` len=16 payload `0E0EE52B90EDBA88`.
result: OK -> dẫn sang H2

## H2 - Đuôi là archive hoặc file khác định dạng
cmd: quét magic `PK\x03\x04`, `\x1f\x8b`, `7zXZ`, `Rar!`, `ID3`, `OggS`, `\xff\xd8\xff` trên toàn file
evidence: 0 hit archive. 6 hit `\x1f\x8b` nhưng tất cả nằm trong stream `IDAT` nén, là ngẫu nhiên.
result: DEAD - không có container thứ hai

## H3 - PNG thứ hai không có chữ ký
cmd: `appended.find(b'\x00\x00\x00\rIHDR')` -> offset 41 trong `appended.bin` (tính từ đầu chunk `deBG`)
evidence: ghép `\x89PNG\r\n\x1a\n` vào thì dựng được PNG 19 chunk, CRC cả 19 đều hợp lệ, IHDR = 1261x1403 depth 8 colortype 6. Chunk cuối trước `IEND` là `deBG` payload `2E1D19437C4E9802`.
result: OK - `binwalk`/`file`/`strings` đều mù vì thiếu 8 byte chữ ký

## H4 - Nội dung nằm ở kênh alpha
cmd: unfilter thủ công 5 kiểu filter, đếm theo kênh
evidence: `moi pixel khong trong suot co RGB = 0,0,0: True`. Alpha hist: 1524642 px = 0, 218322 px = 255, còn lại là anti-alias. Quét theo ngưỡng alpha 1-30 / 31-60 / 61-120 / 121-200 / 201-254: mọi dải đều có cùng bounding box y 28..1056 x 6..1219, không có lớp mờ ẩn riêng.
result: OK - render alpha dao mau ra `analysis/alpha_read.png`, thay net + 4 dong chu tay

## H5 - Chuoi "Extra data is no fun!!" cuoi file
cmd: `print(appended[-80:])`
evidence: `Extra data is no fun!! (unlike the classic crunchy tacobell taco, of course, which is very fun and delicious)\n`
result: DEAD - mồi, nội dung thật nằm ở PNG không chữ ký ngay trước nó

## H6 - deBG la khoa
cmd: XOR hai payload `0E0EE52B90EDBA88` ^ `2E1D19437C4E9802`
evidence: ra `2013FC68ECA1228A`, khong ASCII; khong co khoi mat nao trong file de giai.
result: DEAD - nhan cua tac gia (de-background), khong phai du lieu giai ma

## H7 - Ban doc dau tien (SAI)
cmd: doc `analysis/alpha_read.png` bang mat thuong o anh 1261x1403 bi downscale khi hien thi
evidence: chu `l` va so `1` trong font tay nay gan giong nhau; ban dau chuan hoa ca hai ve chu `l`.
co: `cdctf{I_really_really_1ik3_th3_tac0b3ll_classic_crunchy_taco3}`
result: DEAD - nguoi dung bao bi tu choi. Hai cho sai: `really` (tu thu hai) va `tac0b3ll`.

## H8 - Do chan de glyph de phan loai l / 1
cmd: `python exploit.py files/fat_tacocat.png`
evidence: do do rong doan muc lien tiep trong 12% duoi moi net thang:
  `l` = 19-23px (mong deu), `1` = 39-93px (chan ngang rong bang ca glyph).
  dong 1 'a??y' -> 39 va 41 => `a11y`; dong 2 dau -> 56 va 60 => `11`; dong 0 'really' -> 19 va 19 => giu nguyen `ll`.
  Glyph sau `{`: top=71 stem=19 base=71 => serif hai dau => `I` HOA, khong phai `l`.
  `0` trong `tac0b3` co gach cheo => so khong.
result: OK - co: `cdctf{I_really_rea11y_1ik3_th3_tac0b311_classic_crunchy_taco3}`

---

## Trang thai

Ban H7 bi tu choi. Ban H8 chua thay nguoi dung xac nhan nap duoc hay chua.
Neu van sai, nghi cho khac la `1ik3` -> `lik3` hoac `taco3` -> `tacos`, nhung do chan de cua
`1ik3` la 93px (bang kieu so `1`), nen kha nang do thap.

## Quy trinh cho lan sau

Anh net chu tay khong doc bang mat o ban da bi downscale. Buoc bat buoc: cat vung chu thanh
crop nho (<= 400px rong) roi phong 3-5x, hoac do dac tinh hinh hoc cua glyph. Font tay thuong
lam `l` / `1` / `I` / `|` giong het nhau.

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
