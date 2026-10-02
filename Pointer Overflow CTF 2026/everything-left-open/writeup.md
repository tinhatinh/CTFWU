# Everything Left Open - Forensics

**Điểm:** 100 · **Wave:** 1 
**Cờ:** `POCTF{109.612.I777LWHDFNCWRJ2S.JB6P5ZRASWPVYKKKHXKAPSQFWT}`

**File cung cấp:** `files/left-open-profile-team-612.zip` (3.486 byte, mã băm sha256 `faadae549b93f75a...` khớp với thông tin trên thẻ đề).

## Đề bài

Tình huống đặt ra: Một vị khách rời đi và để lại laptop tại phòng khách sạn. Máy tính vẫn đang mở khoá, trình duyệt web đang hiển thị một biểu mẫu (form) chưa được gửi. Đội phản ứng sự cố đã can thiệp và đóng gói toàn bộ hiện trạng thành một tệp tin zip. Nhiệm vụ của người chơi là tìm lá cờ được giấu trong phiên làm việc (session) đó, với gợi ý "hãy chú ý đến các chi tiết". Mỗi đội chơi sẽ nhận được một file zip có nội dung khác nhau.

## Phân tích ban đầu

Bên trong tệp nén là một thư mục hồ sơ người dùng Firefox tên `k-vance-profile`, chứa 5 tệp tin chính:

| Tên File | Phân tích nội dung |
| --- | --- |
| `places.sqlite` | Bảng `moz_places` chứa 8 dòng lịch sử duyệt web và bảng `moz_bookmarks` chứa 1 dòng. |
| `formhistory.sqlite` | Bảng `moz_formhistory` chứa 3 dòng: tìm kiếm `search` = "eighth session lssf redacted", tài khoản `email` = "e.marchetti@hollis.edu", và `search` = "halberd office hours wednesday". |
| `logins.json` | 2 bản ghi đăng nhập, các trường `encryptedUsername` và `encryptedPassword` được mã hoá base64 thông thường, không dùng cơ chế bảo mật phức tạp. |
| `prefs.js` | Ghi nhận cấu hình: `general.useragent.override` thiết lập thành Firefox/119.0, `browser.startup.page=3`, và `resume_from_crash=true`. |
| `sessionstore-backups/recovery.jsonlz4` | File khôi phục phiên có kích thước 584 byte, được nén dưới định dạng `mozLz40\0`. |
| `README.txt` | Chứa thông điệp: Docket MARCHETTI/2026-14, "Find what she was about to submit." |

Gợi ý "data entered mid-form" và "what she was about to submit" chỉ ra rằng dữ liệu mục tiêu nằm trong tệp lưu trữ phiên (session store). Đây là nơi Firefox lưu lại nội dung người dùng đã nhập vào form nhưng chưa bấm submit. Các file sqlite còn lại cung cấp thông tin ngữ cảnh để hỗ trợ quá trình phân tích.

## Phân tích các dữ liệu nhiễu (Rabbit Holes)

Có ba chi tiết dễ gây nhầm lẫn nhưng không chứa dữ liệu cờ:

- Trong bảng `moz_places`, bản ghi id 99 chứa url `https://catalog.spr.org.uk/apparatus/provenance/lssf`, nhưng trường `rev_host` lại là `moc.ftcwolfrevoretniop.nimda.` (giải mã thành `admin.pointeroverflowctf.com`). Thực tế, `rev_host` là cột do Firefox tự nội suy từ url. Sự mâu thuẫn giữa hai cột này cho thấy bản ghi đã được chỉnh sửa thủ công. Tuy nhiên, do đây là thử thách forensics ngoại tuyến (offline), thông tin này không dẫn đến phương pháp khai thác nào.
- Bookmark duy nhất có tên "flag draft (do not lose)". Tuy nhiên, trường `fk=3` trỏ về một trang của Hollis Special Collections, không phải trang chứa form điền thông tin. Đây là một dữ liệu giả (decoy).
- Tệp `logins.json` trông giống như chứa thông tin xác thực bị mã hoá. Thực tế, các chuỗi `ZS5tYXJjaGV0dGlAaG9sbGlzLmVkdQ==` và `TW5EYXlXM2RuZXNkQHk3` chỉ là dữ liệu base64 của tài khoản `e.marchetti@hollis.edu` / `MnDayW3dnesd@y7`, cặp thứ hai là `anon-analyst` / `hunter2`.

## Quá trình phân tích

**Bước 1 - Xác thực toàn vẹn dữ liệu.** 
Kiểm tra mã băm sha256 của tệp zip để đảm bảo khớp với thông tin trên thẻ đề. File nén bao gồm 6 mục, phần comment trống, không có byte thừa ở khối EOCD.

**Bước 2 - Trích xuất dữ liệu thô.** 
Sử dụng `sqlite3` trong Python để kết xuất dữ liệu các bảng `moz_places`, `moz_bookmarks`, `moz_formhistory`; và thư viện `base64` để phân tích `logins.json`. Không phát hiện chuỗi có tiền tố `POCTF{`. Khi tìm kiếm chuỗi regex `POCTF{[^}]*}` trên toàn bộ thư mục, công cụ trả về một kết quả duy nhất trong tệp `recovery.jsonlz4` đang bị nén.

**Bước 3 - Giải nén định dạng jsonlz4.** 
Tệp Firefox jsonlz4 bắt đầu bằng phần header 8 byte `6d 6f 7a 4c 7a 34 30 00` (`mozLz40\0`). Theo sau là 4 byte little-endian ghi kích thước tệp gốc (`0x00000291` hoặc 657 byte). Ngay sau header là khối nén LZ4. Cần lưu ý đọc đúng độ dài header (8 byte) để tránh lỗi không đủ bộ đệm (insufficient space in destination buffer) khi sử dụng thư viện `lz4.block`. Cài đặt thư viện `lz4` trên Python để hỗ trợ giải nén định dạng này.

**Bước 4 - Phân tích dữ liệu Form.** 
Chuỗi JSON thu được cho thấy trạng thái của một tab đang mở tại URL `catalog.spr.org.uk/apparatus/provenance/lssf`. Thuộc tính `formdata.id` chứa bốn trường thông tin chưa được gửi:

```json
"workstation":   "hollis-office-desktop-elena"
"analyst-name":  "K. Vance"
"artifact-flag": "POCTF{109.612.I777LWHDFNCWRJ2S.JB6P5ZRASWPVYKKKHXKAPSQFWT}"
"case-notes":    "Subject: E. Marchetti disappearance. Chain of custody initiated 2026-06-29..."
```

**Bước 5 - Đối chiếu định dạng cờ.** 
Cờ của giải POCTF có định dạng: `POCTF{<cid>.<team_id>.<nonce>.<sig26>}`.
Chuỗi thu được có chỉ số `cid` là 109, mã đội `team` là 612 (trùng khớp với file zip), `nonce` là `I777LWHDFNCWRJ2S` (16 ký tự), và chữ ký `sig` dài 26 ký tự base32. Cấu trúc này xác nhận tính hợp lệ của cờ tại trường `artifact-flag`.

## Flag

```text
POCTF{109.612.I777LWHDFNCWRJ2S.JB6P5ZRASWPVYKKKHXKAPSQFWT}
```

## Reproduce

```bash
cd everything-left-open
python exploit.py
```

Tệp `exploit.py` tự động hóa các bước: kiểm tra sha256, trích xuất dữ liệu sqlite, giải mã base64 các tài khoản, giải nén định dạng jsonlz4 của Firefox và in cờ. Có thể áp dụng cho tệp zip của đội khác thông qua đối số: `python exploit.py <duong-dan-zip>`.
