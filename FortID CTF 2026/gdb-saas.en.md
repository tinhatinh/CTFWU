---
title: "GDB SaaS"
category: "Pwn"
tags: ["gdb","dwarf-line-table","argument-injection","filter-bypass"]
solve_date: "2026-10-10"
language: "en"
---

# GDB SaaS

**Flag:** `FortID{N0_5h3ll_n33d3D_jU57_m41N_ce0eaeff26}`  
**Service:** `ncat --ssl gdb-saas-53b083dc24af.inst19.ctf.fortid.com 1337` (TLS on port 1337, remote banner `GNU gdb (Ubuntu 17.1…)`). Artifact: `server.py` 1.4 KB. The attempts were recorded on instance `gdb-saas-7e15a5b0c61e`; the solve output comes from instance `gdb-saas-53b083dc24af`.

## Challenge

The service advertises "Get your mains disassembled for free…": it accepts an ELF as base64 plus the name of a function, runs GDB to disassemble that function and returns the result to the client. The problem is to take the flag from a service that gives no shell.

## Analysis

The solve rests on three pieces.

The filter. `server.py` rejects characters through `BAD_CHARS`, but that filter is applied only to the function-name argument, and the blocked set contains neither `/` nor `s`. The string `/s main` therefore passes untouched and is concatenated straight into the GDB command line, so the service ends up running `disassemble /s main` instead of `disassemble main`. This is argument injection into GDB's command line, not a memory corruption bug.

The DWARF line table. The uploaded ELF is built locally with `mkdwarf.py`: an ordinary binary containing `main`, carrying a DWARF-4 line table whose source file #1 is named `flag.txt`. The ELF itself holds no flag; that filename is just a string in the line table, stored as a bare basename with no absolute comp_dir.

How GDB prints source. With `/s`, GDB walks the line table entries and interleaves the matching "source line" for each one. Because the path is a basename with no directory component, GDB resolves it against the current working directory of the service process itself, which is where `server.py` copies the real flag file. The service's flag file is therefore printed as if it were line 1 of `flag.txt`.

All of the data leaves through GDB's standard output inside a session the service already allows, so no command ever has to execute in the service process.

## Solution

1. Build the ELF locally with `mkdwarf.py`: it must define `main` and declare source file #1 as `flag.txt` in the DWARF-4 line table. This step is instance-independent.
2. Base64 the ELF and upload it to the instance over TLS.
3. At the function-name prompt, submit the argument `/s main`. Neither `/` nor `s` is blocked by `BAD_CHARS`, so the command executed server-side becomes `disassemble /s main`.
4. Read the response. The warning line shows that GDB really opened a file in the service's CWD and that the file has a single line; the accompanying disassembly dump prints its contents. Verbatim from the recorded response (the second line kept as one line):

   ```text
   Line number 2 out of range; flag.txt has 1 lines.
   Dump of assembler code for function main: | flag.txt: | 1	FortID{N0_5h3ll_n33d3D_jU57_m41N_ce0eaeff26}
   ```

## Result

```text
FortID{N0_5h3ll_n33d3D_jU57_m41N_ce0eaeff26}
```

The flag was read directly from the challenge service. No submission response recorded.

## Reproduce

Requires Python 3 for base64 and the TLS socket, a GDB build to check the mechanism locally (this solve used local gdb 14.2; the service runs `GNU gdb (Ubuntu 17.1…)`), and a live instance because the flag file sits in the service's CWD. The decisive detail of the uploaded ELF is a single line-table entry:

```text
file_names[1] = "flag.txt"     # basename only, no absolute comp_dir
```

The `mkdwarf.py` that was used is a local helper and is not part of the handout, so it is not reproduced verbatim here; the client skeleton below is equivalent at the connection level:

```python
import base64, socket, ssl

HOST = "gdb-saas-53b083dc24af.inst19.ctf.fortid.com"
ELF_PATH = "out.elf"           # built locally by mkdwarf.py
blob = base64.b64encode(open(ELF_PATH, "rb").read())

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
s = ctx.wrap_socket(socket.socket(), server_hostname=HOST)
s.connect((HOST, 1337))
# upload the base64 blob, then answer the function-name prompt with: /s main
```

Or on a system where input redirection behaves:

```text
ncat --ssl gdb-saas-53b083dc24af.inst19.ctf.fortid.com 1337
```
