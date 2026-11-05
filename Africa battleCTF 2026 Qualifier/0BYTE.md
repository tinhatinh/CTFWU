---
title: "0byte"
category: "RE"
tags: ["reverse-engineering", "pe-binary", "anti-debug", "downloader", "pext", "pdep", "elf-emulation"]
solve_date: "2026-10-07T09:44:00+07:00"
language: "vi"
points: 50
---

# 0byte — PE downloader và giả lập pext/pdep

**Flag:** battleCTF{DespairEnergy} · **Files:** 0byte.exe, 848 384 byte, SHA-256 535436a0403739ae8616755cd67e742fdcb135d0b9df3326ac3f97dc3bb005c4

## Đề bài

Challenge 50 điểm trong nhóm “out context” trên ctf.bugpwn.com, format flag battleCTF{....}. File duy nhất là 0byte.zip (AES-256, password infected), bên trong có 0byte.exe. Thẻ challenge không có gợi ý nào khác.

## Phân tích

```text
0byte.exe: PE32+ executable (console) x86-64, for MS Windows
entry 0x4014e0 · .text 0x401000+0xa1cd0 · .data 0x4a3000 · .rdata 0x4a7000
```

Chạy chương trình trong console sẽ vẽ bàn snake và in hướng dẫn:

```text
######################
# F                  #
#          O         #
######################
Score: 0

Use 'W', 'A', 'S', 'D' to move the snake, 'X' to quit
```

Quan sát từ .rdata:

```text
0x4a7060  'Downloader'        0x4a7074  'Failed.'
0x4a707c  'CreateProcess failed: '      0x4a7160  'Banned'
0x4a7157  'kami'               0x4a715c  'ami'
```

Import table chỉ tham chiếu KERNEL32, msvcrt và WININET (InternetOpenA, InternetOpenUrlA, InternetReadFile, InternetCloseHandle), cùng IsDebuggerPresent. Không có import registry. Nhận định ban đầu: đây là game shell bọc quanh **downloader có anti-debug**, còn 'kami'/'ami' nhiều khả năng là khóa giải mã chứ không phải chuỗi hiển thị.

## Các hướng đã thử

1. **Steganography bằng zero-width character trong mô tả challenge:** kiểm tra U+200B/200C/200D/FEFF/2060 trên raw response /api/v1/challenges/<id>; không có ký tự ẩn. Dữ liệu ẩn thực ra là chuỗi hex dẫn tới github.com/0xbugpwn/AfricabattleCTF2024/.../0byte.zip, tức nguồn artifact chứ không phải lời giải.
2. **Điểm snake mở khóa đáp án:** biến score ở 0x4d0390 chỉ tăng addl $0xa khi ăn food rồi đưa vào printf("Score: "). Nhánh download tại 0x4a245e không đọc biến này; guard chỉ kiểm tra hai string pointer khác null.
3. **Dùng plink/ssh tới host trong “PuTTY config”:** binary có chạy putty.exe, nhưng CreateProcessA nhận lpApplicationName = NULL và lpCommandLine chỉ là path của .exe vừa tải — không có -load, hostname hay registry. Lệnh này không cung cấp host hoặc PuTTY session đã lưu.
4. **Thử XOR / UTF-16 / length-prefix trên payload 9 016 byte:** blob có 93% byte 0, không có chuỗi ASCII dài hơn 4 ký tự; mọi thử nghiệm single-byte và repeating-key đều thất bại. Nguyên nhân thật là đọc nhầm encoding (xem Bước 3), không phải dữ liệu không giải mã được.

## Lời giải

**Bước 1 — Vượt anti-debug và bắt URL thật.** 0x4a2330 gọi IsDebuggerPresent qua IAT slot 0x4d25e8; nếu eax khác 0 thì branch ở 0x4a249f in Banned rồi thoát. Đặt breakpoint **sau** lệnh gọi và ép eax về 0:
 
```gdb
break *0x4a2336
commands
  set $eax = 0
  continue
end
break *0x4016d8        # call *InternetOpenUrlA
commands
  x/s $rdx
  continue
end
```
```text
HIT-URL
0x8316b0:     "https://bugpwn.com/drop.ini"
HIT-PATH
0x831700:     "C:\\Users\\ADMINI~1\\AppData\\Local\\Temp\\08914b150cdd6888bf32d668c9336169.ini"
HIT-URL
0x831980:     "https://the.earth.li/~sgtatham/putty/latest/w32/putty.exe"
HIT-PATH
0x835f30:     "C:\\Users\\ADMINI~1\\AppData\\Local\\Temp\\08914b150cdd6888bf32d668c9336169.exe"
```

Tên file được tạo theo MD5; putty.exe ở đây là PuTTY thật tải từ the.earth.li, nên phần cần tìm nằm trong drop.ini.

**Bước 2 — Cơ chế “0 byte”.** Bốn string (URL và file path) không xuất hiện nguyên văn trong file. Trong .data tại 0x4a3020, 0x4a30c0, 0x4a31c0 và một mảng 27 phần tử trên stack, mỗi ký tự được lưu trong một dword: 1e 00 00 00 0c 00 00 00 13 00 00 00... — ba byte 0 cho mỗi byte dữ liệu. Có hai routine dựng string:

- 0x401cf0 đọc dword với stride 4: ebp = movzbl [rsi]; ebp ^= i; ebp -= 5 → A[i] = ((v[i] ^ i) - 5) & 0xff.
- 0x401dd0 trộn key bằng phép modulo: divq [rsp+0x38] rồi xor (%rax,%rbx,1),%bpl → out[i] = A[i] ^ key[i % len(key)].

Key lấy từ .rdata: 0x402660 gán "kami" cho mảng đầu, "ami" cho ba mảng còn lại. Kiểm tra cho thấy mảng 27 dword giải mã chính xác thành https://bugpwn.com/drop.ini, khớp URL bắt được ở Bước 1.

**Bước 3 — Giải mã drop.ini.** Chuỗi 912 byte được mở theo chuỗi base64 → gzip → pickle (PROTO 4, FRAME, BINBYTES8 dài 18 032). Payload pickle là chuỗi hex. Decode theo chiều xuôi ra 9 016 byte vô nghĩa. Hãy nhìn **8 ký tự cuối**:
 
```text
...010102064C454F7
```

64C454F7 là 7f454c46 đảo ngược — ELF magic. Chuỗi hex bị **đảo ngược hoàn toàn**, vì vậy cách giải đúng:
 
```python
elf = bytes.fromhex(hexstr[::-1])
```

Kết quả là static ELF64 9 016 byte:
 
```text
Type: EXEC · Machine: x86-64 · entry 0x401000 · 3 program headers · 7 sections
.text 0x401000 size 0x1ec · .data 0x402000 size 0x17 · .bss 0x402018 size 0x18
symtab: flag.asm, mask (0x402000), message (0x402008), msg_len = 0xf, output (0x402018), _start
```

.data chứa qword mask = 0xb0bababa và chuỗi Here We Go...!\n.

**Bước 4 — Cơ chế pext/pdep và lý do phải emulation.** .text dài 492 byte, là code thẳng không có loop: 16 cặp mov ebx, imm32 + pext rcx, rbx, rax; mỗi kết quả ghi thành một byte vào .bss, sau đó:
 
```asm
4011c7: mov eax, 0x1          ; SYS_write
4011d1: movabs rsi, 0x402008  ; message, NOT output
4011db: mov edx, 0xf          ; msg_len = 15
4011e0: syscall
4011e2: mov eax, 0x3c         ; SYS_exit
```

Binary chỉ in Here We Go...!\n; flag được tính vào 0x402018 nhưng **không bao giờ được ghi ra output**. Chạy chương trình không hiện thêm gì. Cần giả lập instruction để khôi phục buffer; có thể dùng debugger đọc memory trước khi process thoát.

Thứ tự operand rất quan trọng. Cú pháp Intel PEXT dest, src1, src2: src1 là **value**, src2 là **control**. Trong pext rcx, rbx, rax, rbx giữ immediate (ví dụ 0x890...) còn rax giữ qword mask. Nếu coi immediate là mask chỉ ra byte không in được (\x0f\x04\x00X[G...); cách đúng là value = imm, control = 0xb0bababa:
 
```python
def pext(value, control):
    res = j = 0
    for i in range(64):
        if (control >> i) & 1:
            if (value >> i) & 1:
                res |= 1 << j
            j += 1
    return res
```

Các phép biến đổi còn lại đọc trực tiếp từ machine code: st8(0x402020, ld64(0x40201f) ^ 0x12), st8(0x40202f, 0x3b ^ ld64(0x402020)), pdep(rdx, 0x62) + 5, popcnt(0x1337) + 0x3d và byte hằng 0x6e.

**Bước 5 — Chạy và xác minh.**
 
```bash
python exploit.py drop.ini
```
```text
drop.ini        : 912 byte
ELF recovered   : 9016 byte, magic 7f454c46, machine 0x3e, entry 0x401000
.data mask      : 0xb0bababa
.data message   : b'Here We Go...!\n'
output (.bss)    : b'battleCTF{DespairEnergy}'
all printable   : True
flag            : battleCTF{DespairEnergy}
```

Kiểm tra: chuỗi đúng 24 byte, khớp kích thước .bss (output 0x402018.._end 0x402030); cả 24/24 byte in được; bắt đầu bằng battleCTF{ theo yêu cầu và kết thúc bằng }; mọi thứ được tính từ input duy nhất là drop.ini, không hardcode flag vào script.

## Kết quả

```text
battleCTF{DespairEnergy}
```

Đã nộp trên ctf.bugpwn.com và được chấp nhận.

## Tái hiện

```bash
cd "0byte"
python exploit.py drop.ini          # base64 -> gzip -> pickle -> hex reversed -> ELF -> emulate
```

Tự tải drop.ini từ challenge server:
 
```bash
curl -sSL -o drop.ini https://bugpwn.com/drop.ini
```

Để bắt lại URL và file path runtime (cần gdb và binary phải đi tới downloader branch):
 
```bash
gdb -batch -nx -x capture.gdb ./0byte.exe
```

0byte.exe là Windows PE; phần emulation trong exploit.py thuần Python nên chạy được trên mọi nền tảng, không cần Windows và không cần thực thi binary.
