# Tattle Tale - Pwn (495 points)

**Flag:** none yet (challenge still open at the time of writing) · **Points:** 495 · **Author:** reep236
**Files:** no artifact; `exploit.sh` is the payload that really ran on hop `one`

## Challenge

Alice hides a flag; the rumour passes through Bob, Carol, Dave, Eve and finally reaches the narrator.
The task is to "get back to Alice's machine" and take the flag from her. The instance is a web terminal
in a Debian container (`player@terminal`); the card ships no binary and no service address other than
the hostname `one`.

`~/README.md` on the instance is a verse that names the mechanism through backticked keywords:
`script`, `.ssh/key`, `10s`, `/script`, `S-F-T-P`, and the user/host pairs `zero` on `one`, `one` on
`two`, `two` on `three`, `three` on `four`; then "no more" plus "peek at the floor", and the flag is
passed back ("pass it back") until it "sits as bits down at `one`".

## Analysis

`terminal` has two NICs (172.26.2.2, 172.26.3.2) but no `ip`/`ss`/`nc`; reading `/proc/net/route` and
scanning 172.26.2.1-29 and 172.26.3.1-29 through `/dev/tcp` shows **only** `172.26.2.3:22` open.
Internal DNS resolves `one` -> 172.26.2.3, while `two`/`three`/`four` do not resolve from here.
`~/.ssh/key` is an ed25519 key with the comment `Universal`.

`ssh -i ~/.ssh/key zero@one` authenticates but is restricted:

```output
Warning: Permanently added 'one' (ED25519) to the list of known hosts.
This service allows sftp connections only.
```

Over `sftp` the chroot root contains exactly two entries:

```output
sftp> pwd
Remote working directory: /
sftp> ls -la /
drwxr-xr-x    ? 0        0            4096 Oct  4 02:05 .ssh
drwxr-xr-x    ? 1000     100          4096 Oct  4 02:05 scripts
```

`/.ssh/authorized_keys` (91 B) holds **our own public key** (`Universal`), `/.ssh/keys/key` is also 91 B
and readable, while `/.ssh/key` (399 B, root-owned mode 600) is denied to `zero`. `/scripts` is owned by
uid 1000 gid 100: `mkdir probe` plus `put marker.txt` (then removing both) succeeds.

## Mechanism established

Host `one` is an Alpine container built from a linuxserver/openssh-server style image (it has
`/usr/local/bin/create-sftp-user` and `/etc/sftp.d/`). Once a file is planted, a payload calling back to
`terminal` shows it runs **as root every 10 seconds**, and prints the loop responsible:

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

Three implementation details:

1. The filename must be exactly **`script`** (single word, no extension), anywhere under `/home`; the
   runner chmods it itself, so even a 644 upload still executes.
2. `/scripts` inside `zero`'s chroot is `/home/zero/scripts` on the host, so whatever is uploaded gets
   executed as root.
3. Exfiltration needs no socket: a file root writes into `/home/zero/scripts` can be pulled back over
   SFTP. Verified:

```output
$ sftp ... zero@one
sftp> get /scripts/rec3.txt
Fetching /scripts/rec3.txt to rec3.txt
MARK 2026-10-04T02:47:05+00:00 uid=0 host=one
```

From `one`, DNS gives `one=172.26.4.2` and `two=172.26.4.3`, and `three` does not resolve: each hop only
sees its immediate neighbour, matching the `zero/one/two/three` ladder in the verse. `one` ships `ssh`,
`sftp`, `scp`, `nc` and `bash` (no `python3`, no `socat`), and `/home/*/.ssh/key` is the read-only bind of
the "Universal" key, so a root payload on `one` already has what it needs to upload `script` to `two`.

## Approaches tried

1. **Shell on `one`**: `ForceCommand internal-sftp`, every command returns "This service allows sftp
   connections only." Execution must go through SFTP plus `script`.
2. **Guessing the executed filename**: 11 candidates (`script`, `run.sh`, `zero`, `one`, `a`, `a0`,
   `tattle`, `payload`, `gossip`, `zzz`, `floor`) each tried to write a marker into `/scripts`; after 90
   seconds no marker existed. The cause is not the name but the path: root sees `/home/zero/scripts`, and
   `/scripts` **does not exist** in root's namespace (`ls: /scripts: No such file or directory`), so every
   `> /scripts/h_x` redirect failed silently. False negative, corrected later.
3. **Socket as the evidence channel**: the `python3` listener on `terminal` used `settimeout(10)` and
   closed, while payloads were still waiting on `getent`/`sftp` calls that can exceed 10s, so the capture
   was cut mid-section. Also the runner spawns a fresh instance every 10s and they overwrite the same
   output file. Fix: write to tmp then `cp`, guarded by `flock`.
4. **Writing outside `/scripts`**: `put /tmp/cb /cb` -> `dest open "/cb": Permission denied` (chroot root
   belongs to root). Only `/scripts` is writable.

## Remaining work

- Confirm the `one -> two` hop (user `one`, host `two`, key `/home/zero/.ssh/key`) in one clean run; the
  only attempt so far was truncated by issue 3.
- Determine the real chain length and where the flag lives (`four`? a user or directory named `floor`?
  `/flag` on the last hop?).
- `analysis/propagator.sh` contains the full self-replicating walker with the return path, **not yet run**.

## Result

None. The furthest point reached in the recorded run is root code execution on hop `one`.

## Reproduce

```bash
K="$HOME/.ssh/key"
O="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -i $K"
sftp $O zero@one
sftp> put exploit.sh /scripts/script
sftp> chmod 755 /scripts/script
# 10s later
sftp> get /scripts/tattle.out
```
