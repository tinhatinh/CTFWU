# notes.md - server-juice

Input: không có file. Đề chỉ có đoạn văn, thể loại OSINT, 50 điểm, Beginner.
Định dạng cờ: `CSSCTF{...}`

## Seed dẫn ra được (từ chính domain của đề)

`https://cybersecurity.sydney/` (Next.js, trang của Cybersecurity Society Sydney) công bố bốn kênh:

| Kênh | Định danh | Đo được |
| --- | --- | --- |
| Instagram | `@cybersecuritysydney` | 1,707 followers, 47 following, 27 posts; bio: "CSS is a student-run initiative focused on bringing newcomers and enthusiasts together to explore and coalesce in the world of cybersecurity." |
| Instagram (handle khác, chỉ có ở trang chủ) | `@usyd_cybersoc` | trả về shell rỗng, title chỉ "Instagram", không có og:* -> hoặc không tồn tại hoặc đã đổi tên |
| LinkedIn | company `usyd-csec` | "Cybersecurity Society Sydney \| 538 followers on LinkedIn. Where security and innovation coalesce." |
| Facebook | `facebook.com/profile.php?id=61552628758945` | chưa đọc được |
| Discord | guild `Cybersecurity Society Sydney (CSS)`, id `1119954291831091221` | 1476 thành viên, 293 online, features có `COMMUNITY`, `NEWS`, `PREVIEW_ENABLED`; ba invite code khác nhau (`vRFEPEHy8Z` ở website, `DR6ZvVujvE` ở CTFd, `gUGqmt4Gqf` ở CTFtime) đều trỏ về cùng một guild |

Trang chủ còn liệt kê logo nhà tài trợ: `dewaguard.com`, `dewaweb.com`, `gridware.com.au`, `www.janestreet.com`, và `usu.edu.au/clubs/sydney-university-cyber-security-society/`.

## H1 - Cờ nằm trên chính hai domain của giải
cmd: `curl` `/api/v1/configs`, `/challenges`, `/robots.txt`, `cybersecurity.sydney/{,events,contact,teams,sponsors,robots.txt,sitemap.xml}`
evidence: CTFd chặn khách - `/api/v1/configs` và `/challenges` đều 302 về `/login?next=...`; `robots.txt` của CTFd chỉ có `Disallow: /admin`. Trang society không có `robots.txt`/`sitemap.xml` (404 trả về trang 404 6927 B), và grep `CSSCTF` trên cả sáu trang đều 0 kết quả.
result: DEAD - không có cờ trên web của giải.

## H2 - Đọc Instagram không cần đăng nhập
cmd: `curl` trang profile + `https://www.instagram.com/cybersecuritysydney/embed/` + `https://www.instagram.com/api/v1/users/web_profile_info/?username=...` với `x-ig-app-id: 936619743392459`
evidence: hai bản HTML profile tải được (623 KB và 802 KB) nhưng chỉ chứa shell, không có `biography`/`edge_media_to_caption` trong DOM; đếm chuỗi `flag` và `CTF` trong toàn bộ payload đều bằng 0. API trả **429**. Embed trả về shell trần, title "Instagram".
result: DEAD - caption và ảnh bài viết nằm sau wall, cần phiên đăng nhập.

## H3 - Đọc LinkedIn không cần đăng nhập
cmd: `curl` `/company/usyd-csec/` rồi `/company/usyd-csec/posts/`
evidence: trang about đọc được thật (299 KB, lấy được tagline và số follower), nhưng trang posts trả đúng trang "Đăng nhập LinkedIn" (511 KB, 0 ký tự nội dung).
result: DEAD - chỉ đọc được phần about, không đọc được bài viết.

## H4 - Đọc Discord không cần tham gia
cmd: `GET discord.com/api/v9/invites/<code>?with_counts=true` rồi `GET /api/v9/guilds/1119954291831091221/preview`
evidence: invite API mở, lấy được tên guild, id, số thành viên và danh sách feature (có `PREVIEW_ENABLED`, `NEWS`). Nhưng endpoint preview trả **401** - Discord đã khoá endpoint này phía khách từ lâu, `PREVIEW_ENABLED` không đủ để gọi.
result: DEAD - tên kênh và topic không lấy được khi không có token.

## H5 - Cờ nằm trong bài viết trên kênh social, cần phiên đăng nhập
cmd: chưa chạy được - browser-use trả `NATIVE_BROWSER_VIEWPORT_UNAVAILABLE` (in-app Browser chưa mở)
evidence: bốn kênh đều còn sống sau H1-H4, và mô tả bài chỉ đường tới chúng: "appease the algorithm", "keeping us on your radar by following" là ngôn ngữ của follower/algorithm trên Instagram và LinkedIn ("538 followers"), còn "Server" trong tên bài và tuỳ chọn Discord chưa loại được.
result: PENDING - cần hoặc (a) mở in-app Browser để dẫn đường khi người dùng đã đăng nhập, hoặc (b) người dùng chụp/paste bài viết gần đây của `@cybersecuritysydney` và kênh `#announcements` của Discord.

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
