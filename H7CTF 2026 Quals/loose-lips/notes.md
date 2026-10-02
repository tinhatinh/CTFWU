# notes.md - Loose Lips (crypto / CKKS toy)

## H1 - keyspace của khoá bí mật
target: `ckks.py`
evidence: `keygen() -> small(1)` trên N=8 -> mỗi hệ số thuộc {-1,0,1} -> **3^8 = 6561** khoá, liệt kê hết được
result: CONFIRMED - đây là chỗ "hopeless at keeping a secret" đầu tiên

## H2 - primitive mà service tự tặng
evidence: `POST /vN/encrypt {values}` trả nguyên `b` và `a` của ciphertext ta chọn plaintext. Với `values = [0,0,0,0]` thì `m = encode(0) = 0`, nên `b + a*s = e` với mọi hệ số `|e_i| <= 3`
did: duyệt 6561 khoá ternary, giữ khoá nào làm `centred(b + a*s - m)` nằm trọn trong [-3,3]
result: CONFIRMED - **duy nhất 1 ứng viên** cho mỗi service, ngay với một ciphertext duy nhất, không cần query lần hai

## H3 - v1
did: `python solve_lips.py` -> key `[1,-1,0,-1,1,1,-1,-1]` -> `POST /v1/recover`
result: `{"ok": true, "flag": "H7CTF{08a5c5eb-7571-4a3d-a80d-599ddd46c5ad}"}`

## H4 - v2 có thật sự khó hơn không
target: chỗ "hardened": `decrypt(ct, s, smudge=...)` = noise flooding
evidence: flooding chỉ có ý nghĩa nếu tấn công đi qua **decrypt oracle** (đúng như comment trong ckks.py: "the flaw ... is that the service returns the approximate (noisy) decryption"). Attack ở H2 không đụng tới decrypt oracle -> vô hiệu hoá hoàn toàn phần hardening.
did: đo tại `/v2/decrypt` trên ciphertext vừa xin: max|err| = 2.941e-07, cùng cỡ với v1 (1.952e-07) -> trên đường đi này flooding không quan sát được thêm nhiễu đáng kể
result: CONFIRMED - key `[1,0,0,-1,-1,-1,0,1]` -> `H7CTF{89c0e6b2-9fca-49fd-a02f-07a70e359363}`

## H5 - kiểm chứng khoá recovered là khoá thật của service (không phải khoá giả vẫn khớp một ciphertext)
did: xin **một ciphertext MỚI** với `values=[1.5,-2.25,0.5,3.0]`, rồi tự decrypt bằng ckks.decrypt + key vừa recover
result:
- v1: local decrypt = `[1.500000, -2.250000, 0.500000, 3.000000]`, max|err| = 1.952e-07, poly nhiễu `centred(b+a*s-m) = [2,-3,-3,0,-3,2,1,-2]` (đúng budget small(3))
- v2: max|err| = 1.836e-07, nhiễu `[0,3,2,-2,3,-2,1,-2]`
=> mỗi service dùng **một khoá cố định qua nhiều request**, và khoá ta tìm decrypt đúng ciphertext mà nó vừa sinh -> không còn khả năng trùng hợp.

## Ghi chú kỹ thuật
- `ckks.py` import trực tiếp được (numpy chỉ dùng cho ma trận embedding), nên ring arithmetic phía tấn công khớp 100% phía server: không cần viết lại encode/decode, tránh sai lệch làm rớt nghiệm.
- `requests` có sẵn trên host; `re` để bắt `H7CTF{...}` từ chính JSON response.
- Không cần tối ưu: 6561 × ring_mul(8x8) chạy hết trong vài giây.

## Kết quả cuối
```
v1 key [1,-1,0,-1,1,1,-1,-1] -> H7CTF{08a5c5eb-7571-4a3d-a80d-599ddd46c5ad}
v2 key [1,0,0,-1,-1,-1,0,1]  -> H7CTF{89c0e6b2-9fca-49fd-a02f-07a70e359363}
```
Chạy lại: `python solve_lips.py` (tự recover cả 2, ghi `flags.txt`)
