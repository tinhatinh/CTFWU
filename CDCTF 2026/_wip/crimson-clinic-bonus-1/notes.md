# notes.md - crimson-clinic-bonus-1 (CHƯA CÓ CỜ)

Thẻ bài: CDCTF 2026, OSINT, 500 điểm, tác giả adlee7 / b0b / dontfeedthepenguins.
Định dạng cờ: `cdctf{Firstname Lastname, Firstname Lastname, Firstname Lastname}`, thứ tự bất kỳ.
Input: không có artifact, không có URL trong bản paste.

## H1 - Định vị giải đấu để biết dữ liệu ở đâu
cmd: `curl -s https://ctftime.org/event/3293/` và `curl -sL https://crimsondefense.org/cdctf/`
evidence: CTFtime tiêu đề "CTFtime.org / CDCTF 2026", mô tả "Crimson Defense CTF 2026 will be held on Saturday, October 3rd", do Crimson Defense Cyber Security Club at the University of Alabama. Trang giải đấu trả HTTP 200, 14204 byte, window 03/10 15:00 UTC - 04/10 03:00 UTC, Jeopardy.
result: OK - đây là CDCTF 2026 đang chạy, motif "Crimson" của Alabama (khớp ví dụ cờ Paul Bryant / Gene Stallings / Nick Saban trên thẻ)

## H2 - "Crimson Social" là site thật hay người thật
cmd: `WebSearch: "Crimson Clinic" CTF OSINT "Crimson Social" Medical Director cdctf`
evidence: `No results found`. Search mở rộng (`cdctf{ flag format ...`, `"cdctf{" CTF writeup 2026`) chỉ trả về bài hướng dẫn OSINT chung và trang CTFtime.
result: DEAD cho hướng tra cứu người thật - nhân viên Clinic là hư cấu, tác giả dựng dữ liệu trong hạ tầng của giải

## H3 - Tìm URL nền tảng từ trang công khai
cmd: `curl -sL https://crimsondefense.org/cdctf/ | grep -oE 'href="[^"]+"' | sort -u` và cùng lệnh với `/scoreboard`
evidence: danh sách href chỉ gồm điều hướng nội bộ (`/cdctf`, `/scoreboard`, `/uactf`, `/club-leadership`, ...), form Google Forms đăng ký, GitHub `UACrimsonDefense`, Instagram, LinkedIn, Google Maps. Không có domain chơi bài, không có link "Crimson Social". Trang `/scoreboard` chỉ trỏ bản 2025 (CTFtime event 2846).
result: DEAD - nền tảng 2026 và instance bị đăng nhập chặn, chỉ người chơi có tài khoản mới thấy link trên thẻ bài

## H4 - Ràng buộc cách làm
cmd: đọc text trên `/cdctf`
evidence: hai dòng in trên trang giải: `Attacking the CDCTF platform is strictly prohibited` và `Using automated tools against the CDCTF hosted challenges is prohibited unless specified`.
result: OK - không scan, không spider, không brute-force endpoint. Đầu vào phải do người chơi paste hoặc screenshot

## H5 - Kiểm tra kho và memory của đội
cmd: `grep -rli "crimson" ~/Downloads/CTFWU ~/Downloads/_scratch` và `ls "CDCTF 2026/_wip"`
evidence: `_wip/crimson-clinic-bonus-2/de.md` (session khác) treo đúng cùng dạng: một sự kiện về nhân viên hư cấu, không URL, không file. Memory `reference-ctf-crimson-clinic.md` ghi series Crimson Clinic là kiosk Discord điều khiển bằng `CDCTF Bot`, "the card carries no URL and no file: the interface is a per-team Discord text channel", người chơi là vận chuyển lệnh.
result: PENDING - hướng đi nhiều khả năng đúng là hỏi bot / lấy link từ channel kiosk, nhưng chưa có bằng chứng cho bonus 1

## Trạng thái
BLOCKED chờ đầu vào. Cần một trong hai:
1. URL Crimson Social nguyên văn từ thẻ bài hoặc channel kiosk.
2. Screenshot/paste trang giới thiệu hoặc danh sách nhân viên trên Crimson Social.

Có đầu vào thì việc còn lại chỉ là đọc ba chức danh: Medical Director, Chief Administration Officer, Chief Financial Officer, rồi ghép `cdctf{A B, C D, E F}` (thứ tự không quan trọng).

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
