# Code Breaker — Crypto/Pwn (Hard)

**Flag:** `sun{cr4ck_tHe_ciPh3r_fr33_thE_heaP}` · **Target:** `nc chal.sunshinectf.games 26005`
**Files:** `code_breaker` (PIE, stripped, glibc 2.39), `libc.so.6`, `ld-linux-x86-64.so.2`

## Đề bài

"Key-value storage mã hoá cấp doanh nghiệp, toàn bộ traffic đi qua cipher độc quyền." Không có gợi ý nào khác. Cờ dạng `sun{...}`.

## Phân tích ban đầu

Kết nối thử trả về 20 byte nhị phân:

```
00 11 01 q é 9 Á Ï â Ù È Z h Ø Í . n 1 @
```

`00 11` là độ dài big-endian (17), còn lại là 17 byte không đọc được. Binary imports có `fopen/fread/system/read/write/malloc/free/atoi` và chuỗi `/dev/urandom`, `true`, `CodeBreaker`, cùng một hoán vị 256 byte tại `0x2040`. Protocol tự chế, có S-box.

Traffic bị mã hoá cả hai chiều nên không dò giao thức bằng cách thử được; phải đọc code. Binary nhỏ (14 KB) và stripped nhưng chỉ có 4 hàm đáng chú ý: init/handshake `0x1670`, vòng lặp chính `0x1900`, `send_message` `0x1510`, `recv_message` `0x13f0/0x13a0`.

## Cipher

**Handshake.** Server đọc 16 byte từ `/dev/urandom` rồi gửi cho client:

```
[0x01] || key            (RAW, chưa mã hoá)
```

Khoá nằm nguyên văn trên chính đường truyền mà nó định bảo vệ. Client phải trả `[0x02] || peer16` (RAW), rồi một message đã mã hoá `[0x03] || check16`.

**Key schedule** (`window = key || peer`, 32 byte):

```python
state = bytearray(16)
for outer in range(4):
    for i in range(16):
        x = window[(i + 8*outer) & 0x1f] ^ state[i]
        x = SBOX[x]
        x ^= window[3*outer + i]
        state[i] = rol8(x, 3)
```

**Giá trị chứng minh:** `check[i] = state[(i+5)&15] ^ SBOX[state[i]]`.

**Stream:** `ks(off, i) = SBOX[(off + i + state[i & 15]) & 0xff]`, với hai bộ đếm độc lập cho chiều gửi và chiều nhận (`0x42c4` và `0x42c0`), mỗi cái tăng đúng bằng độ dài thân của message vừa xử lý.

Cài lại bằng Python và để chính server chấm điểm: handshake trả `04 00` = đúng.

## Bảng lệnh

Đã giải mã toàn bộ jump table tại `0x2020`:

| Lệnh | Tác dụng |
| --- | --- |
| `10 slot len_be16 value` | PUT: `malloc(len)` + copy |
| `11 slot` | GET: trả `[11][00][len][value]` |
| `12 slot off_be16 data` | WRITE: `memcpy(ptr, data, off)` |
| `13 slot` | FREE: `free(ptr)` rồi `ref--`, chỉ xoá ptr nếu ref về 0 |
| `14 a b` | ALIAS: slot a (đang trống) lấy con trỏ của b, `b.ref++` |
| `15 string` | RUN: `call [0x40c0]` với rdi = bản sao chuỗi |
| `16` | INFO: dump 240 byte BSS từ `0x40c0` |

`[0x40c0]` được khởi tạo trỏ tới stub `endbr64; ret` ở `0x1390`, nên lệnh `15` vô hại cho tới khi ghi đè ô đó.

Hai chi tiết quyết định:
- `readelf -l`: GNU_RELRO kết thúc đúng tại `0x4000`, còn `.got.plt` trải tới `0x404068` → GOT writable.
- Không PIE-check gì thêm: PIE thật, nhưng lệnh INFO cho đọc `[0x40c0]` = `base + 0x1390` → leak base miễn phí.

## Các hướng đã loại

1. Dò giao thức bằng cách gửi thử. Mọi message sau handshake đều qua stream cipher ở cả hai chiều, phản hồi không đọc được gì. Loại, phải rã binary rồi cài lại cipher.
2. Poison tcache bằng một chunk duy nhất. Lần `PUT` kế tiếp pop đúng chunk đó và đặt head = con trỏ giả, nhưng `counts` về 0 nên `_int_malloc` bỏ qua tcache và cấp từ top chunk. Bằng chứng: marker `WXYZWXYZ` không xuất hiện ở bất kỳ đâu trong dump BSS sau khi poison. Loại; cần hai chunk cùng bin.

## Chuỗi khai thác

**Bước 1 - UAF.** `PUT slot1(0x100)` → P1; `ALIAS 0 1` làm slot0 và slot1 cùng trỏ P1 với `ref=2`; `FREE 1` gọi `free(P1)` nhưng ref chỉ giảm xuống 1 nên ptr không bị xoá → slot0 vẫn trỏ vào chunk đang nằm trong tcache.

**Bước 2 - leak để thắng safe-linking.** Khi chunk là phần tử duy nhất của bin, `tcache_put` lưu `fd = PROTECT_PTR(pos, NULL) = pos >> 12`. `GET` qua alias sống cho đúng giá trị đó → có `P>>12` mà không cần biết P.

**Bước 3 - dựng hai chunk cùng bin.** Tạo P1 và P2 cùng cỡ, free P2 trước rồi P1, và poison `P1->fd` (đầu danh sách). Khi đó `counts = 2`: pop 1 lấy P1 (head thành con trỏ giả, counts còn 1), pop 2 mới thực sự đi qua tcache.

**Bước 4 - đáp vào BSS.** Con trỏ giả = `base + 0x40c0`. Lần PUT thứ hai `memcpy` 256 byte ta chọn thẳng vào đó, nên 8 byte đầu chính là `system@plt = base + 0x1150`. Kiểm chứng bằng cách chạy lại INFO: `[0x40c0] = 0x...bd150` ✓.

**Bước 5 - RCE.** Lệnh `15` gọi `[0x40c0](chuỗi)` → `system("cat /ctf/flag.txt")`. Output của con trỏ ghi trực tiếp vào fd 1 nên không có length-prefix, phải đọc thô thay vì dùng parser của protocol.

```
$ python -u client.py full "cat /ctf/flag.txt"
[*] handshake reply = 0400  (thành công)
[+] fnptr @0x40c0 = 0x56fe8fbbd390  ->  base = 0x56fe8fbbc000
[*] [0x40c0] = 0x56fe8fbbd150  (kỳ vọng 0x56fe8fbbd150)
---- kết quả ----
sun{cr4ck_tHe_ciPh3r_fr33_thE_heaP}
```

## Flag
```
sun{cr4ck_tHe_ciPh3r_fr33_thE_heaP}
```
