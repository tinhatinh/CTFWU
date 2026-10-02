# Print Print Revolution — Pwn (Hard)

**Flag:** `sun{cust0m_fmtstr_n0_t00ls_4ll0wed}`
**Files:** `revolution`, 14520 byte, sha256 `918483831ef0b27d0cfb8afa9e0341f38d0a296931ccc5f73ef80f5d610f8fa5`
**Dịch vụ:** `nc chal.sunshinectf.games 26002`

## Đề bài

Nhiệm vụ của thử thách là phân tích hệ thống kết xuất (renderer) tuỳ chỉnh của máy in điểm để truy xuất cờ. Đề bài không cung cấp thư viện `libc`, yêu cầu người chơi phải trích xuất mọi thông tin cần thiết trực tiếp từ dịch vụ đang chạy bằng các phương pháp thủ công, nghiêm cấm sử dụng các công cụ tự động như pwntools hay ROPgadget.

## Phân tích ban đầu

Tệp thực thi là một ELF 64-bit ở định dạng `ET_EXEC` (không bật PIE, có địa chỉ cơ sở cố định tại `0x400000`), đã bị loại bỏ thông tin gỡ lỗi (stripped), và phân vùng mã nguồn `.text` vô cùng nhỏ gọn với kích thước chỉ 0x4ea byte.
Chương trình chỉ nhập khẩu (import) đúng năm hàm hệ thống: `write`, `strlen`, `strcspn`, `read`, và `setvbuf`. Đáng chú ý là sự vắng mặt hoàn toàn của các hàm mở tệp như `open` hay `fopen`, đồng nghĩa với việc binary không có khả năng tự thân đọc file. Do đó, để truy xuất nội dung tệp `/ctf/flag.txt`, giải pháp duy nhất là phải thực thi một chuỗi ROP (ROP chain) nhằm gọi lệnh `execve`.

Vòng lặp chính của chương trình nằm tại địa chỉ `0x4010d0`:
```asm
lea    rbx, [rsp]           ; buf = rsp của hàm main, cấp phát 512 byte
sub    rsp, 0x200
loop:  write(1,"score> ",7)
       read(0, rbx, 0x1ff)  ; rax lưu số lượng byte đọc được
       mov  rsi, rbp        ; ký tự "\n"
       mov  rdi, rbx
       mov  [rsp+rax], 0
       call strcspn@plt     ; -> rax trả về độ dài của dòng
       xor  eax, eax
       call 0x401330        ; RENDERER(rdi = buf)
       write(1,"\n",1)
       jmp  loop
```

Hàm tại `0x401330` không phải là hàm `printf` tiêu chuẩn của hệ thống, mà là một cơ chế tự xây dựng `va_list` giả mạo ngay trên bộ nhớ stack:
```asm
mov [rsp+0x38], rsi ; [rsp+0x40], rdx ; [rsp+0x48], rcx ; [rsp+0x50], r8 ; [rsp+0x58], r9
mov [rsp+0x18], 8   ; biến gp_offset
mov [rsp+0x1c], 0x30 ; biến fp_offset
lea rax,[rsp+0x120]; mov [rsp+0x20], rax ; vùng overflow_arg_area = rsp+0x120
lea rax,[rsp+0x30];  mov [rsp+0x28], rax ; vùng reg_save_area = rsp+0x30
```

Một chi tiết mấu chốt là vùng `rsp+0x120` của renderer trỏ chính xác vào vùng đệm `buf` (do renderer cách hàm main đúng bằng 6 lần gọi `push` + 8 byte return address + phép trừ `sub 0xe8`, tổng cộng là 0x128 byte). Hệ quả là, từ tham số thứ 6 trở đi, dữ liệu sẽ được đọc trực tiếp từ chính vùng input của người dùng.

## Chuỗi khai thác

**Bước 1 - Trích xuất tập luật (grammar) của renderer.**
Bằng cách phân tích nhánh lệnh so sánh nằm trong khoảng `0x4013e8..0x401524`, ta nhận diện được bốn đặc tả (format specifier) với các tính năng sau:

| Đặc tả | Hành vi | Khả năng khai thác (Primitive) |
|---|---|---|
| `%%` | In ra ký tự `%` | Không áp dụng |
| `%<n>$s` | Thực thi `write(1, (char*)arg[n], strlen(arg[n]))` | Cho phép đọc vùng nhớ tuỳ ý |
| `%<n>$p` / `%<n>$x` | In giá trị dạng `0x%016lx` của biến `arg[n]` | Cho phép làm rò rỉ (leak) dữ liệu tuỳ ý |
| `%<n>$w` | Thực hiện phép gán `*arg[n] = arg[n+1]`, in ra chữ `ok` | Cho phép ghi 8 byte tuỳ ý vào vùng nhớ |

Với quy luật ánh xạ `arg[6+k] = buf[8k]`. Khác với tiêu chuẩn, hàm `va_arg` tại `0x4012c0` nạp danh sách biến `ap` bằng lệnh `movdqu` (tạo một bản sao cục bộ) và chỉ cập nhật độ lệch (offset) trên bản sao đó chứ không hề ghi ngược trở lại bộ nhớ. Điều này khiến cho renderer mang đặc tính phi trạng thái (stateless). Do vậy, cú pháp đặc tả `%8$w` sẽ lập tức lấy cặp tham số nằm liền kề nhau (arg8 và arg9), thay vì dịch chuyển con trỏ một cách tuần tự đến (arg8 và arg17) như cơ chế của hàm `printf` thông thường.

Khảo sát vị trí `buf`: Tham số `arg70` tương ứng với `buf[0x200]`, đây chính là vị trí mà thanh ghi `rbx` được đẩy (push) vào stack, tạo điều kiện thuận lợi để làm rò rỉ địa chỉ bộ đệm bằng chuỗi `%70$p`. Xa hơn, tham số `arg119` chứa cấu trúc `AT_SYSINFO_EHDR` của `auxv`, đóng vai trò là cầu nối để rò rỉ địa chỉ không gian vDSO.

**Bước 2 - Ghi đè bảng GOT.**
Dù chương trình có kích hoạt cơ chế bảo vệ `PT_GNU_RELRO` tại khoảng địa chỉ `[0x403dc0, 0x404000)`, thực tế các khe (slot) PLT lại bắt đầu ở ngoài vùng này, từ địa chỉ `0x404000`:
```
write=0x404000 strlen=0x404008 strcspn=0x404010 read=0x404018 setvbuf=0x404020
```
Các ô nhớ này hiện vẫn đang ở trạng thái mồi (lazy stub - dạng `0x401030`...), và cờ bảo vệ `BIND_NOW` hoàn toàn không được bật. Từ đó khẳng định vùng GOT có thể bị ghi đè thành công.

**Bước 3 - Tìm gadget `syscall` mà không cần thư viện libc.**
Tiến hành đọc GOT entry của hàm `write` để thu thập địa chỉ `write` chính xác bên trong libc. Bằng cách trích xuất từng byte trên 0x40 byte bộ nhớ liền kề (thông qua đặc tả `%<n>$s`), ta sẽ phát hiện opcode của lệnh syscall `0f 05` nằm cố định tại vị trí `write+0x12`.

**Bước 4 - Trích xuất gadget thiết lập tham số từ vDSO.**
Nhờ khả năng rò rỉ, ta tìm được một gadget thiết lập thanh ghi vô cùng đắc lực từ không gian nhớ vDSO:
```
xor edx,edx ; xor ecx,ecx ; xor esi,esi ; xor edi,edi ;
xor r8d,r8d ; xor r9d,r9d ; xor r10d,r10d ; xor r11d,r11d ; ret
```
Gadget này toạ lạc tại vị trí `vdso+0xa14`. Điểm đặc biệt của nó là không chứa lệnh `xor eax, eax`, nhờ vậy giá trị của thanh ghi `rax` được bảo toàn nguyên vẹn xuyên suốt quá trình thiết lập.

**Bước 5 - Thiết lập mã lệnh syscall.**
Tại vị trí `call strcspn@plt` (`0x40112a`), thanh ghi `rax` luôn lưu trữ số lượng byte vừa được trả về từ hàm `read()`. Do đó, chiều dài của chuỗi đầu vào chính là giá trị của mã lệnh syscall. Bằng cách điều hướng input có độ dài chính xác là 59 byte, ta sẽ thiết lập được `rax = 59` (tương ứng với lệnh `execve`).

**Bước 6 - Xây dựng chuỗi ROP hoàn chỉnh.**
Tiến hành ghi đè `strcspn@GOT` thành lệnh `pop rdi; ret` (địa chỉ `0x4014a1`). Cấu trúc chuỗi ROP được thiết lập tại `buf[0]` như sau:
```
buf[0x00] = vdso+0xa14     ; dọn dẹp các thanh ghi: rsi = rdx = 0, bảo toàn rax = 59
buf[0x08] = 0x4014a1       ; lệnh pop rdi; ret
buf[0x10] = buf+0x100      ; trỏ rdi về chuỗi "/bin/sh"
buf[0x18] = write+0x12     ; kích hoạt lệnh syscall -> dẫn đến gọi execve("/bin/sh", NULL, NULL)
buf[0x20] = 0x40114f       ; phương án dự phòng (fallback) nếu execve thất bại
```
Tổng cộng chuỗi trên chiếm chính xác 59 byte. Chuỗi `/bin/sh` đã được chủ động bơm vào từ một request ngay trước đó (dùng `%<n>$w` ghi vào vị trí `buf+0x100`). Vì byte null đầu tiên (bắt buộc phải có để ngắt chuỗi) nằm ngoài phạm vi 5 khe (slot), nên renderer không bao giờ có cơ hội thực thi mã độc hại - lệnh syscall sẽ được kích hoạt sớm hơn nhiều, ngay từ bên trong nội bộ hàm `strcspn`.

**Bước 7 - Xác thực tính đúng đắn.**
Để đảm bảo mọi thông số đều chính xác trước khi bung exploit, ta sử dụng một phép thử bằng cách thay thế vị trí `buf[0x18]` bằng `0x40114f` (phương án này loại bỏ lệnh syscall thực sự). Kết quả thu được từ luồng xử lý này là chuỗi `score>` in ra bình thường, minh chứng cho việc điều khiển luồng thực thi (control flow) hoàn toàn chính xác. Payload khai thác mở shell thành công khi server ngừng trả lời chuỗi nhắc lệnh và bắt đầu tiếp nhận trực tiếp các lệnh hệ thống từ luồng stdin.

## Flag
```bash
python exploit.py
```

```text
[*] buf=0x7fffd0f0b0a8  vdso=0x7ae9f6832000  write=0x7ae9f6732560  syscall=0x7ae9f6732572
[*] ghi GOT + duong dan: 2 x 'ok'
[>] cat /ctf/flag.txt -> sun{cust0m_fmtstr_n0_t00ls_4ll0wed}
[+] CO: sun{cust0m_fmtstr_n0_t00ls_4ll0wed}
```
