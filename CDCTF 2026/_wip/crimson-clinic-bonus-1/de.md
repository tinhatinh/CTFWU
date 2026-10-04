# Đề bài - crimson-clinic-bonus-1

## Nguyên văn đề

```text
Welcome to Crimson Clinic BONUS 1
500
OSINT
adlee7, b0b, dontfeedthepenguins

Looking around Crimson Social is a great way to get information about the Clinic employees outside of work! What are the names of the current Medical Director, Chief Administration Officer, and Chief Financial Officer?

The flag format is cdctf{Firstname Lastname, Firstname Lastname, Firstname Lastname} in any order. E.g. cdctf{Paul Bryant, Gene Stallings, Nick Saban}
```

Bản paste không kèm URL instance, không kèm file.

## Thông tin đã xác minh

| Mục | Giá trị |
| --- | --- |
| Artifact | Không có |
| Giải | CDCTF 2026 (Crimson Defense, University of Alabama), CTFtime event 3293 |
| Thể loại / điểm / tác giả | OSINT / 500 / adlee7, b0b, dontfeedthepenguins |
| Nhiệm vụ | Tên 3 người: Medical Director, Chief Administration Officer, Chief Financial Officer của Crimson Clinic |
| Định dạng cờ | `cdctf{Firstname Lastname, Firstname Lastname, Firstname Lastname}`, thứ tự bất kỳ |
| Bối cảnh series | Crimson Clinic là chuỗi bài chạy qua kiosk Discord của team, điều khiển bằng `CDCTF Bot` (ghi nhận ở Terminal 1 Self Check-In và Terminal 2 Triage). `_wip/crimson-clinic-bonus-2` cũng treo y hệt: một sự kiện về nhân viên hư cấu, không URL, không file |

## Hướng giải (tóm tắt)

Chưa chốt, đang chờ đầu vào. Đã loại kênh "tra web người thật": dữ liệu là nhân viên hư cấu do tác giả dựng, tìm `Crimson Clinic` + `Crimson Social` + chức danh trên web không ra kết quả nào, và trang giải đấu `crimsondefense.org/cdctf/` không expose domain nào ngoài các link câu lạc bộ (form đăng ký, scoreboard 2025, GitHub, Instagram, LinkedIn).

Giả thuyết làm việc: "Crimson Social" là một site instance của giải (hoặc đường link phát trong channel kiosk), và ba chức danh nằm trong profile của nhân viên trên đó. Câu hỏi mở: bonus này có site riêng hay chỉ là dữ liệu bot trả lời khi hỏi đúng cách.

## Việc cần người chơi làm

1. Mở thẻ bài, copy nguyên văn URL của Crimson Social (đừng gõ lại tay).
2. Nếu thẻ không có URL, xem channel Discord kiosk của series Crimson Clinic có post link không, và xin luôn ảnh chụp trang giới thiệu / danh sách nhân viên.
3. Không tự động hoá: trang giải ghi "Attacking the CDCTF platform is strictly prohibited" và "Using automated tools against the CDCTF hosted challenges is prohibited unless specified". Người chơi duyệt bằng tay rồi paste nội dung, tôi phân tích từ paste.

## Chạy lại lời giải

Chưa có script; `exploit.py` vẫn là bản template.
