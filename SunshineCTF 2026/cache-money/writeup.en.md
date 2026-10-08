# Cache Money - Pwn (Hard)

**Flag:** `sun{s4fe_l1nk1ng_w0nt_s4ve_y0ur_tc4che}`

## Challenge

`cache_money` is a menu-driven wallet manager; each wallet is a 0x30-byte struct allocated with
`calloc`, plus a "ledger" allocated with `malloc(size)`:

```
+0x00 name[16]   +0x10 balance   +0x18 ledger*   +0x20 size   +0x28 active
```

The `wallets[16]` array lives in `.bss` at `0x4040c0` (the binary is non-PIE, so the address is
fixed). Three primitives, exactly as the hint "the books haven't been audited" suggests:

- `deposit(i)` = `read(0, wallets[i]->ledger, wallets[i]->size)` -> writes into the chunk
- `withdraw(i)` = `write(1, wallets[i]->ledger, wallets[i]->size)` -> reads out of the chunk
- `open` = `calloc(0x30)` for the struct then `malloc(size)` for the ledger

## Vulnerability

`transfer(src, dst)` frees src's ledger and then assigns that same freed pointer to dst:

```asm
401ac9: rdi = [src+0x18]      ; old ledger of src
401acd: call free
401ad2: rax = [src+0x18]
401ae8: [dst+0x18] = rax      ; dst receives the freed pointer
401b1a: [src+0x28] = 0        ; src is only marked inactive, still in the array
```

This yields a use-after-free on the heap: reading from and writing to a chunk that is sitting in
the tcache.

## Two allocator details that decided the approach

**(a) `calloc` does not take chunks from the tcache, `malloc` does.**
On the target's glibc 2.39, after freeing ledger X and then `open`ing a new wallet, the new wallet's
struct comes from the top chunk, while its ledger is the chunk X popped from the tcache. Verified
with the program itself: after `transfer(A->C)` and then `open B`, `withdraw(B)` prints the name
`"B"` (the struct is still intact) but the 48 bytes read back are the content we just wrote into C,
i.e. `B->ledger == C->ledger`. With the tested allocation order and sizes, the struct does not take the freed ledger chunk, the usual "overwrite
the ledger with a struct" approach is not available.

**(b) Safe-linking.** For a lone bin entry, the null next pointer is encoded as `pos >> 12`, where `pos` is the next field’s address. The leaked `0x2eea7` is that page’s mask; it does not establish the entire heap base or the offset within the page. The chain uses this mask and checks that the next chunk is on the same page. The tcache `key` detects double-free and is not a heap pointer for deriving the base.

## Solution

1. `open A(48)`, `open C(48)`, `open F(48)` -> ledgers X, Z, W.
2. `transfer(A->C)` -> X into the tcache, `C->ledger = X`. `withdraw(C)` reads `fd` => mask.
3. `transfer(F->C)` -> W at the head of the bin, `W->next = X ^ mask`. `withdraw(C)` re-checks
   `(W->next ^ mask) >> 12 == mask` to make sure the model is right.
4. `deposit(C, p64(TARGET ^ mask) + ...)` -> poison `W->next` into
   `TARGET = 0x4040f0 = &wallets[6]`.
   This region was chosen because `open_wallet` has `__memset_chk(ledger, 0, size, size)` right after
   malloc: zeroing 0x30 bytes at `&wallets[6]` only clears six slots that are already empty, while
   `.rodata` would SIGSEGV and the GOT would get `puts`/`read` wiped as well.
5. `open G1, G2, G3`: G1's ledger pops W, G2's ledger pops TARGET -> G2->ledger points straight into
   the wallets array, G3 keeps a different slot 5 that is not NULL.
6. `deposit(G2, p64(0x4040c0))` -> `wallets[6] = &wallets[0]`, turning the array itself into a fake
   wallet: `active` = the low 4 bytes of `wallets[5]`, `ledger` = `wallets[3]`, `size` = `wallets[4]`
   (a heap pointer, i.e. a huge `read()` length, which in practice just takes exactly the bytes sent).
7. `deposit(6, fake_struct(GOT_FREE, 48))` -> overwrites the slot 3 struct, turning it into arbitrary
   read/write.
8. `withdraw(3)` reads 48 bytes from `0x404000` -> the GOT. `free` and `puts` are already resolved
   (`transfer` calls free, the banner calls puts), and the offsets line up:
   `free-0xadd20 == puts-0x87bd0` -> libc base -> `system = base + 0x58740`.
9. `deposit(6, fake_struct(GOT_FREE, 8))` then `deposit(3, p64(system))` -> `GOT[free] := system`
   (size = 8 so the neighbouring slot is not touched).
10. `open CMD(256)`, `deposit(CMD, "cat /ctf/flag.txt")`, `close(CMD)` ->
    `free(ledger)` calls `system("cat /ctf/flag.txt")`.

No ROP needed: there is no `system` in the PLT, but Partial RELRO allows writing the GOT, and the
`rdi` argument of `free()` is precisely the ledger pointer whose contents we control.

## Quick debugging on a Windows host

No pwntools and no gdb for the Linux ELF, so everything was `objdump` + raw sockets. The two
mistakes that cost the most time were both on the client side:

- `setvbuf(stdout, NULL, 2, 0)` with `2 == _IONBF`: stdout is unbuffered, but stdin is not, so lines
  have to be sent one at a time waiting for the right marker, never as one batch.
- A client that slept `sleep 1s` per prompt got disconnected around the 10th command. Switching to
  event-driven recv (answering as soon as the marker appears) made the whole chain run in ~2 seconds.
