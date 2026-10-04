# notes.md - tattle-tale

Input: instance `https://waambrjp.i.cdctf.net` (`player@terminal`), key `~/.ssh/key` (ed25519,
comment `Universal`). Định dạng cờ đề cho: `cdctf{Fl4g!}` (mẫu).

## H1 - Triage box nguoi choi
cmd: `id; hostname; uname -a; cat /etc/hosts; ls -la ~; ps -ef; cat /proc/net/route` + sweep `/dev/tcp`
evidence: PID 1 la `ttyd -p 7681 ... -W /bin/bash -l` chay bang `player`; khong co service local nao
khoa (chi ttyd 0x1E01=7681 va DNS 127.0.0.11). 2 NIC 172.26.2.2 / 172.26.3.2. Portal duy nhất mở 22
trong 58 host quét được: `172.26.2.3` = `one`.
result: OK - phải đi ra ngoài, không có gì để khai thác tại chỗ

## H2 - Doc ba tho trong ~/README.md
cmd: `cat ~/README.md`
evidence: tu khoa `script`, `.ssh/key`, `10s`, `S-F-T-P`, cap user/may `zero`/`one`, `one`/`two`,
`two`/`three`, `three`/`four`, roi "peek at the floor" va "as bits down at `one`".
result: OK - de tu mo ta toan bo co che, chi can kiem chung tung mong

## H3 - ssh zero@one
cmd: `ssh -o BatchMode=yes -i ~/.ssh/key zero@one 'id'`
evidence: xac thuc thanh cong, message `This service allows sftp connections only.` (ForceCommand)
result: DEAD cho huong shell - moi thuc thi phai di qua SFTP

## H4 - Leo SFTP chroot
cmd: `sftp -i ~/.ssh/key zero@one` + `ls -la /`, `ls -la /.ssh`, `get /.ssh/*`
evidence: `/` = `.ssh` (root) + `scripts` (1000:100). `authorized_keys` = public key cua ta.
`/.ssh/keys/key` doc duoc (91 B, public). `/.ssh/key` 399 B root 600 -> `Permission denied`.
`put /tmp/x /cb` ( goc chroot) -> Permission denied; `mkdir probe` + `put marker.txt` trong `/scripts` -> OK.
result: OK - /scripts la cho duy nhat ghi duoc

## H5 - Thu ten file ma runner chay
cmd: 11 probe (`script`, `run.sh`, `zero`, `one`, `a`, `a0`, `tattle`, `payload`, `gossip`, `zzz`,
`floor`), moi file ghi `h_<ten>` vao /scripts; doi 90s
evidence: khong co `h_*` nao xuat hien, khong file nao bien mat
result: FALSE NEGATIVE - ly do thuc te duoc tim thay o H7: root nhin thay `/home/zero/scripts`,
con duong dan `/scripts` **khong ton tai** trong namespace cua root (`ls: /scripts: No such file or
directory`), nen redirect `> /scripts/h_x` that bai im lang. Ten file khong phai van de.

## H6 - Kenh socket va loi doc du lieu
cmd: listener `python3` 9999/9998 tren terminal (recv 1 lan roi close; sau do settimeout(10))
evidence: callback dau tien chi co 1 dong `MARK uid=0 host=one ...` roi mat; cac lan sau bi cat
dung giua muc `=== names`. Payload van chay root deu 10s (6 ket noi cach deu 10s).
result: DEAD end (kenh khong on dinh) - hai loi: (a) listener dong som hon payload xong viec,
(b) runner de chet instance moi moi 10s va chung ghi de cung mot file

## H7 - Doc co che runner (thu thanh cong)
cmd: payload root cat `/etc/sftp.d/run_scripts` + `ps -ef` + `/proc/self/mountinfo`, tra ve qua socket
evidence:
`find /home -name script -exec chmod +x {} \;` / `find /home -name script -exec {} \;` / `sleep 10s`,
process `find /home -name script -exec {} \;` + `{script} /bin/bash /home/zero/scripts/script` (root),
mount `tattletale/run_scripts -> /etc/sftp.d/run_scripts (ro)`, `tattletale/key -> /home/zero/.ssh/key (ro)`,
host `one` = Alpine/linuxserver-openssh, user `zero:1000:/home/zero:/bin/ash`,
ten phan giai `one=172.26.4.2`, `two=172.26.4.3`, `three=none`
result: OK - **root code execution tren hop `one`**, chu ky 10s, va `/scripts` == `/home/zero/scripts`

## H8 - Kenh keo file ve
cmd: payload ghi `/home/zero/scripts/rec3.txt` (root), player `sftp get /scripts/rec3.txt`
evidence: tai ve duoc `MARK 2026-10-04T02:47:05+00:00 uid=0 host=one` + nguyen listing
`/home/zero/scripts` (rec3.txt root 644, xen ke cac probe cua ta)
result: OK - khong can socket, khong can reverse shell

## H9 - Test hop one -> two
cmd: payload chay `timeout 12 sftp -b /tmp/b.txt -i /home/zero/.ssh/key one@two` voi batch `pwd; ls -la`
evidence: lan chay dau bi cat boi loi H6; lan chay sau (rec4) van chua lay duoc doan nay vi output
tron trong mot file bi ghi de
result: OPEN - buoc tiep theo phai chay lai voi flock + tmp/cp (da sua trong exploit.sh)

## H10 - Bien dang con mo
- Do dai day hop that (so name phan giai duoc tiep dien khong?).
- Cho co: `four`? mot user/thu muc ten `floor`? `/flag` tren hop cuoi?
- `analysis/propagator.sh` la bo lan hoan chinh, chua chay.
