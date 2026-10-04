# notes.md - gerry-the-larry-1

Input: `files/catcounty_results.zip` (37241 B, sha256 `462c4d84…5a9cb4`)
Bên trong: `gerry_final_files/info.csv` (38328 B), `check_in.log` (45881 B), `votes.log` (49441 B)
Định dạng cờ đề yêu cầu: `cdctf{##}` (hai chữ số)

## H1 - info.csv và check_in.log nối được với nhau
cmd: `python solve.py` (bản scratch, nay là bước 1 của `exploit.py`)
evidence: 1067/1067 `voter_id` trong `check_in.log` khớp `info.csv` (`vid in checkin not in info = 0`,
`voters never used = 0`, không id nào hai lần); `info.csv` có 36 giá trị `block`, tổng cử tri mỗi
block bằng 1067.
result: OK (một phần) - xác định được block của từng lượt điểm danh, nhưng vẫn chưa có phiếu.

## H2 - votes.log có khoá nối thẳng sang check_in.log
cmd: `python solve.py` (nối theo số thứ tự) rồi `cut -d: -f4 votes.log | sort | uniq -c | sort -rn`
evidence: `checkin sn without vote = 1067`, `vote sn without checkin = 1067`, giao rỗng. Receipt là
dãy 9 chữ số 550408395..550409461, ballot là dãy 12 chữ số 381009204091..381009205157. Lệnh `cut`
in ra 1067 giá trị khác nhau mỗi giá trị một lần, tức field 4 là số ballot chứ không phải tên đảng.
result: DEAD - hai log dùng hai không gian đánh số độc lập, không có join key; tên đảng nằm từ field 5
trở đi vì timestamp cũng chứa dấu chấm hai (`2026-10-01 08:00:45:381009204091:Nap Rights`).

## H3 - nối hai log theo thứ tự dòng (giả thuyết hàng đợi FIFO)
cmd: `python link.py` (bản scratch, nay là `analysis/alignment.py`)
evidence: `checkin monotonic: True`, `votes monotonic: True`, hai dãy số thứ tự đều tăng đúng 1,
cùng 1067 dòng. Độ lệch `votes[i] - checkin[i]`: min=560 s, mean=869.4 s, max=1184 s, `neg=0`. Cửa sổ
thời gian: check_in 07:45:27..17:46:32, votes 08:00:45..17:59:50, tức phiếu luôn trễ hơn lượt điểm
danh ở cả đầu lẫn cuối.
result: PENDING -> xác nhận ở H4 và H5.

## H4 - phép nối có thể bị dịch pha một dòng mà không phát hiện ra
cmd: `python analysis/sensitivity.py files/catcounty_results.zip`
evidence: lag -1 và +1 vẫn cho toàn bộ độ lệch dương (min 599 s và 522 s), nên tính dương một mình
không phân biệt được; nhưng hai cách đó chỉ ghép được 1066 cặp (thừa một lượt điểm danh và một phiếu
không đối tượng) và cho số ghế khác: 10 (lag -1), 12 (lag 0), 9 (lag +1).
result: DEAD cho lag khác 0 - hai log dài bằng nhau, mỗi cử tri điểm danh đúng một lần, nên phép gán
1-1 giữ thứ tự duy nhất là i với i; dịch pha sẽ bỏ lại một đối tượng không có phiếu hoặc không có cử tri.

## H5 - kiểm chứng độc lập cho phép gán
cmd: `python validate.py` (bản scratch, nay tích hợp ở bước 3 của `exploit.py`)
evidence: số phiếu gom được của từng block bằng đúng số cử tri đăng ký của block đó, 36/36 block khớp,
tổng 1067 = 1067; mỗi voter xuất hiện đúng một lần trong `check_in.log`.
result: OK - phép gán không làm mất phiếu, không gán nhầm block.

## H6 - thể lệ phân định block: plurality hay đa số tuyệt đối
cmd: đọc bảng kết quả trong `analysis/exploit_output.txt`
evidence: không block nào hoà phiếu (36/36 có đảng nhiều phiếu nhất duy nhất). Plurality cho Meowjority
12/36 ghế dù về nhì số phiếu (286/1067 = 26.8%); đa số tuyệt đối (>50%) cho 9 ghế, làm rớt Scratching
Post Street 11/32, Tuna Terrace 11/25, Windowsill Way 6/20. Plurality cũng khớp tình tiết gerrymandering
của đề (tỉ lệ ghế 33.3% vượt tỉ lệ phiếu 26.8%), trong khi Domestic Loafs nhiều phiếu nhất (293) chỉ giữ
9 ghế.
result: OK (plurality) - ghi nhận đề không nêu rõ thể lệ; lựa chọn này dựa trên bảng phân bố ghế và
tình tiết của đề.

## H7 - có đối chiếu được cờ qua nộp bài không
cmd: không chạy - CDCTF là instance live và theo quy trình của giải thì người chơi thao tác tay
evidence: `cdctf{12}` được tính cục bộ từ 1067 phiếu, không phải chuỗi có sẵn trong artifact; định dạng
hai chữ số khớp yêu cầu của đề.
result: PENDING - cần người nộp để xác nhận, giá trị dự kiến `cdctf{12}`.

## Ghi chú thêm

- Tên 36 block trong `info.csv` trùng bảng precinct 6x6 của client bài Gerry the Larry (2/2) (Treat Jar
  Terrace, Cushion Hill, Biscuit Bend, ...), nên danh sách 12 block thắng ở đây là đầu vào trực tiếp cho phần 2.
- Scratch của phiên làm bài: `Downloads/_scratch/catcounty/{solve,link,validate,sensitivity}.py`.

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
