# Mad Libs — Pwn (Medium)

## Challenge

`Fill in the blanks! Our Mad Libs game prints back whatever you type. It's just a simple word game... right?`

Target `nc chal.sunshinectf.games 26001`, with `mad_libs`, `libc.so.6`, `ld-linux-x86-64.so.2` attached.
499 points, 38 solves, author Oreomeister.

## Initial Analysis

The binary is 14584 bytes, a 64-bit PIE ELF, stripped. Mitigations: PIE, NX, canary, partial RELRO
(no `BIND_NOW`), libc is Ubuntu glibc 2.39.

`main` sits at `0x11c9`, and disassembling it gives a single loop:

```c
for (i = 0; i <= 7; i++) {
    printf("(%d) > ", i + 1);
    if (fgets(buf, 0x100, stdin) == NULL) break;
    printf(buf);                  // <= format string
}
```

The buffer is at `[rbp-0x110]`, i.e. 272 bytes wide, while `fgets` only reads 256 bytes, so there is
no overflow and no reaching the return address. The program has one single primitive: `printf(buf)`
with `buf` entirely chosen by us, repeated 8 times.

`.rela.plt` gives the GOT positions, and because RELRO is only partial this region is writable:

```
0x4000 puts   0x4008 __stack_chk_fail   0x4010 printf   0x4018 fgets   0x4020 setvbuf
```

## Exploit Chain

### Step 1, locating the stack

Send `%1$p %2$p ...` and read it back. Slot 8 prints exactly the first 8 bytes of the very string we
sent (`0x2432252070243125` = `"%1$p %2$"`), meaning the varargs area begins right at the buffer: slot
`k` corresponds to `buf[8*(k-8)]`. So placing an address in `buf` immediately gives arbitrary
read/write through `%k$s` / `%k$hhn`.

Keep sweeping the slots above the buffer. Two consecutive sweeps give identical results, so they are
stable:

```
40 0x7fffa7bb40e0 (stack)   41 0x2ef1945964c7bb00 (canary)   42 0x7fffa7bb4160 (stack)
47 0x60de6e4031c9           52 0x60de6e405db8
```

The low 12 bits of slot 47 are `0x1c9`, matching `main` at `0x11c9` exactly. That is the pointer to
`main` left behind by `__libc_start_call_main`. So PIE base = slot 47 - 0x11c9, and the result is
always divisible by 0x1000, exactly the property a base must have.

### Step 2, leaking libc through the GOT itself

No need to guess which symbol sits at slot 1 (slots 1-7 are leftover register values, unstable
between runs). Instead use the GOT itself: `printf` was already called when the first prompt printed,
so `printf@GOT` has resolved to a real address inside libc.

Layout of the read string: the prefix must be exactly 8 bytes long so the address falls into
`buf[8:16]`, i.e. slot 9:

```
"%9$s" + "AAAA" + p64(base + 0x4010)
```

`%9$s` prints the 6 bytes of the pointer and then stops (the top 2 bytes are NUL).
`libc_base = ptr - 0x600f0`.

Before trusting that number, I planted a known answer as a check: read on from `libc_base + 0x1cb42f`
and require it to print exactly the string `/bin/sh`. If the base were wrong this step fails and the
exploit stops, instead of escalating on a meaningless address.

### Step 3, writing the GOT

In libc, `printf = 0x600f0` and `system = 0x58740`, `0x79b0` apart (under 16 MB). That means the top 3
bytes of the two addresses are identical, and the GOT already contains exactly the right top 3 bytes.
So only the low 3 bytes need to be written, not all 8:

```
%hhn vào base+0x4010, +1, +2 với giá trị = 3 byte thấp của system
```

The format-string builder computes the delta for each byte (`d = (wanted - already printed) mod 256`), sorts the
targets by increasing value so it never has to wrap around, then pads to exactly 40 bytes so the three
addresses land precisely in slots 13, 14, 15. I validated this builder by simulating printf against
500 random byte triples: all 500 wrote correctly (`analysis/selftest_fmt.py`).

### Step 4, shell

Once the GOT points at `system`, the next `printf(buf)` call becomes `system(buf)`. Sending `/bin/sh`
as the buffer content is enough, since `buf` is itself the first argument.

```
uid=1337(mad_libs) gid=1337(mad_libs)
/ctf/flag.txt:  -rw-r----- 1 root mad_libs 27
```

## Flag
```
sun{f1ll_iN_th3_g0T_eNtry}
```

```bash
python exploit.py                  # mặc định: ls -l /ctf; cat /ctf/*; env | grep -i flag
python exploit.py 'cat /ctf/flag.txt'
python analysis/selftest_fmt.py    # mô phỏng printf, kiểm bộ dựng chuỗi %hhn
```

The flag lives at `/ctf/flag.txt` (27 bytes, owner `root:mad_libs`, mode `-rw-r-----`). The script
uses only the stdlib, connects to `chal.sunshinectf.games:26001` on its own, re-derives the base on
every run (5 attempts), self-checks `libc_base` against the `/bin/sh` string before writing the GOT,
and writes `flag.txt` once the flag string shows up in the output.
