# Everything Left Open - Forensics

**Điểm:** 100 · **Wave:** 1 · **Cờ:** `POCTF{109.612.I777LWHDFNCWRJ2S.JB6P5ZRASWPVYKKKHXKAPSQFWT}`

**File cho trước:** `files/left-open-profile-team-612.zip` 3.486 byte, sha256 `faadae549b93f75a...` khớp thẻ đề.

## Đề bài

Một khách bỏ lại laptop ở khách sạn, máy chưa khoá và trình duyệt đang mở giữa một form.
Firm IT bên ngoài đóng gói lại thành zip. Nhiệm vụ: tìm cờ trong session đó, và "chú ý các
chi tiết". Zip sinh theo team, nên mỗi team một file khác nhau.

## Phân tích ban đầu

Bên trong là Firefox profile `k-vance-profile` với năm mục:

| File | Nội dung đọc được |
| --- | --- |
| `places.sqlite` | `moz_places` 8 dòng (lịch sử) + `moz_bookmarks` 1 dòng |
| `formhistory.sqlite` | `moz_formhistory` 3 dòng: `search` = "eighth session lssf redacted", `email` = "e.marchetti@hollis.edu", `search` = "halberd office hours wednesday" |
| `logins.json` | 2 login, `encryptedUsername`/`encryptedPassword` chỉ là base64 thường |
| `prefs.js` | `general.useragent.override` về Firefox/119.0, `browser.startup.page=3`, `resume_from_crash=true` |
| `sessionstore-backups/recovery.jsonlz4` | 584 byte, container `mozLz40\0` |
| `README.txt` | Docket MARCHETTI/2026-14, "Find what she was about to submit." |

Câu "data entered mid-form" và "what she was about to submit" trỏ thẳng tới session store:
đó là nơi Firefox giữ nội dung form chưa nộp. Các file sqlite chỉ chứa ngữ cảnh điều tra.

## Các chi tiết lạc hướng đã ghi nhận

Ba chỗ không phục vụ việc lấy cờ nhưng đáng ghi lại vì chúng đúng loại "pay attention to the details":

- Dòng `moz_places` id 99 có `url` là `https://catalog.spr.org.uk/apparatus/provenance/lssf`
  nhưng `rev_host` lại là `moc.ftcwolfrevoretniop.nimda.`, giải ra `admin.pointeroverflowctf.com`.
  `rev_host` là cột Firefox tự dẫn xuất từ `url`, ở đây hai cột mâu thuẫn nên bản ghi này được
  ghép tay. Nó không mở ra hướng nào vì bài là forensics offline, không có service để chạm tới.
- Bookmark duy nhất tên "flag draft (do not lose)" nhưng `fk=3` trỏ tới trang
  Hollis Special Collections, không phải trang có form. Tên bookmark là mồi.
- `logins.json` trông như có encrypted credential. Thực ra `ZS5tYXJjaGV0dGlAaG9sbGlzLmVkdQ==`
  và `TW5EYXlXM2RuZXNkQHk3` chỉ là base64 của `e.marchetti@hollis.edu` / `MnDayW3dnesd@y7`,
  và cặp thứ hai là `anon-analyst` / `hunter2`. Không có PKCS#11 hay 3DES nào ở đây.

## Chuỗi khai thác

**Bước 1 - Xác minh artifact.** `sha256sum` trên zip khớp con số in trên thẻ đề trước khi mở,
rồi kiểm tra zip không có bất thường: 6 entry, comment rỗng, không có byte sau EOCD
(3486 - 3464 = 22 byte đúng bằng kích thước EOCD tối thiểu).

**Bước 2 - Đọc các nguồn tường minh.** `sqlite3` qua Python cho toàn bộ `moz_places`,
`moz_bookmarks`, `moz_formhistory`; `base64` cho `logins.json`. Không có chuỗi `POCTF{` nào
trong bốn nguồn đó. Quét `grep -rao "POCTF{[^}]*}"` trên toàn bộ tree giải nén ra đúng một kết
quả, nằm trong `recovery.jsonlz4` đang bị nén.

**Bước 3 - Giải mã container jsonlz4.** File mở đầu bằng `6d 6f 7a 4c 7a 34 30 00` tức
`mozLz40\0` (8 byte), tiếp là 4 byte kích thước gốc little-endian (`0x00000291` = 657), rồi tới
một LZ4 block thuần. Điểm dễ sai: nếu đoán header là 6 byte rồi đọc size ở offset 6 sẽ nhận về
`0x0291_0000` và `lz4.block` chết với "insufficient space in destination buffer":

```python
assert blob[:8] == b"mozLz40\x00"
size = struct.unpack("<I", blob[8:12])[0]
data = lz4.block.decompress(blob[12:], uncompressed_size=size)
```

`pip install lz4` có wheel Windows cho cp312, không cần build.

**Bước 4 - Đọc form data.** JSON giải ra một cửa sổ một tab, URL là trang provenance
`catalog.spr.org.uk/apparatus/provenance/lssf`, và `formdata.id` còn nguyên bốn field người
dùng đã gõ nhưng chưa submit:

```json
"workstation":   "hollis-office-desktop-elena"
"analyst-name":  "K. Vance"
"artifact-flag": "POCTF{109.612.I777LWHDFNCWRJ2S.JB6P5ZRASWPVYKKKHXKAPSQFWT}"
"case-notes":    "Subject: E. Marchetti disappearance. Chain of custody initiated 2026-06-29..."
```

**Bước 5 - Kiểm tra tính hợp lệ của cờ.** Khuôn cờ POCTF là
`POCTF{<cid>.<team_id>.<nonce>.<sig26>}` với `sig26` là base32 của HMAC-SHA256 cắt còn 26 ký tự
(rút từ `_build_marker()` trong source bài read-me-my-fortune). Chuỗi này khớp: cid 109,
team 612 đúng team của zip, nonce `I777LWHDFNCWRJ2S` 16 ký tự alphanumeric, sig 26 ký tự base32.
Đó là lý do chọn field `artifact-flag` chứ không phải ba field kia, và cũng là cách xác nhận
không cần chờ server trả lời.

## Cờ

```text
POCTF{109.612.I777LWHDFNCWRJ2S.JB6P5ZRASWPVYKKKHXKAPSQFWT}
```

## Chạy lại

```bash
cd everything-left-open
python exploit.py
```

Script tự verify sha256, dump hết các nguồn sqlite và logins, giải jsonlz4 và in field chứa cờ.
Chạy với bản zip của team khác: `python exploit.py <duong-dan-zip>`.
