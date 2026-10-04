# Đề bài - tattle-tale

## Nguyên văn đề

```text
Tattle Tale
495
Pwn
reep236

Hey, did you hear??? Alice told Bob told Carol told Dave told Eve told ... told me that Alice has a
secret flag she's been hiding from everyone! I don't think I was supposed to tell anyone, but how
could I help but tattle a bit? If you can get back to Alice's machine, you can probably get the flag
from her!

The flag format is cdctf{Fl4g!}
```

## `~/README.md` trên instance (nguyên văn)

```text
Tattle tattle tattle,
Your `script` goes up the chain
Tattle tattle tattle,
With `.ssh/key` she won't complain

As each `10s` passes,
`/script` `/script` `/script`
Each `10s` passes,
`one` to `two` to `three`

Send the `script`, S-F-T-P
User `zero` on `one`'s machine
And `one` on `two`, hence
`two` on `three`

Then `three` to `four`,
and when at last there's no more,
take a peek at the floor:
*"It's a flag!"*

Oh back then it goes
From door to door,
Pass it back, 'cross the floor
Reel in your reward

Until there it sits
As bits down at `one`
And then, my friend
You'll have had some fun
```

## Thông tin đã xác minh trên instance

| Mục | Giá trị |
| --- | --- |
| Instance | `https://waambrjp.i.cdctf.net`, hostname `terminal`, `player` uid 1000 |
| Kernel | `Linux terminal 6.12.111+deb13-cloud-amd64` (Debian 13) |
| NIC | 172.26.2.2 (eth1) và 172.26.3.2 (eth0), default gateway 172.26.3.1 |
| Host reachable | chỉ `172.26.2.3:22` (tên `one`) trong 172.26.2.1-29 và 172.26.3.1-29 |
| Credential | `~/.ssh/key`, ed25519 không passphrase, comment `Universal` |
| Tool trên `terminal` | `python3`, `curl`, `socat`, `ssh`, `sftp`, `scp`, `ssh-keygen`; **không** `nc`, `gdb`, `gcc`, `ip`, `ss` |
| `one` | container Alpine (image kiểu linuxserver/openssh-server, có `/etc/sftp.d/`, `/usr/local/bin/create-sftp-user`) |
| Tài khoản trên `one` | `zero` uid 1000, shell `/bin/ash`, `ForceCommand internal-sftp` (thông báo "This service allows sftp connections only.") |
| Chroot của `zero` | `/` gồm đúng `/.ssh` (root) và `/scripts` (uid 1000 gid 100) - ánh xạ của `/home/zero/scripts` |
| Bind-mount trên `one` | `/opt/ctf-challenges/tattletale/key -> /home/zero/.ssh/key` (ro), `key.pub -> /home/zero/.ssh/keys/key` (ro), `run_scripts -> /etc/sftp.d/run_scripts` (ro) |
| Tên phân giải từ `one` | `one=172.26.4.2`, `two=172.26.4.3`, `three` không resolve |
| Định dạng cờ | `cdctf{Fl4g!}` (đề ghi mẫu, chưa xác nhận chuỗi thật) |

## Hướng giải (tóm tắt)

Chuỗi "tattle" là một tuyến SFTP: máy `terminal` (identity `zero`) -> máy `one` (user `zero`) -> máy
`two` (user `one`) -> `three` (user `two`) -> `four` (user `three`). Trên mỗi máy có một vòng lặp
chạy với root, mỗi 10 giây làm `find /home -name script -exec {} \;`, tức **file tên chính xác `script`
đặt ở bất kỳ đâu dưới `/home` sẽ được chạy bằng root**. Vì `zero@one` chỉ được SFTP và `/home/zero/scripts`
ghi được, việc upload `script` tương đương với remote code execution bằng root trên `one`, và key
"Universal" cho phép nhân bản payload đi tiếp. Chưa đóng được vòng cuối (nơi cờ nằm) tại thời điểm ghi file này.
