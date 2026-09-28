# notes.md - nas-coal

Input: `files/gem_collection.pptm` (2229848 B, sha256 `929726804037cc9b2e8779814aabf88361a6f4035ca1d93803662bdee543e855`)
Định dạng cờ đề yêu cầu: `sun{...}` (KHÔNG phải `H7CTF{...}` như các bài khác cùng giải)

## H1 - Cờ là plaintext, `strings` ra ngay
cmd: `strings -a gem_collection.pptm | grep -E 'H7CTF|flag\{'`
evidence: 0 kết quả trên toàn file và trên từng entry ZIP đã giải nén.
result: DEAD - cờ không ở dạng plaintext, và mình đã grep sai prefix (`H7CTF{` thay vì `sun{`).

## H2 - ZIP có dữ liệu nối thêm / entry lạ
cmd: kiểm tra EOCD, byte coverage, comment/extra field từng entry
evidence: 63 entry, `compress_size`/`CRC` khớp cả hai chiều local↔central, 0 byte
không được phủ, `comment=b''`, `extra=b''` toàn bộ, EOI JPEG nằm ở byte cuối.
result: DEAD - container sạch.

## H3 - Một "ảnh" thực ra là file khác (`coal.bin`)
cmd: đọc magic 12 byte đầu mọi phần tử `ppt/media/*` + `docProps/thumbnail.jpeg`
evidence: `image1.jpg&w=1920&q=75` = `FF D8 FF DB` (JPEG progressive thật),
5 file PNG = `\x89PNG`, thumbnail = `FF D8 FF E0 JFIF`.
result: DEAD - không có file giả danh.

## H4 - Bẫy trong cấu trúc OOXML (part mồ côi, rels, customXml)
cmd: liệt kê mọi `.rels`, đối chiếu `[Content_Types].xml`, dump `customXml/item*.xml`,
`changesInfo1.xml`, `presProps`, `viewProps`, `presentation.xml`
evidence: chỉ có 3 `customXml` chuẩn của template SharePoint; `changesInfo1.xml`
chỉ ghi marker sửa file của "Ardian Peach"; mọi quan hệ đều hợp lệ.
result: DEAD.

## H5 - Text ẩn trong slide (chữ trắng, off-canvas, zero-width, hidden slide)
cmd: `grep -o '<a:t>.*</a:t>'` trên CẢ 5 slide + 11 layout + master + theme
evidence: chỉ có 5 tiêu đề meme và một textbox `> mfw olevba oneshot chall`;
`HiddenSlides=0`, `Notes=0`, không có ký tự zero-width.
result: DEAD - nhưng chính textbox này là gợi ý thật (xem H9).

## H6 - LSB steganography trong ảnh
cmd: quét bit-plane 1 và 2 (LSB-first + MSB-first), từng kênh và cả 3 kênh,
tìm `H7CTF{`/`flag{`/`PK\x03\x04`/`zlib`/`gzip`
evidence: chỉ có vài lần chạm header 2 byte (`78 9C`) do ngẫu nhiên;
mọi thử `zlib.decompressobj()` đều lỗi - 0 stream thật.
result: DEAD - **và phép thử này từng vô nghĩa vì mình tìm sai chuỗi đích**.

## H7 - Ảnh có vùng đen/kênh alpha bất thường
cmd: `PIL` giải mã đúng filter rồi thống kê alpha + tỉ lệ pixel gần đen
evidence: `image5.png` RGBA nhưng 227494/227555 pixel alpha=255;
near-black fraction lớn nhất 0.087. (Lưu ý: đọc byte thô của IDAT mà chưa đảo
filter `Up` sẽ cho histogram alpha giả - đã gặp và đã sửa.)
result: DEAD.

## H8 - JPEG progressive DCT stego (JSteg/jphide/outguess)
cmd: đi hết marker `FFDB/FFC2/FFC4/FFDA`, dựng bảng DQT, tính hệ số
evidence: 5 scan progressive chuẩn (DC 3 thành phần → AC Y Ah0Al1 → AC Y refine
→ AC Cb → AC Cr), không có segment thừa, không có data sau EOI.
Hai bảng DQT giống hệt nhau - khác chuẩn nhưng là dấu vết của encoder web, không
phải kênh giấu. Máy không có `stegseek`/`outguess`/WSL.
result: DEAD (chưa giải được hệ số progressive, nhưng hướng này không cần thiết).

## H9 - olevba one-shot
cmd: `python -m pip install --index-url https://pypi.org/simple oletools` rồi `olevba`
evidence: trích được module `MediaCache` (`VBA/MediaCache`, 2515 B, code offset
1894 B trong `dir`): một `Public Sub RefreshCache()` gọi
`powershell.exe -NoProfile -EncodedCommand <base64>`.
Base64 là UTF-16LE, giải mã ra 4 dòng, trong đó
`$campaign = 'sun{yup_issa_gem}'`. URL `gem-cache.example.invalid` là TLD `.invalid`
nên không tải gì cả - macro không chạy được, chỉ để chứa cờ.
Slide 5 viết thẳng: `> mfw olevba oneshot chall`.
result: OK - cờ: `sun{yup_issa_gem}`

## H10 - Quét đa mã hoá để chắc không còn cờ `sun{` nào khác
cmd: sinh biến thể (raw, UTF-16LE/BE, reversed, ROT13, hex, base64 4 offset,
base64-of-UTF-16, hex-trong-file) trên 63 entry + pixel + bit-plane + mọi OLE stream
evidence: đúng 1 chuỗi `sun{...}` duy nhất trong toàn bộ archive, nằm ở H9.
result: OK - xác nhận `sun{yup_issa_gem}` là cờ, không phải mồi nhử.

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
