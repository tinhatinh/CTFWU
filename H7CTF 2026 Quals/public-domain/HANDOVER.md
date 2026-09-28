# HANDOVER — Public Domain (OSINT, External, 420đ, format `flag{...}`)

Đồng đội đã tìm ra flag — file này chỉ ghi lại những gì mình đã loại trừ/đào được, kèm các bẫy của host.

## 0. Card không có seed (đã kiểm tra bằng phiên đăng nhập thật)
`https://ctf.h7tex.com/challenges/public-domain` sau khi Launch chỉ chứa đúng một câu:
"Some operators still think their domains are private. Infrastructure has a longer memory than they do."
Không Files, không Instance, không hint thêm. Objectives: 1 `flag`, format `flag{...}` (khác `H7CTF{...}`).

## 1. Bẫy lớn nhất của máy này: DNS nội bộ trả lời sai
`nslookup <bất kỳ tên nào>.h7tex.com` -> **192.168.0.1**, kể cả `h7tex.com`, `ctf.h7tex.com` (những host đang chạy bình thường qua curl).
=> Đừng kết luận "domain trỏ vào LAN" từ nslookup. Dùng DoH để hỏi sự thật:
```
curl -sS -H "accept: application/dns-json" "https://cloudflare-dns.com/dns-query?name=<host>&type=A"
```
Và khi cần gọi HTTP tới host công khai thì bypass resolver: `curl --resolve <host>:443:<IP>`.

## 2. Certificate Transparency (crt.sh?q=h7tex.com&output=json) — 82 cert, 11 tên
```
h7tex.com  *.h7tex.com  2025.h7tex.com  2026.h7tex.com  app  ctf  info  abu
paperchase  proserv  upload
```
Kết quả DoH thực tế:
| host | tình trạng |
| --- | --- |
| h7tex.com, app.h7tex.com | Cloudflare (104.21.54.207 / 172.67.142.20), Next.js + CTFd-ish, sống |
| ctf.h7tex.com | 34.93.46.24 (GCP), Anvil SPA, sống |
| 2026.h7tex.com | CNAME **h7-tex.github.io** -> GitHub Pages (185.199.108-110.153) |
| upload.h7tex.com | **34.68.254.54** — DNS còn, cert LE 2026-01-31, nhưng 80/443 timeout (không scan port thêm) |
| abu / info / paperchase / proserv | NXDOMAIN (Status=3) |
| play.h7tex.com (từ repo, không có trong CT) | Cloudflare DNS nhưng origin timeout |
| h7ctf / web1 / night / admin / internal | NXDOMAIN |

## 3. GitHub org `H7-Tex` (rút ra từ CNAME của 2026)
`https://api.github.com/users/h7-tex/repos` -> 4 repo public:
| repo | branch | size | mô tả |
| --- | --- | --- | --- |
| h7-tex.github.io | main | 14 MB | "CTF Infra 2025" — **cả bộ CTFd + dump API** |
| H7CTF25 | **master** | 43 MB | "Challenge Repo for H7CTF'25" — **mình chưa tải về** |
| TX | master | 247 KB | team website (29 commits, không có flag{) |
| W26 | main | 1.1 MB | CTF'26 Lander (35 commits, không có flag{; có file `CNAME` = h7ctf.h7tex.com) |

Trong `h7-tex.github.io` có `api/v1/...` = **3816 file snapshot** dữ liệu challenge mùa 2025
(`api/v1/challenges/<id>/index.json` — tên, category, docker image `Night | chal3-pwn:latest`,
`custom_subdomain: play.h7tex.com`, file đính kèm `/files/<md5>/<name>`). Không có field `flag` trong dump.
Lịch sử repo chỉ 12 commit; file đã xoá: `CNAME`, `login.html`, `register.html`, `reset_password.html`.

## 4. Wayback (web.archive.org/cdx/search/cdx?url=h7tex.com&matchType=domain) — 698 URL
Host khác ngoài ctf: `newsleaks`(8), `paperchase`(6), `paste`(6), `info`(5), `codebreaker`(2), `proserv`(1).
Đã fetch raw 21 URL (`/web/<ts>id_/<url>`) và grep `flag{`: **không thấy gì**.
Đó là challenge host của mùa 2024/2025: `paperchase` + `newsleaks` có `/view.php?file=...etc/passwd` (LFI cũ),
`info/about` 403 sau Cloudflare challenge, `paste` 403.

## 5. Những hướng mình chưa đi (nếu cần đào lại)
- `H7CTF25` (master, 43 MB) — repo challenge 2025, chưa mở.
- Pickaxe toàn bộ history mọi repo: `git log -S 'flag{' --all`, và grep trong blob đã xoá.
- CDX **không** `collapse=urlkey` cho từng host private (nhiều timestamp hơn).
- Passive DNS/history cho 34.68.254.54 (upload) và 34.93.46.24 (ctf) — Shodan/Censys.
- Common Crawl index cho các host đã chết.

## 6. Vệ sinh đĩa
Case này đã tải về nhiều: `files/www25/` (~242 MB giải nén từ tarball), `files/repos/*` (4 clone,
trong đó `infra25` dùng `--filter=blob:none`), `files/h7-tex.github.io.tar.gz` (55 MB).
Xoá được nếu không cần: `rm -rf files/www25 files/repos files/*.tar.gz`.

## 7. Secret scanning trên GitHub (đã redact 2026-09-28)

Bản chụp `files/www25/` chứa mô tả hai challenge Cloud của một CTF cũ, và chính mô tả đó công bố
một cặp AWS key:

| File | Giá trị gốc | Sau redact |
| --- | --- | --- |
| `files/www25/api/v1/challenges/31/index.json` | `AKIA4DBSBEHX7JWOZ5H2` + secret 40 ký tự | `AKIA-REDACTED-CTF-PROP-01` / `REDACTED-CTF-PROP-secret-31` |
| `files/www25/api/v1/challenges/32/index.json` | `AKIAQOPT3DJVRPRTAFXP` + `/rP7fHH/...` | `AKIA-REDACTED-CTF-PROP-02` / `REDACTED-CTF-PROP-secret-32` |

Mỗi giá trị xuất hiện hai lần (mô tả markdown + bản render HTML), nên cả bốn lần đều bị GitHub
Secret Scanning bật alert "Public leak". Đây là key đạo cụ do tác giả challenge cũ đặt trong đề,
không phải key thật của ai - kiểm chứng nhanh: cặp key của `deputy` trong cùng event là
`AKIAANALYST000000000`, và toàn bộ cloud của H7TEX chạy mock AWS không kiểm SigV4.

Đã redact trong working copy để default branch không còn chuỗi dạng `AKIA[0-9A-Z]{16}`. Hai lưu ý:

- Alert cũ **không tự đóng** khi xoá chuỗi khỏi branch. Phải vào Security → Secret scanning alerts
  → từng alert → Close alert → chọn "Not a valid secret" (hoặc "Used in tests").
- Giá trị gốc vẫn nằm trong lịch sử commit. Muốn xoá hẳn thì cần `filter-repo` + force push, và
  với key đạo cụ thì không đáng.

## 8. `files/repos/*` khong con la submodule (2026-09-28)

Ba ban clone cua H7-Tex (`TX`, `W26`, `infra25`) duoc commit nhu **gitlink** ma repo khong co
`.gitmodules`, nen nguoi clone ve chi nhan ba thu muc rong. Da bo `.git` long cua tung ban va
lưu lai nhu file thuong, kem `SOURCE.txt` ghi URL + commit + ngay:

| Folder | URL | Commit | Trang thai |
| --- | --- | --- | --- |
| `TX/` | github.com/H7-Tex/TX.git | `9d768f0` (2025-12-25) | 44 file, day du |
| `W26/` | github.com/H7-Tex/W26.git | `83046e2` (2026-09-25) | 16 file, day du |
| `infra25/` | github.com/H7-Tex/h7-tex.github.io.git | `81014f8` (2025-10-22) | **chi co SOURCE.txt** |

`infra25` duoc clone bang `--filter=blob:none` va working tree chua bao gio materialize day du
(git checkout cua Windows chet giua chung khi tao `CTFd/...`), nen thay vi luu mot ban vo sinh
thieu, folder chi ghi lai lenh tai tao. Toan bo noi dung that nam trong
`files/h7-tex.github.io.tar.gz` (54.937.575 B) - file bi `.gitignore` vi nhe hon nguong 100 MB
cua GitHub nhung van nang voi repo writeup.
