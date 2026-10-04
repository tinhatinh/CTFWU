# Đề bài - epic-rat-encoding

## Nguyên văn đề

```text
Epic Rat Encoding
Reverse Engineering
alex

My buddy (who happens to be a rat named Ratón) gave me this piece of code the other day. He was
saying that numbers and letters are theoretical constructs, and that he can turn them into
whatever he pleases. Ratón gave me some numbers and said that they contain information about
our super epic and baller awesome secret meeting, which I can't miss!! Please help me to figure
out the when and the where of this super epic and baller awesome secret meeting.

5576975263002879264 7022273403317198932 8029109180213651820 7791300427398276201 7955362869705469551 8029390844169057312 8603394173939509365 8247045712450168172

flag format cdctf{Place_Place_Place_at_time_time_time_Time}
```

Thẻ challenge: tác giả `alex`, thể loại Reverse Engineering. Điểm hiển thị trên thẻ thay đổi
trong lúc làm: 499 lúc mở đề, 498 lúc nộp cờ (bài có nhiều solve nên điểm hạ theo số solve).

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact 1 | `files/message_encoder.c` (copy từ: `C:/Users/Administrator/Downloads/message_encoder.c`) |
| Kích thước 1 | 360 byte |
| SHA-256 1 | `738e4cbaa71cc9a48260ed6130718c04f66d910582a10d4760fc27466deb2734` |
| Loại file 1 | C source, Unicode text, UTF-8 text |
| Artifact 2 | `files/nums.txt` (8 số chép nguyên văn từ đề) |
| Kích thước 2 | 160 byte |
| SHA-256 2 | `188ff63f2326345e495fffc6b2199384b87c021d92489a027354fe4d4f9085b5` |
| Loại file 2 | ASCII text |
| Nhiệm vụ | Đọc `message_encoder.c` để suy ra cách đóng gói, rồi giải mã 8 số về chuỗi mô tả địa điểm và giờ gặp mặt |
| Định dạng cờ | `cdctf{Place_Place_Place_at_time_time_time_Time}` |

## Hướng giải (tóm tắt)

Vòng lặp trong encoder cộng dồn 8 byte liên tiếp của `message` và chỉ `<< 8` khi `i != 7`, nên
`nums[j]` chính là 8 byte `message[8j..8j+7]` đóng gói big-endian trong một `uint64_t`. Lời giải
là phép ngược lại: tách mỗi số thành 8 byte theo big-endian và nối lại thành 64 byte.

## Chạy lại lời giải

```bash
python exploit.py files/nums.txt
```

Kết quả: `cdctf{Tom_Bevill_Building_at_noon_next_week_Thursday}` (đã lưu trong `flag.txt`).
