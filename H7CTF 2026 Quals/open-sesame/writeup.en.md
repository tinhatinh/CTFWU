# Open Sesame - Hardware (Hard)

**Flag:** `H7CTF{f6091c17-1155-4d06-8a90-b826fd758185}` (received from `/unlock`, saved in `flag.txt`)
**Target:** `https://web-7a56034b5423964c.web.h7tex.com` · Artifact: `capture.cf32` (I/Q float32 LE @ 1 MHz)

## Challenge

A cheap garage remote emits a fresh code on every press, and the challenge gives exactly 8 presses captured as raw
baseband. The hint: "unguessable" is not the same as "unpredictable". The job is to compute the code the remote will
transmit on the 9th press and submit it to the service.

## Initial Analysis

`capture.cf32` = I/Q float32 LE @ 1 MHz. The host has no GNU Radio and no urh, so the demodulation is done by hand.

## Exploit Chain

**Step 1 - Envelope.** `env = I^2 + Q^2`, smoothed over a 20 µs window to flatten ripple within one chip.

**Step 2 - OOK threshold.** `p1 + 0.35*(max - p1)` → 392 bursts.

**Step 3 - Splitting the presses.** Break on silence gaps > 1.5 ms → exactly 8 presses (7 long gaps of ~10T).

**Step 4 - Reading the bits inside one press.** The run-lengths take only two widths, 1T and 2T with T = 303 µs, and
97 runs = 1 + 2×48 → 48 bits, each bit being an (H,L) pair: `H1L2` = 0, `H2L1` = 1.

**Step 5 - The eight recovered frames.**

```
4f122809be13
4f122809c117
4f122809c41a
4f122809c71d
4f122809ca10
4f122809cd13
4f122809d017
4f122809d31a
```

**Step 6 - Rolling code model.** Splitting the 48 bits into `32 bit fixed | 12 bit counter | 4 bit checksum`:

| press | counter | crc nibble | sum of first 11 nibbles mod 16 |
| --- | --- | --- | --- |
| 0 | 0xbe1 | 3 | 3 |
| 1 | 0xc11 | 7 | 7 |
| 2 | 0xc41 | a | a |
| 3 | 0xc71 | d | d |
| 4 | 0xca1 | 0 | 0 |
| 5 | 0xcd1 | 3 | 3 |
| 6 | 0xd01 | 7 | 7 |
| 7 | 0xd31 | a | a |

- The counter steps uniformly by `+0x30` across all 8 presses.
- `crc = (sum of the first 11 nibble values) mod 16`, matching all 8 frames.

The code really does change with every press, but only because the counter does. That is where "unguessable ≠
unpredictable" bites: the generator is a public counter plus a checksum computed by nibble addition.

**Step 7 - Predicting the 9th press.**

```
counter = 0xd31 + 0x30 = 0xd61
frame   = 4f122809 d61  + crc
crc     = (4+15+1+2+2+8+0+9 + 13+6+1) mod 16 = 61 mod 16 = 13 = d
code    = 4f122809d61d
```

**Step 8 - Verifying correctness.** Both invariants above are checked over all 8 frames rather than a single one: the
first 32 bits are identical in every frame, and the counter difference between two consecutive frames is always `0x30`.
For each frame, the crc recomputed from the formula equals the last nibble exactly.

## Flag
```
python solve.py https://web-7a56034b5423964c.web.h7tex.com analysis/capture.cf32 --submit
[*] /unlock -> 200
{"status": "unlocked", "flag": "H7CTF{f6091c17-1155-4d06-8a90-b826fd758185}"}
```
