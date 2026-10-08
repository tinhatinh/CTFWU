# Loose Ends - Pwn (Hard)

**Flag:** `H7CTF{4d0e9693-88bd-4749-87d8-c64dd2ef80ab}`
**Máy chủ mục tiêu:** `pwn.h7tex.com:42589`
**File cung cấp:** `ledger.zip` (chứa binary `ledger` định dạng ELF x86-64, thư viện `libc.so.6` phiên bản glibc 2.39-0ubuntu8.9, và bộ nạp `ld-linux-x86-64.so.2`).

## Đề bài

Đề mô phỏng hệ thống sổ cái (ledger) của công ty Sparrow Freight. Hệ thống có lỗi bảo mật trong việc quản lý bộ nhớ: các bản ghi bị xoá bỏ (free) không được xử lý bộ nhớ đầy đủ. Cùng lúc, hệ thống chứa tính năng kiểm toán (audit) cho phép đọc mã thông hành (flag) trong ngày, nhưng tính năng này bị cô lập và không được kết nối.
Nhiệm vụ là lợi dụng thiếu sót bộ nhớ, liên kết các thành phần để kích hoạt chức năng ẩn và trích xuất cờ.

## Phân tích

Đánh giá cơ chế bảo mật của file:
```text
Cấu trúc ET_EXEC không bật PIE | Cờ báo NX được kích hoạt (cấm thực thi trên ngăn xếp) | Có tích hợp Canary bảo vệ (trong các hàm menu/idx/audit).
Bảo vệ GNU_RELRO kích hoạt một phần, chỉ bảo vệ 0x403df8..0x404000  ->  Toàn bộ các slot JUMP_SLOT dạt vào vùng 0x404000..0x404060 vẫn ở chế độ cho phép ghi.
```

Hàm `main` thiết kế một menu gồm 4 chức năng, quản lý qua một mảng con trỏ toàn cục:

```c
Mảng notes[16] đặt tại vùng 0x4040a0
Lệnh add    : Khởi tạo notes[i] = malloc(0x50); Cho phép read(0, notes[i], 0x50).
Lệnh delete : Gọi free(notes[i]).                      <- Lỗ hổng: Không xử lý gán notes[i] = NULL sau khi free.
Lệnh edit   : Cắm cờ if (notes[i]), sau đó nạp read(0, notes[i], 0x50).
Lệnh view   : Cắm cờ if (notes[i]), in ra write(1, notes[i], 0x50).
```

Do hàm `delete` không vô hiệu hóa con trỏ sau khi giải phóng (free), và các lệnh `edit` cùng `view` chỉ kiểm tra giá trị con trỏ khác 0, hệ thống tồn tại lỗ hổng Use-After-Free (UAF). Lỗ hổng này cho phép người dùng thao tác đọc (view) và ghi (edit) trên vùng nhớ đã giải phóng.

Hàm `audit` nằm ở địa chỉ `0x4012b6`. Hàm này mở file `/flag`, đọc 80 byte dữ liệu và in ra dòng chữ `printf("[audit] %s\n", ...)`. Tuy nhiên, lệnh này không được liệt kê trong bảng chọn (jump table), yêu cầu kỹ thuật điều hướng luồng thực thi (jump) để kích hoạt.

Hai yếu tố giúp việc khai thác thuận lợi hơn: Bộ nhớ Heap tĩnh, không bị ngẫu nhiên hoá (no ASLR trên heap) - khối cấp phát đầu tiên mặc định chốt tại `0x4062b0`, kề vùng BSS. RELRO bị vô hiệu hóa ở `0x404000`, cho phép ghi đè lên phân đoạn PLT (GOT). Việc PIE bị tắt đồng nghĩa các địa chỉ đều là hằng số cố định, loại bỏ thao tác phức tạp liên quan đến rò rỉ (leak) bộ nhớ.

## Lời giải

**Bước 1 - Khai thác cơ chế mã hoá safe-linking để rò rỉ `heap >> 12`.**
Từ glibc 2.32, tcache áp dụng thuật toán mã hoá con trỏ: `giá trị_lưu (stored) = (vị trí_hiện_tại (pos) >> 12) ^ giá trị_thực (real)`.
Bản chất: Khi gọi lệnh `free(A)` (với A là phần tử cuối của tcache bin), con trỏ tiếp theo trỏ về `NULL` (`real = NULL`). Suy ra: 8 byte mào đầu của khối A chứa giá trị trượt bit `A >> 12`.

```text
Quy trình: add(0); add(1); delete(0); view(0)   ->  Đọc 8 byte đầu = 06 04 00 ...  =>  Quy nạp ra t = 0x406.
```

**Bước 2 - Ghi đè (Poisoning) con trỏ Forward (fd).**
Triển khai `delete(1)`, khối dữ liệu B được đẩy lên đỉnh của bin (tcache). Lợi dụng UAF, sử dụng lệnh `edit(1)` để ghi đè lên con trỏ `B->next`:

```python
edit(1, p64(t ^ 0x404060))     # Địa chỉ mục tiêu 0x404060 là vị trí của lệnh exit@GOT
```

Do khối B và A chia sẻ chung một trang nhớ (page), phép trượt bit `B >> 12` có giá trị `t`. Khi hệ thống cấp phát bộ nhớ (`tcache_get`), quá trình giải mã (unmangle) hoạt động: `(B>>12) ^ (t ^ 0x404060) = 0x404060`. Hệ thống bị điều hướng, trỏ con trỏ tiếp theo của bin vào vị trí của exit@GOT.

**Bước 3 - Thực hiện hai thao tác cấp phát để trích xuất con trỏ.**
Gọi `add(2)` để lấy khối B ra khỏi bin, tiếp tục `add(3)` để hệ thống gán bộ nhớ tại `0x404060` cho con trỏ mới → Biến `notes[3]` được gán trực tiếp vào địa chỉ `exit@GOT`.
Xác nhận bằng lệnh `view(3)`: Dữ liệu trả về chứa hằng số `0x7f91ca0054c0` / `0x7f91ca0048e0` (bản đồ bộ nhớ stdout/stdin) và các mốc `0x4062b0` / `0x406310` (nhà của notes[0], notes[1]) khớp chính xác với thiết kế của vùng BSS.

**Bước 4 - Thay đổi luồng thực thi của `exit@GOT` thành `audit` và kích hoạt.**

```python
edit(3, p64(0x4012b6))     # Hàm read() chỉ cập nhật đúng 8 byte dữ liệu cung cấp, tránh ghi đè lỗi.
shutdown(SHUT_WR)          # Đóng đường truyền Socket: Hàm fgets(stdin) của menu báo lỗi NULL -> tự động gọi exit(0) -> hệ thống thực thi lệnh nhảy jmp audit đã được sửa đổi.
```

Phương pháp ngắt (shutdown) luồng ghi socket là thao tác quan trọng. Điều này làm hàm đọc `fgets` trả về lỗi NULL, buộc hệ thống gọi hàm `exit`. Do đã ghi đè từ trước, hàm `exit` sẽ kích hoạt luồng `0x4012b6` (tức là `audit`).

## Tái hiện

```bash
python -u exploit.py pwn.h7tex.com 42589
```

Kịch bản `exploit.py` sử dụng thư viện cơ bản `socket` + `struct`. Mã thực thi tự động, không yêu cầu sử dụng chức năng lấy địa chỉ cấp phát từ thư viện libc.

## Kết quả
```text
[audit] H7CTF{4d0e9693-88bd-4749-87d8-c64dd2ef80ab}
```
