# notes.md - crimson-clinic-bonus-2

Đề: "What is the name of Jeffery Barrett's cat?", format `cdctf{Name}`, 500 điểm, tác giả `adlee7`, `b0b`, `dontfeedthepenguins`. Không có URL/file kèm theo.

## H1 - Jeffery Barrett là nhân vật có thật, tên con mèo nằm ở nguồn công khai
cmd: `WebSearch "Jeffery Barrett" cat name`; `"Jeffery Barrett" OR "Jeffrey Barrett" "Crimson"`; `"Jeffery Barrett" cat named pet owner trivia`
evidence: kết quả chỉ có trang nhiễu (bài Facebook về vụ ngược đãi thú y ở Hunt County, PDF học thuật, patent); không có trang nào gắn một Jeffery Barrett với Crimson Clinic
result: DEAD - không có nhân vật công khai khớp tên

## H2 - Crimson Clinic là site web của giải đấu, có trang hồ sơ nhân sự
cmd: `curl -o /dev/null -w "%{http_code}" -L` trên `crimsondefense.org/crimsonclinic`, `/clinic`, `/cdctf/clinic`, `clinic.crimsondefense.org`, `crimsonclinic.org`
evidence: `404 404 404` cho ba path trên miền chính, `000` (không resolve) cho hai miền giả định
result: DEAD - hạ tầng club không phục vụ clinic

## H3 - Tác giả công khai source của series trên GitHub
cmd: `curl https://api.github.com/orgs/UACrimsonDefense/repos` + `git/trees/main?recursive=1` cho `ClubResources`, `UACrimsonDefense.github.io`, `CyberSecurityClub`
evidence: org có 4 repo, cây file không có path nào khớp `clinic|barrett|cat|lore|cdctf`; `crimsondefense.org/blog` và `/feed.xml` không nhắc Crimson Clinic hay Barrett (GitHub code search cần auth, chưa kiểm tra)
result: DEAD (riêng code search vẫn mở)

## H4 - Data nằm trong kiosk của series Crimson Clinic
evidence: cùng event, cùng prefix `cdctf{}`, và tên chuỗi "Crimson Clinic" trùng với series AI Terminal 1 (Self Check-In, 493 điểm) và Terminal 2 (Triage, 500 điểm) mà giao diện là Discord channel do `CDCTF Bot` điều khiển; các thẻ đó cũng không kèm URL
result: PENDING - cần bản paste nội dung thẻ BONUS 1 và channel/instance của BONUS 2

## Kênh dự kiến khi có kiosk
- Hỏi trực tiếp bản ghi bệnh nhân: hồ sơ Jeffery Barrett, trường thông tin thú cưng.
- Khung "bệnh nhân yêu cầu bản ghi của chính mình" (subject access) như lane còn mở của Terminal 2.
- Rủi ro đã ghi nhận ở Terminal 2: bot chấp nhận khung "code giả cho script đào tạo" và bịa giá trị, nên mọi tên mèo nhận được phải đối chiếu qua một khung hỏi thứ hai trước khi nộp.
- Không tìm writeup trên mạng; chỉ dùng dữ liệu của instance.

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
