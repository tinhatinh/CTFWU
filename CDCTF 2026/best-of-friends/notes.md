# notes.md - best-of-friends

Input: `files/bestfriends.txt` (107 B, sha256 `24d05085a4c80d16f3110682536ec0d314ae49412ebe0b4a7285f0a98c537269`)
Định dạng cờ đề yêu cầu: `cdctf{...}`, ví dụ `cdctf{plaintextgoeshere}`.

## H1 - Morse, mỗi nhóm một chữ cái
cmd: `python analysis/triage.py` (mục `[*] morse scan`)
evidence: `/` = dit cho 24/26 nhóm hợp lệ, hai nhóm `\\\/` = `---.` không có trong bảng;
`\` = dit cho 25/26 nhóm, một nhóm `////` = `----` không có. Chuỗi chữ cái:
`ULJABHKWJFJKE?RQ?JGASWAAKA` và `GYBNJ?RDBQBRTVKFVBUNODNNRN`.
result: DEAD - bảng Morse đóng không kín, và cả hai chuỗi vẫn vô nghĩa sau 25 Caesar
cộng với Vigenère/Beaufort/autokey với khoá TOM, JERRY, TOMANDJERRY, BESTFRIENDS,
BESTOFFRIENDS, ENEMIES, WORST, CAT, MOUSE, LOOP, CHASE, 1940, ADLEE, PAL, SPY, COPS.

## H2 - Mỗi nhóm là một số
cmd: `python analysis/triage.py` (mục `[*] numeric reads`)
evidence: lengths `[3,4,4,2,4,4,3,3,4,4,4,3,1,4,3,4,4,4,3,2,3,3,2,2,3,2]`,
count(`/`) 0..4, count(`\`) 0..3, binary (`/`=0) 0..14, có các bộ `(4,0)`, `(3,0)`,
`(1,0)` nên không dùng được toạ độ lưới 1..5.
result: DEAD - quét ~20 hàm đặc trưng (độ dài, số `/`, số `\`, hiệu, giá trị nhị phân
thuận/nghịch, số lần đổi hướng, chỉ số ký tự đầu/cuối...), mỗi hàm thử 26 dịch chuyển
trực tiếp và 26 dịch chuyển cộng dồn; riêng ghép 2 nhóm liên tiếp làm toạ độ thì quét
cơ số 4/5/6/7/8/10/16/26/27 với dịch trong khoảng -3..+3; không chuỗi nào chứa từ
tiếng Anh hay `cdctf`.

## H3 - Bỏ khoảng trắng, đọc như bit stream
cmd: `python analysis/triage.py` (mục `[*] group lengths as run-lengths of an alternating bit stream`)
evidence: 82 symbol = 10 byte + 2 bit thừa; run-length với bit đầu 0 cho
`1e 18 78 e1 e1 de 3c 3c 63 98` (4/10 byte in được), bit đầu 1 cho
`e1 e7 87 1e 1e 21 c3 c3 9c 67` (2/10).
result: DEAD - độ dài không chia hết cho 8, phần lớn byte ra không in được.

## H4 - File có kênh phụ (stego)
cmd: `cat -A files/bestfriends.txt`, `wc -c`, `od -c`
evidence: 107 byte = 82 ký tự + 25 space, đúng một dòng, không newline cuối file,
không BOM, không ký tự trắng lặp.
result: DEAD - không còn byte nào để đọc ngoài hình dạng nhóm.

## H5 - Bảng chữ cái hai ký tự: Code Tom-Tom
cmd: tra technique "mã hoá chỉ dùng `/` và `\` chia nhóm" -> dCode Code Tom-Tom
evidence: mỗi chữ cái A-Z có một mẫu `/`\` cố định, space tách chữ; 15 mẫu trong file
khớp 15 chữ cái của bảng và không mẫu nào trùng.
result: PENDING -> xác nhận ở H6

## H6 - Giải mã và round-trip
cmd: `python exploit.py files/bestfriends.txt`
evidence: 26 nhóm -> `FRIENDSHIPISALOTLIKECHEESE` -> re-encode khớp 107/107 byte với
file gốc, và câu đọc thành tiếng Anh ("Friendship is a lot like cheese").
result: OK - cờ: `cdctf{friendshipisalotlikecheese}` (xem `flag.txt`), tính cục bộ,
chưa nộp để đối chiếu

---

Ghi chú tái sử dụng: với CTF khác, dấu hiệu nhận Code Tom-Tom là "chỉ `/` và `\`, chia
nhóm bằng space, độ dài nhóm 1..4, có nhóm lặp lại y nguyên hình dạng". Đừng thử lại
H1 (Morse) và H2 (đếm ký tự) trước: cả hai đều trông hợp lý nhưng chết ở tính đóng của
bảng và ở các bộ đếm có thành phần 0.
