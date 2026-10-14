---
title: "Editorial Board"
category: "Pwn"
tags: ["charset-shellcode","ret-overwrite","language-tool-oracle","self-modifying"]
solve_date: "2026-10-10"
language: "en"
---

# Editorial Board

**Flag:** `FortID{Sh3llc0d1n6_L1k3_Sh4k3sp34r3_G3ts_7h3_Fl4G!_31475ec574}`  
**Service:** `ncat --ssl editorial-board-ad8e57922c7a.inst2.ctf.fortid.com 1337` (instance that produced the flag; instance `a20043e92cc9` was used in the earlier run). Artifact: `handout.zip` 5.7 KB containing `editorial_board` 13936 B (ELF 32-bit, base `0x08048000`) and `validate.py` 5623 B.

## Challenge

The service takes a piece of text and only runs its internal processing when that text is "clean". Two conditions have to hold together:

- Pass the "anti-slop desk": 640–900 characters, at least 90 words, at least 4 sentences, no spelling errors. The desk consults a LanguageTool oracle (the public `languagetool.org` instance returned `matches: 0` with software `6.9-SNAPSHOT`).
- Once accepted, the text goes through a typesetter pipeline containing a `leave; ret` overflow that allows the return address to be overwritten.

## Analysis

`validate.py` in the handout is the anti-slop desk: it encodes the character / word / sentence limits and forwards the spelling check to LanguageTool. Any accepted submission therefore has to be genuine English.

Behind the desk sits the typesetter pipeline. Once the text is accepted, a function ends with the `leave; ret` pair: `leave` reloads the stack pointer from the frame pointer, `ret` then takes the return address sitting at that stack pointer, so EIP becomes input-controlled. The target address is an RWX `mmap` page at `0x656c6000`, memset to `0xff` before the payload is copied in. Because that page is both writable and executable, overwriting the return address with `0x656c6261` (base + `0x261`) transfers control into the bytes of the text itself.

The hardest constraint is the payload charset `[A-Za-z .,;:'-?!]` — printable characters of English prose only. No `\x00` bytes, no braces, no control characters. Ordinary x86 shellcode does not fit this set, including the `int 0x80` pair (`0xcd 0x80`) needed for `execve("/bin/sh")` on 32-bit.

The way out is self-modifying code assembled from real English words: pick words whose ASCII bytes happen to form valid 32-bit instructions that write the two bytes `0xcd 0x80` into executable memory, then jump into the `execve("/bin/sh")` stub. The same text is simultaneously clean English according to LanguageTool and shellcode once executed.

## Solution

The payload was only ever executed against the live instance; on the local side the work stopped at simulating the payload in Unicorn (see Directions Tested).

1. Build the English-words-as-shellcode payload with `build.py`, emitting `ms.bin` at 694 B. The 693 text bytes before the newline stay inside `[A-Za-z .,;:'-?!]`, and the blob is long enough to cover the input buffer up to the return address, overwriting it with `0x656c6261`.
2. Validate the payload offline with `emu.py` (Unicorn-based): simulate `leave; ret` landing at `0x656c6261` in a page memset to `0xff`, run `ms.bin`, and confirm it writes `0xcd 0x80` into itself and then calls `execve("/bin/sh")` without touching a byte outside the charset or faulting. This step is simulation only; nothing is sent.
3. Open TLS to the instance. The service prints the checksum of its own validator, matching `validate.py` from the handout:

   ```text
   57d0eb4d48604a922583646dea18594e41958b0ad8ef3dccfc66e930b0542610 /challenge/validate.py
   validator checksum MATCH
   ```

4. Send `ms.bin` over TLS. The text clears the anti-slop desk, the return address is overwritten into the RWX page, the shellcode modifies itself and execs `sh`:

   ```text
   [+28.3s] Accepted by the anti-slop desk
   [+40.9s] uid=1000(ctf)
   ```

5. From the shell obtained through RCE, `cat` the flag file on the instance to read the flag directly.

## Result

```text
FortID{Sh3llc0d1n6_L1k3_Sh4k3sp34r3_G3ts_7h3_Fl4G!_31475ec574}
```

The flag was read directly from the challenge service. No submission response recorded.

## Reproduce

Requires Python 3, Unicorn (`pip install unicorn`) and a TLS client (nmap-ncat or equivalent). The first three rows of the table below come from the handout and from the checksum the service prints itself; the last row is the locally built artifact:

```text
handout.zip      5.7 KB
editorial_board  13936 B   ELF 32-bit, base 0x08048000
validate.py       5623 B   57d0eb4d48604a922583646dea18594e41958b0ad8ef3dccfc66e930b0542610
ms.bin             694 B   payload, charset [A-Za-z .,;:'-?!]
```

`build.py` produces `ms.bin`: it constructs English text that satisfies 640–900 characters, at least 90 words and at least 4 sentences, while keeping the byte sequence inside the charset and long enough to cover the input buffer up to the return address at `0x656c6000`. `emu.py` loads `ms.bin` into a Unicorn model of the `0x656c6000` page (memset `0xff`) to check the charset and the `0xcd 0x80` self-write before sending. Both scripts are local helpers, not part of the handout, so they are not reproduced here; the mechanism described above is the complete set of information needed to rebuild them.

Connection to the instance:

```text
ncat --ssl editorial-board-ad8e57922c7a.inst2.ctf.fortid.com 1337
```

Once `execve("/bin/sh")` gives a shell, read the flag with `cat` on the instance's flag file.
