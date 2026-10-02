# Everything Left Open - Forensics

**Điểm:** 100 · **Wave:** 1 
**Cờ:** `POCTF{109.612.I777LWHDFNCWRJ2S.JB6P5ZRASWPVYKKKHXKAPSQFWT}`

**File cung cấp:** `files/left-open-profile-team-612.zip` (3.486 byte, mã băm sha256 `faadae549b93f75a...` khớp với thông tin trên thẻ đề).

## Đề bài

Tình huống đặt ra: Một vị khách vội vã rời đi, bỏ quên lại chiếc laptop tại phòng khách sạn. Máy tính vẫn đang trong trạng thái mở khoá, và trình duyệt web thì đang hiển thị dang dở một biểu mẫu (form) chưa kịp gửi. Đội phản ứng sự cố IT bên ngoài đã can thiệp và đóng gói toàn bộ hiện trạng này thành một tệp tin zip. 
Nhiệm vụ của bạn là truy tìm lá cờ được giấu trong phiên làm việc (session) đó, với lời dặn dò "hãy chú ý đến các chi tiết". Đáng chú ý, file zip được sinh riêng biệt cho từng đội chơi (mỗi đội nhận một file độc bản).

## Phân tích ban đầu

Bên trong tệp nén là một thư mục hồ sơ người dùng Firefox mang tên `k-vance-profile`, chứa đúng 5 tệp tin cốt lõi:

| Tên File | Chẩn đoán nội dung |
| --- | --- |
| `places.sqlite` | Bảng `moz_places` chứa 8 dòng lịch sử duyệt web + bảng `moz_bookmarks` chứa 1 dòng. |
| `formhistory.sqlite` | Bảng `moz_formhistory` chứa 3 dòng: tìm kiếm `search` = "eighth session lssf redacted", tài khoản `email` = "e.marchetti@hollis.edu", và `search` = "halberd office hours wednesday". |
| `logins.json` | 2 bản ghi đăng nhập, các trường `encryptedUsername` và `encryptedPassword` thực chất chỉ mã hoá base64 thông thường chứ không dùng cơ chế bảo mật mạnh. |
| `prefs.js` | Ghi nhận cấu hình: giả mạo `general.useragent.override` thành Firefox/119.0, `browser.startup.page=3`, và bật `resume_from_crash=true`. |
| `sessionstore-backups/recovery.jsonlz4` | File khôi phục phiên nặng 584 byte, được nén dưới định dạng container `mozLz40\0`. |
| `README.txt` | Dòng thông điệp bí ẩn: Docket MARCHETTI/2026-14, "Find what she was about to submit." (Hãy tìm thứ cô ấy định gửi đi). |

Lời gợi ý "data entered mid-form" (dữ liệu nhập dở giữa chừng) và "what she was about to submit" (thứ cô ấy định gửi) là mũi tên chỉ thẳng vào tệp lưu trữ phiên (session store): bởi đây chính là nơi duy nhất Firefox tự động lưu lại những nội dung người dùng đã gõ vào form nhưng chưa kịp bấm nút submit. Các file sqlite còn lại đóng vai trò như những gia vị để tái tạo lại bức tranh toàn cảnh của cuộc điều tra.

## Khám nghiệm các chi tiết lạc hướng (Rabbit Holes)

Có ba chi tiết cực kỳ dễ đánh lừa người chơi, chúng không dẫn tới cờ nhưng lại phục vụ hoàn hảo cho tiêu chí "chú ý đến các chi tiết" của tác giả:

- Trong bảng `moz_places`, bản ghi mang id 99 chứa url là `https://catalog.spr.org.uk/apparatus/provenance/lssf`, nhưng trường `rev_host` (chuỗi hostname đảo ngược) lại là `moc.ftcwolfrevoretniop.nimda.` (giải mã ra là `admin.pointeroverflowctf.com`). Trên thực tế, `rev_host` là một cột do Firefox tự động nội suy từ url; việc hai cột này mâu thuẫn khốc liệt chứng tỏ bản ghi này đã được ai đó (hoặc tác giả) "ghép tay" giả mạo. Tuy nhiên, nó không mở ra hướng tấn công nào vì đây là thử thách forensics ngoại tuyến (offline), không hề có service thật để chúng ta tương tác.
- Bookmark duy nhất có tên gọi cực kỳ khiêu khích "flag draft (do not lose)". Thế nhưng trường `fk=3` lại trỏ nó về một trang của Hollis Special Collections, hoàn toàn không phải là trang web chứa form điền thông tin. Cái tên hấp dẫn kia chỉ là một mồi nhử rẻ tiền.
- Tệp `logins.json` nhìn bề ngoài có vẻ chứa thông tin xác thực bị mã hoá sâu. Nhưng nếu tinh mắt, các chuỗi `ZS5tYXJjaGV0dGlAaG9sbGlzLmVkdQ==` và `TW5EYXlXM2RuZXNkQHk3` chỉ là lớp mặt nạ base64 ngây ngô của tài khoản `e.marchetti@hollis.edu` / `MnDayW3dnesd@y7`, và cặp thứ hai lột ra là `anon-analyst` / `hunter2`. Hoàn toàn không có thuật toán PKCS#11 hay 3DES cao siêu nào ở đây.

## Chuỗi khai thác

**Bước 1 - Giám định hiện trường (Artifact Verification).** 
Việc đầu tiên là chạy lệnh `sha256sum` trên tệp zip để đảm bảo nó nguyên vẹn và khớp với mã băm trên thẻ đề trước khi bung nén. File nén sạch sẽ: 6 mục (entry), phần comment trống rỗng, không hề có byte thừa thãi giấu sau khối EOCD (phép tính 3486 - 3464 = 22 byte vừa vặn với kích thước chuẩn tối thiểu của một khối EOCD).

**Bước 2 - Vét cạn các nguồn dữ liệu thô.** 
Dùng `sqlite3` nhúng trong Python để kết xuất (dump) sạch sẽ toàn bộ các bảng `moz_places`, `moz_bookmarks`, `moz_formhistory`; và dùng thư viện `base64` để bóc tách `logins.json`. Không tìm thấy bất kỳ dấu vết nào của chuỗi tiền tố `POCTF{` trong các nguồn tĩnh này. Khi quét bằng lệnh bạo lực `grep -rao "POCTF{[^}]*}"` lên toàn bộ cây thư mục vừa giải nén, công cụ trả về đúng một kết quả duy nhất đang nằm thoi thóp trong tệp `recovery.jsonlz4` đang bị nén chặt.

**Bước 3 - Phá vỡ container jsonlz4.** 
Tệp tin Firefox jsonlz4 luôn được bảo vệ bởi phần header mở đầu bằng chuỗi 8 byte `6d 6f 7a 4c 7a 34 30 00` (dịch ra là `mozLz40\0`). Tiếp nối ngay sau đó là 4 byte ghi lại kích thước tệp gốc trước khi nén dưới định dạng little-endian (ở đây là `0x00000291`, tương đương 657 byte). Ngay sau header là một khối nén LZ4 thuần tuý. Cạm bẫy chết người nằm ở đây: nếu bạn nhầm tưởng header chỉ dài 6 byte và cố đọc kích thước ở offset 6, bạn sẽ nhận về một con số điên rồ `0x0291_0000`, khiến thư viện giải nén `lz4.block` chết sặc với lỗi "insufficient space in destination buffer":

```python
assert blob[:8] == b"mozLz40\x00"
size = struct.unpack("<I", blob[8:12])[0]
data = lz4.block.decompress(blob[12:], uncompressed_size=size)
```

Gói `pip install lz4` đã có sẵn wheel Windows cho Python 3.12, không đòi hỏi biên dịch phức tạp.

**Bước 4 - Bóc tách dữ liệu Form.** 
Chuỗi JSON thu được sau khi giải nén hé lộ trạng thái của một cửa sổ trình duyệt chỉ mở một tab duy nhất. Tab này đang chốt tại URL `catalog.spr.org.uk/apparatus/provenance/lssf`. Quý giá hơn, thuộc tính `formdata.id` vẫn còn lưu giữ nguyên vẹn bốn trường thông tin mà người dùng đã cặm cụi gõ vào nhưng chưa kịp nhấn submit:

```json
"workstation":   "hollis-office-desktop-elena"
"analyst-name":  "K. Vance"
"artifact-flag": "POCTF{109.612.I777LWHDFNCWRJ2S.JB6P5ZRASWPVYKKKHXKAPSQFWT}"
"case-notes":    "Subject: E. Marchetti disappearance. Chain of custody initiated 2026-06-29..."
```

**Bước 5 - Đối chiếu chữ ký bảo mật.** 
Chuẩn cờ của giải POCTF luôn tuân thủ nghiêm ngặt định dạng:
`POCTF{<cid>.<team_id>.<nonce>.<sig26>}` 
(với `sig26` là hệ chữ số base32 của mã băm HMAC-SHA256 bị cắt cụt còn 26 ký tự - cấu trúc này từng bị lộ trong mã nguồn của bài `read-me-my-fortune`). 
Chuỗi thu được khớp hoàn hảo: chỉ số `cid` là 109, mã đội `team` là 612 (trùng khớp với file zip cấp cho đội), phần `nonce` là chuỗi `I777LWHDFNCWRJ2S` dài 16 ký tự, và phần chữ ký `sig` dài đúng 26 ký tự base32. 
Đó chính là lý do tuyệt đối để khẳng định field `artifact-flag` là nơi chứa lá cờ thực sự, chứ không phải ba field còn lại, và ta có thể nộp cờ tự tin mà không cần máy chủ phải mớm lời xác nhận.

## Flag

```text
POCTF{109.612.I777LWHDFNCWRJ2S.JB6P5ZRASWPVYKKKHXKAPSQFWT}
```

## Phục dựng (Reproduce)

```bash
cd everything-left-open
python exploit.py
```

Công cụ `exploit.py` được thiết kế để tự động hoá từ A đến Z: xác thực toàn vẹn sha256, móc ruột toàn bộ các bảng sqlite, bóc tách tài khoản trong logins, giải nén hoàn chỉnh định dạng jsonlz4 đặc thù của Firefox và in trực tiếp trường chứa cờ. Nếu muốn chạy với tệp zip cấp cho một đội khác, chỉ cần nối thêm đối số: `python exploit.py <duong-dan-zip>`.
