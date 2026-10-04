# soupOS 2: Salt to Taste - Rev Eng pwn (489 points)

**Flag:** FLAG2, printed by `chef special` (the string was not captured verbatim in this session)
· **Points:** 489 · **Author:** soup (CDCTF)
**Handout:** `soupos-handout.tar.gz` + `symbols.txt` (same files as stages 0 and 1)

## The task

"Only the headchef knows today's special. The kitchen roster is world-readable."

## First look

The roster is a FAT file readable with a normal shell command (`/etc/kitchen` is world-readable):

```text
cook@soupOS:/> pour /etc/kitchen
headchef:0:f63a9eb7
cook:1:e7d471fc
```

Format `name:uid:hexhash`, compared in `users.c`:

```c
int users_check(const char *name, const char *secret) {
        if (roster[i].hash == hash_secret(secret)) return (int)roster[i].uid;   /* so HASH */
```

Two consequences straight from the source:

1. **No salt, no key** ⇒ no way to rule out an exhaustive search; but
2. **the gate compares the hash value only** ⇒ we do **not** need the real password, just any preimage of
   `0xf63a9eb7`.

Hash test vector: `alphasoup("soup") = e7d471fc`, exactly the `cook` line - proof that we are reading
the right file and modelling the right hash before spending effort on `headchef`.

## Routes ruled out

1. **Typing the redacted literal `xxxxxxxx`.** The handout contains `roster[0].hash = hash_secret("xxxxxxxx")`,
   but `alphasoup("xxxxxxxx") = 0e4273c9` ≠ `f63a9eb7` ⇒ the shipped image was built with a different
   secret.
2. **Typing `chef special` at the login prompt.** The login gate reads the **account name** first, so the
   string is interpreted as a username. `chef` is a shell command and only exists after logging in as
   `cook`.
3. **Using the author's own `src/solve/crack.c`** (exhaustive 36^7 ≈ 783 M with OpenMP). It works, but is
   unnecessary: AlphaSOUP-32 mixes **one byte at a time and every step is invertible** (`^b`, `rotl 13`,
   `* NOODLE` with odd NOODLE, `^ h>>17`), so splitting the 7-character string 3 + 4 and meeting in the
   middle is ~450x cheaper. Kept as a fallback.

## The chain

**Step 1 - invert the hash to build a meet-in-the-middle table.** Each byte is a bijection on the 32-bit
state, so the reverse steps exist: `rotr 13`, a modular inverse multiply, and `x = z ^ (x >> s)` solved by
4 iterations. `analysis/collide.c` uses the kernel's real `alphasoup_hash()` for the forward direction and
its inverse for the backward one: 1,679,616 backward states against 46,656 forward ones.

```bash
gcc -O2 -w -idirafter "../soupos/src" -o collide.exe collide.c ../soupos/src/alphasoup.c
./collide.exe -selftest          # 7/7: hashing then inverting must return the original string
./collide.exe 0xf63a9eb7
```

```text
target      : 0xf63a9eb7
preimage    : saohjea
verify      : alphasoup("saohjea") = f63a9eb7
```

**Step 2 - test with the handout authentication code.** `analysis/gate_test.c` links the
handout's own `users.c` + `alphasoup.c`, rebuilds the same roster (`headchef:0:f63a9eb7`) and calls
`users_check()`:

```bash
gcc -O2 -w -idirafter "../soupos/src" -o gate.exe gate_test.c \
     ../soupos/src/users.c ../soupos/src/alphasoup.c
./gate.exe 0xf63a9eb7 saohjea      # -> uid 0 (accepted)
./gate.exe 0xf63a9eb7 zzzzzzz      # -> -1  (rejected)
```

The positive and negative controls confirm that the preimage passes the handout authentication code with the local test roster.

**Step 3 - become uid 0 and order the special.** `chef <command>` dispatches with uid 0, and
`challenge_special()` prints the flag only when `users_is_headchef()`:

```text
cook@soupOS:/> chef special
headchef's secret: saohjea
  Today's special: cdctf{...}
```

## Flag

`chef special` prints the stage-2 flag on the VM. The team reported using this method to unlock stage 3, but the flag value was not saved. Local tests confirm that `saohjea` hashes to `f63a9eb7` and `users_check()` returns uid 0 with the test roster.

## Reproduce

```bash
# local: generate the preimage and verify it with the challenge's own sources
gcc -O2 -w -idirafter "../soupos/src" -o collide.exe analysis/collide.c ../soupos/src/alphasoup.c
./collide.exe 0xf63a9eb7
gcc -O2 -w -idirafter "../soupos/src" -o gate.exe analysis/gate_test.c \
     ../soupos/src/users.c ../soupos/src/alphasoup.c
./gate.exe 0xf63a9eb7 saohjea

# on the box:
pour /etc/kitchen
chef special            # enter: saohjea
```
