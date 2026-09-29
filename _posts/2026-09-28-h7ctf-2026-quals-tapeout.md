---
title: "Tapeout — Misc (Hard)"
date: 2026-09-28 16:53:17 +0700
lastmod_at: 2026-09-28 16:53:17 +0700
categories: [Misc]
tags: [h7ctf-quals, Misc]
image:
  path: /CTFWU/H7CTF%202026%20Quals/tapeout/files/de.png
---
**Flag:** `H7CTF{afd4beac-e86e-409b-907d-b519bb748599}`

## Đề bài

FoundryProof xác nhận thiết kế tổ hợp tương đương với bản vàng rồi mới "đóng dấu" tape-out,
sau đó chọc probe một lần lên chip đã sản xuất để bắt kẻ gian. Luật thắng ghi rõ trong `SPEC.md`:

```
audit vector:   A_AUDIT = 0xDEADBEEF
sabotage value: MAGIC   = 0xB105F00D
Win = your netlist is certified AND T(A_AUDIT) == MAGIC
```

Phải có một netlist vừa được chứng minh là tương đương, vừa cho ra giá trị phá hoại ở điểm audit.

## Phân tích ban đầu

Ba file cho trước là `hdl.py` (parser + simulator + bộ sinh công thức z3), `verifier.py`
(nguyên văn certifier) và `reference.hdl`:

```
input a
k1 = const 0x9E3779B9
k2 = const 0x1337C0DE
t1 = xor a k1
hi = shr a 16
t2 = add t1 hi
y  = xor t2 k2
```

Đề bảo "Read the certifier closely", và cái bẫy nằm đúng một dòng:

```python
SAMPLE_BITS = 16
sample = z3.BitVec("sample", SAMPLE_BITS)
a = z3.ZeroExt(WIDTH - SAMPLE_BITS, sample)      # 16 bit cao bị ép bằng 0
solver.add(build(ref, a) != build(sub, a))
return solver.check() == z3.unsat
```

`certify()` không chứng minh tương đương trên toàn `2^32` input. Nó chứng minh trên tập
`{ZeroExt(16, s) : s in 2^16}` = chính xác các giá trị `a < 0x10000`.
Còn audit lại chạy ở `0xDEADBEEF`, tức ngoài miền được lượng hoá. "probes the finished part
once" là chi tiết then chốt: chỉ một điểm kiểm tra, và điểm đó nằm ngoài vùng chứng minh.

Vậy không cần đánh bại bài toán equivalence checking - chỉ cần lợi dụng phạm vi của nó.

## Chuỗi khai thác

**Bước 1 - Dựng chỉ báo "outside the proof".** `eq` trong Tiny-HDL trả `0xFFFFFFFF` khi bằng,
`0x00000000` khi khác, nên:

```
hi    = shr a 16      # 0 với mọi input trong miền chứng minh
islow = eq hi zero    # 0xFFFFFFFF trong miền, 0 ở ngoài miền
```

**Bước 2 - Chọn giữa hai hành vi bằng `mux`.** `mux s x y = (x & s) | (y & ~s)` là select theo
từng bit, nên với mask toàn-1/toàn-0 nó hoạt động như một multiplexer thật:

```
yref  = xor t2 k2                     # đúng transform của reference
y     = mux islow yref magic          # magic = const 0xB105F00D
```

Toàn bộ netlist:

```
input a
k1 = const 0x9E3779B9
k2 = const 0x1337C0DE
magic = const 0xB105F00D
zero = const 0
t1 = xor a k1
hi = shr a 16
t2 = add t1 hi
yref = xor t2 k2
islow = eq hi zero
y = mux islow yref magic
output y
```

Với `a < 2^16`: `islow = 0xFFFFFFFF` -> `y = yref` bit-for-bit -> z3 tìm không ra counterexample -> CERTIFIED.
Với `a >= 2^16`: `islow = 0` -> `y = MAGIC`.

**Bước 3 - Kiểm chứng cục bộ trước khi nộp.** Máy này không có z3, nên `hdl.py` không import được;
mình viết lại đúng simulator Tiny-HDL trong exploit và test hai chiều:

```
[+] matches the reference across the sampled domain a<2^16
[+] differs outside it, as intended: T(0x00010000)=0xb105f00d vs ref 0x8d01b964
[+] T(0xDEADBEEF) = 0xb105f00d (want 0xb105f00d)
```

Bước "phải KHÁC ở ngoài miền" quan trọng ngang bước "phải GIỐNG trong miền": nó là phát biểu
chính xác của điều kiện thắng.

**Bước 4 - Nộp qua socket và đọc kết quả.**

```
CERTIFIED: equivalent to the golden reference.
audit: T(0xDEADBEEF) = 0xB105F00D
sign-off compromised -- a certified design carries a trojan.
H7CTF{afd4beac-e86e-409b-907d-b519bb748599}
```

## Flag
```bash
python exploit.py pwn.h7tex.com 40634
```

Exploit được verify đúng một lần ở bước 4; ngay sau đó service ngừng phản hồi (0
byte qua 3 lần thử) nên không chạy lại để đối chiếu được. Transcript ở trên là output
thật của lần chạy thành công duy nhất đó.
