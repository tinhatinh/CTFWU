# notes.md - Shared Blood (crypto / RSA shared prime)

## H1 - đọc đề ra hướng
evidence: "fleet of identical cameras", "same hurry", "family resemblance runs deeper than you'd think", "one device whose console you'd like to open"
hypothesis: nhiều thiết bị cùng sinh key vội -> **prime dùng chung giữa hai modulus** (không phải common-modulus, không phải small e, không phải Wiener)
result: đúng, xác nhận ở H3

## H2 - surface của service
target: `GET /`, `/fleet`, `/captured`
evidence: 30 modulus 1023/1024 bit, e=65537 toàn fleet; ciphertext 128 byte cho đúng serial `VE-C1E90650`; `ct < n` và bit length 1018 (2 byte đầu bị số hoá nhỏ) -> ciphertext hợp lệ với modulus 1024 bit
did: parse JSON, ép `n`, `ct` sang int
result: CONFIRMED - không có oracle decrypt nào, chỉ có một ciphertext duy nhất -> phải phân tích hoàn toàn `n` của target

## H3 - pairwise GCD
did: `gcd(n_i, n_j)` cho toàn bộ C(30,2) = 435 cặp
evidence: **đúng một** cặp có gcd > 1: `VE-C1E90650 ~ VE-23795497`, gcd 512 bit
result: CONFIRMED - và gcd đó chia hết `n` của target, `q = n/p` cũng 512 bit, `p*q == n`
ghi chú: may mắn là thiết bị "anh em" không phải target cũng nằm trong fleet được liệt kê, nếu không thì không có dữ liệu để gcd

## H4 - dựng khoá riêng và giải mã
did: `phi=(p-1)(q-1)`, `d=pow(e,-1,phi)`, `m=pow(ct,d,n)`
evidence: block 128 byte bắt đầu `00 02`, kết thúc `... 5d5d 00 766c745f...` -> `vlt_482528c8142ca9b1fe57cfe3`
    (PS dài 97 byte, không có byte 0 ở giữa -> đúng PKCS#1 v1.5 type 2)
result: CONFIRMED - 28 byte message là token dạng `vlt_<hex>` khớp placeholder "admin bootstrap token" của form

## H5 - nộp
did: `POST /admin {"token": "vlt_482528c8142ca9b1fe57cfe3"}`
result: `200 {"authed": true, "flag": "H7CTF{a727587f-67d5-4246-b7c3-e57798659fac}"}`
=> chuỗi khoá/giải mã/nộp bài khép kín, không còn giả thuyết mở.

## Lỗi đã gặp
1. `m.to_bytes((m.bit_length()+7)//8)` cho ra 127 byte vì `EM` bắt đầu bằng `0x00` bị int hoá mất -> điều kiện `msg[0]==0x00` fail và script báo "wrong key?" trong khi khoá đã đúng. Sửa: độ dài cố định `k=(n.bit_length()+7)//8`.
   Đây là bẫy kinh điển của RSA/PKCS#1, không phải tín hiệu sai nghiệm.

## Chạy lại
`python solve_blood.py` (tự tải fleet, gcd, factor, decrypt, POST /admin, ghi flag.txt)
