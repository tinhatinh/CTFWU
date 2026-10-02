# Loose Ends — Pwn (Hard)

**Flag:** `H7CTF{4d0e9693-88bd-4749-87d8-c64dd2ef80ab}`
**Máy chủ mục tiêu:** `pwn.h7tex.com:42589` 
**File cung cấp:** `ledger.zip` (bung ra tệp thực thi `ledger` chuẩn ELF x86-64, thư viện `libc.so.6` phiên bản glibc 2.39-0ubuntu8.9, và bộ nạp `ld-linux-x86-64.so.2`).

## Đề bài

Trò chơi đưa ta vào hệ thống sổ cái (ledger) của công ty Sparrow Freight. Những nhân viên ghi chép sổ sách mắc một sai lầm chết người: họ xoá bỏ (free) các bản ghi cũ kỹ không hề sạch sẽ như họ tưởng tượng. Song song với đó, hệ thống lại giấu một tính năng kiểm toán (audit) cho phép đọc to mã thông hành (flag) trong ngày, nhưng tính năng này lại bị cô lập, chưa từng được ai trên đời gọi tới. 
Nhiệm vụ của ta là lợi dụng sự cẩu thả kia, khâu nối những mối bung bét (loose ends) lại với nhau để vươn tới cái mã thông hành đó.

## Phân tích ban đầu

Đánh giá các hàng rào phòng thủ của tệp tin:
```text
Cấu trúc ET_EXEC không bật PIE | Cờ báo NX được kích hoạt (cấm thực thi trên ngăn xếp) | Có tích hợp Canary bảo vệ (hiển diện trong các hàm menu/idx/audit).
Bảo vệ GNU_RELRO kích hoạt lưng chừng, chỉ che chắn 0x403df8..0x404000  ->  Nghĩa là toàn bộ các slot JUMP_SLOT của hàm dạt vào vùng 0x404000..0x404060 vẫn chình ình ở chế độ cho phép ghi đè (writable).
```

Cấu trúc cốt lõi của hàm `main` là một cái menu gồm 4 chức năng, xoay quanh một mảng con trỏ khai báo biến toàn cục (global):

```c
Mảng notes[16] toạ lạc tại vùng 0x4040a0
Lệnh add    : Khởi tạo notes[i] = malloc(0x50); Sau đó cho phép read(0, notes[i], 0x50).
Lệnh delete : Gọi free(notes[i]).                      <- Lỗ hổng: Xoá mà quên không gán notes[i] = NULL.
Lệnh edit   : Cắm cờ if (notes[i]), sau đó nạp đạn read(0, notes[i], 0x50).
Lệnh view   : Cắm cờ if (notes[i]), in ra write(1, notes[i], 0x50).
```

Chính vì hàm `delete` hồn nhiên vứt xác con trỏ lại sau khi giải phóng bộ nhớ (free), mà các lệnh `edit` và `view` lại ngây thơ chỉ thèm check xem con trỏ có khác 0 hay không. Kết quả là hệ thống thủng một lỗ to đùng mang tên Use-After-Free (UAF - sử dụng lại bộ nhớ đã giải phóng), cho phép thao túng cả quyền Đọc (view) lẫn quyền Ghi (edit).

Luồng `audit` ẩn náu tại mốc địa chỉ `0x4012b6`. Nó mang sứ mệnh mở tệp `/flag`, xúc 80 byte dữ liệu rồi thét lên dòng chữ `printf("[audit] %s\n", ...)`. Khổ nỗi, lệnh này không hề có mặt trong bảng chọn (jump table) của menu, vì vậy con đường độc đạo để thâm nhập nó là ép hệ thống tự lèo lái (nhảy - jump) tới đó.

Hai lỗ hổng hạ tầng giúp bài này "dễ thở" hơn tưởng tượng: Bộ nhớ Heap tĩnh như tờ, không hề bị nhào nặn ngẫu nhiên hoá (no ASLR trên heap) - khối cấp phát đầu tiên mặc định chốt sổ tại `0x4062b0`, kẹp ngay sát vách vùng BSS. Hàng rào RELRO bị xén ngang ở mốc `0x404000`, phơi nguyên toàn bộ mảng GOT của phân đoạn PLT thành mồi ngon cho phép ghi. Đặc ân lớn nhất là PIE bị tắt, đồng nghĩa với việc các con số địa chỉ đều là hằng số vật lý, loại bỏ hoàn toàn cái cực hình phải chọc rò rỉ (leak) địa chỉ.

## Chuỗi khai thác

**Bước 1 - Lật tẩy chiêu trò mã hoá safe-linking bằng cách rò rỉ `heap >> 12`.** 
Kể từ phiên bản glibc 2.32 (bài này dùng 2.39), tcache được bọc thép bằng thuật toán mã hoá con trỏ: `giá trị_lưu (stored) = (vị trí_hiện_tại (pos) >> 12) ^ giá trị_thực (real)`. 
Bản chất của lỗ hổng: Khi ta gọi lệnh `free(A)` (với A đang là phần tử nằm ở vị trí chót cùng của thùng rác bin), lúc đó con trỏ tiếp theo trỏ về cõi hư vô (`real = NULL`). Suy ra, phương trình triệt tiêu biến thành: 8 byte mào đầu của khối A chính là phép trượt bit `A >> 12`.

```text
Quy trình: add(0); add(1); delete(0); view(0)   ->  Đọc 8 byte đầu = 06 04 00 ...  =>  Quy nạp ra t = 0x406.
```

**Bước 2 - Bỏ thuốc độc (Poisoning) vào con trỏ Forward (fd).** 
Triển khai `delete(1)`, cục máu đông B được đẩy lên chóp đỉnh của bin (tcache). Lợi dụng cờ UAF, ta bồi lệnh `edit(1)` để đè tàn bạo lên chính con trỏ `B->next` của nó:

```python
edit(1, p64(t ^ 0x404060))     # Địa chỉ mục tiêu 0x404060 chính là vị trí của lệnh exit@GOT
```

Nhờ B và A có quan hệ láng giềng cùng chia sẻ chung một trang nhớ (page), nên phép trượt bit `B >> 12` nghiễm nhiên bằng `t`. Khi hệ thống cấp phát bộ nhớ (gọi `tcache_get`), quá trình giải mã (unmangle) được thực thi: `(B>>12) ^ (t ^ 0x404060) = 0x404060`. Hệ thống bị dắt mũi, trỏ cái móc tiếp theo của bin thẳng vào vòm họng của exit@GOT.

**Bước 3 - Bơm hai mũi cấp phát để chộp con trỏ máu.** 
Ra đòn `add(2)` để móc khối B ra khỏi bin, tung cú chốt hạ `add(3)` ép hệ thống bốc luôn cái địa chỉ `0x404060` ra ngoài → Hệ quả là biến `notes[3]` bị gán cứng vào địa chỉ `exit@GOT`. 
Để tự tin, gọi lệnh `view(3)` kiểm tra lại: Trong 80 byte nôn ra, có chứa hằng số `0x7f91ca0054c0` / `0x7f91ca0048e0` (bản đồ địa chỉ của stdout/stdin) và các mốc `0x4062b0` / `0x406310` (nhà riêng của notes[0], notes[1]) khớp khít từng ly với thiết kế của vùng BSS.

**Bước 4 - Tráo linh hồn `audit` vào xác `exit@GOT` và ấn nút phát nổ.**

```python
edit(3, p64(0x4012b6))     # Hàm đọc read() cực kỳ ngoan, chỉ hút đúng số byte được nhả ra -> Bảo chứng chỉ có 8 byte bị đè bẹp.
shutdown(SHUT_WR)          # Chặt đứt đường truyền của Socket: Hàm lấy chuỗi fgets(stdin) của menu bị vấp trả về NULL -> tự động gọi exit(0) -> mà xác exit giờ đã bị tráo hồn thành lệnh nhảy jmp audit.
```

Chiêu bài đóng (shutdown) luồng ghi của socket là một đòn chí mạng. Cú đánh này làm hàm đọc `fgets` sụp đổ (báo lỗi NULL), đẩy guồng xoáy menu văng tự do vào hàm `exit`. Và như ta đã cài cắm, lệnh `exit` giờ đây chính là lệnh khởi động `0x4012b6` (tức là `audit`).

## Phục dựng (Reproduce)

```bash
python -u exploit.py pwn.h7tex.com 42589
```

Bản mã `exploit.py` thuần chủng, chỉ sài bộ thư viện có sẵn `socket` + `struct`. Mã tự hành từ A tới Z mà chẳng cần ngửa tay xin bất cứ leak nào của thư viện libc.

## Flag
```text
[audit] H7CTF{4d0e9693-88bd-4749-87d8-c64dd2ef80ab}
```
