# Loose Lips — Crypto (Hard)

**Cờ v1:** `H7CTF{08a5c5eb-7571-4a3d-a80d-599ddd46c5ad}`
**Cờ v2:** `H7CTF{89c0e6b2-9fca-49fd-a02f-07a70e359363}`
**Files:** `ckks.py` (2272 B, sha256 `f905e01981fc8049…`) · **Instance:** `https://web-550a48e366fd77e3.web.h7tex.com`

## Đề bài

"DecryptoStat" xử lý số liệu mà (theo quảng cáo) không bao giờ nhìn thấy dữ liệu của bạn, dùng một biến thể CKKS thu nhỏ. Có hai service song song: bản gốc và bản "hardened rewrite". Cả hai đều phải bị lấy mất khoá bí mật; nộp khoá lên `/v1/recover` hoặc `/v2/recover` để nhận cờ.

## Phân tích ban đầu

GET `/` trả bảng mô tả endpoints kèm tham số hệ mật: `N=8`, `Q=2^40-87`, `DELTA=2^25`, và note quan trọng nhất: the secret key is a length-8 ternary vector.

Trong `ckks.py`:

```python
def small(bound=1): return [secrets.randbelow(2*bound+1) - bound for _ in range(N)]
def keygen(): return small(1)                    # mỗi hệ số chỉ là -1/0/+1
def encrypt(values, s):
    m = encode(values); a = rand_poly(); e = small(3)
    b = ring_add(ring_sub([0]*N, ring_mul(a, s)), ring_add(m, e))   # b = -a*s + m + e
    return b, a
def decrypt(ct, s, smudge=0):
    d = ring_add(b, ring_mul(a, s))              # b + a*s = m + e
    if smudge: d = ring_add(d, small(smudge))    # "noise flooding" của v2
    return decode(d)
```

Ba sự kiện ghép lại thành lời giải:

1. Keyspace của khoá là `3^8 = 6561`, liệt kê hết được trong vài giây.
2. `POST /vN/encrypt` cho ta chọn plaintext và trả về đúng cặp (b, a).
3. `e = small(3)`, tức mọi hệ số của `b + a*s - m` nằm trong [-3, 3]; độ lớn chuẩn của ciphertext là ~Q = 2^40, nên đây là một test gần như tuyệt đối.

Comment mở đầu của `ckks.py` nói "the flaw is not in this code; it is that the service returns the approximate (noisy) decryption": đó là đường tấn công mà tác giả dự tính (và là lý do v2 đổ thêm nhiễu vào decrypt). Không cần đi theo đường đó.

## Chuỗi khai thác

### Bước 1: xin một ciphertext của số 0

Với `values = [0,0,0,0]` thì `m = encode(0) = 0`, nên điều kiện còn lại chỉ là `b + a*s = e` nhỏ:

```python
c1 = post("/v1/encrypt", {"values": [0,0,0,0]})     # -> id, b, a
```

### Bước 2: quét toàn bộ keyspace ternary, giữ lại khoá khớp ngân sách nhiễu

```python
m = ckks.encode(values)
for s in itertools.product((-1,0,1), repeat=8):
    d   = ckks.ring_add(c1["b"], ckks.ring_mul(c1["a"], list(s)))
    res = ckks.ring_sub(d, m)
    if max(abs(int(x.real)) for x in ckks._center(res)) <= 3:
        cand.append(list(s))
```

Kịch bản `ckks.py` của đề được import thẳng (`sys.path.insert(0,"files"); import ckks`) để ring_mul/encode/_center phía tấn công khớp 100% phía server, tránh mọi sai lệch làm rớt nghiệm.

Result: một ciphertext duy nhất đã cho đúng một ứng viên cho cả hai service, không cần vòng phân liệt nào:

```
=== v1 ===
[*] ternary keys matching the zero-plaintext ciphertext: 1 -> [[1, -1, 0, -1, 1, 1, -1, -1]]
=== v2 ===
[*] ternary keys matching the zero-plaintext ciphertext: 1 -> [[1, 0, 0, -1, -1, -1, 0, 1]]
```

### Bước 3: chứng minh đó là khoá thật, rồi nộp

Xin một ciphertext mới với `values=[1.5,-2.25,0.5,3.0]` rồi tự giải mã bằng khoá vừa recover:

```
v1: local decrypt = [1.500000, -2.250000, 0.500000, 3.000000]  max|err| = 1.952e-07
    noise poly centred(b + a*s - m) = [ 2, -3, -3, 0, -3, 2,  1, -2]   (đúng budget small(3))
v2: max|err| = 1.836e-07
    noise poly centred(b + a*s - m) = [ 0,  3,  2,-2,  3,-2,  1, -2]
```

Nghĩa là mỗi service dùng một khoá cố định qua nhiều request, và khoá đó giải mã đúng ciphertext do chính nó sinh ra.

`POST /v1/recover` và `POST /v2/recover`:

```
{"ok": true, "flag": "H7CTF{08a5c5eb-7571-4a3d-a80d-599ddd46c5ad}"}
{"ok": true, "flag": "H7CTF{89c0e6b2-9fca-49fd-a02f-07a70e359363}"}
```

### Vì sao bản "hardened" không cứu được v2

`smudge` chỉ được cộng vào kết quả decrypt: nó làm bẩn đầu ra của oracle để bạn không suy ra `s` từ các lần gọi `/v2/decrypt`. Nhưng tấn công ở trên không hề gọi decrypt oracle: nó lấy `(b, a)` từ chính `/v2/encrypt` rồi tự kiểm tra nghiệm bằng số học chính xác trên máy mình. Đo thực tế thì `/v2/decrypt` trên một ciphertext vừa xin cho sai số 2.94e-07, cùng cỡ 1.95e-07 của v1, tức phần flooding không đáng kể trên đường đi đó; và dù nó có lớn thì cũng không liên quan tới primitive đã dùng.

## Flag
```
v1  H7CTF{08a5c5eb-7571-4a3d-a80d-599ddd46c5ad}   key [1,-1,0,-1,1,1,-1,-1]
v2  H7CTF{89c0e6b2-9fca-49fd-a02f-07a70e359363}   key [1, 0, 0,-1,-1,-1, 0, 1]
```

Chạy lại: `python solve_lips.py` (recover cả hai, ghi `flags.txt`).
