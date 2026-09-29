---
title: "Shared Blood — Crypto (Medium)"
date: 2026-09-28 16:53:17 +0700
lastmod_at: 2026-09-28 16:53:17 +0700
categories: [Crypto]
tags: [h7ctf-quals, Crypto]
image:
  path: /CTFWU/H7CTF%202026%20Quals/shared-blood/files/de.png
---
{% raw %}
**Flag:** `H7CTF{a727587f-67d5-4246-b7c3-e57798659fac}`
**Instance:** `https://web-bd09e5c5af420bbc.web.h7tex.com`

## Đề bài

Cam VoltEye xuất xưởng cả một fleet bằng nhau, "cùng một dây chuyền, cùng một sự vội". Trong đám đó có một thiết bị mà ta muốn mở console. Đề cho đúng ba endpoint và không cho code nào cả.

## Phân tích ban đầu

```
GET /          -> "Device fleet console. Admin bootstrap required."
                  GET /fleet · GET /captured · POST /admin {"token":"..."}
GET /fleet     -> {"e": 65537, "devices": [{"serial","n"} x30]}    modulus 1023/1024 bit
GET /captured  -> {"note": "RSA/PKCS1v1.5, encrypted to the device cert",
                   "serial": "VE-C1E90650", "e": 65537, "ciphertext": <128 byte hex>}
```

Không có decrypt oracle: chỉ một ciphertext duy nhất, nên con đường duy nhất tới plaintext là phân tích hoàn toàn modulus của device đích. Một số nguyên 1024 bit thì không tự phân tích được, nhưng "family resemblance runs deeper than you'd think" chỉ thẳng vào lỗi kinh điển của fleet keygen: hai thiết bị cùng rút phải một số nguyên tố.

## Chuỗi khai thác

### Bước 1: pairwise GCD trên cả fleet

```python
hits = [(a, b, math.gcd(an, bn))
        for i,(a,an) in enumerate(devs) for j,(b,bn) in enumerate(devs)
        if j > i and math.gcd(an, bn) > 1]
```

Trong C(30,2) = 435 cặp chỉ có đúng một va chạm, và nó liên quan trực tiếp tới target:

```
[*] shared-prime pairs: 1
    VE-C1E90650 ~ VE-23795497   gcd = 512-bit prime
```

### Bước 2: từ một thừa số chung tới khoá riêng tư

```
p = 792448642746425956602219402032306819204...44085721   (512 bit)
q = n // p                                               (512 bit)
p * q == n  ->  True
phi = (p-1)*(q-1);  d = pow(65537, -1, phi);  m = pow(ct, d, n)
```

### Bước 3: bỏ phiếu PKCS#1 v1.5

Block giải mã ra dài 128 byte:

```
0002 81c2c61e...415d5d 00 766c745f343832353238633831343263613962316665353763666533
└type 2┘└── 97 byte padding, không có byte 0 ──┘└┘└──── message: "vlt_482528c8142ca9b1fe57cfe3" ────┘
```

Cấu trúc `00 02 PS 00 M` với PS không chứa byte 0 xác nhận khoá riêng tìm được là đúng (một sai một bit ở `d` sẽ ra rác không có đầu `00 02`). Token `vlt_<hex>` cũng khớp exactly placeholder "admin bootstrap token" của form.

### Bước 4: nộp

```
$ python solve_blood.py
[+] token = 'vlt_482528c8142ca9b1fe57cfe3'
[*] POST /admin -> 200 {"authed": true, "flag": "H7CTF{a727587f-67d5-4246-b7c3-e57798659fac}"}
[+] FLAG: H7CTF{a727587f-67d5-4246-b7c3-e57798659fac}
```

## Flag
```
H7CTF{a727587f-67d5-4246-b7c3-e57798659fac}
```

{% endraw %}
