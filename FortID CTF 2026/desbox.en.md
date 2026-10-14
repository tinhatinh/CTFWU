---
title: "DESBox"
category: "Crypto"
tags: ["3des", "ecb", "key-permutation", "chosen-key-oracle", "parity-adjustment"]
solve_date: "2026-10-10"
language: "en"
---

# DESBox

**Flag:** `FortID{C0mPl1m3n75_0n_3XP101t1n6_C0Mp13M3n75!!1}`
**Service:** `ncat --ssl desbox-95f41e75a512.inst4.ctf.fortid.com 1337`. **Handout:** `handout.zip` (2036 B) — `DESBox.py` 4977 B, `secret.py` 56 B (`FLAG = b"<REDACTED>"`, `MASK = bytes.fromhex("<REDACTED>")`). Author: ipaljak.

## Challenge

A fake DOS shell (`Z:\>MOUNT C C:\DESBOX`) offering `DIR`, `TYPE README.TXT`, `KEYB`, `DOOM`, `EXIT`. The directory listing states:

```text
KEYB     COM        3,584  06-24-26  12:00p
README   TXT          640  06-24-26  12:00p
FLAG     BIN           48  06-24-26  12:00p
```

`README.TXT` describes exactly the mechanism to defeat:

```text
DESBox README.TXT
-----------------
KEYB.COM accepts two different 24-byte 3DES keys, written as hex.

Before a key is loaded, the keyboard controller randomly permutes its bytes
and xors the result with a resident secret table.

Commands: DIR, TYPE README.TXT, KEYB, DOOM, EXIT
```

`KEYB` reads two 24-byte hex keys, prints `C:\FLAG.BIN encrypted under Key A:`, then prompts `Debug ciphertext>` and decrypts whatever is entered with Key B. `TYPE FLAG.BIN` answers `Access denied.`

## Analysis

The key derivation and its two helpers in `DESBox.py`:

```python
RNG = secrets.SystemRandom()


def xor(a, b):
    return bytes(x ^ y for x, y in zip(a, b))


def permute(a):
    p = list(range(len(a)))
    RNG.shuffle(p)
    return bytes(a[i] for i in p)


def load_key(user_key):
    key = xor(permute(user_key), MASK)
    return DES3.adjust_key_parity(key)
```

`permute` shuffles byte positions with a fresh permutation drawn from `SystemRandom` on *every call*, and no output of `permute` is ever printed, so the permutation is both unknown and non-reusable. One way to make the permutation irrelevant is to submit a key whose bytes are all identical: for `a = c * 24` we get `permute(a) == a` for every permutation, hence `load_key(c * 24) == DES3.adjust_key_parity(MASK ^ (c * 24))` — a deterministic value, independent of the permutation and of which call it is.

The four guards in `read_keys` compare A and B *within a single KEYB run* only:

```python
if len(key_a) != 24 or len(key_b) != 24:
    print("Bad key size.")
    exit()

if key_a == key_b:
    print("Keyboard layouts must be different.")
    exit()

if effective_bytes(key_a) == effective_bytes(key_b):
    print("Keyboard layouts are equivalent.")
    exit()

if sorted(effective_bytes(key_a)) == sorted(effective_bytes(key_b)):
    print("Keyboard layouts use the same scan code multiset.")
    exit()

if is_effective_complement(key_a, key_b):
    print("Keyboard layouts are too symmetric.")
    exit()
```

where `effective_bytes(k) = [b & 0xFE for b in k]` and `is_effective_complement(a, b)` compares `effective_bytes(a)` with `effective_bytes(bytes(x ^ 0xff for x in b))`. The pair `00*24` / `02*24` clears all four: they differ, they differ under the `0xFE` mask, their multisets differ, and `[0]*24` is not the `0xFF` complement of `[2]*24`.

`MASK` lives in `secret.py` and is imported once when the process starts, so it is unknown to the player but constant for the lifetime of the session. Two `KEYB` runs on the same connection therefore share one `MASK`, and no check compares this run's keys against the previous run's.

Put together, that is two beats on one connection:

- Beat 1: `A = 00*24`, `B = 02*24`. Key A becomes `adjust_key_parity(MASK)`, so the printed line is exactly `C = 3DES_MASK(FLAG.BIN)` — the target ciphertext, under precisely the key the player is not supposed to know.
- Beat 2: `A = 02*24`, `B = 00*24`. `MASK` is unchanged, so this time Key B is `adjust_key_parity(MASK)`, which makes the `Debug ciphertext` oracle decrypt under beat 1's key. Feeding `C` into it returns the plaintext of `FLAG.BIN`.

`FLAG` is 48 bytes (`assert len(FLAG) % BLOCK_SIZE == 0` plus the `FLAG BIN 48` line in `DIR`), and the mode is ECB, so all 6 blocks are handled independently in one `decrypt` call.

## Solution

The local logic check (`local_test.py`) runs first, with a stand-in `MASK` and the service's own functions:

```python
import random
from Crypto.Cipher import DES3

MASK = bytes(range(24))          # stand-in for the resident secret table
FLAG = b"FLAG{test_flag_payload_padding_here_48bytes}!!!!!!!!"[:48]
RNG = random.SystemRandom()


def xor(a, b):
    return bytes(x ^ y for x, y in zip(a, b))


def permute(a):
    p = list(range(len(a)))
    RNG.shuffle(p)
    return bytes(a[i] for i in p)


def load_key(k):
    return DES3.adjust_key_parity(xor(permute(k), MASK))


def eff(k):
    return [b & 0xFE for b in k]


def checks(a, b):
    assert a != b
    assert eff(a) != eff(b)
    assert sorted(eff(a)) != sorted(eff(b))
    assert eff(a) != [x ^ 0xFE for x in eff(b)], "complement"


Z = bytes(24)
O2 = b"\x02" * 24

k_a1 = load_key(Z)          # run 1, KEY A  -> should be MASK
k_b2 = load_key(Z)          # run 2, KEY B  -> should be MASK
print("MASK-equivalent keys stable:", k_a1 == k_b2)

checks(Z, O2)               # run 1: A=00*24, B=02*24
checks(O2, Z)               # run 2: A=02*24, B=00*24

ct = DES3.new(k_a1, DES3.MODE_ECB).encrypt(FLAG)
out = DES3.new(k_b2, DES3.MODE_ECB).decrypt(ct)
print("recovered:", out)
assert out == FLAG
print("attack logic verified")
```

```text
MASK-equivalent keys stable: True
recovered: b'FLAG{test_flag_payload_padding_here_48bytes}!!!!'
attack logic verified
```

The first two lines confirm the decisive property: `load_key(00*24)` returns the same key across two separate calls (so both beats use one key), and `checks` replays the four `read_keys` guards for both orderings of A/B.

The remote script (`exploit.py`) keeps a single TLS connection and runs `KEYB` twice:

```python
import ssl
import socket
import sys

HOST = "desbox-95f41e75a512.inst4.ctf.fortid.com"
PORT = 1337

Z = "00" * 24
TWO = "02" * 24


def recv_until(s, markers, timeout=25):
    s.settimeout(timeout)
    buf = b""
    while True:
        try:
            data = s.recv(4096)
        except socket.timeout:
            return buf.decode(errors="replace")
        if not data:
            return buf.decode(errors="replace")
        buf += data
        text = buf.decode(errors="replace")
        if any(m in text for m in markers):
            return text


def send(s, line):
    s.sendall((line + "\n").encode())


def keyb(s, key_a, key_b):
    send(s, "KEYB")
    recv_until(s, ["KEY A>"])
    send(s, key_a)
    recv_until(s, ["KEY B>"])
    send(s, key_b)
    out = recv_until(s, ["Debug ciphertext>"])
    return out


def debug(s, ct_hex):
    send(s, ct_hex)
    return recv_until(s, ["C:\\>", "Bad ciphertext size", "$ "], timeout=25)


ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

with socket.create_connection((HOST, PORT), timeout=25) as raw:
    s = ctx.wrap_socket(raw, server_hostname=HOST)
    banner = recv_until(s, ["C:\\>"])
    print(banner[-400:])

    print("\n=== RUN 1: A=00*24 (key = MASK), B=02*24 ===")
    out1 = keyb(s, Z, TWO)
    print(out1)
    line = [l.strip() for l in out1.splitlines() if all(c in "0123456789abcdefABCDEF" for c in l.strip()) and len(l.strip()) >= 96]
    if not line:
        print("!! no ciphertext found")
        sys.exit(1)
    C = line[-1]
    print("FLAG ciphertext under MASK:", C)

    d = debug(s, "00" * 8)
    print("run1 debug:", d.strip()[-200:])

    print("\n=== RUN 2: A=02*24, B=00*24 (debug key = MASK) ===")
    out2 = keyb(s, TWO, Z)
    print(out2[-300:])

    out3 = debug(s, C)
    print("run2 debug:", out3)

    hexline = [l.strip() for l in out3.splitlines() if len(l.strip()) >= 96 and all(c in "0123456789abcdefABCDEF" for c in l.strip())]
    if hexline:
        pt = bytes.fromhex(hexline[-1])
        print("\nDECRYPTED FLAG BYTES:", pt)
        print("ASCII:", pt.decode(errors="replace"))
    send(s, "EXIT")
```

Against the live instance, beat 1 prints the 96-hex-character ciphertext of `FLAG.BIN` under the `MASK` key (the saved record keeps only the prefix `a1d6b23a` and the suffix `da687dbc`; the full value changes per instance because `MASK` is per-process, and the script reads it straight from the output, so nothing has to be transcribed). Beat 2 submits exactly that string to the oracle:

```text
run2 debug: Debug output:
466f727449447b43306d506c316d336e37355f306e5f33585031303174316e365f43304d7031334d336e37352121317d

DECRYPTED FLAG BYTES: b'FortID{C0mPl1m3n75_0n_3XP101t1n6_C0Mp13M3n75!!1}'
```

Turning those 96 hex characters (48 bytes) into ASCII is the only local step in the whole solve; the service had already emitted the plaintext.

## Result

```text
FortID{C0mPl1m3n75_0n_3XP101t1n6_C0Mp13M3n75!!1}
```

The flag was read directly from the challenge service. No submission response recorded.

## Reproduce

A live instance is required: `MASK` is a per-process secret, so the pair `00*24`/`02*24` yields a different key on every instance and every service restart. The solve does not run offline against the redacted `secret.py`.

```console
$ pip install pycryptodome
$ python local_test.py
$ python exploit.py
```

Save the `local_test.py` block as `local_test.py` and the `exploit.py` block as `exploit.py` in the same directory. `exploit.py` reads the ciphertext from beat 1 by itself, so nothing needs editing when `MASK` differs.

The same two beats can be typed by hand as long as one connection is kept open:

```console
$ ncat --ssl desbox-95f41e75a512.inst4.ctf.fortid.com 1337
C:\> KEYB
KEY A> 000000000000000000000000000000000000000000000000
KEY B> 020202020202020202020202020202020202020202020202
C:\FLAG.BIN encrypted under Key A:
<96 hex chars>            <- keep this value
Debug ciphertext> 0000000000000000
Debug output:
<...>
C:\> KEYB
KEY A> 020202020202020202020202020202020202020202020202
KEY B> 000000000000000000000000000000000000000000000000
C:\FLAG.BIN encrypted under Key A:
<96 hex chars, different>
Debug ciphertext> <the 96 hex chars kept from run 1>
Debug output:
466f727449447b...
```

The `Debug output:` of beat 2 is the plaintext in hex; `echo <hex> | xxd -r -p` gives the flag.
