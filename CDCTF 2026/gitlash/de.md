# Đề bài - gitlash

## Nguyên văn đề

```text
GitLash
496
pwn Forensics
b0b

My team has a super important diagnostics script we run every 5 minutes on a remote server. The
server is special because it keeps a flag in the root dir, so ofc we need updated specs constantly!
In case we ever need to update the script, we have it set up to pull from a local GitLab repo so we
don't have to actually edit the script on the box. Neat! You'll find more info in your instance.

(PS: swaks exists on the box)

Flag format is cdctf{3pic_fl4G_123456789}
```

Ảnh đề bài gốc, chụp từ thẻ challenge:

*(chưa có thẻ challenge dạng ảnh cho bài này)*

## Thông tin đã xác minh trên instance

| Mục | Giá trị |
| --- | --- |
| Instance | `https://thbtjpai.i.cdctf.net` (ttyd web terminal), `player@bcc0367dc82c`, uid 1000 |
| Instance trước | `https://ztzdsxqi.i.cdctf.net` -> `player@d1ce9636e9fc`, repo `diagbot/diag-fb610669` (project 42) |
| Repo hiện tại | `diagbot/diag-d9dbe170`, project id **54**, nhánh `main`, HEAD `2f7853aaab43f76c2bc17315857d6a402806ec95` |
| `~/challenge.txt` | chỉ có URL repo và lệnh clone, không có dòng email nào |
| `README.md` trong repo | chứa địa chỉ mail-to-issue `incoming+diagbot-diag-d9dbe170-54-glimt-<TOKEN>-issue@gitlash.internal` |
| GitLab | `http://gitlab.gitlash.internal` = 172.18.0.2, mở 80 và 22, đóng 25 |
| Mail | `mail.gitlash.internal` = 172.18.0.3, mở 25 (postfix), 143 (Dovecot), 587 |
| Forward trên box | root `socat TCP-LISTEN:25,fork,reuseaddr TCP:mail.gitlash.internal:25` |
| Job root mỗi 5 phút | `/usr/local/sbin/diagnostic-runner.sh` (0700), bên trong `git fetch --quiet --prune origin +refs/heads/*:refs/remotes/origin/*` |
| Số project liệt kê được khi ẩn danh | 54 (`X-Total: 54`), tất cả `diagbot/diag-<hex>`, `visibility: public` |
| Artifact | không có file tải về, toàn bộ tương tác qua instance |
| Định dạng cờ thật | `cdctf{mY_3m41L_is_a_TOKEN_<hex>}` (dòng `cdctf{3pic_fl4G_123456789}` trong đề chỉ là ví dụ format) |

## Hướng giải (tóm tắt)

`GET /api/v4/projects?per_page=100` trên chính cái GitLab "local" mà đề nhắc trả về **cả 54 instance**
của 54 đội, repo nào cũng public. Trong số đó có những repo đã bị các đội khác ghi đè `run.sh`;
cron root của box họ chạy script đó và mail kết quả về địa chỉ GLIMT của dự án, nên body issue của
họ chứa nguyên output chạy bằng `uid=0(root)` kèm chuỗi cờ. Cờ lấy được bằng cách đọc issue công
khai, không cần quyền ghi vào repo nào.
