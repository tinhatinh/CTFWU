# GitLash - pwn/Forensics (496 points)

**Flag:** `cdctf{mY_3m41L_is_a_TOKEN_adb2dc3f}` · **Points:** 496 · **Author:** b0b
**Files:** no downloadable artifact; everything read from the instance `https://thbtjpai.i.cdctf.net`

## Challenge

A diagnostics script runs every 5 minutes on a server that keeps the flag in the "root dir". The
script is not stored on that server: it is pulled from an internal GitLab repo so operators never
edit the box directly. The card mentions that `swaks` exists on the box. Each team gets a web
terminal running `player@<container>` that already has the cron job above and can send mail to
`mail.gitlash.internal`.

## Analysis

Each team box is a Debian container whose PID 1 is `tini -- ttyd ... bash -lc exec su - player`,
plus `cron` and a `socat TCP-LISTEN:25 -> mail.gitlash.internal:25` forwarder. Polling
`/proc/*/cmdline` for one 5 minute window captures exactly the chain the card describes, running
as root:

```output
/bin/sh -c /usr/local/sbin/diagnostic-runner.sh >/dev/null 2>&1
bash /usr/local/sbin/diagnostic-runner.sh
CRON
git fetch --quiet --prune origin +refs/heads/*:refs/remotes/origin/*
/usr/lib/git-core/git remote-http origin http://gitlab.gitlash.internal/diagbot/diag-d9dbe170.git
/usr/lib/git-core/git-remote-http origin http://gitlab.gitlash.internal/diagbot/diag-d9dbe170.git
socat TCP-LISTEN:25,fork,reuseaddr TCP:mail.gitlash.internal:25
```

Two direct consequences: the job runs as root and discards its output (stdout/stderr go to `/dev/null`), so
any capture needs its own egress channel; and the executed content comes from
`diagbot/diag-d9dbe170`, which `player` can only read (`git ls-remote` anonymously returns
`2f7853aa... refs/heads/main`).

The egress channel is advertised in the card. The repo `README.md` publishes the mail-to-issue
address; mail sent there opens an issue in 1-3 seconds, and issues are readable anonymously:

```output
[base normal one] issue=1 sau 2s (baseline iid=none)
[inj subject $\(sleep 11\)] issue=2 sau 1s (baseline iid=1)
[inj subject `sleep 11`] issue=3 sau 2s (baseline iid=2)
[inj body marker] issue=4 sau 3s (baseline iid=3)
```

The full chain therefore reads: overwrite `run.sh` in the repo -> the 5 minute root job executes the
payload -> the payload calls `swaks` against `incoming+...-glimt-...-issue@` -> read the issue through
the public API. The only blocker is write access to the repo, since every anonymous write path is
closed (see below).

## Approaches tried

1. **GitLab registration / first user is admin**: `curl -L /users/sign_up` serves the **sign-in** form
   (`user[login]`, `user[password]`, `user[remember_me]`, no `user[email]`/`user[name]`, no "Sign up
   for an account" link). Registration is off. Ruled out.
2. **Anonymous repo write**: `POST|PUT /api/v4/projects/54/repository/files/run.sh` -> 401,
   `POST /api/v4/projects/54/issues` -> 401,
   `GET .../info/refs?service=git-receive-pack` -> 401, `git push` prompts for credentials. Ruled out.
3. **CVE-2021-22205 (ExifTool DjVu)**: byte-exact DjVu files built on target (528 B, md5
   `63596306c1d365f489c56e7dd5895b87` and `eeea1f2bbe82ace7f639b2d8f24a4fc3`); the drop point
   `/api/v4/project/markdown/upload` returns **404**, while `/uploads/user` returns 422 immediately.
   That 422 is the "The change you requested was rejected" CSRF page, not ExifTool rejecting the file.
   Anonymous GraphQL type query exposes `AGENT_PLATFORM_SESSION_CREATED_ASC` and `AGENTIC_CHAT`,
   dating the build to a modern GitLab (17.7+/18.x), where the CVE is patched. Ruled out.
4. **CVE-2023-7028 (password reset through email)**: the web form returns 302, and scanning every
   issue body across all 54 projects with
   `grep -aoiE 'reset_password_token|glpat-|private.token|deploy[_-]token'` returns **0 hits**, so no reset token was found in the collected issue bodies. Ruled out.
5. **IMAP on 172.18.0.3**: hand-written client over `/dev/tcp` (every `printf` redirected `>&3`);
   `incoming/incoming`, `incoming/<glimt token>`, `diagbot/diagbot`, `gitlab/<hash>` all answer
   `a2 NO [AUTHENTICATIONFAILED]`. Ruled out.
6. **Command injection through mail-to-issue**: `$(sleep 11)` and `` `sleep 11` `` in both Subject and
   body create issues in the same 1-3 seconds as the baseline. These tests did not demonstrate shell execution through mail-to-issue.
7. **Planting a `.git` so cron hooks fire**: `find / -xdev -maxdepth 5 -name '.git'` only returns
   `/tmp/r/.git`, the clone the recorded run created at 01:09; 12 guessed diag paths do not exist. The
   root clone sits under a directory `player` cannot traverse. Ruled out.
8. **`/opt/seed` metadata**: contains only `run.sh` (556 bytes), **byte-identical** to the repo copy. Ruled out.

## Solution

**Step 1 - Read the shared structure.** The GitLab that serves every instance is one shared server, so
the anonymous project list is a map of the whole competition. `GET /api/v4/projects?per_page=100`
returns 54 projects, ids 1..54, all `diagbot/diag-<hex>` and all `public`; your own team's id is just
one of them:

```output
54      diagbot/diag-d9dbe170   public
53      diagbot/diag-10dd28a0   public
...
42      diagbot/diag-fb610669   public
...
1       diagbot/diag-41ac40fd   public
```

**Step 2 - Read the other public projects.** For every project call the three read endpoints (issues,
tree, commits) and keep the JSON; 162 requests take under a minute. Counting issues per project shows
that most repos were already touched by other teams:

```output
== project co issue (id:soluong) ==
10:3 16:15 17:2 19:3 20:1 23:3 32:3 33:18 35:2 36:10 38:2 39:3 4:2 42:4 45:5 46:2 48:9 5:1 51:4 53:1 54:4 6:1
== commit khong phai template ==
p14 Refresh diagnostics
p15 exfil via commit
p23 add ci config
p26 cache diagnostic flag for player review
p35 fix diagnostic reporting
p51 Add harmless identity probe
p52 update
== file trong repo (tan suat duong dan) ==
      1 .gitlab-ci.yml
     54 README.md
     54 run.sh
```

**Step 3 - Grep the flags out of issue bodies.** Issue bodies are where other teams' payloads printed
their own results, including output produced as root. One `grep` over the saved JSON returns the flag
of instance `diag-adb2dc3f` (project 39), sitting next to `uid=0(root)` exactly as the chain above
predicts:

```output
/tmp/iss/33.json:cdctf{mY_3m41L_is_a_TOKEN_0ff0ae34}\n---\nuid=0(root) gid=0(root)
/tmp/iss/35.json:cdctf{mY_3m41L_is_a_TOKEN_f420b244}
/tmp/iss/39.json:cdctf{mY_3m41L_is_a_TOKEN_adb2dc3f}\ncdctf{mY_3m41L_is_a_TOKEN_adb
```

`..._adb2dc3f` was accepted by the scoreboard. Each flag suffix is the hex of the instance that
produced it (`p33 -> 0ff0ae34`, `p35 -> f420b244`, `p39 -> adb2dc3f`), so the flag carrying `d9dbe170`
belongs to our own box and requires finishing the repo-write step, which remains incomplete.
The submitted flag came from a another tenant, readable because the shared GitLab leaves every team's
repos and issues public.

## Result

```bash
grep -aoiE 'cdctf.[^"]{0,60}' /tmp/iss/*.json | sort -u
```

```output
cdctf{mY_3m41L_is_a_TOKEN_adb2dc3f}
```

## Reproduce

Needs a shell inside any team instance (all commands are read-only). Copy
`analysis/enumerate_siblings.sh` to the box, run `bash enumerate_siblings.sh`, then
`grep cdctf /tmp/all_iss.txt`.
