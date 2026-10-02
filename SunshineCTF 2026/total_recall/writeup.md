# Total Recall — Pwn (Medium)

**Flag:** `sun{r3caLl_ev3Ry_reGist3r_sR0p}`
**Tác giả:** Oreomeister
**Target:** `nc chal.sunshinectf.games 26003` · **Files:** `total_recall`

## Đề bài

> `Can you recall how to get out of this one?`

Đề bài chỉ cung cấp duy nhất một câu hỏi gợi mở như trên: không hề có bất kỳ gợi ý (hint) kỹ thuật nào, không đính kèm thư viện `libc`, và cũng không có script tham khảo. Toàn bộ các kết luận khai thác dưới đây đều được đúc kết hoàn toàn từ quá trình dịch ngược trực tiếp binary.

## Phân tích ban đầu

Kiểm tra thông số cơ bản của tệp thực thi:
```text
Kiểu tệp: EXEC (không bật PIE), liên kết tĩnh (statically linked), loại bỏ symbol (stripped), entry point tại 0x401000
phnum = 2: LOAD 0x400000 R (0xb0) | LOAD 0x401000 R+X (0x6c)
Hoàn toàn không có PT_GNU_STACK
```

Định dạng `Type: EXEC` cho thấy chương trình không sử dụng cơ chế PIE, do đó mọi địa chỉ mã lệnh (code segment) đều là các hằng số cố định, loại bỏ gánh nặng phải làm rò rỉ (leak) địa chỉ. Thú vị hơn, toàn bộ chương trình cực kỳ siêu nhỏ, chỉ vọn vẹn 108 byte (`analysis/disasm.txt`):

```asm
401000  call f1
401005  call f2
40100a  mov rax,60 ; xor rdi,rdi ; syscall                          exit(0)

401016  push rsp                                                    f1: leak
        mov rsi,rsp ; mov rdi,1 ; mov rdx,8 ; mov rax,1 ; syscall   write(1, rsp, 8)
401031  pop rax
401032  lea rsi,[rsp-0x40] ; mov rdi,0 ; mov rdx,0x18 ; mov rax,0 ; syscall   read(0, rsp-0x40, 24)
40104e  ret

40104f  lea rsi,[rsp-0x80] ; mov rdi,0 ; mov rdx,0x400 ; mov rax,0 ; syscall  read(0, rsp-0x80, 1024)
40106b  ret
```

Chỉ với 108 byte mã lệnh, ta có thể rút ra 4 kết luận sắc bén:

1. Phép làm rò rỉ (leak) diễn ra trực tiếp qua hàm `write` lấy `rsi = rsp` ngay sau khi gọi `push rsp`. Điều này làm rò rỉ thẳng thừng một con trỏ ngăn xếp (stack pointer) định dạng little-endian, không bị pha lẫn các chuỗi văn bản rườm rà.
2. Hàm `f2` cho phép đọc tới 1024 byte vào vùng `rsp-0x80`, trong khi địa chỉ trả về (return address) lại nằm tại `rsp+0x80` (tương đương với khoảng cách offset 0x80 tính từ đầu buffer). Đây chính là một lỗi tràn bộ đệm (buffer overflow) kinh điển, ban tặng cho ta hẳn 1024 byte để tuỳ ý nhào nặn.
3. Hàm `read` không bị cản trở bởi byte null `0x00`, nên ta có thể bơm bất kỳ mã nhị phân (payload) nào vào vùng nhớ.
4. Điều tối quan trọng: lệnh `read` sẽ trả về số lượng byte thực tế đọc được vào thanh ghi `rax`. Kết hợp với việc binary có sẵn một đoạn `syscall; ret` trần trụi, đây chính là cửa thoát hiểm hoàn hảo cho một cuộc tấn công Sigreturn Oriented Programming (SROP).

## Chuỗi khai thác

### Bước 1 - Đo đạc hình học stack (Stack Geometry) bằng ROP

Việc xác định `RET_OFF = 0x80` và điểm kết thúc lệnh `ret` của `f2` bỏ lại `rsp = buf+0x88` được chứng minh thông qua một chuỗi thực thi nhỏ chỉ sử dụng hai gadget sẵn có (`analysis/probe_exec.py`, `analysis/walk_leak.py`).

Tuy nhiên, do mọi điểm rò rỉ đều đi qua lệnh `push rsp`, sai số 8 byte của bộ đệm không thể bị phát hiện nếu chỉ nhìn vào dữ liệu rò rỉ. Phép đo tinh vi hơn được sử dụng ở đây (`analysis/measure_rsp.py`): cài cắm vào mỗi ô của khung (frame) một lính gác (sentinel) dạng `buf+0x300+j`, sau đó điều hướng sigframe nhảy ngược về `0x401000`. Khi chương trình khởi động lại, nó sẽ làm lộ ra `rsp - 16`, và con số thu về khớp chính xác với ô `0xA0`. Suy ngược logic, ta xác nhận được độ lệch `delta` phải là **`buf = L - 0x80`**.

Ngoài ra còn một cách kiểm chứng độc lập khác không cần đến sigreturn: gadget tại `0x401032` nuốt input đầu vào và tự động đẩy `rsp` lên 8 byte sau mỗi vòng. Nếu gọi vòng lặp này `k` lần rồi phi thẳng vào `0x401017`, ta sẽ làm rò rỉ chính xác vị trí `buf+0x88+8k`. Cả năm giá trị thử nghiệm đều khớp hoàn toàn với thực tế.

### Bước 2 - Dùng `read` điều khiển `__NR_rt_sigreturn` qua `rax`

Binary có sẵn một lệnh `syscall; ret` trần tại `0x40104c` và `0x401069` (luồng nhảy ngay sau khi chuỗi gán `mov rax,0` hoạt động). Gadget tại `0x401032` kích hoạt `read(0, rsp-0x40, 24)` và bỏ lại số lượng byte đọc được trong thanh ghi `rax`. Lợi dụng đặc điểm này, ta chỉ cần gửi đi chính xác 15 byte, thanh ghi `rax` sẽ lập tức chứa giá trị 15:

```asm
[buf+0x80] = 0x401032   gọi read(0, buf+0x48, 24) -> thiết lập rax = 15, ret
[buf+0x88] = 0x401069   gọi syscall               -> chuyển thành rt_sigreturn, nhận diện frame tại [rsp] = buf+0x90
```

Ngay tại thời khắc kích hoạt syscall, `rsp` đang trỏ đúng vào ô `buf+0x90`, do đó sigframe bắt buộc phải được đặt liền kề tại vị trí này.

### Bước 3 - Thi công Sigframe

Trong nhân (kernel) hệ thống trên máy chủ, việc đọc cấu trúc `ucontext` diễn ra bắt đầu ngay tại vị trí `rsp` (không có khoảng đệm 128 byte `siginfo` đứng trước). Vì vậy, khối `sigcontext` thực sự sẽ toạ lạc ở `frame+0x28`:

```text
frame+0x68 rdi    frame+0x70 rsi    frame+0x88 rdx    frame+0x90 rax = 59 (mã syscall execve)
frame+0xA0 rsp    frame+0xA8 rip    frame+0xB0 eflags = 0x246
frame+0xB8 cs=0x33, gs=0, fs=0, ss=0x2b               frame+0xD8 fpstate = 0
```

Với cấu hình `rip = 0x401069`: ngay sau khi tiến trình sigreturn trả lại toàn bộ ngữ cảnh, lệnh `syscall` sẽ được kích hoạt lại. Nhưng lần này, thanh ghi `rax` mang giá trị 59, có nghĩa là hệ thống sẽ thi hành `execve(rdi, rsi, rdx)`. Đồng thời, `rsp` sẽ trỏ vào ô `buf+0x78` mang giá trị `0x401000`. Ô này hoạt động như một con bài chẩn đoán: nếu lệnh `execve` thất bại, lệnh `ret` cuối cùng của `f2` sẽ lập tức nhảy về đó, khiến chương trình tái khởi động (và ta nhận thêm 8 byte leak). Ngược lại, nếu mọi thứ chìm vào tĩnh lặng, lệnh `execve` đã khai hoả thành công.

Cách dàn xếp bộ đệm, mọi thứ đều nằm gọn trong phạm vi 512 byte đầu tiên (khoảng `buf+0x40..0x57` bị hai lệnh `read` ghi đè nên phải để trống cố ý):

```text
0x00  argv = { &"/bin/sh", NULL }
0x20  chuỗi "/bin/sh"
0x78  0x401000                        <- con trỏ rsp sau sigreturn, dùng làm mồi chẩn đoán
0x80  0x401032      0x88  0x401069
0x90  khối dữ liệu sigframe
```

### Bước 4 - Chốt hạ từng thanh ghi trước khi tung lệnh execve

Script `analysis/probe_args.py` đóng vai trò nhảy can thiệp vào giữa chuỗi `write` của hàm `f1`. Tại khoảnh khắc đó, giá trị các thanh ghi `rsi`/`rdi`/`rdx`/`rax` **chỉ có thể xuất phát từ sigframe**:

```text
0x401017 -> 8 byte    (rsi = rsp)
0x401021 -> 8 byte    (nạp thêm rdi, rsi từ frame)
0x401028 -> 24 byte   (nạp thêm rdx từ frame)
0x401069 -> 24 byte   (nạp thêm rax từ frame)  <== Toàn quyền kiểm soát một syscall tuỳ ý
```

Cả hệ thống bậc thang này đều đo đạc thành công và khớp hoàn hảo, xác nhận khung (frame) đã được hệ thống nạp đầy đủ. Sau đó, công cụ `analysis/probe_syscall_allow.py` sẽ sử dụng chính cơ chế nhảy chẩn đoán để kiểm tra xem hệ thống cho phép gọi những syscall nào trước khi bung payload.

## Flag
```
sun{r3caLl_ev3Ry_reGist3r_sR0p}
```

Cờ được giấu tại đường dẫn `/ctf/flag.txt` (dài 32 byte, phân quyền nhóm `root:total_recall`, chế độ cấp phép `-rw-r-----`). Luồng shell ta cướp được chạy dưới đặc quyền cho phép đọc trực tiếp tệp tin này.

## Phục dựng (Reproduce)

```bash
python exploit.py                              # Chạy mặc định: cat /ctf/flag.txt + ls -la /ctf /home
python exploit.py 'id' 'cat /ctf/flag.txt'     # Mỗi đối số argv là một lệnh, thực thi tuần tự
python analysis/probe_args.py                  # Công cụ bậc thang kiểm tra từng thanh ghi của sigframe
python analysis/measure_rsp.py                 # Công cụ đo đạc lại sai số delta buf = L - 0x80
```

Script `exploit.py` chỉ phụ thuộc vào thư viện chuẩn (stdlib), tự động kết nối và làm rò rỉ base lại ở mỗi vòng đời; bên cạnh các gadget nguyên bản của binary thì hoàn toàn không hardcode bất cứ địa chỉ nào. Tệp `analysis/disasm.txt` chứa trọn vẹn bản dịch ngược 108 byte mã lệnh.
