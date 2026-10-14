---
title: "Sticker Booth"
category: "Pwn"
tags: ["use-after-free", "out-of-bounds-read", "arbitrary-file-read"]
solve_date: "2026-10-10"
language: "en"
---

# Sticker Booth

**Flag:** `FortID{I_h0p3_Y0u_W1ll_Pu7_Th15_5t1ck3r_0n_Y0ur_L4p70p_4f42043742}`  
**Service:** `ncat --ssl sticker-booth-51680d7b0aa2.inst18.ctf.fortid.com 1337` (TLS on port 1337) — handout `handout.zip` 338 KB, containing `chall` (790416 bytes, ELF), `recipe_docs.md`, `sample.recipe`

## Challenge

The service is a `Sticker Booth recipe runner`: it accepts data in the recipe format described by `recipe_docs.md` (a valid `sample.recipe` ships in the handout) and prints the stickers that recipe describes. The objective is to read `flag.txt` on the instance.

```text
Sticker Booth recipe runner
```

## Analysis

The chain uses two primitives:

1. **Use-after-free → out-of-bounds read.** Once an entry is freed, the recipe printing path still references that heap region, so the read runs past the end of the object and echoes whatever is left there. Among the values that come back is the booth's internal ticket:

   ```text
   [+] booth_ticket = 0xe57de37aa7603634
   ```

2. **The sticker header is trusted.** A sticker header is used as the parameter set for the print operation without being checked against the real length and content of the entry. A rebuilt (forged) header makes the runner call `open()`, then `read()`, then `write()` with a path chosen by the input: the file contents are pushed into the `b:` slot of the sticker being displayed. This primitive is arbitrary file read under the privileges of the `chall` process, not code execution.

## Solution

The sequence sent to the instance, from leak to flag read.

1. Drive the booth into the UAF state through the normal recipe lifecycle (create an entry, then delete it), then request the recipe print so that the out-of-bounds read yields `booth_ticket`. This is runtime data of the instance process, so it has to be read through the leak rather than rebuilt from the handout.
2. Forge a sticker header whose path points at `flag.txt`, keeping the remaining fields consistent with what the runner validates.
3. Send the recipe carrying the forged header. The runner prints its status line for the file and pushes the contents into the `b:` slot:

   ```text
   --- flag.txt (133 bytes) ---
   ```

   ```text
   b: FortID{I_h0p3_Y0u_W1ll_Pu7_Th15_5t1ck3r_0n_Y0ur_L4p70p_4f42043742}
   ```

   The runner reports `flag.txt` as 133 bytes, larger than the 66 bytes of the flag string; only the `b:` slot line carrying the flag was retained here, not the whole file body.
4. Step 3 uses a relative path, so the working directory needs confirming before drawing conclusions. The same file-read primitive is pointed at `/proc/self/cmdline`:

   ```text
   /home/ctf/chall
   ```

   `/proc/self/cmdline` confirms argv is `/home/ctf/chall`, not the CWD. The saved response shows that reading `flag.txt` succeeded, but does not establish why the relative path resolved. Read `/proc/self/cwd` or inspect the launcher to reproduce that detail.

The two blocks in step 3 are lines extracted from a single instance response; they are not contiguous in the output.

## Result

```text
FortID{I_h0p3_Y0u_W1ll_Pu7_Th15_5t1ck3r_0n_Y0ur_L4p70p_4f42043742}
```

The flag was read directly from the challenge service. No submission response recorded.

## Reproduce

A TLS client that can talk to port 1337 (nmap-ncat or equivalent) plus a recipe built per `recipe_docs.md`:

```text
ncat --ssl sticker-booth-51680d7b0aa2.inst18.ctf.fortid.com 1337
```

The record is insufficient to rebuild a complete payload; this description is not a runnable solver.
