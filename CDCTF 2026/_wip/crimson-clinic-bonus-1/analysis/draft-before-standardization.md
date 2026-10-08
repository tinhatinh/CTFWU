# crimson-clinic-bonus-1 - OSINT (500 points) - CHƯA GIẢI

**Trạng thái:** Chưa giải. Chưa có flag hoặc dữ liệu từ Crimson Social để xác định ba người.

## Đề bài

Đề hỏi tên ba chức danh hiện tại của Crimson Clinic: Medical Director, Chief Administration Officer, Chief Financial Officer, dựa vào việc "looking around Crimson Social". Cờ dạng `cdctf{Firstname Lastname, Firstname Lastname, Firstname Lastname}`, chấp nhận mọi thứ tự. Bản paste của thẻ không kèm URL instance và không kèm file.

## Đã làm trong phiên

- Xác định giải: CDCTF 2026 (Crimson Defense Cyber Security Club, University of Alabama), CTFtime event 3293, cửa sổ 03/10 15:00 UTC đến 04/10 03:00 UTC.
- Loại hướng tra cứu người thật: web search tổ hợp `Crimson Clinic` + `Crimson Social` + chức danh trả `No results found`; nhân viên Clinic là dữ liệu hư cấu của tác giả.
- Loại hướng tự tìm nền tảng: `crimsondefense.org/cdctf/` không expose domain chơi bài (chỉ điều hướng nội bộ, form đăng ký, GitHub, Instagram, LinkedIn, Google Maps), `/scoreboard` chỉ có bản 2025.
- Ghi nhận ràng buộc của giải: cấm tấn công platform, cấm tool tự động trên challenge host trừ khi đề cho phép, nên không scan và không spider.
- Đối chiếu session khác: `_wip/crimson-clinic-bonus-2` treo cùng dạng; memory của đội ghi series Crimson Clinic là kiosk Discord qua `CDCTF Bot`, thẻ bài cũng không có URL lẫn file.

## Bước tiếp theo

Cần URL Crimson Social hoặc nội dung danh sách nhân viên để tiếp tục xác minh:

1. URL Crimson Social nguyên văn trên thẻ bài hoặc trong channel kiosk (copy, không gõ lại).
2. Screenshot hoặc paste nội dung trang giới thiệu / danh sách nhân viên trên Crimson Social.

Khi có dữ liệu, cần xác định từng tên cùng chức danh và ghép theo format của đề. Chưa có bằng chứng để ghi flag.

Log truy vết đầy đủ: `notes.md`.
