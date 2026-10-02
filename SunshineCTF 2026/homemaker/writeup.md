# Homemaker — Pwn (Hard)

**Flag:** `sun{the_future_is_now_today_well_wait_how_are_you_reading_this}`
**Instance:** `nc sunshinectf.games 26008`, file đính kèm chỉ bao gồm binary `homemaker`, không cung cấp thư viện `libc`.

## Đề bài

Bài toán là một hệ thống giả lập nạp thẻ đục lỗ: người chơi gửi dữ liệu thẻ lên, máy chủ tiến hành kiểm tra khóa (key), chép nội dung thẻ vào bộ nhớ và sau đó in ra. Bài không cung cấp thư viện libc cũng như không có gợi ý nào kèm theo.

## Phân tích

### Giao thức

Cấu trúc của một frame giao tiếp hai chiều được quy định như sau:
```
ESC '[' <len:u16 BE> <payload[len]> <crc8(payload)> ESC '\'
```

- Hàm `crc8` (`0x11e9`) sử dụng đa thức `0x12f` để tính toán kiểm tra lỗi.
- Lệnh 1 nhận một thẻ dịch vụ, trong đó khoá so sánh tại địa chỉ `0x12a7` là `0x1337c35f`.
- Lệnh 2 đảm nhiệm việc chép nội dung thẻ vào vùng nhớ `mem`, trong khi lệnh 3 dùng để in vùng nhớ `mem` ra ngoài.

### Lỗi Off-by-one (`0x174c`)

```c
n = len - 1;
if (n > capacity) return 0xe2;
for (i = 0; i <= n; ++i) mem[i] = p[1+i]; // Ghi n+1 byte
```

Vòng lặp trong hàm sao chép sử dụng toán tử `<=` nên đã ghi thừa một byte so với tính toán. Khi `len = 257` (tương đương `n = 256 = capacity`), byte thừa này sẽ được ghi vào `mem[256]` (vị trí tương ứng với byte thấp của biến `capacity` nằm tại `mem+0x100`). Đáng chú ý là giá trị ghi vào vị trí này chính là byte CRC của frame, một giá trị mà kẻ tấn công hoàn toàn có thể kiểm soát.

Thông qua việc tinh chỉnh byte CRC, ta có thể chủ động thay đổi `capacity` thành `0x1FF`. Bằng cách gửi một thẻ 512 byte ngay sau đó, biến `capacity` tiếp tục bị ghi đè thành `0x7F8`. Quá trình này đã trực tiếp nâng cấp một lỗi off-by-one nhỏ lẻ thành lỗ hổng tràn bộ đệm (buffer overflow) mạnh mẽ, cho phép ghi đè lên đến 2041 byte (bao phủ toàn bộ vùng `mem` và lan sang cả stack của hàm điều phối - dispatcher).

### Memory Leak (`0x1810`)

Dưới đây là bố cục bộ nhớ của vùng `mem` (hàm điều phối thiết lập stack bằng `sub rsp, 0x120`; `mem` nằm tại `rbp-0x110`):

| Offset | Nội dung |
| --- | --- |
| `0x100` | `capacity` (kiểu u16) |
| `0x102` | số thẻ đã nạp (kiểu u16) |
| `0x108` | stack canary |
| `0x110` | saved rbp -> chứa địa chỉ stack |
| `0x118` | return address -> chứa PIE base |

Bằng việc khéo léo thay đổi cấu trúc của các frame đọc và ghi, ta có thể rò rỉ thành công stack canary, địa chỉ cơ sở của mã nguồn (base address) và con trỏ stack.

## Chuỗi khai thác

Dù tập tin thực thi có nhập khẩu hàm `system`, môi trường thực thi trên máy chủ không hề tồn tại tập tin `/bin/sh`. Điều này bắt buộc ta phải thực hiện chuỗi tấn công ORW (Open-Read-Write). Tuy nhiên, một trở ngại lớn là binary không chứa lệnh `syscall` hay bất kỳ đoạn mã libc nào để sử dụng làm ROP gadget.

### Bước 1 - Leak libc base và tìm kiếm ROP gadgets
Tận dụng hàm phát dữ liệu (emit) `0x1810(ctx)` để đọc mã máy từ phía máy chủ:
- Ghi đè tham số đọc ra bên ngoài vùng nhớ kiểm soát (cụ thể là nhắm vào biến `ctx` nằm tại vùng `.bss` của binary) nhằm đọc các phân vùng hệ thống như `.dynamic`, `.got`, `.data`.
- Từ các phân vùng này, ta trích xuất được địa chỉ thực của các hàm `write`, `read`, `system` thuộc thư viện libc.
- Tiếp tục đọc vùng mã nguồn của hàm `write` trong libc để lùng sục các lệnh assembly hữu ích như `syscall; ret` (được tìm thấy tại `write+0x1779`) và `pop rsi; ret` (tại `write+0x1a02`). Offset cố định `0x11e790` có thể được tính toán ngược lại từ một con trỏ có sẵn trên stack.

### Bước 2 - ORW chain

Có thể gọi syscall mà không cần đến các gadget `pop rdx` và `pop rax` bằng cách lợi dụng trạng thái tự nhiên của chương trình:
1. Các hàm `read@plt` và `write@plt` luôn tự thiết lập `eax = 0` và `eax = 1` tương ứng trước khi gọi syscall hệ thống.
2. Giá trị trả về của `read` chính là số byte đọc được. Bằng cách gửi chính xác 2 byte qua socket, ta có thể chủ động gán `rax = 2` (tương ứng với syscall `__NR_open`).
3. Giá trị của thanh ghi `rdx` (đại diện cho độ dài) được điều khiển gián tiếp qua thông số độ dài lệnh của frame. Thanh ghi `rsi = 0` (cờ `O_RDONLY`) được nạp thông qua gadget `pop rsi`.

Chuỗi ROP hoàn chỉnh được thiết lập như sau:
```
pop rdi, mema+0x600 ; 0x1810        # Thiết lập rsi, rdx
pop rdi, 0          ; read@plt      # Đọc 2 byte từ client -> gán rax = 2 (syscall open)
pop rsi, 0                          # Đặt flags = O_RDONLY
pop rdi, mema+0x600                 # Trỏ path = "/ctf/flag.txt"
syscall                             # Gọi open -> trả file descriptor fd = 3 vào rax
pop rdi, mema+0x600 ; 0x1810        # Thiết lập lại rsi, rdx
pop rdi, 3          ; read@plt      # Thực hiện read(3, buf, 257)
pop rdi, 1          ; write@plt     # Thực hiện write(1, buf, 257) -> in cờ trả về cho client
```

## Flag

```
sun{the_future_is_now_today_well_wait_how_are_you_reading_this}
```

## Reproduce

```bash
python exploit_homemaker.py 3
```
