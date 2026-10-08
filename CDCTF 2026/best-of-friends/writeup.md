# Best of Friends - Crypto (500 points)

**Flag:** `cdctf{friendshipisalotlikecheese}`
**Files:** `files/bestfriends.txt`, 107 byte, sha256 `24d05085a4c80d16f3110682536ec0d314ae49412ebe0b4a7285f0a98c537269`

## Đề bài

adlee7 cho một file ciphertext duy nhất và gợi ý Tom & Jerry, cặp mèo chuột "đuổi
nhau trong vòng lặp bất tận từ 1940". Cờ có dạng `cdctf{plaintextgoeshere}`, tức là
kết quả giải mã phải là một chuỗi chữ cái viết thường, không khoảng trắng.

## Phân tích

```text
//\ /\// /\\\ /\ \/// //// \/\ /\\ /\\\ //\/ /\\\ \/\ / \\\/ /\/ \\/\ \\\/ /\\\ \\/ /\ /// /\\ /\ /\ \/\ /\
```

- 107 byte = 82 ký tự + 25 khoảng trắng. Ngoài `/`, `\` và space không còn byte nào
  khác; không BOM, không newline cuối file, không tìm thấy dữ liệu byte bổ sung.
- 26 nhóm, chỉ 15 hình dạng khác nhau. Nhóm lặp lại y nguyên hình dạng: `/\` 5 lần,
  `/\\\` 4 lần, `\/\` 3 lần, `\\\/` và `/\\` mỗi loại 2 lần.
- Độ dài nhóm từ 1 đến 4 (histogram 1/5/9/11). Cùng bộ đếm nhưng khác thứ tự vẫn là
  mẫu khác nhau: bộ `(3 slash, 1 backslash)` có `\///`, `//\/`, `/\//`; bộ
  `(1 slash, 2 backslash)` có `/\\`, `\/\`, `\\/`. Đơn vị mã hoá là cả hình dạng,
  không phải số lượng.
- Tính lặp ở trên là dấu hiệu của bảng chữ cái thay thế một-một (mẫu = chữ cái),
  không phải mã bit theo vị trí.

## Hướng đã thử

Bằng chứng số liệu ở `analysis/triage.txt`, sinh lại bằng `python analysis/triage.py`.

1. **Morse, mỗi nhóm một chữ cái**: 24/26 nhóm là mã Morse hợp lệ khi `/` = dit (hai
   nhóm `\\\/` = `---.` không có trong bảng), 25/26 khi `\` = dit (nhóm `////` =
   `----`). Chuỗi thu được `ULJABHKWJFJKE?RQ?JGASWAAKA` và
   `GYBNJ?RDBQBRTVKFVBUNODNNRN` vẫn vô nghĩa sau 25 dịch chuyển Caesar và
   Vigenère/Beaufort/autokey với khoá theo theme (TOM, JERRY, TOMANDJERRY,
   BESTFRIENDS, 1940, CAT, MOUSE, CHASE, LOOP).
2. **Nhóm là số**: độ dài nhóm (1..4), số `/` (0..4), số `\` (0..3), hiệu hai số,
   giá trị nhị phân của nhóm (0..14), số lần đổi hướng. Quét mỗi đại lượng đọc trực
   tiếp A1Z26, đọc cộng dồn mod 26, và ghép 2 nhóm liên tiếp làm toạ độ với cơ số
   4, 5, 6, 7, 8, 10, 16, 26, 27. Không có tổ hợp nào cho chuỗi chứa từ tiếng Anh
   hay `cdctf`.
3. **Bỏ khoảng trắng, đọc 82 ký tự như bit stream**: 82 = 10 byte + 2 bit thừa; đọc
   độ dài nhóm theo run-length của một bit stream đảo xen kẽ cho
   `1e 18 78 e1 e1 de 3c 3c 63 98` (4/10 byte in được) và với bit đầu là 1 cho
   `e1 e7 87 1e 1e 21 c3 c3 9c 67` (2/10).

## Lời giải

**Bước 1 - Nhận diện Code Tom-Tom.** Ciphertext dùng đúng hai ký tự, chia nhóm biến
độ dài, tách chữ bằng space: đó là cấu trúc của một bảng chữ cái thay thế hai ký tự.
Code Tom-Tom gán cho mỗi chữ cái A-Z một mẫu `/` và `\` cố định. 15 mẫu trong file
khớp 15 chữ cái của bảng, và không mẫu nào trong bảng trùng nhau nên phép tách nhóm
là xác định:

| Mẫu | Chữ | Mẫu | Chữ | Mẫu | Chữ | Mẫu | Chữ |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `/` | A | `/\` | E | `///` | C | `////` | D |
| `//\` | F | `/\\` | H | `/\\\` | I | `\\/` | K |
| `\/\` | S | `\///` | N | `/\//` | R | `//\/` | P |
| `/\/` | O | `\\\/` | L | `\\/\` | T | | |

**Bước 2 - Giải mã và kiểm chứng round-trip.** `exploit.py` ánh xạ 26 nhóm theo bảng,
rồi mã hoá lại chính chuỗi chữ cái vừa thu được bằng bảng đó và so từng byte với file
gốc:

```bash
python exploit.py files/bestfriends.txt
```

```text
groups    : 26
characters: 82
plaintext : FRIENDSHIPISALOTLIKECHEESE
round-trip: OK (re-encode khop tung byte voi file goc)
flag      : cdctf{friendshipisalotlikecheese}
```

Kết quả được đối chiếu như sau: 26/26 nhóm đều có mặt trong
bảng và ánh xạ là 1-1; re-encode khớp cả 107 byte của file; và 26 chữ cái ghép thành
câu tiếng Anh "Friendship is a lot like cheese", đúng hướng gợi ý của đề.

## Kết quả

```text
cdctf{friendshipisalotlikecheese}
```

Cờ tính từ dữ liệu trong file đề, chưa đối chiếu bằng submission lên nền tảng CDCTF.

## Tái hiện

```bash
cd "CDCTF 2026/best-of-friends"
python analysis/triage.py                  # so lieu phan tich va 3 huong da loai
python exploit.py files/bestfriends.txt    # stage 2: decode + round-trip
```
