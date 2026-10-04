# soupOS 1: Mise en Place - Rev Eng pwn (479 points)

**Flag:** `cdctf{mise_en_place_two_paths_one_check}` · **Points:** 479 · **Author:** soup (CDCTF)
**Handout:** `soupos-handout.tar.gz` + `symbols.txt` (identical to soupOS 0)

## The task

"There is a flag file in the root bowl and you cannot read it. serve / will tell you why."

## First look

`serve` lists the **current** bowl and takes no argument (`cmd_serve(void)`, `shell.c:545`), so the card's
hint only works bare; typing `serve /` falls into the shell's unknown-command branch:

```text
cook@soupOS:/> serve /
No soup for you: 'serve /'

cook@soupOS:/> cd
HELLO.TXT README.TXT RECIPE.TXT SECRET.TXT FORTUNE.TXT FLAG.TXT DEMO.SC ... ETC PREP FLAG1.TXT
```

So `FLAG1.TXT` really exists in the root bowl. The handout's own `challenge_init()` names the broken link:

```c
/* Stage 1: the flag file exists, is owned by headchef, and is readable
 * only by its owner. The shell's may() honours that, so a cook is
 * refused; soupyc's open() never asks, which is the bug being taught. */
fat_chown("FLAG1.TXT", 0);
fat_chmod("FLAG1.TXT", FAT_PERM_MARK | FAT_PERM_OR | FAT_PERM_OW);
```

Two code paths perform the same read:

| | shell path | soupyc path |
|---|---|---|
| entry | `pour FLAG1.TXT` → `cmd_pour` (`shell.c:595`) | `soup -c ...` → `soupyc_run` (`shell.c:618`) |
| check | `if (!may(path,'r')) { deny(path); return; }` | **none** |
| read | `fat_read()` | `vfs_open()` → `vfs_read()` |

`may()` (`shell.c:151`) is the only permission gate in the system and it is only ever called from the
shell. The interpreter runs in ring 0 and calls the VFS directly:

```c
if (strcmp(name, "open") == 0) {
    ...
    vfs_node_t *nd = vfs_open(a[0].sval, flags);   /* khong hoi may() */
```

Hence the card's title: **two paths, one check**.

## Routes ruled out

1. **Typing it as the card suggests (`serve /`)** - the shell takes no argument for `serve` and falls back
   to `"No soup for you: '%s'"` (`shell.c:2489`). Use bare `serve`, or `cd <bowl>` then `serve`.
2. **Changing the mode from the shell** - `chmod`/`chown` also go through `may()` and only the headchef
   passes.
3. **`copy`/`move` FLAG1.TXT into `/prep` and reading it there** - both call `may(src,'r')` at
   `shell.c:807`.
4. **Guessing `SVAL_LEN` to read the whole line** - `read()` clamps to `SVAL_LEN - 1`, so a bigger number
   does nothing; the value must be exactly 47 or the trailing `}` is cut. Verified in a harness built from
   the real sources.

## The chain

**Step 1 - call the interpreter's builtins directly, skipping the shell gate.** In soupyc `pour` is the
print statement (`TK_POUR`, `soupyc.c:757`), not the shell command, and `read()` is capped at 47 bytes
(`SVAL_LEN - 1`) - one flag plus `\n`:

```text
cook@soupOS:/> soup -c pour read(open("/FLAG1.TXT"),47)
cdctf{mise_en_place_two_paths_one_check}
```

**Step 2 - why `soup -c` needs no quotes.** `cmd_soup` takes `args + 2`, skips spaces and never strips
quoting, so `soup -c "code"` and `soup -c code` are equivalent - which also means one missing closing
quote produces a very unhelpful parse error:

```text
cook@soupOS:/> soup -c pour read(open("/FLAG1.TXT),47)
soupyc: parse error (line 1): expected ')'
```

That exact error was reproduced in the local harness during parser testing.

**Step 3 - Check with the local harness.** `soupctest.exe` compiles `soupyc.c` and `vfs.c` against a mock FAT volume. The test confirms the 47-byte limit and the `open → read → pour` path using a local flag:

```bash
./soupctest.exe 'pour read(open("/FLAG1.TXT"),47)'
```

## Flag

```text
cdctf{mise_en_place_two_paths_one_check}
```

The flag string was recorded in the stage-3 kernel-memory scan, which also covers `.rodata`. No stage-1 screenshot is recorded; the soupyc read mechanism was reported to have scored.

## Reproduce

```text
login: cook / soup
serve                                              # lists the current bowl (no arguments)
cd                                                 # root bowl contains FLAG1.TXT
soup -c pour read(open("/FLAG1.TXT"),47)           # read through the soupyc path
```
