# Kuiper Belt Relay Core

**Event:** CSS CTF 2026  
**Category:** pwn  
**Level:** Beginner (50 points)

## Problem Description

The system provides a string response service (echo service) operating based on the `vuln()` function. This function receives input data via the unsafe function call `gets(buffer[64])`. A function named `win()` has been pre-declared in the source code but has no valid execution path (dead code). The challenge objective: Exploit the buffer overflow vulnerability at `gets` to overwrite the return address, thereby redirecting the program's control flow to jump directly into the `win()` function to output the flag.

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
- The binary file is compiled compatible with x86-64 architecture and does not activate the PIE (Position Independent Executable) mechanism. Scanning static addresses is successful and confirms all partitions are within the `0x40xxxx` range.

## Excluded Directions

### Stack Memory Leak via Format String Vulnerability

- Trial: Transmit format payload `b"A"*n + b"%s%s%s..."` with the intention of reading out values located on the adjacent stack after the buffer region.
- Result: Could not retrieve any usable address values. Deepening the analysis of the `gets()` function architecture, this function automatically inserts a NUL terminator `\x00` immediately after the input data block. Because 64-bit systems use addresses starting with byte `0x40` and apply Little-Endian formatting, the Least Significant Byte (LSB, e.g., `0x16`) will be loaded first. The insertion of the `\x00` character inadvertently overwrites the low byte of the return address itself, leading to the format string being immediately disconnected, completely nullifying the efficacy of the memory leak technique.
- Conclusion: Forced to discard the plan of using a format string vulnerability to probe for the `win()` function address. The optimal alternative plan is a direct probing technique based on system feedback (oracle-based scanning).

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

Under conditions lacking a local executable file to extract the static address directory, the probing procedure is mandatorily conducted directly against the server within the `.text` code partition range (Extending from `0x401000` to `0x401500`).

- Payload structure for each test step: `b"A"*72 + low_bytes(addr)` (Little-Endian format, ensuring safety when the NUL character terminates the string).
- Distinguishing sign (Oracle): Based on analyzing whether the server response contains the string "hijacked" or "CSSCTF".

The automated scan results detected the `win()` function exists at address: **0x401216**.

**Step 3 - Exploit Payload Architecture.**

Because address `0x401216` is smaller than the `0x1000000` threshold, the system only requires overwriting the 3 lowest bytes: `0x16 0x12 0x40`.

Completed Payload structure: `b"A"*72 + b"\x16\x12\x40"`.

**Step 4 - Practical testing (Verification).**

Deploy the Payload to the target server in 3 independent sessions. All 3 sessions bypassed the defense barrier, seized control, and returned the flag successfully.

## Flag

Result:
```text
CSSCTF{s1gn4l_r3c0v3r3d_fr0m_th3_v01d}
```

## Reproduce

Automated re-establishment process using script:

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
