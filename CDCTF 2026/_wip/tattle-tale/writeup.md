# Tattle Tale - Pwn (495 điểm)

**Flag:** chưa có (bài đang dở, xem mục "Còn thiếu") · **Điểm:** 495 · **Tác giả:** reep236
**Files:** không có artifact; `exploit.sh` là payload đã chạy thật trên hop `one`

## Đề bài

Alice giấu cờ, tin đồn đi qua Bob, Carol, Dave, Eve rồi tới tai người kể. Nhiệm vụ là "quay lại máy
của Alice" để lấy cờ. Instance là một terminal web trong container Debian (`player@terminal`), đề
không cho binary, không cho địa chỉ service nào ngoài hostname `one`.

`~/README.md` của instance là một bài thơ mô tả cơ chế bằng từ khóa trong cặp backtick: `script`,
`.ssh/key`, `10s`, `/script`, `S-F-T-P`, và cặp user/máy `zero` trên `one`, `one` trên `two`, `two`
trên `three`, `three` trên `four`; xong "no more" thì "peek at the floor", cờ truyền ngược
("pass it back") cho tới khi "sits as bits down at `one`".

## Phân tích ban đầu

`terminal` có hai NIC (172.26.2.2, 172.26.3.2) nhưng không có `ip`/`ss`/`nc`; đọc `/proc/net/route`
và quét 172.26.2.1-29, 172.26.3.1-29 bằng `/dev/tcp` cho thấy **duy nhất** `172.26.2.3:22` mở. DNS
nội bộ phân giải `one` -> 172.26.2.3, còn `two`/`three`/`four` không resolve từ đây. Trong `~/.ssh`
có `key`: ed25519, comment `Universal`.

`ssh -i ~/.ssh/key zero@one` xác thực thành công nhưng bị giới hạn:

```output
Warning: Permanently added 'one' (ED25519) to the list of known hosts.
This service allows sftp connections only.
```

Vào bằng `sftp` thì thấy root của chroot chỉ có hai mục:

```output
sftp> pwd
Remote working directory: /
sftp> ls -la /
drwxr-xr-x    ? 0        0            4096 Oct  4 02:05 .ssh
drwxr-xr-x    ? 1000     100          4096 Oct  4 02:05 scripts
```

`/.ssh/authorized_keys` (91 B) chứa **đúng public key của ta** (`Universal`), `/.ssh/keys/key` cũng 91 B
và đọc được, còn `/.ssh/key` 399 B thuộc root mode 600 nên `zero` không xem được. `/scripts` thuộc
uid 1000 gid 100: upload thử `mkdir probe` + `put marker.txt` rồi xóa, cả hai đều thành công.

## Cơ chế đã dựng được

Host `one` là container Alpine theo mẫu linuxserver/openssh-server (có `/usr/local/bin/create-sftp-user`,
`/etc/sftp.d/`). Sau khi đặt được file, một payload gọi ngược về `terminal` cho thấy nó chạy **bằng root
mỗi 10 giây**, và in ra đúng vòng lặp tạo nên cơ chế:

```output
=== MARK uid=0 host=one date=2026-10-04T02:39:03+00:00
=== run_scripts
#!/usr/bin/env bash

Loop() {
    while [ true ];
    do
        find /home -name script -exec chmod +x {} \;
        find /home -name script -exec {} \;
        sleep 10s
    done
}

Loop &
=== ps
    1 root      0:00 sshd: /usr/sbin/sshd -D -e [listener] 0 of 10-100 startups
   39 root      0:00 bash /etc/sftp.d/run_scripts
  894 root      0:00 find /home -name script -exec {} \;
  895 root      0:00 {script} /bin/bash /home/zero/scripts/script
```

Ba chi tiết cần lưu ý:

1. Tên file phải là **`script`** (đúng một từ, không phần mở rộng), đặt đâu cũng được dưới `/home`;
   runner tự `chmod +x` nên kể cả file upload mang mode 644 vẫn được chạy.
2. `/scripts` trong chroot của `zero` chính là `/home/zero/scripts` trên host, nên thứ ta upload sẽ
   được root thực thi.
3. Kênh kéo dữ liệu về không cần socket: root ghi file vào `/home/zero/scripts` thì `player` `get`
   được bằng SFTP. Kiểm chứng:

```output
$ sftp ... zero@one
sftp> get /scripts/rec3.txt
Fetching /scripts/rec3.txt to rec3.txt
MARK 2026-10-04T02:47:05+00:00 uid=0 host=one
```

Từ `one`, DNS cho `one=172.26.4.2`, `two=172.26.4.3`, `three` không resolve: mỗi hop chỉ nhìn thấy
hàng xóm kế tiếp, đúng như chuỗi `zero/one/two/three` trong thơ. Trên `one` có `ssh`, `sftp`, `scp`,
`nc`, `bash` (không có `python3`, không có `socat`), và `/home/*/.ssh/key` là bản read-only bind của
key "Universal" - nghĩa là payload chạy root ở `one` có key cần thiết để upload `script` sang `two`.

## Các hướng đã loại

1. **Vào `one` bằng shell**: `ForceCommand internal-sftp`, mọi lệnh trả "This service allows sftp
   connections only." Loại; mọi thực thi phải đi qua kênh SFTP + `script`.
2. **Đoán tên file thực thi**: 11 tên ứng viên (`script`, `run.sh`, `zero`, `one`, `a`, `a0`, `tattle`,
   `payload`, `gossip`, `zzz`, `floor`) cùng ghi dấu vết vào `/scripts`; sau 90s **không** có dấu vết nào.
   Lý do không phải tên file mà là đường dẫn: root nhìn `/home/zero/scripts`, còn `/scripts` theo góc
   nhìn của root **không tồn tại** (`ls: /scripts: No such file or directory`), nên mọi redirect kiểu
   `> /scripts/h_x` fail im lặng. Đây là âm tính giả, đã sửa ở bước sau.
3. **Kênh socket làm bằng chứng**: listener `python3` trên `terminal` đặt `settimeout(10)` rồi đóng,
   trong khi payload vẫn đang chờ `getent`/`sftp` (mỗi lần gọi có thể chậm hơn 10s), nên dữ liệu bị cắt
   giữa output. Đã thay bằng kênh file (mục cơ chế). Payload còn một lỗi nhỏ: runner khởi
   động instance mới mỗi 10s và các instance **ghi đè cùng một file**, nên đọc luôn thấy nội dung dở
   dang; phải ghi ra tmp rồi `cp`, kèm khóa `flock`.
4. **`put` file vào gốc chroot**: `put /tmp/cb /cb` -> `dest open "/cb": Permission denied` (gốc chroot
   thuộc root). Chỉ `/scripts` mới ghi được.

## Còn thiếu

- Chưa xác nhận vòng `one -> two` (user `one`, host `two`, key `/home/zero/.ssh/key`) trong một lần chạy
  đầy đủ; lần thử duy nhất bị cắt bởi lỗi timeout ở mục 3.
- Chưa biết độ dài thật của chuỗi và chỗ cờ nằm (`four`? một user/máy tên `floor`? `/flag` trên hop cuối?).
- Chuỗi payload hoàn chỉnh (tự nhân bản xuống `four`, rồi kéo cờ ngược về `/home/zero/scripts` trên `one`)
  đã viết ở `analysis/propagator.sh` nhưng **chưa chạy**.

## Flag

Chưa có. Lần chạy xa nhất trong phiên này là root code execution trên hop `one`.

## Reproduce

```bash
# tu terminal cua instance
K="$HOME/.ssh/key"
O="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -i $K"
sftp $O zero@one
sftp> put exploit.sh /scripts/script
sftp> chmod 755 /scripts/script
# 10s sau
sftp> get /scripts/tattle.out
```
