# Everything Left Open - log phân tích

Quy ước: mỗi giả thuyết một mục, nhánh sai ghi `result: DEAD - <lý do>`.

## H1 - Cờ nằm trong dữ liệu form chưa nộp
Đề nói "data entered mid-form" và README trong zip nói "Find what she was about to submit".
Trong Firefox, nội dung form chưa submit sống trong session store, bản backup gần nhất là
`sessionstore-backups/recovery.jsonlz4`.
`result: ALIVE - formdata.id["artifact-flag"] chứa cờ.`

## H2 - Quét cờ trong các nguồn chưa nén
`grep -rao "POCTF{[^}]*}"` trên toàn bộ tree giải nén: đúng một kết quả, và nó nằm trong
`recovery.jsonlz4` (grep đọc được vì file nén nhưng chuỗi base64-ish tình cờ không che được
plaintext? không - xem H3). `places.sqlite`, `formhistory.sqlite`, `logins.json`, `prefs.js`,
`README.txt` không có chuỗi `POCTF{` nào.
`result: DEAD cho 5 file đầu; file jsonlz4 thật ra được tìm thấy sau khi giải nén.`

## H3 - Giải mã jsonlz4
Ba lần thử sai trước khi đúng:
- `lz4.frame.decompress(raw[5:])` (đoán header `data:` như tài liệu cũ) ->
  `RuntimeError: LZ4F_getFrameInfo failed with code: ERROR_frameType_unknown`. Đây không phải
  LZ4 frame, mà là một LZ4 block.
- `lz4.block.decompress(raw[6:], uncompressed_size=1<<20)` -> "thành công" nhưng ra 664 byte
  bắt đầu bằng 6 byte rác rồi mới tới `{"version"`, nên `json.loads` fail. Con số 664 lớn hơn
  kích thước thật 657 chính là dấu hiệu header bị tính thiếu.
- Đọc size ở `raw[6:10]` rồi decompress từ `raw[10:]` -> `LZ4BlockError ... insufficient space`.
Header đúng là `mozLz40\0` = 8 byte, size LE tại `raw[8:12]` = 657, block tại `raw[12:]`.
`result: ALIVE - đúng offset thì json.loads chạy thẳng.`

## H4 - `rev_host` của bản ghi id 99
`moc.ftcwolfrevoretniop.nimda.` đảo ra `admin.pointeroverflowctf.com`, trong khi cột `url` của
cùng hàng là `catalog.spr.org.uk`. Hai cột Firefox vốn luôn dẫn xuất từ nhau nên đây là bản ghi
ghép tay, frecency 2000 (cao nhất bảng) để kéo mắt nhìn.
`result: DEAD - bài là forensics offline, không có endpoint nào để chạm, và cờ không ở đó.`

## H5 - Bookmark "flag draft (do not lose)"
Hàng duy nhất của `moz_bookmarks`, `fk=3` trỏ tới `https://hollis.edu/special-collections/lssf-papers`,
là trang lịch sử thường. Tên bookmark là mồi.
`result: DEAD.`

## H6 - Credential trong `logins.json`
`encryptedUsername`/`encryptedPassword` trông như cần key3.db. Thực ra chỉ là base64:
`ZS5tYXJjaGV0dGlAaG9sbGlzLmVkdQ==` -> `e.marchetti@hollis.edu`, `TW5EYXlXM2RuZXNkQHk3` ->
`MnDayW3dnesd@y7`, `YW5vbi1hbmFseXN0` -> `anon-analyst`, `aHVudGVyMg==` -> `hunter2`.
`result: DEAD - không phải đường tới cờ, chỉ là màu điều tra.`

## H7 - Zip có phần đuôi ẩn
`PK\x05\x06` ở offset 3464, tổng 3486 byte, hiệu 22 = đúng kích thước EOCD tối thiểu.
`z.comment` rỗng, 6 entry.
`result: DEAD - không có appended data.`

## Ghi chú
- `pip install lz4` có wheel cp312 win_amd64, không cần compiler.
- Cờ khớp khuôn `POCTF{<cid>.<team_id>.<nonce>.<sig26>}` (cid 109, team 612), nên tự xác
  nhận được tính hợp lệ mà không cần nộp thử.
