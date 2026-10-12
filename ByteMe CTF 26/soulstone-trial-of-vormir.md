---
title: "SoulStone (The Trial of Vormir)"
category: "Reverse"
tags: ["chacha20", "hmac-sha256", "brute-force", "radare2", "ghidra"]
solve_date: "2026-10-09"
language: "vi"
---

# SoulStone (The Trial of Vormir)

**Flag:** `OWASP{a_s0ul_f0r_a_s0ul_v0rm1r_cl1ff_7c8d9e2a}`
**Artifact:** `soulstone` (18568 B, ELF 64-bit, PIE, stripped).

## Đề bài

Binary stripped (Hard, 300 điểm, 13 lời giải). Chương trình in dữ liệu gây nhiễung `THE ALTAR OF VORMIR`, nhắc người chơi nộp một lễ vật theo định dạng ghi rõ trong chuỗi của binary, rồi in cờ bằng `[+] Flag: %s\n` khi các điều kiện kiểm tra đều thoả. `strings` trả 0 lần xuất hiện của `OWASP` trong 18568 byte, nên không đọc được trực tiếp bất kỳ phần nào của cờ.

## Phân tích

Công cụ dùng trên host: Ghidra 12.1.4 chế độ headless để phân rã toàn bộ, radare2 6.2.2 để đọc từng khối lệnh và định vị hằng số. `file soulstone` báo `stripped`, nên mọi tên hàm dưới đây là địa chỉ thô.

Bản đồ dữ liệu trong `.rodata`, đọc bằng `r2 -q -c "iz" soulstone`:

```text
7   0x000032f0 0x000032f0 64  66   .rodata ascii Enter Sacred Offering (format: SOUL{<SACRIFICE>:<RESONANCE>}):\n>
11  0x00003410 0x00003410 91  92   .rodata ascii [-] The Stonekeeper shakes his head: "The resonance key must be a 6-character astral seal."
20  0x0000367f 0x0000367f 5   6    .rodata ascii SOUL{
22  0x0000368e 0x0000368e 22  23   .rodata ascii VORMIR_SOUL_TITHE_2026
23  0x000036a5 0x000036a5 13  14   .rodata ascii [+] Flag: %s\n
```

Định dạng đầu vào lấy nguyên văn từ binary là `SOUL{<SACRIFICE>:<RESONANCE>}`; ngoài ra còn chuỗi `%s:%s:%s` tại `0x3685`, dùng ở bước dựng preimage. `main@0x11a0` kiểm tra `strncmp(input, "SOUL{", 5)` (`0x12cb`) và byte `}` ở cuối, rồi tách phần trước/sau dấu `:` bằng `strchr` (`0x1345`).

**Kiểm tra tên** (`0x17b0`, gọi tại `0x1360`): `strlen` phải bằng 6, sau đó là vòng XOR với hai dữ liệu gây nhiễung liên tiếp trong `.rodata`:

```text
0x000017c7      cmp rdx, 6
0x000017cb      jne 0x17f8
0x000017cf      lea rsi, [0x00003714]
0x000017d6      lea rcx, [0x0000370e]
0x000017dd      movzx edx, byte [rbx + rax]
0x000017e1      xor dl, byte [rcx + rax]
0x000017e4      cmp byte [rsi + rax], dl
```

Điều kiện là `name[i] ^ key[i] == tgt[i]`:

```text
- offset -   E F 1011 1213 1415 1617 1819 1A1B 1C1D  EF0123456789ABCD
0x0000370e  5a6b 7c8d 9eaf 1d2a 31c2 ccee            Zk|....*1...
```

`key = 5a 6b 7c 8d 9e af`, `tgt = 1d 2a 31 c2 cc ee`, nên `name = GAMORA`.

**Kiểm tra resonance** (`0x1750`, gọi tại `0x13d9` với `rdi` = tên và `esi` = V là giá trị 24 bit đọc từ 6 ký tự hex; `0x1375` bắt `strlen == 6`):

```text
0x00001750      endbr64
0x00001754      movzx edx, byte [rdi]
0x00001757      mov eax, 0x5a17f00d
0x0000175c      test dl, dl
0x0000175e      je 0x177a
0x00001760      mov ecx, eax
0x00001762      add rdi, 1
0x00001766      shl ecx, 5
0x00001769      sub ecx, eax
0x0000176b      lea eax, [rcx + rdx]
0x0000176e      movzx edx, byte [rdi]
0x00001771      xor eax, 0x9e3779b9
0x00001776      test dl, dl
0x00001778      jne 0x1760
0x0000177a      xor eax, esi
0x0000177c      mov ecx, 4
0x00001781      mov edx, eax
0x00001783      shr edx, 0xf
0x00001786      xor edx, eax
0x00001788      imul eax, edx, 0x85ebca6b
0x0000178e      mov edx, eax
0x00001790      shr edx, 0xd
0x00001793      xor edx, eax
0x00001795      imul edx, edx, 0xc2b2ae35
0x0000179b      mov eax, edx
0x0000179d      shr eax, 0x10
```

Tức là `h = 0x5A17F00D`, mỗi ký tự `c` của tên: `h = ((h*31 + c) ^ 0x9E3779B9)`; sau đó `t = h ^ V` và lặp 4 lần `t = fmix(t) + V`; kết quả phải bằng `0xE7F841B8` (`cmp eax, 0xe7f841b8` tại `0x13de`).

`fmix` ở đây là `fmix32` của murmur3 nhưng dịch đầu tiên là `shr edx, 0xf` (>>15) thay vì >>16. Hai bước sau vẫn là >>13 và >>16 với cùng hằng số `0x85ebca6b`, `0xc2b2ae35`. Đây chính là điểm làm một dữ liệu gây nhiễun murmur3 chép nguyên văn tìm ra 0 nghiệm trên toàn không gian 2^24.

**Lịch sinh khóa và lớp xác thực** (`0x1f90` = SHA-256, `0x2010` = HMAC-SHA-256, `0x2220` = khởi tạo trạng thái ChaCha20, `0x2260` = XOR keystream):

```text
0x00001410      lea rax, str.VORMIR_SOUL_TITHE_2026 ; 0x368e ; "VORMIR_SOUL_TITHE_2026"
0x00001437      lea r8, str._s:_s:_s                ; 0x3685 ; "%s:%s:%s"
```

`__snprintf_chk` dựng `"<NAME>:<RESONANCE HOA>:VORMIR_SOUL_TITHE_2026"` (0x13f3..0x140e chuyển a-f thành A-F). Bốn chuỗi phân cách miền được ghép từ immediate nên `strings` không thấy:

```text
0x000014a7      movabs rax, 0x5245485049433a3a                         ; '::CIPHER'
0x000014b1      mov dword [rsp + 0x168], 0x59454b5f                    ; '_KEY'
0x000014bc      mov qword [rsp + 0x160], rax
0x000014c4      movaps xmmword [rsp + 0x140], xmm0
0x000014cc      movaps xmmword [rsp + 0x150], xmm1
0x000014d4      call 0x1f90
0x000014df      mov esi, 0x27                                          ; '\''
0x000014e4      mov dword [rsp + 0x160], 0x4f4e3a3a                    ; '::NO'
0x000014ef      mov dword [rsp + 0x163], 0x45434e4f                    ; 'ONCE'
0x000014fa      call 0x1f90
```

Ba lần gọi `0x1f90` tiếp theo có độ dài 0x2c = 44, 0x27 = 39, 0x2a = 42, tức `PRK (32) + "::CIPHER_KEY" (12)`, `PRK + "::NONCE" (7)`, `PRK + "::HMAC_KEY" (10)`. Gate xác thực và giải mã:

```text
0x00001536      mov ecx, 0x2e                                          ; '.'
0x0000153b      mov rdx, r13
0x0000153e      mov esi, 0x20                                          ; "@"
0x00001546      call 0x2010
0x0000154b      mov edx, 0x20                                          ; "@"
0x00001553      lea rsi, [0x000036c0]
0x0000155a      call sym.imp.memcmp
```

HMAC-SHA-256 tính trên chính 46 byte mật mã (`0x2e` = 46) tại `0x36e0`, so với 32 byte lưu tại `0x36c0`:

```text
- offset -  C0C1 C2C3 C4C5 C6C7 C8C9 CACB CCCD CECF  0123456789ABCDEF
0x000036c0  c2a2 e390 6273 c4c7 bf42 3d2a e244 900f  ....bs...B=*.D..
0x000036d0  e045 4741 7976 88c3 ede6 e48d 591a b4da  .EGAyv......Y...
- offset -  E0E1 E2E3 E4E5 E6E7 E8E9 EAEB ECED EEEF  0123456789ABCDEF
0x000036e0  3374 3e56 3b3c 9442 2705 01f8 67eb e7fc  3t>V;<.B'...g...
0x000036f0  1915 ef24 f5cb 436f 3f98 ba72 62bc 0574  ...$..Co?..rb..t
0x00003700  a3fe a498 3896 2284 ca92 69b2 5796       ....8."...i.W.
```

`0x2220` nạp đúng bố cục ChaCha20 chuẩn: words 0-3 là sigma, words 4-11 là khóa, word 12 là counter (`mov ecx, 1` tại `0x1576`), words 13-15 là 12 byte nonce lấy từ đầu ra SHA-256:

```text
0x00002224      movdqa xmm0, xmmword [0x00003870]                      ; [0x3870:16]=-1 ; "expand 32-byte k\x01\x1b\x03;\x84"
0x0000222e      movups xmmword [rdi], xmm0
0x00002238      mov r8d, dword [rsi + rax]
0x0000223c      mov dword [rdi + rax + 0x10], r8d
0x00002241      add rax, 4
0x00002245      cmp rax, 0x20                                          ; "@"
0x00002249      jne 0x2238
0x0000224b      mov dword [rdi + 0x30], ecx
0x0000224e      mov eax, dword [rdx]
0x00002250      mov dword [rdi + 0x34], eax
0x00002253      mov eax, dword [rdx + 4]
0x00002256      mov dword [rdi + 0x38], eax
0x00002259      mov eax, dword [rdx + 8]
0x0000225c      mov dword [rdi + 0x3c], eax
```

## Lời giải

V chỉ 24 bit nên vét cạn trực tiếp toàn bộ `2^24` giá trị là cách gọn nhất; vector hóa bằng numpy. Với tên `GAMORA`, `h = 0x58f35c68`, và nghiệm duy nhất là `V = 0xa73d91`, tức resonance `A73D91`.

Toàn bộ chuỗi khóa, gate HMAC và phép giải mã ChaCha20 chạy lại từ binary trong một script duy nhất (`solve.py`, cần `numpy`):

```python
import hashlib, hmac, struct
import numpy as np

BIN = "soulstone"
M = 0xFFFFFFFF

data = open(BIN, "rb").read()
NAME_KEY = data[0x370e:0x370e + 6]        # 5a6b7c8d9eaf
NAME_TGT = data[0x3714:0x3714 + 6]        # 1d2a31c2ccee
CIPHER   = data[0x36e0:0x36e0 + 0x2e]     # 46 bytes
TAG      = data[0x36c0:0x36c0 + 0x20]     # stored HMAC-SHA256

name = bytes(a ^ b for a, b in zip(NAME_KEY, NAME_TGT)).decode()

h = 0x5A17F00D
for c in name.encode():
    h = ((h * 31 + c) & M) ^ 0x9E3779B9
V = np.arange(1 << 24, dtype=np.uint32)
t = (np.uint32(h) ^ V).astype(np.uint32)
for _ in range(4):
    x = t.copy()
    x = (x ^ np.right_shift(x, np.uint32(15))).astype(np.uint32)   # shr edx, 0xf
    x = (x * np.uint32(0x85EBCA6B)).astype(np.uint32)
    x = (x ^ np.right_shift(x, np.uint32(13))).astype(np.uint32)
    x = (x * np.uint32(0xC2B2AE35)).astype(np.uint32)
    x = (x ^ np.right_shift(x, np.uint32(16))).astype(np.uint32)
    t = (x + V).astype(np.uint32)
hit = np.flatnonzero(t == np.uint32(0xE7F841B8))
resonance = int(V[hit[0]])
print("name     :", name, " candidates:", [hex(int(V[i])) for i in hit])

preimage = ("%s:%s:VORMIR_SOUL_TITHE_2026" % (name, format(resonance, "06X"))).encode()
prk = hashlib.sha256(preimage).digest()
cipher_key = hashlib.sha256(prk + b"::CIPHER_KEY").digest()
nonce = hashlib.sha256(prk + b"::NONCE").digest()[:12]
hmac_key = hashlib.sha256(prk + b"::HMAC_KEY").digest()

def rotl(x, n): return ((x << n) | (x >> (32 - n))) & M
def quarter(w, a, b, c, d):
    w[a] = (w[a] + w[b]) & M; w[d] = rotl(w[d] ^ w[a], 16)
    w[c] = (w[c] + w[d]) & M; w[b] = rotl(w[b] ^ w[c], 12)
    w[a] = (w[a] + w[b]) & M; w[d] = rotl(w[d] ^ w[a], 8)
    w[c] = (w[c] + w[d]) & M; w[b] = rotl(w[b] ^ w[c], 7)
def block(key, counter, nonce):
    v = list(struct.unpack("<16I", b"expand 32-byte k" + key + struct.pack("<I", counter) + nonce))
    w = v[:]
    for _ in range(10):
        for i in range(4): quarter(w, i, i + 4, i + 8, i + 12)
        quarter(w, 0, 5, 10, 15); quarter(w, 1, 6, 11, 12)
        quarter(w, 2, 7, 8, 13);  quarter(w, 3, 4, 9, 14)
    return struct.pack("<16I", *[(a + b) & M for a, b in zip(w, v)])

print("HMAC ok  :", hmac.new(hmac_key, CIPHER, hashlib.sha256).digest() == TAG,
      " stored:", TAG.hex())
ks, ctr = b"", 1
while len(ks) < len(CIPHER):
    ks += block(cipher_key, ctr, nonce); ctr += 1
flag = bytes(a ^ b for a, b in zip(CIPHER, ks[:len(CIPHER)]))
print("offering :", "SOUL" + "{" + name + ":" + format(resonance, "06X") + "}")
print("flag     :", flag.decode())
```

```text
name     : GAMORA  candidates: ['0xa73d91']
HMAC ok  : True  stored: c2a2e3906273c4c7bf423d2ae244900fe0454741797688c3ede6e48d591ab4da
offering : SOUL{GAMORA:A73D91}
flag     : OWASP{a_s0ul_f0r_a_s0ul_v0rm1r_cl1ff_7c8d9e2a}
```

Bằng chứng mạnh ở đây không phải dòng cờ mà là `HMAC ok : True`: HMAC được tính bằng đúng công thức chương trình dùng (khóa từ `PRK || "::HMAC_KEY"`, tin nhắn là 46 byte mật mã tại `0x36e0`), nên preimage `GAMORA:A73D91:VORMIR_SOUL_TITHE_2026` là preimage mà binary chấp nhận; chuỗi 46 byte giải mã được là nội dung mà `[+] Flag: %s\n` sẽ in ra khi nạp `SOUL{GAMORA:A73D91}`.

## Kết quả

```text
OWASP{a_s0ul_f0r_a_s0ul_v0rm1r_cl1ff_7c8d9e2a}
```

Cờ được khôi phục bằng phân tích tĩnh (Ghidra headless + radare2) và kiểm chứng cục bộ bằng gate HMAC-SHA-256 trên chính dữ liệu của binary; binary không được chạy trên host Windows. Chưa lưu phản hồi submission.

## Tái hiện

Cần Python 3 với `numpy`, `hashlib`/`hmac`/`struct` (standard library), radare2 6.2.2; Ghidra 12.1.4 headless là tùy chọn vì toàn bộ hằng số ở trên đọc được bằng radare2.

Đặt `soulstone` cạnh script, lưu khối Python ở mục Lời giải thành `solve.py` rồi chạy:

```console
$ python solve.py
```

Đọc tĩnh các địa chỉ đã dùng:

```console
$ file soulstone
$ r2 -q -c "iz" soulstone | grep -E "SOUL|VORMIR|Flag"
$ r2 -q -c "px 12 @ 0x370e; px 32 @ 0x36c0; px 46 @ 0x36e0" soulstone
$ r2 -q -e bin.relocs.apply=true -c "e asm.bytes=false; e asm.lines=false; \
    e asm.comment=false; pd 26 @ 0x1750" soulstone
$ r2 -q -e bin.relocs.apply=true -c "e asm.bytes=false; e asm.lines=false; \
    e asm.comment=false; pd 16 @ 0x17b0" soulstone
```

Kiểm tra nhanh là binary không chứa cờ dưới dạng chuỗi:

```console
$ python -c "d=open('soulstone','rb').read(); print(len(d), d.count(b'OWASP'))"
18568 0
```
