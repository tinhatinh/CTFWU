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

## H6 - Bio link: Linktree
cmd: `curl -sk https://151.101.2.133/CybersecuritySocietySydney -H "Host: linktr.ee"` (linktr.ee bị RST theo SNI trên máy này, phải gọi thẳng IP Fastly và bỏ SNI)
evidence: tải được 238 KB, parse `__NEXT_DATA__` ra 40 link. Link thật của society: `ctf.cybersecurity.sydney`, `au.cglink.me/25W/r382336` (tutorial), `clubs.usu.edu.au/CyberSoc/club_signup`, Instagram `cybersecuritysydney`, Instagram `usyd_cybersoc`, **TikTok `@cybersecuritysydney`**, LinkedIn `usyd-csec`, Discord `gUGqmt4Gqf`. Phần còn lại là affiliate mặc định của Linktree (Hulu, HelloFresh, Fabletics...). Grep `CSSCTF` trong trang: 0.
result: PENDING - bản thân Linktree không chứa cờ, nhưng nó là nguồn duy nhất khai ra TikTok.

## H7 - TikTok @cybersecuritysydney
cmd: `curl` profile (bị bot-check, trả 1462 B) -> mở bằng browser; `GET /api/post/item_list/?secUid=...&aid=1988`
evidence: đọc được `webapp.user-detail`: `videoCount 13`, `followerCount 8`, `heartCount 104`, signature giống hệt bio Instagram. API item_list trả rỗng (thiếu signature), và grid video không mount nên DOM chỉ có 395 ký tự, 0 thẻ `/video/`.
result: PENDING - 13 video là ứng viên nặng ký nhất cho "appease the algorithm", chưa đọc được caption.

## H8 - Lười render của in-app Browser
cmd: `evaluate_script` gọi `window.scrollTo` rồi đếm `a[href*="/p/"]` / `a[href*="/video/"]`
evidence: lưới Instagram kẹt ở 12/27 bài và không tăng sau nhiều lần scroll; `scrollHeight` đứng nguyên 1918. Nguyên nhân: tab bị ẩn (`visibilityState: hidden`, `visible=false` ở lỗi pointer, và `click` báo `NATIVE_BROWSER_VIEWPORT_UNAVAILABLE`). Ép `Object.defineProperty(document,'visibilityState',{get:()=>'visible'})` + dispatch `visibilitychange`/`focus`/`pageshow` thì `document.visibilityState` trả `visible` nhưng React vẫn không mount lưới.
result: DEAD (kỹ thuật) - không lách được từ script; cần người dùng mở và focus cửa sổ in-app Browser.

## H9 - Hint chính thức của bài: "Social / instagram.com/cybersecuritysociety"
cmd: mở `https://www.instagram.com/cybersecuritysociety/` bằng browser đã đăng nhập
evidence: đó là tài khoản **Ba Tư**, tên hiển thị "جامعه امن سایبری" (Cyber Security Society), 18 bài / 950 followers / **5,356 following**, bio "بهترین اخبار هک و امنیت را با ما دنبال کنید" + link `T.me/cybersecuritysociety`. Cả 12 bài đọc được đều là tin an ninh năm 2018 (Cisco, Firefox <=62, sân bay Mashhad, Wings for Life...). Grep `CSSCTF` trong toàn bộ DOM: 0.
result: DEAD - không phải tài khoản của ban tổ chức, và cũng không có cờ nào cài ở đó.

## H10 - Telegram của tài khoản trong hint
cmd: `curl https://t.me/s/cybersecuritysociety`
evidence: 9772 B, title "Telegram: Contact @cybersecuritysociety", 0 tin nhắn trong preview, 0 lần `CSSCTF`.
result: DEAD.

## H11 - Tìm công khai chuỗi cờ trên Instagram
cmd: `https://www.instagram.com/explore/search/keyword/?q=CSSCTF` (đọc bằng phiên đã đăng nhập)
evidence: 5 kết quả, tất cả là khớp gần đúng chữ: 3 tin của ATERRA Metals mang ticker **CSSCF**, một booking `trybooking.com/CSSCF`, một hashtag `#CSSCF` về supply chain, và một symposium của "CSSCF". Không bài nào của society, không bài nào chứa `CSSCTF{`.
result: DEAD - trên Instagram công khai không có bài nào mang prefix cờ.

## H12 - Cờ trong ảnh poster / mã QR của @cybersecuritysydney
cmd: tải `img.src` từ lưới bài viết (CDN fbcdn) rồi `pyzbar.decode` từng ảnh
evidence: 9/12 ảnh tải được (độ phân giải 1080x1350 đến 2116x2821). QR giải ra 6 liên kết, tất cả là link đăng ký: `ctf.cybersecurity.sydney`, `docs.google.com/forms/d/e/1FAIpQLSfP1D3Ch9...`, `forms.gle/1o64Moscwo1ScS3v8`, `au.cglink.me/25W/r382007`, `linktr.ee/qr/d2e754eb-...`. Bốn ảnh còn lại không có QR.
result: DEAD - QR chỉ trỏ tới form đăng ký sự kiện.

## H13 - Caption của 12 video TikTok @cybersecuritysydney
cmd: `fetch('/@cybersecuritysydney/video/<id>')` rồi đọc `webapp.video-detail.itemInfo.itemStruct.desc`
evidence: 12/13 video (videoCount = 13, API `/api/post/item_list` trả rỗng vì thiếu signature). Toàn bộ caption là tin sự kiện; hai video ngày 2026-09-26 là thông báo Return of Nexus, chỉ chứa chữ "flag" trong "#capturetheflag" và "get to the flags before everyone else does". Không có `CSSCTF{`.
result: DEAD (với caption) - chưa xem nội dung từng khung hình.

## H14 - Comment của bài ghim
cmd: mở `/p/DdsfW2IR8N5/`, cuộn, grep `CSSCTF` trong DOM
evidence: `bodyLen` 1999, 0 phần tử `ul li`, 0 hit. Bài ghim không có comment nào hiển thị.
result: DEAD.

## Kênh còn mở
- **Discord** guild `1119954291831091221`: chưa vào được từ ngoài (preview 401). Tên bài là "Server" và Discord là kênh duy nhất mà nội dung bị khoá theo tư cách thành viên, nên đây vẫn là ứng viên số một.
- **Facebook** `profile.php?id=61552628758945`: chưa đọc được.
- 15 bài Instagram cũ hơn của @cybersecuritysydney: lưới kẹt ở 12/27, `scrollBy`/`WheelEvent`/phím End đều không kích hoạt IntersectionObserver; `scrollHeight` đứng nguyên 1918.

## H15 - Quét lại toàn bộ 27/27 bài của @cybersecuritysydney
cmd: `window.scrollTo` + `dispatchEvent(new Event('scroll'))` lặp 4 lần, mỗi lần chờ 2.2s, rồi lấy `img.alt` của mọi `a[href*="/p/"]`
evidence: lưới bung từ 12 lên 24 rồi 27 bài (đúng `media_count`). Đọc hết 27 caption: toàn tin sự kiện (Bug Bounty Google Gruyère, First Flag: the Entry Point, ⇧Shift in CTRL, Wings for Life, COMP2017 101, Linux Basics, AGM, International Women's Day, Hack the Harbour, Return of Nexus, tutorial). Không caption nào chứa `CSSCTF{`. 12 ảnh poster giải QR ra toàn link đăng ký. Bài ghim 0 comment.
result: DEAD - không có cờ trong text công khai của tài khoản thật.

## H16 - Đọc hết 18/18 bài của chính tài khoản trong hint
cmd: mở `/cybersecuritysociety/`, scroll tới khi `n == 18`, grep `CSSCTF` trong `documentElement.innerHTML`
evidence: 18/18 bài, toàn bộ là tin an ninh tiếng Ba Tư khoảng 2018 (shortcode đầu `BqP3joTgilY`, cũ nhất `BoWP6qIFyE6`); DOM grep trả `[]`.
result: DEAD - đây là kênh Iran đã chết từ 2018, không phải tài sản của ban tổ chức.

## H17 - Server: header, HTML comment, favicon của nền tảng CTFd
cmd: `curl -sI https://ctf.cybersecurity.sydney/`, grep `<!--` và `CSSCTF{` trên trang login
evidence: header chỉ là Cloudflare + CTFd chuẩn (`Server: cloudflare`, `cf-cache-status: DYNAMIC`, session cookie `HttpOnly`), không có header lạ. Trang login không có HTML comment đáng chú ý, 0 hit `CSSCTF{`. Đường dẫn favicon lấy từ trang login trả 404 (link gắn theo phiên).
result: DEAD.

## Kết luận tạm thời
Hint trỏ tới `instagram.com/cybersecuritysociety`, nhưng handle đó **không thuộc về ban tổ chức** - bài AGM của họ ("selecting a refreshed society name, some sweet rebranding") cho thấy society vừa rebrand sang "Cybersecurity Society Sydney" và phải lấy handle `@cybersecuritysydney` vì `@cybersecuritysociety` đã bị chiếm từ 2018. Mọi thứ đọc được trên các kênh công khai của họ đều sạch cờ, nên nhiều khả năng cờ nằm ở nơi cần một trong hai thứ mà agent không tự có: (a) một tài khoản Instagram chị em chưa đoán được handle, hoặc (b) nội dung chỉ hiển thị sau khi follow/tương tác.

Việc còn mở: tab Reels và Tagged của @cybersecuritysydney (fetch thô chỉ ra shell, phải render thật), 13/13 video TikTok (đã đọc 12), ảnh poster chưa OCR (máy chưa có `pytesseract`), và trang Facebook `profile.php?id=61552628758945`.

## H18 - Quét nốt các tab và highlight của @cybersecuritysydney (browser đã render được)
cmd: `navigate_page` từng tab rồi `evaluate_script` cuộn + grep `CSSCTF` trong `documentElement.innerHTML`
evidence:
- `…/reels/`: lưới rỗng thật (0 phần tử, body chỉ còn header profile). Không có reel nào.
- `…/tagged/`: 19 bài, tất cả là bài của tài khoản khác tag society (GDG, WIT/SUAIA, Coding Fest, Engineering Revue, OffSec Red Team…). 0 hit `CSSCTF`.
- Highlight `EVENTS` (7 tuần), `FUN FRIDAYS!` (18 tuần), `ARCHIVE` (27 tuần): mỗi collection chỉ render 1 story, có nhạc nền, không có chữ overlay nào chứa cờ; DOM grep `[]` cho cả ba.
- Header profile vẫn hiện nút **Follow** -> tài khoản đang dùng chưa follow họ.
result: DEAD - toàn bộ bề mặt công khai của Instagram đã sạch.

## Đọc lại đề sau khi H1-H18 sạch
"Maybe get a head start on **future hints**" + "appease the **algorithm**" + "keeping us on your radar by **following**" là ba cụm mô tả cơ chế creator của Instagram: like/comment/share để thuật toán đẩy bài, và follow để được nhận **DM tự động** hoặc vào **broadcast channel**. Cả hai kênh đó đều gắn với tài khoản đang đăng nhập, không phải trang công khai, nên không có cách nào đọc từ ngoài - đây là chỗ duy nhất còn sót lại.

## H19 - Stego trên 2 poster CTF (giả thuyết của người dùng)
cmd: `python` - so sha256 với bản CDN, dò segment JPEG, tìm magic nhúng, `rfind(b'\xff\xd9')` đo byte thừa, rồi quét LSB ở **mức bit** (không chỉ biên byte) cho R/G/B, hai chiều dòng, cả bit0 và bit1 của 2-bit plane, chuỗi interleaved pixel-major và chuỗi đảo ngược
evidence: bản người dùng tải về **trùng từng byte** với bản CDN (269269 B, sha256 `5143ac71…`), nên không phải bản gốc. JPEG chỉ có `SOI + APP1/JFIF + DQT/DHT/SOF0/SOS + EOI`, **không EXIF, không XMP, không COM**, 0 byte sau `FFD9`, 0 magic file lạ. Quét bit-level trên cả `DdsfW2IR8N5` và `DdspWldRzAj`: 0 vị trí khớp `CSSCTF`/`cssctf`/`flag{`/`FLAG{`.
result: DEAD - và còn có lý do cấu trúc: Instagram re-encode JPEG lossy nên LSB không thể sống qua bước upload. Muốn ra đề stego thì tác giả phải phát file trực tiếp (như Colour Shift cho BMP), không thể đăng qua Instagram.

## H20 - QR của toàn bộ poster
cmd: `pyzbar.decode` trên 16/25 ảnh đã tải, có thử lại ở 1/2 và 1/3 độ phân giải
evidence: 7 QR, tất cả là link đăng ký: `ctf.cybersecurity.sydney`, `docs.google.com/forms/d/e/1FAIpQLSfP1D3Ch9…`, `forms.gle/1o64Moscwo1ScS3v8`, `au.cglink.me/25W/r382007|r382336|r382696`, `linktr.ee/qr/d2e754eb-…`. Chuỗi cglink giải ngân 3 bước về `clubs.usu.edu.au/CSS/rsvp_boot?id=<số>` - chỉ là trang RSVP của câu lạc bộ.
result: DEAD.

## H21 - Story đang hoạt động (CTF vừa mở ~3h)
cmd: grep `/stories/<user>/<id>/` và `aria-label` trên trang profile
evidence: chỉ 3 URL story, tất cả là highlight (`EVENTS`, `FUN FRIDAYS!`, `ARCHIVE`) đã đọc ở H18. Không có story đang chạy, không có vòng story mới.
result: DEAD.

## H22 - Auto-DM sau khi follow
cmd: mở `/direct/inbox/` sau khi tài khoản đang dùng đã follow (header profile chuyển thành "Following")
evidence: không có hội thoại nào từ `cybersecuritysydney`. Thread duy nhất liên quan tới giải là cuộc trò chuyện với `جامعه امن سایبری` (chính là tài khoản Ba Tư trong hint sai), và chỉ có tin "yo" do người dùng gửi, không có phản hồi.
result: DEAD.

## Kết luận
Hint đã phải sửa một lần (`cybersecuritysociety` -> `cybersecuritysydney`), chứng tỏ khâu ra đề social của bài này đang không chắc tay. Toàn bộ nội dung công khai của tài khoản đúng - 27/27 caption, 19/19 bài tagged, 3 highlight, reels trống, story, bio, Linktree, 7 QR - đều không chứa `CSSCTF{`, và hai poster CTF đã được kiểm stego ở mức bit. Bài này nhiều khả năng **lỗi đề hoặc cờ chưa được đăng**, nên bước hợp lệ còn lại là hỏi trực tiếp ban tổ chức thay vì tiếp tục quét.

## H23 - Manh mối đồng đội đưa: `https://www.vesen.app/?utm_source=ig&utm_medium=social&utm_content=link_in_bio`
cmd: tải trang, tải bundle `/assets/index-C48B2XTr.js` (143 KB) + CSS, grep `CSSCTF|nexus|ctf|sydney|usyd`, bóc toàn bộ cây filesystem khai báo trong bundle, fetch 3 file có `filePath`, rồi thử `flag.txt`/`hint.txt`/`robots.txt`/`.git/config`
evidence:
- `meta description` = "Web-based terminal powered by Svelte", title "Vesen Terminal". Bundle chứa `version:"1.2.0"`, `license:"MIT"`, `author:{name:"Has Salvesen", url:"https://www.vesen.app"}`, `repository: github.com/hsalvesen/vesen`.
- Cây filesystem là **demo gốc của project**: `index.html` = "My Portfolio", `main.c` và `javascript-basics.js` = Hello World, `playlist.m3u` = "Song Title", `backup.sh` = script mẫu. 3 file có `filePath` (`/README.md`, `/history.txt`, `/linux.txt`) đúng là nội dung upstream giới thiệu lịch sử terminal.
- Grep trong bundle: 0 lần `CSSCTF`, 0 lần `nexus`/`ctf`/`sydney`/`usyd`. Chuỗi duy nhất chứa "flag" là `flags:t,items:new Map` (cờ của RegExp).
- Server là static SPA có catch-all: `flag.txt`, `cssctf.txt`, `hint.txt`, `robots.txt`, `.git/config` đều trả **đúng 623 byte** giống trang index -> không có file ẩn.
- Linktree của society (`lt2.html`, 238 KB đã tải ở H6) chứa **0** lần "vesen".
result: DEAD - đây là site cá nhân của tác giả mã nguồn mở Vesen Terminal, không liên quan giải. UTM `link_in_bio` chỉ chứng minh một tài khoản Instagram nào đó để vesen.app ở bio, và tài khoản đó không phải của ban tổ chức.

## H24 - Slide lễ khai mạc do một BTC gửi ("Opening Ceremony.pdf")
cmd: `pymupdf` trích text 14 trang; `zlib.decompress` toàn bộ 191 stream rồi grep `CSSCTF\{|flag\{|FLAG\{`; grep trực tiếp trên file thô
evidence: file 15072852 B, 14 trang, `/Producer = Canva`, không mã hoá, 79 ảnh. Text trích được không chứa cờ. **0 hit** trong mọi stream đã giải nén; chuỗi `CSSCTF{` duy nhất trong file là dòng luật ở trang 7: "Submit all flags in the standard CSSCTF{...} format (**case-sensitive**) unless stated otherwise". Trang 13 là nguồn của hint: `Follow instagram.com/cybersecuritysociety :)` + `ctf.cybersecurity.sydney` + `discord.gg/gUGqmt4Gqf` (lưu ở `analysis/opening_ceremony_p13.jpg`).
result: DEAD cho việc tìm cờ trong PDF, nhưng **OK cho việc giải thích đề**: chính slide tổng kết của BTC ghi sai handle, và hint trên CTFd chỉ là chép lại dòng đó.

## Hai ràng buộc rút ra từ luật, ảnh hưởng tới cách xử lý
- **Luật 3** cấm hỏi/đoán/bàn cờ ở nơi công khai, "including but not limited to Discord channels" -> không được post câu hỏi "flag Server Juice ở đâu" lên kênh chung; phải dùng **support ticket** theo **Luật 8**.
- **Luật 6**: cờ **phân biệt hoa thường**, nên nếu sau này tìm được thì submit đúng nguyên văn.
- Trang 9 và 10 nhiều lần nhắc "**the welcome flag**" (được loại khỏi số 12 cờ cần cho PEP hours) -> khả năng đây là bài welcome, và nội dung "follow us" trên slide là quảng bá chứ không gắn với một cờ nào đã được đặt lên Instagram.

## H25 - Comment của các bài khác (kênh đúng)
cmd: mở `https://www.instagram.com/p/DWL9S-wkyJT/` trong trình duyệt đã đăng nhập, bấm "more" cho hiện hết caption, rồi grep `CSSCTF\{` trong `documentElement.innerHTML`
evidence: 2 hit `CSSCTF{premiumreserve}`, nằm trong phần comment của `harrysalvesen`, "8h", 11 likes. Caption của cùng bài hiển thị chữ "Edited" và kết bằng "We hope to see you there; BYO water. 💧". Áp phích của bài đó có đoạn chat giả lập với hai dòng "u seriously care more about a club than the premium reserve??" và "come for the server juiceeeee" - dòng dưới là tên bài, dòng trên là nội dung cờ.
result: OK - cờ: `CSSCTF{premiumreserve}`

## H26 - Danh tính người đăng comment
cmd: so `harrysalvesen` với chuỗi tác giả trong bundle `vesen.app`
evidence: bundle Vesen khai `author:{name:"Has Salvesen", url:"https://www.vesen.app"}`, `repository: github.com/hsalvesen/vesen`. Trùng tên tới mức `vesen.app` để ở bio Instagram của chính tài khoản này, giải thích luôn cái UTM `link_in_bio` mà đồng đội đưa ra ở H23.
result: OK - H23 không phải hướng sai hoàn toàn, nó trỏ đúng người nhưng sai chỗ.

## Lỗi phương pháp của lần tìm này
H14 đã kiểm comment nhưng chỉ kiểm **bài ghim**, thấy 0 comment rồi loại luôn cả kênh comment. Đó là bước nhảy sai: một bài không có comment không có nghĩa cả tài khoản không có comment nào. Toàn bộ nỗ lực sau đó dồn vào caption và pixel, là hai kênh đã cạn từ lâu. Điểm giữ được là không xoá nhánh sai trong log, nên khi quay lại thấy ngay kênh duy nhất chưa phủ đủ.

## Kết luận
Đề không lỗi. Hint sai handle là thật (trang chót slide khai mạc ghi `cybersecuritysociety`, handle đó thuộc về một kênh Ba Tư dừng từ 2018), nhưng ban tổ chức đã đính chính và cờ có nằm trên Instagram của họ, trong comment của bài `DWL9S-wkyJT`.

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
