# CSS CTF 2026

Writeups for challenges solved at [ctf.cybersecurity.sydney](https://ctf.cybersecurity.sydney/).  
CTFtime: [CSS CTF 2026: Return of Nexus](https://ctftime.org/event/3434) — 40 giờ, online, Jeopardy (Team & Solo), do Cybersecurity Society của Đại học Sydney tổ chức.

Flag format: `CSSCTF{...}` (xác nhận từ bài colour-shift, đề ghi rõ trên thẻ bài).

## Thông tin lấy từ CTFtime (30/09/2026)

- Mở: Wed 30 Sep 2026 06:00 UTC (tức 16:00 AEST) — Đóng: Thu 1 Oct 2026 22:00 UTC.
- Chuyên mục theo mô tả của ban tổ chức: Web Exploitation, Pwn, Reverse Engineering, Cryptography, Forensics, OSINT, AI/Prompt Injection.
- Rating weight đang là 0 và còn chờ bình chọn công khai, nên nhiều khả năng giải này không cộng điểm CTFTime cho đội; bảng "Thành tích" trên site sẽ không có thêm dòng nào từ CSS CTF.
- Discord ban tổ chức: [discord.gg/gUGqmt4Gqf](https://discord.gg/gUGqmt4Gqf)

## Tập tin của một bài

Tạo bằng script có sẵn, thêm `--wip` khi chưa ra cờ:

```bash
bash _template/new_case.sh "CSS CTF 2026" <ten-bai> "<duong-dan-file-de>" --wip
```

Ra cờ thì chuyển thư mục bài lên thẳng `<Event>/`, điền vào bảng dưới, và thêm dòng
`<Event>/<ten-bai>` vào `tools/solve_times.json` với giờ thực tế lúc ghi cờ (UTC+7).

## Solved Challenges

| Challenge | Category | Difficulty | Flag |
|-----------|----------|------------|------|
| [a-star-trail](a-star-trail/writeup.md) | Misc | Beginner* | `CSSCTF{P1JT-21.0}` |
| [a-star-trail-2](a-star-trail-2/writeup.md) | Misc | Intermediate | `CSSCTF{STARmaPdElAUNaY…geOMeTRy}` (136 ký tự, bản đầy đủ trong `a-star-trail-2/flag.txt`) |
| [chrono-i](chrono-i/writeup.md) | Crypto | Beginner | `CSSCTF{every_second_hides_a_secret}` |
| [chrono-ii](chrono-ii/) | Crypto | Intermediate | `CSSCTF{th3_cl0ck_r3m3mb3rs_3very_s3c0nd}` |
| [cloudy-spaceships](cloudy-spaceships/writeup.md) | Web | n/a | `CSSCTF{your_forecast_says_love_is_on_its_way}` |
| [colour-shift](colour-shift/) | Forensics | Beginner | `CSSCTF{SHINE ON}` |
| [dockside-ticket](dockside-ticket/writeup.md) | Pwn | Beginner | `CSSCTF{us3_4ft3r_fr33_d0cks1d3}` |
| [flappy-board](flappy-board/writeup.md) | Misc | Intermediate | `CSSCTF{birdddd}` |
| [lamp-drill](lamp-drill/writeup.md) | Warm-up | n/a | `CSSCTF{css}` |
| [lottery](lottery/writeup.md) | Web3 | n/a | `CSSCTF{CSS{U5E_4_R4ND0M_FUNCT10N}}` |
| [maintenance-log](maintenance-log/writeup.md) | Pwn | n/a | `CSSCTF{Duh_m4t3_1_4m_sl33py}` |
| [prince-walk](prince-walk/writeup.md) | Reverse | n/a | `CSSCTF{P12INC3_0R_P1NC3?}` |
| [server-juice](server-juice/) | OSINT | Beginner | `CSSCTF{premiumreserve}` |
| [severed-symmetry](severed-symmetry/writeup.md) | Crypto | Expert | `CSSCTF{P35T0_5CH3M3_4TT4CK2026}` |

Thẻ của prince-walk chỉ in số điểm (50), không có hạng độ khó, nên cột Difficulty để `n/a`
như lamp-drill và maintenance-log. Ba bài mới đều có bằng chứng độc lập: severed-symmetry được
xác nhận bằng cách mã hoá lại plaintext vừa thu với đúng public key của `out.txt` cho ra nguyên
3 block ciphertext gốc; prince-walk có FNV-1a do tác giả nhét trong payload (`763cc96c`) khớp với
72 byte trích ra; flappy-board nhận cờ thẳng từ response của `/api/complete` sau khi cả ba round
trả HTTP 200, và mô phỏng vật lý đã được `verified_score` của practice oracle đối chiếu trước đó.

Thẻ của lamp-drill và maintenance-log không in hạng độ khó (chỉ có số điểm), nên cột
Difficulty để `n/a`. Hai dòng đó link thẳng `writeup.md` vì `tools/build_site.py` chỉ
nhận diện thể loại từ ô link dạng `<ten-bai>/writeup.md`; các dòng khác trong bảng này
đang link thư mục nên site không lấy được Category của chúng.

\* Thẻ của a-star-trail không được lưu lại trong phiên (chỉ giữ phần mô tả), nên `Beginner` là
ước lượng theo thẻ a-star-trail-2 (187 / Intermediate), và cột này chưa có điểm số. Cờ của
chrono-i và a-star-trail-2 mới kiểm chứng cục bộ: mã hoá ngược lại ra đúng ciphertext gốc và xâu
ghép đọc thành danh sách thuật toán hình học. Riêng a-star-trail có xác nhận bảng điểm: bản tính
cả hai đầu `EP1JTL-21.0` bị từ chối, `CSSCTF{P1JT-21.0}` được chấp nhận.
