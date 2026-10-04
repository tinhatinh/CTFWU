# Đề bài - corporate-rat

## Nguyên văn đề

```text
Corporate RAT!
500
Log Analysis
adlee7

Here at BigBadOrganizationTM we don't tolerate RATS! One of our employees is actively stealing
our secrets to take over the world- I mean, make lots of money- and leaked it to the press!
Find out which employee did it so we can fire them!!!

The flag format is cdctf{Firstname Lastname}. You have five (5) submission attempts for this challenge.
```

Định dạng cờ: `cdctf{Firstname Lastname}`. Điểm hiển thị trên thẻ khi chụp: 500. Tác giả: adlee7.

## Thông tin đã xác minh từ file

Artifact là một zip chứa 5 file, giải nén ra thư mục con `corpo_rat/`.

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/corpo_rat.zip` (copy từ: `C:\Users\Administrator\Downloads\corpo_rat.zip`) |
| Kích thước | 128747 byte |
| SHA-256 | `5109835422566de5a581fe8a8b58d9aa037d8639fa633fa2d486a45f7f6c5a66` |
| Loại file | Zip archive data, made by v2.0 UNIX |
| Nhiệm vụ | Chỉ ra một nhân viên trong roster là người cài RAT lên host `ubnt-app02` |
| Định dạng cờ | `cdctf{Firstname Lastname}` |

Các file bên trong và SHA-256 từng file:

| File | Kích thước | Số dòng | Nội dung |
| --- | --- | --- | --- |
| `audit.log` | 752470 B | 3454 | auditd: SYSCALL, EXECVE, SOCKADDR, USER_LOGIN, USER_CHAUTHTOK, CONFIG_CHANGE, PATH |
| `auth.log` | 398061 B | 3948 | sshd (Accepted/Failed/Invalid user), sudo COMMAND, pam session, systemd-logind |
| `cron.log` | 58917 B | 679 | CRON `CMD (...)`, `crontab[] REPLACE`, `CRON RELOAD` |
| `syslog` | 122404 B | 944 | 106 dòng UFW BLOCK (quét cổng từ ngoài), 570 dòng UFW ALLOW (egress tới C2), dhclient, NetworkManager, unattended-upgrades, dpkg |
| `users.txt` | 4662 B | 100 | roster 98 user: `username  uid  full_name  dept  sudo  shell` |

```text
1fdf8575ceabe38f1079870588a25206b2ff4ec48c7f531331faa87db08b5339  audit.log
9ff3b049a380fbcc02104601e5c07b613167fd19dc2296216ca6be65b10c5de5  auth.log
da8b9dd4038da32868126897eaf139df19c7524751e97d1bd1a28529c3ae00da  cron.log
72dcc6adbd934e2172a21f287cb8c26bc0de78ae4167b6ad91fd4067adc41028  syslog
44873c09f73b06610d7c9ceeac66d9ac745d73f7131ae4771592fc0967ca7929  users.txt
```

Cửa sổ thời gian của log: `Sep 14` đến `Sep 27`, mốc epoch trong `audit.log` là giây UTC và trùng
giờ ghi trong `cron.log` / `auth.log` (beacon đầu tiên `Sep 20 02:43:01` UTC, dòng cron đầu tiên
`Sep 20 02:43:00`).

Không có `files/de.png`: thẻ đề được copy dạng văn bản, chưa có ảnh chụp.

## Hướng giải (tóm tắt)

Implant duy nhất là `/tmp/.cache/.upd`: chạy 568 lần, beacon 568 lần tới một socket đích, được
cron của root gọi lại mỗi ~20 phút. Chuỗi liên kết ba log trói nó với một uid: dòng `crontab[4711]:
(root) REPLACE (root)` trong `cron.log` khớp `USER_CHAUTHTOK pid=4711 auid=1066` trong `audit.log`,
và `users.txt` dịch uid 1066 thành tên khai sinh. Cùng `auid=1066` cũng là chủ ba lệnh
`curl`/`chmod`/`crontab` cài implant, chạy trong phiên sshd có pid 4344 đúng như trường `ppid` trong audit.

## Chạy lại lời giải

```bash
python exploit.py files/corpo_rat.zip          # suy ra cờ từ 5 file trong zip
python analysis/beacons.py files/corpo_rat.zip  # thống kê nhịp beacon và số lần cron
```

Kết quả: `cdctf{Lamar Hackson}` (đã lưu trong `flag.txt`).
