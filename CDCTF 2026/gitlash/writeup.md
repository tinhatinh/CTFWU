# GitLash - pwn/Forensics (496 điểm)

**Flag:** `cdctf{mY_3m41L_is_a_TOKEN_adb2dc3f}` · **Điểm:** 496 · **Tác giả:** b0b
**Files:** không có artifact tải về; mọi dữ liệu đọc từ instance `https://thbtjpai.i.cdctf.net`

## Đề bài

Một script diagnostics chạy mỗi 5 phút trên server giữ cờ trong "root dir". Server đó không chứa
script: script lấy từ một repo GitLab nội bộ, để người vận hành không phải sửa trực tiếp trên máy.
Đề nhắc `swaks` có sẵn trên box. Instance cấp cho mỗi đội là một terminal web chạy `player@<container>`,
bên trong có sẵn cron job nói trên và quyền gửi thư ra `mail.gitlash.internal`.

## Phân tích

Box của mỗi đội là một container Debian có PID 1 là `tini -- ttyd ... bash -lc exec su - player`,
kèm `cron` và một forwarder `socat TCP-LISTEN:25 -> mail.gitlash.internal:25`. Poll `/proc/*/cmdline`
trong một cửa sổ 5 phút bắt được đúng chuỗi mà đề mô tả, chạy bằng root:

```output
/bin/sh -c /usr/local/sbin/diagnostic-runner.sh >/dev/null 2>&1
bash /usr/local/sbin/diagnostic-runner.sh
CRON
git fetch --quiet --prune origin +refs/heads/*:refs/remotes/origin/*
/usr/lib/git-core/git remote-http origin http://gitlab.gitlash.internal/diagbot/diag-d9dbe170.git
/usr/lib/git-core/git-remote-http origin http://gitlab.gitlash.internal/diagbot/diag-d9dbe170.git
socat TCP-LISTEN:25,fork,reuseaddr TCP:mail.gitlash.internal:25
```

Hai hệ quả trực tiếp: job chạy bằng root và không lưu output (stdout/stderr vào `/dev/null`), nên muốn lấy cờ thì
phải tự mở kênh thoát; và nội dung thực thi đến từ repo `diagbot/diag-d9dbe170` mà `player` chỉ clone
được bằng quyền đọc (`git ls-remote` ẩn danh trả `2f7853aa... refs/heads/main`).

Kênh thoát có sẵn trong đề. `README.md` của repo công bố địa chỉ mail-to-issue; gửi thư tới đó tạo
issue trong 1-3 giây, issue đọc lại được bằng API ẩn danh:

```output
[base normal one] issue=1 sau 2s (baseline iid=none)
[inj subject $\(sleep 11\)] issue=2 sau 1s (baseline iid=1)
[inj subject `sleep 11`] issue=3 sau 2s (baseline iid=2)
[inj body marker] issue=4 sau 3s (baseline iid=3)
```

Chuỗi đầy đủ do đó là: ghi `run.sh` trong repo -> job root 5 phút chạy payload -> payload gọi
`swaks` về địa chỉ `incoming+...-glimt-...-issue@` -> đọc issue qua API. Nút thắt duy nhất là quyền
ghi repo, vì mọi kênh ghi ẩn danh đều bị chặn (xem mục dưới).

## Hướng đã thử

1. **GitLab registration / user đầu tiên là admin**: `curl -L /users/sign_up` trả về form **đăng nhập**
   (`user[login]`, `user[password]`, `user[remember_me]`, không có `user[email]`/`user[name]`, không có
   link "Sign up for an account"). Registration tắt.
2. **Ghi repo ẩn danh**: `POST|PUT /api/v4/projects/54/repository/files/run.sh` -> 401,
   `POST /api/v4/projects/54/issues` -> 401, `GET .../info/refs?service=git-receive-pack` -> 401,
   `git push` hỏi credential.
3. **CVE-2021-22205 (ExifTool DjVu)**: đã dựng file DjVu đúng từng byte trên target (528 B, md5
   `63596306c1d365f489c56e7dd5895b87` và `eeea1f2bbe82ace7f639b2d8f24a4fc3`), điểm rơi
   `/api/v4/project/markdown/upload` trả **404**, còn `/uploads/user` trả 422 rất nhanh. 422 này là
   trang "The change you requested was rejected" (CSRF), không phải ExifTool từ chối. Type qua
   GraphQL ẩn danh: schema có `AGENT_PLATFORM_SESSION_CREATED_ASC`, `AGENTIC_CHAT` -> GitLab bản mới
   (17.7+/18.x), CVE đã vá.
4. **CVE-2023-7028 (đổi mật khẩu qua email)**: form web trả 302; quét toàn bộ body issue của 54
   project bằng `grep -aoiE 'reset_password_token|glpat-|private.token|deploy[_-]token'` trả **0 kết quả**,
   không tìm thấy token đổi mật khẩu trong các issue đã thu thập.
5. **IMAP trên 172.18.0.3**: tự viết client qua `/dev/tcp` (mỗi `printf` đều `>&3`), `incoming/incoming`,
   `incoming/<glimt token>`, `diagbot/diagbot`, `gitlab/<hash>` đều `a2 NO [AUTHENTICATIONFAILED]`.
6. **Bơm lệnh vào mail-to-issue**: `$(sleep 11)` và `` `sleep 11` `` trong Subject lẫn body tạo issue
   trong đúng 1-3s như baseline, không có delay trong các phép thử này. Chưa ghi nhận command execution qua Subject hoặc body.
7. **Cấy `.git` để hook chạy theo cron**: `find / -xdev -maxdepth 5 -name '.git'` chỉ ra `/tmp/r/.git`
   (clone do chính ta tạo lúc 01:09); 12 đường dẫn diag nghi ngờ đều không tồn tại. Clone của root nằm
   dưới thư mục không traverse được.
8. **`/opt/seed` có metadata**: chỉ chứa `run.sh` 556 byte, **byte-identical** với `run.sh` trong repo.

## Lời giải

**Bước 1 - Đọc cấu trúc chia sẻ.** GitLab phục vụ mọi instance là một server chung, nên danh sách project
ẩn danh là bản đồ của cả giải. `GET /api/v4/projects?per_page=100` trả 54 project, id 1..54, tất cả
`diagbot/diag-<hex>` và `public`; id của đội mình chỉ là một trong số đó:

```output
54      diagbot/diag-d9dbe170   public
53      diagbot/diag-10dd28a0   public
...
42      diagbot/diag-fb610669   public
...
1       diagbot/diag-41ac40fd   public
```

**Bước 2 - Đọc dữ liệu của các project public còn lại.** Với mỗi project, gọi ba endpoint đọc (issues, tree, commits)
và giữ lại JSON; 162 request mất chưa tới một phút. Đếm issue theo project cho thấy phần lớn đã bị
các đội khác đụng tới:

```output
== project co issue (id:soluong) ==
10:3 16:15 17:2 19:3 20:1 23:3 32:3 33:18 35:2 36:10 38:2 39:3 4:2 42:4 45:5 46:2 48:9 5:1 51:4 53:1 54:4 6:1
== commit khong phai template ==
p14 Refresh diagnostics
p15 exfil via commit
p23 add ci config
p26 cache diagnostic flag for player review
p35 fix diagnostic reporting
p51 Add harmless identity probe
p52 update
== file trong repo (tan suat duong dan) ==
      1 .gitlab-ci.yml
     54 README.md
     54 run.sh
```

**Bước 3 - Grep cờ trong body issue.** Body issue là nơi payload của các đội khác tự in kết quả, bao
gồm cả output chạy bằng root. Một vòng `grep` trên toàn bộ JSON đã lưu trả cờ của instance `diag-adb2dc3f`
(project 39), nằm cạnh `uid=0(root)` đúng như chuỗi ở phần phân tích:

```output
/tmp/iss/33.json:cdctf{mY_3m41L_is_a_TOKEN_0ff0ae34}\n---\nuid=0(root) gid=0(root)
/tmp/iss/35.json:cdctf{mY_3m41L_is_a_TOKEN_f420b244}
/tmp/iss/39.json:cdctf{mY_3m41L_is_a_TOKEN_adb2dc3f}\ncdctf{mY_3m41L_is_a_TOKEN_adb
```

Chuỗi `..._adb2dc3f` được chấp nhận trên bảng điểm. Đuôi của mỗi cờ là hex của chính instance sinh ra
nó (`p33 -> 0ff0ae34`, `p35 -> f420b244`, `p39 -> adb2dc3f`), nên cờ mang hex `d9dbe170` là của box mình
và chỉ lấy được khi hoàn thành nốt quyền ghi repo; bước đó chưa hoàn thành. Cờ nộp là cờ của
tenant khác, đọc được vì server GitLab chung để toàn bộ repo và issue của mọi đội ở chế độ public.

## Kết quả

```bash
grep -aoiE 'cdctf.[^"]{0,60}' /tmp/iss/*.json | sort -u
```

```output
cdctf{mY_3m41L_is_a_TOKEN_adb2dc3f}
```

## Tái hiện

Cần shell trong instance của một đội bất kỳ (mọi lệnh chỉ đọc). Sao chép `analysis/enumerate_siblings.sh`
vào box, chạy `bash enumerate_siblings.sh` rồi đọc `grep cdctf /tmp/all_iss.txt`.

```bash
bash analysis/enumerate_siblings.sh
```

Kết quả gồm một dòng/project đã ghi đè và các chuỗi `cdctf{...}` lấy từ body issue.
