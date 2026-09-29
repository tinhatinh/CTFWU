---
title: "Take Two — Crypto (Hard)"
date: 2026-09-28 16:53:17 +0700
lastmod_at: 2026-09-28 16:53:17 +0700
categories: [Crypto]
tags: [h7ctf-quals, Crypto]
image:
  path: /CTFWU/H7CTF%202026%20Quals/take-two/files/de.png
---
{% raw %}
**Flag:** `H7CTF{63b0dde3-3edd-4a95-92d3-4e8c26e38483}`

## Đề bài

Helios chỉ boot firmware được notary đóng dấu. Notary từ chối ký mọi build chứa `BACKDOOR`,
nên không thể xin chữ ký hợp lệ cho cái mình muốn. Câu "it is not above a second take" chỉ vào
chỗ hỏng: một lá chữ ký one-time được cho ký lại.

`lms.py` được phát kèm, và chính nó thú nhận: *"the vulnerability is operational (a leaf reused
via a counter reset), not in this code"*.

## Phân tích ban đầu

Scheme là WOTS+ khép kín trong cây Merkle 16 lá:

```python
msg_digits(msg):  d = sha256(msg) -> 64 nibble + 3 nibble checksum   # LEN = 67
wots_sign(sk,msg): sig[i] = chain(sk[i], d[i])                       # chain = hash tới trước
verify:  leaf = H(0x00 || H(chain(sig[i], 15-d_i))) so với root qua auth path
```

Hai tính chất quyết định:

1. `chain` chỉ đi một chiều. Biết `chain(sk_i, a)` thì suy ra được `chain(sk_i, a+k)` với mọi `k >= 0`,
   nhưng không lùi được về `a-1`.
2. `verify` chỉ kiểm chữ ký khớp root đã công bố, không có ràng buộc nào rằng notary phải là
   người tạo ra chữ ký.

API cho ta đúng ba thứ cần thiết: `POST /sign` (ký message mình chọn, miễn không có `BACKDOOR`),
`POST /rollback` (rewind counter), và `GET /root`.

Thử nhanh: chữ ký đầu rơi vào leaf 1, sau một lần rollback thì leaf quay về 0 và các lần ký sau đó
đều dùng lại lá 0. Đây chính là "second take".

## Chuỗi khai thác

**Bước 1 - Gom nhiều chữ ký trên cùng một lá.** Vòng `rollback -> sign("benign-<i>")` lặp 260 lần,
tất cả đều ra `leaf = 0`. Với mỗi toạ độ `j` trong 67 toạ độ, ghi lại chữ số nhỏ nhất từng xuất hiện
`mins[j]` và giá trị chuỗi `base[j] = sig[j]` tại chữ số đó.

**Bước 2 - Vì sao đủ chữ ký là đủ.** Chữ số phân phối đều trên 0..15, nên mỗi toạ độ có xác suất
`1-(15/16)^k` từng thấy số 0 sau `k` chữ ký. Với `k = 260`, kỳ vọng là gần như mọi toạ độ chạm 0;
kết quả đo được là `max(mins) = 1`, `sum(mins) = 1` - tức 66/67 toạ độ đã có gốc tại chữ số 0,
một toạ độ dừng ở 1.

**Bước 3 - Ký message bị cấm.** Với message đích có chữ số `t[j]`, chỉ cần `t[j] >= mins[j]` là
dựng được:

```python
forged[j] = chain(base[j], t[j] - mins[j])
```

Vì `mins` gần như toàn 0, điều kiện này gần như luôn đúng; thực tế chỉ cần thử đúng 1 candidate
`HELIOS-OTA-BACKDOOR-1` là đạt mọi toạ độ.

**Bước 4 - Tự kiểm chứng trước khi nộp.** Dùng đúng hàm verify của đề tính lại root từ lá suy ra
chữ ký giả và so với root công bố - khớp. Bước này rẻ và tránh cảnh "deploy" thử mò; nó cũng chứng
minh chữ ký hợp lệ thật chứ không phải server rộng lượng.

**Bước 5 - Deploy.**

```json
{"ok": true, "booted": true, "flag": "H7CTF{63b0dde3-3edd-4a95-92d3-4e8c26e38483}"}
```

## Flag
```bash
python exploit.py https://web-18955a87eb148fa7.web.h7tex.com
```

```
[*] leaf 0 signed 260 distinct messages (other leaves: [])
[*] per-coordinate min digit: max=1 sum=1
[+] target build found after 1 grind: HELIOS-OTA-BACKDOOR-1
[+] forged signature verifies against the published root locally
[*] deploy -> 200
[+] FLAG: H7CTF{63b0dde3-3edd-4a95-92d3-4e8c26e38483}
```

{% endraw %}
