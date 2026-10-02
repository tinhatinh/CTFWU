# Tapeout — Misc (Hard)

**Flag:** `H7CTF{afd4beac-e86e-409b-907d-b519bb748599}`

## Challenge

FoundryProof certifies a combinational design as equivalent to the golden version and only then "stamps" the tape-out,
afterwards poking a probe once on the manufactured chip to catch cheaters. The win rule is spelled out in `SPEC.md`:

```
audit vector:   A_AUDIT = 0xDEADBEEF
sabotage value: MAGIC   = 0xB105F00D
Win = your netlist is certified AND T(A_AUDIT) == MAGIC
```

We need a netlist that is both certified equivalent and produces the sabotage value at the audit point.

## Initial Analysis

The three given files are `hdl.py` (parser + simulator + z3 formula generator), `verifier.py`
(the certifier verbatim) and `reference.hdl`:

```
input a
k1 = const 0x9E3779B9
k2 = const 0x1337C0DE
t1 = xor a k1
hi = shr a 16
t2 = add t1 hi
y  = xor t2 k2
```

The challenge says "Read the certifier closely", and the trap is in exactly one line:

```python
SAMPLE_BITS = 16
sample = z3.BitVec("sample", SAMPLE_BITS)
a = z3.ZeroExt(WIDTH - SAMPLE_BITS, sample)      # 16 bit cao bị ép bằng 0
solver.add(build(ref, a) != build(sub, a))
return solver.check() == z3.unsat
```

`certify()` does not prove equivalence over all `2^32` inputs. It proves it over the set
`{ZeroExt(16, s) : s in 2^16}` = exactly the values `a < 0x10000`.
The audit, however, runs at `0xDEADBEEF`, outside the quantified domain. "probes the finished part
once" is the decisive detail: a single check point, and that point lies outside the proven region.

So there is no need to beat the equivalence checking problem - only to exploit its scope.

## Exploit Chain

**Step 1 - Building an "outside the proof" indicator.** `eq` in Tiny-HDL returns `0xFFFFFFFF` when equal,
`0x00000000` when different, so:

```
hi    = shr a 16      # 0 for every input in the proof domain
islow = eq hi zero    # 0xFFFFFFFF in domain, 0 out of domain
```

**Step 2 - Choosing between the two behaviours with `mux`.** `mux s x y = (x & s) | (y & ~s)` selects per
bit, so with an all-1/all-0 mask it works as a real multiplexer:

```
yref  = xor t2 k2                     # exact transform of the reference
y     = mux islow yref magic          # magic = const 0xB105F00D
```

The whole netlist:

```
input a
k1 = const 0x9E3779B9
k2 = const 0x1337C0DE
magic = const 0xB105F00D
zero = const 0
t1 = xor a k1
hi = shr a 16
t2 = add t1 hi
yref = xor t2 k2
islow = eq hi zero
y = mux islow yref magic
output y
```

With `a < 2^16`: `islow = 0xFFFFFFFF` -> `y = yref` bit-for-bit -> z3 finds no counterexample -> CERTIFIED.
With `a >= 2^16`: `islow = 0` -> `y = MAGIC`.

**Step 3 - Verifying locally before submitting.** This machine has no z3, so `hdl.py` cannot be imported;
the Tiny-HDL simulator was rewritten inside the exploit and tested in both directions:

```
[+] matches the reference across the sampled domain a<2^16
[+] differs outside it, as intended: T(0x00010000)=0xb105f00d vs ref 0x8d01b964
[+] T(0xDEADBEEF) = 0xb105f00d (want 0xb105f00d)
```

The "must DIFFER outside the domain" step matters as much as the "must MATCH inside the domain" one: it is the
exact statement of the win condition.

**Step 4 - Submitting over the socket and reading the result.**

```
CERTIFIED: equivalent to the golden reference.
audit: T(0xDEADBEEF) = 0xB105F00D
sign-off compromised -- a certified design carries a trojan.
H7CTF{afd4beac-e86e-409b-907d-b519bb748599}
```

## Flag
```bash
python exploit.py pwn.h7tex.com 40634
```

The exploit was verified exactly once, at step 4; right after that the service stopped responding (0
bytes over 3 attempts) so it cannot be rerun for comparison. The transcript above is the real output
of that single successful run.
