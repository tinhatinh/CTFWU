---
title: "DESBox"
category: "Crypto"
tags: ["3des", "ecb", "key-permutation", "chosen-key-oracle", "parity-adjustment"]
solve_date: "2026-10-10"
language: "vi"
---

# DESBox

**Flag:** `FortID{C0mPl1m3n75_0n_3XP101t1n6_C0Mp13M3n75!!1}`
**Service:** `ncat --ssl desbox-95f41e75a512.inst4.ctf.fortid.com 1337`. **Handout:** `handout.zip` (2036 B) — `DESBox.py` 4977 B, `secret.py` 56 B (`FLAG = b"<REDACTED>"`, `MASK = bytes.fromhex("<REDACTED>")`). Tác giả: ipaljak.

## Đề bài

Một shell giả kiểu DOS (`Z:\>MOUNT C C:\DESBOX`) với các lệnh `DIR`, `TYPE README.TXT`, `KEYB`, `DOOM`, `EXIT`. Bảng thư mục liệt kê:

```text
KEYB     COM        3,584  06-24-26  12:00p
README   TXT          640  06-24-26  12:00p
FLAG     BIN           48  06-24-26  12:00p
```

`README.TXT` mô tả đúng cơ chế cần đánh bại:

```text
DESBox README.TXT
-----------------
KEYB.COM accepts two different 24-byte 3DES keys, written as hex.

Before a key is loaded, the keyboard controller randomly permutes its bytes
and xors the result with a resident secret table.

Commands: DIR, TYPE README.TXT, KEYB, DOOM, EXIT
```

`KEYB` nhận hai khoá 24 byte dạng hex, in ra `C:\FLAG.BIN encrypted under Key A:` rồi hỏi `Debug ciphertext>` và giải mã giá trị nộp vào bằng Key B. `TYPE FLAG.BIN` trả `Access denied.`

## Phân tích

Đường sinh khoá và hai hàm liên quan trong `DESBox.py`:

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

`permute` xáo vị trí byte bằng một hoán vị mới rút từ `SystemRandom` ở *mỗi lần gọi*, và không có đầu ra nào của `permute` được in ra, nên hoán vị vừa không biết vừa không tái sử dụng. Một cách làm hoán vị không ảnh hưởng đến khoá là nộp một khoá mà mọi byte đều giống nhau: với `a = c * 24` thì `permute(a) == a` với mọi hoán vị, do đó `load_key(c * 24) == DES3.adjust_key_parity(MASK ^ (c * 24))` — một giá trị tất định, không phụ thuộc hoán vị và cũng không phụ thuộc lần gọi.

Bốn ràng buộc của `read_keys` chỉ so A và B *trong cùng một lần chạy KEYB*:

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

với `effective_bytes(k) = [b & 0xFE for b in k]` và `is_effective_complement(a, b)` so `effective_bytes(a)` với `effective_bytes(bytes(x ^ 0xff for x in b))`. Cặp `00*24` / `02*24` vượt cả bốn: khác nhau, khác theo mask `0xFE`, khác multiset, và `[0]*24` không bằng phần bù `0xFF` của `[2]*24`.

`MASK` nằm trong `secret.py` và được import một lần khi process khởi động, nên người chơi không biết giá trị của nó, nhưng nó cố định trong suốt phiên. Hai lần chạy `KEYB` trên cùng một kết nối vì thế dùng chung `MASK`, mà không có kiểm tra nào so khoá của lần này với khoá của lần trước.

Ghép lại thành hai nhịp trên cùng một kết nối:

- Nhịp 1: `A = 00*24`, `B = 02*24`. Key A trở thành `adjust_key_parity(MASK)`, nên dòng in ra chính là `C = 3DES_MASK(FLAG.BIN)` — bản mã cần tìm, dưới đúng khoá mà người chơi không được phép biết.
- Nhịp 2: `A = 02*24`, `B = 00*24`. Vẫn `MASK`, nên lần này Key B mới là `adjust_key_parity(MASK)`, tức oracle `Debug ciphertext` giải mã theo đúng khoá của nhịp 1. Nộp `C` vào đó sẽ nhận lại plaintext của `FLAG.BIN`.

`FLAG` dài 48 byte (`assert len(FLAG) % BLOCK_SIZE == 0` và cột `FLAG BIN 48` trong `DIR`), mã hoá ECB nên toàn bộ 6 block được xử lý độc lập trong một lần gọi `decrypt`.

## Lời giải

Kịch bản kiểm tra logic cục bộ trước (`local_test.py`), dùng một `MASK` giả và chính xác các hàm của dịch vụ:

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

Hai dòng đầu xác nhận điều kiện quyết định: `load_key(00*24)` trả cùng một khoá ở hai lần gọi khác nhau (tức hai nhịp dùng chung một khoá), và `checks` mô phỏng lại đúng bốn guard của `read_keys` cho cả hai thứ tự A/B.

Kịch bản remote (`exploit.py`) đi một kết nối TLS duy nhất và hai lần `KEYB`:

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

Chạy trên instance đang sống, nhịp 1 in ra bản mã 96 ký tự hex của `FLAG.BIN` dưới khoá `MASK` (bản ghi chỉ giữ phần đầu `a1d6b23a` và phần cuối `da687dbc`; giá trị đầy đủ thay đổi theo instance vì `MASK` per-process, và script đọc nó trực tiếp từ output nên không cần chép tay). Nhịp 2 nộp chính xác xâu đó vào oracle:

```text
run2 debug: Debug output:
466f727449447b43306d506c316d336e37355f306e5f33585031303174316e365f43304d7031334d336e37352121317d

DECRYPTED FLAG BYTES: b'FortID{C0mPl1m3n75_0n_3XP101t1n6_C0Mp13M3n75!!1}'
```

Dịch hex 96 ký tự (48 byte) ra ASCII là bước cục bộ duy nhất trong toàn bộ lời giải; plaintext đã được dịch vụ in ra ở dạng rõ.

## Kết quả

```text
FortID{C0mPl1m3n75_0n_3XP101t1n6_C0Mp13M3n75!!1}
```

Cờ đọc trực tiếp từ dịch vụ đề bài. Chưa lưu phản hồi submission.

## Tái hiện

Cần instance đang sống: `MASK` là secret per-process, nên cặp khoá `00*24`/`02*24` cho ra một khoá khác nhau ở mỗi instance và mỗi lần khởi động lại service. Lời giải không chạy offline với `secret.py` đã redact.

```console
$ pip install pycryptodome
$ python local_test.py
$ python exploit.py
```

Lưu block `local_test.py` thành `local_test.py` và block `exploit.py` thành `exploit.py` cùng thư mục. `exploit.py` tự đọc bản mã từ nhịp 1, vì vậy không phải sửa gì khi `MASK` khác.

Có thể làm thủ công nếu muốn tự tay gõ lệnh, chỉ cần giữ đúng một kết nối:

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

Bản `Debug output:` của nhịp 2 là hex của plaintext; `echo <hex> | xxd -r -p` cho ra cờ.
