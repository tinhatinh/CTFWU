# soupOS 0: Welcome to the Kitchen - Rev Eng pwn (431 points)

**Flag:** `cdctf{soupOS_is_better_than_arch}` · **Points:** 431 · **Author:** soup (CDCTF)
**Handout:** `soupos-handout.tar.gz` (redacted source) + `symbols.txt` (kmap of the running kernel)

## The task

Free flag of a five-card soupOS chain: a 32-bit OS "vibe-coded" from scratch. The card itself says there
are **four places where it trusts the wrong thing**, and one instance serves all five challenges. The flag
is printed on the card so you can verify the submission channel.

## Solution

**Step 1 - submit the free flag.** `Start Instance` → open the URL → log in:

```text
login: cook
password: soup
```

`cdctf{soupOS_is_better_than_arch}` is verbatim on the card.

**Step 2 - overview of the remaining stages.** The handout is the real source (only the flag
strings in `src/challenge.c` are redacted), so all four remaining links are readable right here:

```text
./soupos/src/challenge.c:14:#define FLAG1 "cdctf{REDACTED_STAGE_1_________________}"
./soupos/src/challenge.c:15:#define FLAG2 "cdctf{REDACTED_STAGE_2________________}"
./soupos/src/challenge.c:16:#define FLAG3 "cdctf{REDACTED_STAGE_3________________}"
./soupos/src/challenge.c:17:#define FLAG4 "cdctf{REDACTED_STAGE_4__________________}"
```

| Stage | Primitive | What it trusts wrongly | Card |
|---|---|---|---|
| 1 | read a permission-blocked file | `soupyc` calls `open()` straight into the VFS, skipping the shell's `may()` | Mise en Place |
| 2 | become uid 0 | `AlphaSOUP-32` is unsalted and unkeyed; roster `/etc/kitchen` is world-readable | Salt to Taste |
| 3 | read kernel memory | the ELF loader validates `p_vaddr` for the destination but never `p_offset` for the source | Bad Recipe |
| 4 | write kernel memory | array assignment does not reject a negative index → write below `pool`, hijack a function pointer | Too Many Cooks |

`challenge_init()` also hands over two facts used in stages 3-4: the stage-3 flag is `kmalloc(64)`'d and
pinned on the heap (never written to disk), and `/prep` is the only bowl a `cook` may write to:

```c
g_stage3 = (char *)kmalloc(64);
strcpy(g_stage3, FLAG3);
klog("[chal] stage3 flag pinned at %p\n", (void *)g_stage3);
```

**Step 3 - Test with a local harness.** `soupctest.exe` compiles the handout source to test soupyc commands before running them on the VM:

```bash
gcc -O0 -w -idirafter "../soupos/src" -o soupctest.exe stubs.c main.c \
     ../soupos/src/soupyc.c ../soupos/src/vfs.c ../soupos/src/alphasoup.c
```

`-idirafter` (not `-I`) is mandatory: the handout ships its own `src/stdio.h` that remaps `printf` to
`doom_printf`, and `-I` makes the harness pick up the challenge header and fail to build.

## Flag

```text
cdctf{soupOS_is_better_than_arch}
```

## Reproduce

```bash
tar -xzf soupos-handout.tar.gz && grep -n 'FLAG[1-4]' soupos/src/challenge.c
grep -n 'may(' soupos/src/shell.c | head            # stage 1
grep -n 'hash_secret' soupos/src/users.c            # stage 2
grep -n 'p_offset' soupos/src/usermode.c            # stage 3
grep -n 'N_INDEX_SET' soupos/src/soupyc.c           # stage 4
```
