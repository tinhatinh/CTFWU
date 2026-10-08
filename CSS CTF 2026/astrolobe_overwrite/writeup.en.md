# Astrolobe Overwrite - Pwn/Reverse (Expert, 746pts)

**Flag:** `CSSCTF{0ur0b0r0s_g00d_j0b_b01s_heh3_67}`
**Attached file:** `ouroboros.7z` (Size: 4121 bytes, SHA256: `e7aecc224f6ead512639a33f42f9aa0464ce309ea758b180764ec8dd053e5f2e`)

## Challenge

The challenge provides an executable file `nexus_core` deployed as a service via the netcat protocol at `34.116.80.78:7654`. This service accepts input (payload) as a hex string, with a maximum capacity limit of 512 bytes. The entire execution process is constrained by an alarm function of under 45 seconds. The objective is to send a code sequence capable of satisfying 6 internal check gates (referred to as "harmonic resonance"). When the system passes these check rounds, the command to overwrite the system key will be triggered and return the flag.

Upon connection, the service will output a beacon signal as a hexadecimal string, then wait to receive input data. This data must be a hex string representing low-level machine code. The system does not provide accompanying technical documentation; if the check fails, it only responds with static error messages such as "COHERENCE FAULT", "THERMAL DETONATION", or "HARMONIC FAULT".

## Analysis

Evaluating the binary:
```text
elf64 x86-64 PIE NX full-relro
interpreter: /lib64/ld-linux-x86-64.so.2
entry: 0x12f0
imports: printf, fgets, time, fopen, fclose, strlen, puts, exit, alarm, setvbuf, sscanf
strings: "flag.txt", "[!] COHERENCE FAULT: Quantum state cold", 
         "[!] THERMAL DETONATION: Core runaway", "[+] TELEMETRY STABILIZED"
```

Core point: The binary calls the `time()` and `alarm(45)` functions. This imposes a requirement for real-time interaction with a strict time limit. The check logic blocks do not directly read the flag file; instead, the system requires internal state variables to satisfy complex mathematical conditions before allowing access.

## Solution

**Step 1 - Extract the check block and run it independently via an Assembly Trampoline.**
Since the Linux ELF analysis code cannot be compiled directly for the emulator environment, the entire check code block (from address `0x15AD` to `0x1966`) is extracted straight into the memory of a test application on Windows using the `VirtualAlloc(..., PAGE_EXECUTE_READWRITE)` command. This code snippet is activated via an Assembly trampoline: backup registers (`push registers`), save the stack pointer `rsp` to `r14`, allocate a temporary stack, and `jmp` straight into the code block. When the code encounters a return branch, it will exit to the stub and output an error identifier tag (tag: 0, 1, 2, 3, etc.). This technique helps isolate and precisely confirm the condition of each error branch, completely eliminating guesswork.

```bash
gcc -O0 -o one.exe one.c
one.exe seg
seg 15AD-15B1 -> 50 want 50
seg 15AD-15C8 -> 51 want 51
...
```

**Step 2 - Model the system of 6 modulo 65521 congruence equations.**
The assembly decompilation process fragments the logic into three main equation groups:
- Gates 0-3 group: Has the form `(X·C + T_i) mod 2^64 <= K`, where `C = 0x58862fdccdf01111` and `K = 2^64 // M`. Based on the algebraic property `C·M == 1 mod 2^64`, this equation is actually a conversion to the least residue on the finite field `F_M`.
- Gate 4 group: Has the form `c1^2 = c0^3 + 17c0 + 43 mod M`.
- Gate 5 group: Has the form `c3^2 = c2^3 + 17c2 + 43 mod M`.

Implement the Python model in `model.py` and compare it with the oracle on 200 random samples. All 200 tested samples agree; this is a check of that sample set, not a proof for every input.

**Step 3 - Solve the system of equations via the degenerate space.**
Based on the established mathematical model, a C source code optimized for multithreading (using OpenMP via the `-fopenmp` flag) is used to scan the variable space `t0 in [0..300]`:

```bash
gcc -O3 -fopenmp -o search.exe search.c
./search.exe 0 300
SOLUTION t=(1,218,59611,783)  u=(37101,35947,43627,40060) c=(37319,30037,44410,40061)
done: qr=9892500 hits=1
```

The system recorded the unique solution `(1, 218, 59611, 783)` in the first scan range. This solution was then proven correct by comparing it with the beacon parameters on the server.

**Step 4 - Simulate the Assembly VM and set up the Payload.**
The service possesses a virtual machine (VM) that executes 8 opcodes. These opcodes are addressed via a self-referencing permutation table `P`. Specifically, each 4-byte code is decoded according to the formula `opcode = P[(byte0 ^ z) & 7]`. Use the simulator `vm.py::build(beacon, TVEC)` to generate a 420-byte low-level machine code (including 105 instructions, Program Counter value pc=114). This machine code ensures proper initialization of the variable range `w[0..3] = (t_i + beacon) mod M`.

```python
blob, v = vm.build(beacon, TVEC)
hexstr = binascii.hexlify(blob).decode()
s.sendall(hexstr.encode() + b"\n")
```

**Step 5 - Deployment and Verification.**
The service returns the beacon code `0x13D6`. The system initializes the payload corresponding to the `PC=114` level, which is within the safe range `[112,128]` to avoid triggering the alarm. Send the data to the service, receive the response `[+] TELEMETRY STABILIZED` and recover the flag.

## Result

Execution process on the workstation:

```bash
python exploit.py files/ouroboros.7z
```

```text
BEACON: 0x13D6
beacon=0x13D6  pc=114  w=[5079, 5296, 64689, 5861]  bytes=420
[+] TELEMETRY STABILIZED. OVERWRITING SYSTEM MASTER KEY...
CSSCTF{0ur0b0r0s_g00d_j0b_b01s_heh3_67}
FLAG: CSSCTF{0ur0b0r0s_g00d_j0b_b01s_heh3_67}
```

Result:
```text
CSSCTF{0ur0b0r0s_g00d_j0b_b01s_heh3_67}
```
