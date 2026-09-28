# Notes — Code Breaker

## Giao thức

`send_raw` = 2 byte độ dài big-endian + thân. Sau handshake, mọi message đều bị mã hoá bằng một stream tự chế.

### Handshake (hàm 0x1670)

1. `fopen("/dev/urandom")` → `fread(key, 1, 0x10)` → **16 byte khoá**.
2. Server gửi RAW `[0x01] || key` → **khoá bị gửi cho chính client, không mã hoá**.
3. Client phải gửi RAW `[0x02] || peer16` (độ dài > 16).
4. Client gửi ĐÃ MÃ HOÁ `[0x03] || check16`, độ dài > 16.
5. Server trả `[0x04][0x00]` nếu khớp.

### Key schedule

`window = key(16) || peer(16)` (32 byte), `state` 16 byte khởi tạo 0:

```
for outer in 0..3:
    for i in 0..15:
        x  = window[(i + 8*outer) & 0x1f] ^ state[i]
        x  = SBOX[x]
        x ^= window[3*outer + i]
        state[i] = rol8(x, 3)
```

`SBOX` = hoán vị 256 byte tại vaddr `0x2040` (file offset cũng là 0x2040).

### Check của bước 4

```
check[i] = state[(i + 5) & 15] ^ SBOX[state[i]]
```

(Sai một lần vì viết nhầm thành `state[i] ^ SBOX[state[(i+5)&15]]`; server trả `04ff`.)

### Stream cipher

```
ks(off, i) = SBOX[(off + i + state[i & 15]) & 0xff]
```

Hai bộ đếm **độc lập**: `[0x42c0]` cho chiều server nhận, `[0x42c4]` cho chiều server gửi; mỗi cái tăng đúng bằng độ dài thân của message vừa xử lý. Message đầu của mỗi chiều được gửi RAW nên cả hai bộ đếm bắt đầu từ 0 và chỉ nhích sau message đã mã hoá.

## Menu lệnh (payload đã mã hoá)

| Lệnh | Thân | Handler | Ghi chú |
| --- | --- | --- | --- |
| 0x10 PUT | `[10][slot][len_be16][value]` | 0x1c50 | slot phải trống, `1 <= len <= 0x400`, `len+2 < msglen` |
| 0x11 GET | `[11][slot]` | 0x1bc0 | trả `[11][00][len_be16][value]` |
| 0x12 WRITE | `[12][slot][off_be16][data]` | 0x1b40 | **`memcpy(ptr, data, off)`**: độ dài ghi đúng bằng trường offset, và bắt buộc `off+2 < msglen` |
| 0x13 FREE | `[13][slot]` | 0x1ae8 | `free(ptr)` rồi mới `ref--`; **chỉ xoá ptr khi ref về 0** |
| 0x14 ALIAS | `[14][a][b]` | 0x1a80 | a trống thì `a.ptr = b.ptr`, `a.ref = 1`, `b.ref++` |
| 0x15 RUN | `[15][string]` | 0x1a00 | copy string rồi **`call [0x40c0]`** với rdi = string |
| 0x16 INFO | `[16]` | 0x1d08 | dump 240 byte BSS từ `0x40c0` |

`[0x40c0]` được init trỏ tới stub `endbr64; ret` ở `0x1390` → cmd 0x15 vô hại cho tới khi ghi đè nó.

## Bug

`ALIAS` + `FREE`: sau `alias(a,b)` thì hai slot cùng trỏ một chunk và `b.ref = 2`.
`free(b)` gọi `free()` thật nhưng `ref` chỉ giảm 2→1 nên **`b.ptr` không bị xoá** → use-after-free, và `a` vẫn là alias sống.

## Chuỗi khai thác

1. Handshake với cipher tự cài → tự tính `state` và `check` (server xác nhận `0400`).
2. `INFO` → 8 byte đầu là `[0x40c0]` = `base + 0x1390` → **leak PIE base**.
3. Hai chunk P1, P2 cùng cỡ 0x100 qua `PUT`; `ALIAS` để giữ alias sống cho từng cái; `FREE` P2 trước rồi P1 → bin tcache = `[P1 -> P2]`, `counts = 2`.
4. `GET` qua alias của P2 → 8 byte đầu = `P2 >> 12` (vì khi đó bin đang trống, `PROTECT_PTR(pos, NULL) = pos>>12`).
5. `WRITE` qua alias của P1 → đè `P1->fd = (P2>>12) ^ (base+0x40c0)` (P1 và P2 cùng trang).
6. `PUT` #1 pop P1 → head thành `base+0x40c0`, `counts` còn 1.
   `PUT` #2 pop chính nó → slot trỏ vào BSS; value 256 byte ta gửi **ghi đè luôn `[0x40c0] = system@plt`**.
7. `RUN` với chuỗi shell → `system("cat /ctf/flag.txt")`; output là dữ liệu thô trên fd 1, không có length-prefix.

## Ba chỗ phải sửa mới chạy được

1. **`counts` của glibc**: nếu chỉ free MỘT chunk thì sau lần pop đầu, `counts` về 0 và `_int_malloc` bỏ qua tcache dù `entries[idx]` còn giá trị poison → lần cấp thứ hai lấy chunk mới từ top. Phải có HAI chunk free để con trỏ giả nằm ở vị trí pop thứ hai.
2. **Semantics của WRITE**: `memcpy(ptr, data, offset)` chứ không phải `memcpy(ptr+offset, ...)`. Kiểm chứng bằng thực nghiệm (ghi marker rồi đọc lại) thay vì tin lần đọc disassembly đầu tiên.
3. **Phân tích response**: header là 2 byte `[cmd][0x00]` rồi mới tới payload; đọc lệch 1 byte cho ra "con trỏ" vô nghĩa.

## Cờ

```
sun{cr4ck_tHe_ciPh3r_fr33_thE_heaP}
```
