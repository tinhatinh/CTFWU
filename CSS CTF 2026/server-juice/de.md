# Đề bài - server-juice

## Nguyên văn đề

```text
Server Juice
50
Beginner
If you want to appease the algorithm (and maybe get a head start on future hints), consider keeping us on your radar by following.

Flag Format: CSSCTF{...}
```

Thể loại: OSINT. Không kèm file, không có instance, không có URL nào trong mô tả.

Hint của bài (lúc đầu):

```text
View Hint: Social
instagram.com/cybersecuritysociety
```

Hint sau đó được ban tổ chức đính chính:

```text
https://www.instagram.com/cybersecuritysydney/
```

Cả hai chuỗi đều lấy từ trang chót của slide lễ khai mạc (xem `analysis/opening_ceremony_p13.jpg`), trang đó ghi `Follow instagram.com/cybersecuritysociety :)` - tức chính slide ghi sai handle.

## Thông tin đã xác minh

| Mục | Giá trị |
| --- | --- |
| Artifact | không có file; dữ kiện là một trang công khai |
| Tài khoản thật | `@cybersecuritysydney`, "Cybersecurity Society Sydney (CSS)", 27 bài |
| Bài chứa cờ | `https://www.instagram.com/p/DWL9S-wkyJT/` - áp phích "General Meeting 01!" |
| Vị trí cờ | **comment** của `harrysalvesen` dưới bài đó, đăng 8 giờ trước khi giải được, 11 likes |
| Người đăng comment | `harrysalvesen` - cũng là tác giả `hsalvesen` / `vesen.app` (web terminal mã nguồn mở MIT 1.2.0) |
| Câu chốt của caption | "We hope to see you there; BYO water. 💧" (caption bị sửa, Instagram hiển thị chữ "Edited") |
| Định dạng cờ | `CSSCTF{...}`, luật 6 của giải ghi rõ **case-sensitive** |
| Cờ | `CSSCTF{premiumreserve}` |

## Hướng giải (tóm tắt)

Tên bài lấy từ đúng cái áp phích chứa cờ: trong ảnh có một đoạn tin nhắn giả lập, dòng áp chót ghi "come for the server juiceeeee", và dòng ngay trên ghi "u seriously care more about a club than the premium reserve??". Hint chỉ dẫn tới Instagram của ban tổ chức, nhưng không nói ở đâu; toàn bộ caption của 27 bài, 19 bài tagged, 3 highlight và 25 ảnh áp phích đều không có cờ. Kênh còn lại là comment, và đó chính là chỗ tác giả đặt cờ thành một comment trần, không mã hoá, không stego.

## Chạy lại lời giải

Instagram khoá comment với khách vãng lai, nên phần thu thập phải chạy trong trình duyệt đã đăng nhập; đoạn script để làm việc đó nằm trong biến `BROWSER` của `exploit.py`. Bằng chứng đã lưu ở `analysis/evidence.json` (caption + comment, đã bỏ URL ký sẵn và avatar để không lộ handle cá nhân).

```bash
python exploit.py
```

Kết quả: `CSSCTF{premiumreserve}` (đã lưu trong `flag.txt`).
