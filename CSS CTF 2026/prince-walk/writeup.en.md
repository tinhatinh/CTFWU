# Prince Walk - Reverse (50 pts)

**Flag:** `CSSCTF{P12INC3_0R_P1NC3?}`
**Attached file:** `prince_walk` (Size: 92,384 B, SHA256: `2d0c95f7...`)

## Challenge

The challenge provides a Linux binary named `prince_walk`. The application description indicates this is a "planetary survey" simulator. The starting avatar is at coordinates `(1, 1)` and the beacon is located at coordinates `(999999, 999999)`. The flag is situated at the destination. However, no Linux virtual machine environment is provided to directly execute this binary (the program requires an interactive terminal environment, the `isatty` function will reject if the I/O stream is piped).

## Analysis

Evaluating the file format via the `file` command: The file is a 64-bit ELF, featuring a Position Independent Executable (PIE) structure, stripped, and dynamically linked. The overall entropy value of the file is 7.416. The `rabin2 -z` command reveals that the segment containing character strings ends at address `0x8a12`. Immediately adjacent, in the `.rodata` segment, appears a 66,560-byte opaque data blob with a very high entropy level of 7.98. The Imports dependencies such as `tcgetattr`, `tcsetattr`, `ioctl`, `poll`, `isatty`, `prctl`, and `raise` indicate that this is a terminal-based game equipped with an anti-debug mechanism.

The source code decompilation process yielded two observations:

1. Terrain generation mechanism: The map coordinate system is not stored statically but generated procedurally. The `FUN_00102c52` function uses bitwise rotation `rol` and 32-bit reduction operation `lowbias32` (with constants `0x7feb352d`, `0x846ca68b`) to initialize 16 words. This proves the 66,560-byte data block is not map data.
2. Arithmetic structure: The size 66,560 is equivalent to the formula `8320 * 8`. This is far too round and unusual a number to be a standard image file or compressed data block.

## Solution

**Step 1 - Locate the data block processing function.**
There are two `lea` (load effective address) instructions pointing to this data block located in the `FUN_00102c52` function. The preamble of this function contains the condition:

```c
if (param_1 == 999999 && param_2 == 999999) { ... }
```

This logic structure confirms that the entire data block sequence is only decoded when the character stands exactly at the destination coordinates. Consequently, moving millions of steps in the simulation environment is unnecessary. Instead, the exploitation script will simulate calling the decoding function directly with the default coordinate parameters `x = y = 999999`.

**Step 2 - Extract the key initialization algorithm from coordinates.**
The decoding operand is designed based on the input coordinates:

```c
for (i = 0; i < 16; i++)
    A[i] = lowbias32(((i+1) * 0x9e3779b9) ^ rol(999999, i+1) ^ 999999);
key  = lowbias32((rol(999999, 19) + 999999) ^ 0xa4093822);
```

**Step 3 - VM Decoder Loop architecture.**
With the variable `j` cycling from 0 to 8319, the system determines the record array index via the permutation `idx = (217*j + 3286) mod 8320` (coefficients 217 and 8320 are coprime, ensuring a full space scan). The decoding process extracts each parameter pair:

```python
v1 = blob[2*idx]     ^ lowbias32((j * 0x9e3779b9) ^ key)
v2 = blob[2*idx + 1] ^ lowbias32(key + j + 0x6a09e667)
```
`v1` encodes the opcode and operand fields: `s = (v1>>8)&0xf`, `a = (v1>>12)&0xf` and `b = (v1>>16)&0xf` are four-bit fields; `r = (v1>>20)&0x1f` is five bits. The low byte `v1 & 0xff` is the opcode. The interpreter updates state array `A` according to these fields.

```python
pos = v2 >> 25
val = (v2 ^ A[a] ^ rol(A[b], r)) & 0xff
out[pos] = val; used[pos] = 1
A[s] ^= ((pos + val) * 0x45d9f3b) & 0xffffffff
key = (j * 0x3c6ef372 + v2 + rol(A[s] ^ A[a] ^ key ^ v1, 9)) & 0xffffffff
```
State array `A` changes after each output byte. Decode the bytes in order and retain the state between steps.

**Step 4 - Acceptance Criteria.**
The decoding function is only certified complete and returns a result when the system records exactly 128 bytes emitted without being redundantly overwritten at any position. At the output, the first byte `out[0]` holds the flag text content length parameter (mandatory to be within `1..123`). The byte string from `out[1]` to `out[len]` must be printable text characters. Finally, the 4-byte cluster from `out[len+1]` to `out[len+4]` is the FNV-1a hash code (using init parameter `0x811c9dc5`, prime `0x1000193`) calculated from the exact text string above, acting as a self-checksum data integrity mechanism.

**Verification.** The decoded output has FNV-1a checksum `0x763cc96c`, matching the four checksum bytes stored in the bytecode. This checks the interpreter output against the binary’s embedded value.

## Result

Executing the script:

```bash
python exploit.py files/prince_walk
```

```text
result: ok  (FNV signature 763cc96c verification complete, successfully generated 128 bytes, length len=72)
FLAG: Developer:
"No you didn't."

MISSION COMPLETE

CSSCTF{P12INC3_0R_P1NC3?}
```

Result:
```text
CSSCTF{P12INC3_0R_P1NC3?}
```

## Reproduce

Reproduce:

```bash
python exploit.py files/prince_walk
```

Note: The script requires the `numpy` math library. The `analysis/` directory contains the `text.asm` and `main.asm` files storing the disassembly results of the entire `.text` partition and the structures of the core functions (`main`/`FUN_00104c3`/`FUN_001051a2`). These documents are used for structural cross-referencing while establishing the simulated calculation functions.
