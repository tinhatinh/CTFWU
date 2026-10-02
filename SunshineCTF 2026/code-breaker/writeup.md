# Code Breaker - Crypto/Pwn (Hard)

**Flag:** `sun{cr4ck_tHe_ciPh3r_fr33_thE_heaP}` · **Target:** `nc chal.sunshinectf.games 26005`
**Files:** `code_breaker` (PIE, stripped, glibc 2.39), `libc.so.6`, `ld-linux-x86-64.so.2`

## Đề bài

"Enterprise-grade encrypted key-value storage, all traffic passes through the proprietary cipher."

## Phân tích ban đầu

Khi thử kết nối đến dịch vụ, máy chủ trả về một chuỗi 20 byte nhị phân thô:

```
00 11 01 q é 9 Á Ï â Ù È Z h Ø Í . n 1 @
```

Phân tích chuỗi này cho thấy `00 11` là một giá trị số nguyên 16-bit ở định dạng big-endian (tương đương với 17), theo sau đó là chính xác 17 byte dữ liệu. Bằng cách kiểm tra binary (binary), ta nhận thấy nó nhập khẩu (import) một số hàm hệ thống tiêu chuẩn như `fopen`, `fread`, `system`, `read`, `write`, `malloc`, `free`, `atoi`. Ngoài ra, còn có các chuỗi đáng chú ý như `/dev/urandom`, `true`, `CodeBreaker`, cùng với một mảng hoán vị (S-box) kích thước 256 byte nằm tại địa chỉ `0x2040`. Dịch vụ này sử dụng một giao thức giao tiếp tự chế (custom protocol) với lưu lượng dữ liệu được mã hoá hoàn toàn bằng S-box nói trên.

Lưu lượng mạng được mã hoá ở cả hai chiều. Binary có kích thước khá nhỏ (khoảng 14 KB) và đã bị loại bỏ toàn bộ các symbol (stripped). Phân tích mã máy cho thấy có 4 hàm xử lý cốt lõi: quá trình khởi tạo và bắt tay (handshake) tại `0x1670`, vòng lặp chính của chương trình tại `0x1900`, hàm gửi tin nhắn (`send_message`) tại `0x1510`, và quá trình nhận/xử lý tin nhắn (`recv_message`) tại `0x13f0/0x13a0`.

## Giao thức mã hoá (Cipher)

**Quá trình bắt tay (Handshake):** Máy chủ bắt đầu bằng việc đọc 16 byte ngẫu nhiên từ `/dev/urandom` rồi gửi nguyên bản (chưa mã hoá) cho client dưới định dạng:
```
[0x01] || key            (Dữ liệu thô - RAW)
```

Client phải đáp trả bằng cách gửi một mã nhận diện `[0x02] || peer16` (RAW), sau đó lập tức gửi thêm một đoạn tin nhắn đã được mã hoá `[0x03] || check16` để chứng minh quyền truy cập.

**Quá trình tạo khoá (Key schedule):** Trạng thái nội bộ (window) được ghép từ `key` và `peer`, tạo thành một khối 32 byte. Khối này được dùng để khởi tạo trạng thái `state`:

```python
state = bytearray(16)
for outer in range(4):
    for i in range(16):
        x = window[(i + 8*outer) & 0x1f] ^ state[i]
        x = SBOX[x]
        x ^= window[3*outer + i]
        state[i] = rol8(x, 3)
```

**Giá trị chứng minh (Check value):** Client tạo khối xác thực theo công thức `check[i] = state[(i+5)&15] ^ SBOX[state[i]]`.

**Dòng khoá (Stream):** Byte khoá tại mỗi vị trí được sinh ra bằng công thức `ks(off, i) = SBOX[(off + i + state[i & 15]) & 0xff]`. Hệ thống duy trì hai bộ đếm (counter) hoàn toàn độc lập cho chiều gửi và chiều nhận (đặt tại `0x42c4` và `0x42c0`), mỗi bộ đếm sẽ tự động tăng lên bằng đúng độ dài của payload sau mỗi lượt trao đổi.

## Bảng lệnh (Jump Table)

Chương trình cung cấp một bảng lệnh (jump table) tại địa chỉ `0x2020` với các chức năng như sau:

| Lệnh | Cú pháp | Tác dụng |
| --- | --- | --- |
| `10` | `10 slot len_be16 value` | **PUT:** Gọi `malloc(len)` để cấp phát bộ nhớ và chép `value` vào đó. |
| `11` | `11 slot` | **GET:** Trả về dữ liệu trong slot dưới định dạng `[11][00][len][value]`. |
| `12` | `12 slot off_be16 data` | **WRITE:** Gọi `memcpy(ptr, data, off)` để ghi đè vào một vùng nhớ đã cấp phát. |
| `13` | `13 slot` | **FREE:** Gọi `free(ptr)` để giải phóng bộ nhớ, sau đó giảm biến đếm tham chiếu (`ref--`). Con trỏ chỉ bị xoá khi `ref` giảm về 0. |
| `14` | `14 a b` | **ALIAS:** Cho phép slot `a` (phải đang trống) trỏ cùng vào địa chỉ bộ nhớ của slot `b`, đồng thời tăng biến đếm `b.ref++`. |
| `15` | `15 string` | **RUN:** Gọi hàm thông qua con trỏ tại `[0x40c0]` với tham số `rdi` trỏ tới chuỗi truyền vào. |
| `16` | `16` | **INFO:** Đọc trực tiếp 240 byte dữ liệu trên vùng BSS bắt đầu từ `0x40c0`. |

Đáng chú ý, con trỏ tại `[0x40c0]` được khởi tạo mặc định trỏ tới đoạn mã `endbr64; ret` an toàn ở vị trí `0x1390`. Lệnh `15` sẽ mù quáng thực thi bất kỳ hàm nào mà con trỏ này đang trỏ tới.

`readelf -l` cho thấy GNU_RELRO kết thúc ở `0x4000`, còn `.got.plt` nằm ngoài vùng này và ghi được. Lệnh INFO (`16`) đọc `[0x40c0]`, có giá trị `base + 0x1390`; lấy giá trị đó trừ `0x1390` để tính PIE base.

## Chuỗi khai thác

**Bước 1 - Lỗ hổng Use-After-Free (UAF).** Gửi lệnh `PUT` vào `slot1` với độ dài 0x100 (gọi là P1). Sau đó, dùng lệnh `ALIAS 0 1` để `slot0` và `slot1` cùng trỏ chung vào P1, làm biến đếm tham chiếu (ref) tăng lên 2. Lúc này, gọi `FREE 1`. Hàm `free(P1)` được thực thi trên heap, sau đó biến `ref` giảm xuống còn 1. Do `ref` khác 0, chương trình không xoá con trỏ tại `slot0`. `slot0` giờ đây trỏ thẳng vào một chunk đã bị giải phóng và đang nằm trong danh sách tcache.

**Bước 2 - Rò rỉ cơ chế Safe-linking.** Khi chunk P1 là phần tử duy nhất trong tcache bin, thao tác `tcache_put` sẽ lưu giá trị `fd = PROTECT_PTR(pos, NULL) = pos >> 12`. Bằng cách dùng lệnh `GET` thông qua `slot0`, ta dễ dàng đọc được giá trị này và tính toán được địa chỉ heap base.

**Bước 3 - Đầu độc Tcache (Tcache poisoning).** Lần lượt tạo hai chunk P1 và P2 có cùng kích thước, sau đó giải phóng P2 rồi đến P1. Bằng cách ghi đè trường `fd` của P1 (lúc này đang đứng đầu danh sách tcache) thành một con trỏ mục tiêu, ta thao túng được danh sách liên kết. Với `counts = 2`, quá trình cấp phát sẽ pop (lấy) P1 ở lần thứ nhất, và pop ra con trỏ mục tiêu ở lần thứ hai.

**Bước 4 - Ghi đè vùng BSS.** Thiết lập con trỏ giả (fake pointer) trỏ về `base + 0x40c0`. Lần gọi `PUT` thứ hai sẽ nhận được chunk nằm tại đúng vị trí này. Khi đó, thao tác `memcpy` 256 byte sẽ ghi đè lên `0x40c0`. Bằng cách đặt 8 byte đầu tiên thành địa chỉ của hàm `system@plt` (tương đương `base + 0x1150`), ta có thể nắm quyền điều khiển thực thi.

**Bước 5 - Thực thi mã từ xa (RCE).** Gọi lệnh `15` với chuỗi tuỳ ý. Chương trình sẽ gọi qua con trỏ tại `[0x40c0]`, kích hoạt `system("chuỗi")` và ta có thể truyền vào lệnh `cat /ctf/flag.txt` để đọc cờ.

```
$ python -u client.py full "cat /ctf/flag.txt"
[*] handshake reply = 0400
[+] fnptr @0x40c0 = 0x56fe8fbbd390  ->  base = 0x56fe8fbbc000
[*] [0x40c0] = 0x56fe8fbbd150 
sun{cr4ck_tHe_ciPh3r_fr33_thE_heaP}
```

## Flag
```
sun{cr4ck_tHe_ciPh3r_fr33_thE_heaP}
```
