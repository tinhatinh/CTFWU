# notes.md - Troubled Translation

Input: `files/translation.zip` (19609739 B, sha256 `b4e5df962599ce981bc05a8d1fd9e3d007f9f74a55b305f58537540eff51e10b`).
Định dạng cờ: `cdctf{Business_in_City}`.

## H1 - Kiểm tra dữ liệu đề

cmd: mở ZIP bằng `System.IO.Compression.ZipFile.OpenRead`, liệt kê `Entries`.
evidence: thư mục `translation/`; năm JPEG, kích thước lần lượt 4354763, 4520027, 4650003, 4236298, 4268873 byte.
result: OK - đủ năm ảnh để đọc hội thoại.

## H2 - Dịch trực tiếp ảnh

cmd: `Expand-Archive -LiteralPath 'C:\Users\Administrator\Downloads\translation.zip' -DestinationPath 'C:\Users\Administrator\Downloads\ctf-skills-main\ctf-skills-main\translation_evidence' -Force`, sau đó `view_image` lần lượt năm ảnh.
evidence: ảnh 4, 9:20: “不对，是一个芝加哥的麦当劳”; ảnh 2, 9:33: “但是我还是觉得的前一个是最好的目标”; 9:35: “那个？麦当劳？”. Ảnh 1 đề cập `bubu778` và quên số 8. Thứ tự thời gian là 5, 4, 3, 2, 1.
result: PENDING - suy luận mục tiêu McDonald’s ở Chicago; chưa xác nhận flag.

## H3 - Tìm chứng cứ bên ngoài

cmd: web search `"ctf" "Troubled Translation"` và `"cdctf" "Chatterly"`.
evidence: kết quả không liên quan, không có lời giải hữu ích.
result: DEAD - không dùng các trang này làm nguồn cho kết luận.

## H4 - Flag không có dấu nháy

cmd: không có lệnh nộp trong phiên; người dùng cung cấp bảng submission.
evidence: `cdctf{McDonalds_in_Chicago}` bị từ chối hai lần, bảng ghi October 4, 2026 at 12:17 AM (không xác định timezone của bảng).
result: DEAD - chuỗi này sai theo hệ thống chấm.

## H5 - Giữ dấu nháy ASCII

cmd: `view_image` lại ảnh 4 và ảnh 2 để kiểm tra câu dịch.
evidence: tên Trung Quốc vẫn là 麦当劳, thành phố 芝加哥. Đề xuất `cdctf{McDonald's_in_Chicago}` chỉ thay cách viết thương hiệu.
result: PENDING - chưa có submission hoặc nguồn xác nhận; không ghi thành flag đã capture.

## Đóng gói theo rule

cmd: đọc `AI_README.md`, README root, README cuộc thi và `_template/{writeup.md,de.md,notes.md,new_case.sh}`; copy ZIP nguyên vẹn vào `files/`; lấy kích thước bằng `Get-Item`, hash bằng `Get-FileHash -Algorithm SHA256`.
evidence: bài chưa ra cờ phải đặt trong `CDCTF 2026/_wip/`; writeup không có YAML, cần VI/EN và giữ code fence giống nhau.
result: OK - đóng gói WIP, không thêm vào bảng solved hoặc `tools/solve_times.json`.

## Kiểm tra gói

- `python exploit.py files/translation.zip`: chạy thành công, hash khớp và liệt kê đúng năm ảnh; không in flag.
- Đối chiếu bằng Python: code fence trong VI/EN giống nhau, dòng đầu là heading.
- `python tools/build_site.py`: thành công cho VI/EN; WIP không đưa vào danh sách bài công bố.
- `python tools/test_editor.py`: 20 tests pass.
- Build Jekyll VI: dừng với `bundler: command not found: jekyll`. Không cài runtime/gem, không chạy tiếp EN hoặc htmlproofer khi build VI chưa thành công.

## H6 - Xác nhận flag và chuyển khỏi WIP

Nguồn: người dùng xác nhận trực tiếp trong chat ngày 2026-10-04 rằng `cdctf{McDonald's_in_Chicago}` là flag đúng và yêu cầu chuyển khỏi WIP.
result: OK - lưu `flag.txt`, chuyển sang `CDCTF 2026/troubled-translation/`, cập nhật VI/EN và bảng cuộc thi. Các kết quả PENDING ở trên là nhật ký trước khi được xác nhận.
