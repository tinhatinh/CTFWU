# FoundryProof — Tiny-HDL sign-off

FoundryProof certifies that a candidate combinational design is equivalent to our golden
reference before tape-out. A certified design is then probed once, on the post-fab audit
vector, to catch tampering.

You think our sign-off is airtight. It isn't. Submit a design that FoundryProof **certifies
as equivalent** to the reference, yet whose output on the audit vector is the sabotage value.

## The target
- audit vector:   `A_AUDIT = 0xDEADBEEF`
- sabotage value: `MAGIC   = 0xB105F00D`

Win = your netlist is **certified** AND `T(A_AUDIT) == MAGIC`.

## Tiny-HDL
Combinational only. One 32-bit input, one 32-bit output. Every signal is a 32-bit word.
Signals are single-assignment and must be defined before use.

```
input a               # the sole input, 32-bit
output y              # names the output signal
name = const 0x1234  # 32-bit literal (decimal or 0x hex)
name = not x         # bitwise NOT
name = and x y       # bitwise AND     (also: or, xor)
name = add x y       # (x + y) mod 2^32
name = shl x 5       # x << 5   (immediate amount, 0..31)
name = shr x 5       # x >> 5   (logical)
name = eq x y        # 0xFFFFFFFF if x == y else 0x00000000
name = mux s x y     # (x & s) | (y & ~s)   -- bitwise select by mask s
```

Text after `#` is a comment. Submit your netlist over the socket, then a final line
containing only `END`.

## Provided
- `hdl.py`        the parser / simulator / z3 encoder
- `verifier.py`   the exact certifier FoundryProof runs
- `reference.hdl` the golden reference design

FoundryProof runs `verifier.certify(reference, yours)` and then audits the result. Read the
certifier closely.
