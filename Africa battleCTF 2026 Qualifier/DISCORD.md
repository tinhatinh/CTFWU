---
title: "Discord"
category: "OSINT"
tags: ["osint", "discord", "linktree", "invite-api", "curl", "social-media"]
solve_date: "2026-10-07T09:36:00+07:00"
language: "vi"
points: 4
---

# Discord — flag trong bài Rules được ghim

**Flag:** `CTF{OffWeGo}` (đã nộp và được chấp nhận) · **Solves:** 114 · **Ảnh challenge:** `challenge-modal.png`, 17 864 byte, SHA-256 `54b31508c1a100edd2dedf2434ca1b0a6fed3d83d2a52a9252b13c5c0eadc1aa`

## Đề bài

Thẻ challenge trên `ctf.bugpwn.com` chỉ có tiêu đề **Discord**, 4 điểm, không có mô tả, file hay service. Tiêu đề và ô nhập flag là toàn bộ đề bài; `challenge-modal.png` chụp lại thẻ đúng lúc vừa mở. Vì vậy, cần tự tìm Discord của Africa battleCTF 2026 Qualifier và đọc flag bên trong.

## Phân tích

Footer của nền tảng dẫn tới `linktr.ee/bugpwn`, nơi có invite Discord. Public invite API cho biết server và channel đích. Các cách tra cứu khác được ghi lại trong `notes.md`.

## Lời giải

**Bước 1 — Từ challenge tìm nguồn link chính thức.** CTFtime mô tả sự kiện là “A technical CTF by BUG|PWN” và ghi website `ctf.bugpwn.com`. Liệt kê các liên kết ngoài trên trang nền tảng:

```bash
curl -sL -A "Mozilla/5.0" https://ctf.bugpwn.com/ | grep -oiE 'href="[^"]+"' | sort -u | grep -viE 'static|assets'
```
```text
href="/"
href="/challenges"
href="/confirm?flow=init"
href="/login"
href="/register"
href="/rules"
href="/scoreboard"
href="/users"
href="https://ctfd.io"
href="https://linktr.ee/bugpwn"
```

Liên kết footer `linktr.ee/bugpwn` là nơi ban tổ chức đăng invite.

**Bước 2 — Đọc Linktree khi kết nối trực tiếp bị reset.** Môi trường solve không truy cập được `linktr.ee`: `curl` trả HTTP `000`, còn headless browser báo `ERR_CONNECTION_RESET`; các domain khác vẫn hoạt động nên vấn đề nằm trên đường kết nối tới Linktree. Dùng text proxy để lấy nội dung tĩnh:

```bash
curl -sL "https://r.jina.ai/https://linktr.ee/bugpwn" | grep -n -i -B6 -A6 "discord"
```
```text
8-# BUG|PWN Team
14:[My community Discord Server • Free to join](https://discord.gg/WvUrypNDv)
```

**Bước 3 — Xác thực invite trước khi dùng.** Nhãn “My community Discord Server” khá chung chung, và output từ proxy trộn thêm nhiều profile Linktree không liên quan do khối gợi ý. Vì vậy, resolve invite code bằng public API của Discord — endpoint này không cần token:

```bash
curl -s -A "Mozilla/5.0" "https://discord.com/api/v9/invites/WvUrypNDv?with_counts=true&with_expiration=true"
```
```json
{
    "code": "WvUrypNDv",
    "inviter": { "username": "weird.raven", "global_name": "WEIRD RAVEN" },
    "expires_at": "2026-10-28T14:30:16+00:00",
    "guild": { "id": "1082707709004095658", "name": "BattleCTF" },
    "channel": { "id": "1115911426003980318", "name": "announcements" },
    "profile": { "name": "BattleCTF", "member_count": 399, "online_count": 32 }
}
```

Server có tên `BattleCTF`, invite mở vào channel `#announcements`. Đây đúng là event cần tìm; API cũng cho biết channel đáng đọc.

**Bước 4 — Đọc `#announcements`.** Sau khi tham gia server bằng tài khoản Discord, channel `#announcements` có một bài post được ghim: “battleCTF Qualifier Rules” của RAVEN. Trong mục **Scoring**, gạch đầu dòng đầu tiên ghi:

> Flag có định dạng `CTF{OffWeGo}`. Hãy nộp đúng chuỗi đề bài đưa ra, không thêm hoặc bỏ ký tự nào.

Đọc trực tiếp bài post được ghim rồi chép lại chuỗi flag ví dụ. Channel ở chế độ chỉ đọc vẫn cho phép xem và tìm kiếm tin nhắn.

*Ảnh chụp: flag trong mục Scoring của bài Rules (discord-announcements.png).*

**Bước 5 — Đối chiếu.** Invite dẫn tới guild `BattleCTF`, không phải một server cộng đồng bất kỳ; bài post nằm trong `#announcements`, đúng với `channel.name` API trả về; và nền tảng đã ghi nhận prefix `CTF{...}` cho một số challenge của sự kiện (xem ghi chú format flag trong [README sự kiện](README.md)), nên `CTF{OffWeGo}` phù hợp với quy ước.

## Kết quả

```text
CTF{OffWeGo}
```

Khôi phục bằng cách đọc trực tiếp bài Rules trong `#announcements` của server BattleCTF (`discord.gg/WvUrypNDv`); ảnh chụp nằm trong `discord-announcements.png`. Flag đã được nộp lên `ctf.bugpwn.com` và chấp nhận; `challenge-modal.png` cho thấy thẻ challenge **trước khi** nhập flag.

## Tái hiện

Cần Git Bash trên Windows, `curl` và tài khoản Discord đã tham gia server. Invite có thời hạn — code `WvUrypNDv` hết hạn lúc `2026-10-28T14:30:16+00:00`; sau thời điểm đó hãy lấy code mới từ `linktr.ee/bugpwn` theo Bước 2.

```bash
cd "discord"
bash repro.sh
```

Hoặc chạy thủ công ba lệnh:

```bash
curl -sL -A "Mozilla/5.0" https://ctf.bugpwn.com/ | grep -oiE 'href="[^"]+"' | sort -u
curl -sL "https://r.jina.ai/https://linktr.ee/bugpwn" | grep -n -i "discord"
curl -s -A "Mozilla/5.0" "https://discord.com/api/v9/invites/WvUrypNDv?with_counts=true" | head -c 400
```

Bước cuối — đọc `#announcements` — cần thao tác thủ công, không có lệnh tương ứng.
