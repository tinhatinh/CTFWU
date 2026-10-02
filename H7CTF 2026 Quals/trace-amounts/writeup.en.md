# Trace Amounts — Hardware (Medium)

**Flag:** `H7CTF{48333086-d56b-41f5-b24b-a1d53fb122ec}` · The card's AES-128 key: `f937e70cf8f9f6f287a14b0da829ba47`

## Challenge

A contactless card runs AES-128 to approve each tap. A current probe is clipped onto the power line and 500 approvals
are recorded, together with the known plaintext challenge of each one. The key never leaves the chip - but its electrical
trace does. Three files are given: `traces.npy` (500×700), `plaintexts.npy` (500×16)
and `secret.enc` (48 B, exactly 3 AES-ECB blocks). The job: recover the key, then decrypt `secret.enc`.

## Initial Analysis

The challenge page is a Python `SimpleHTTP` listing the three resources outright, so there is no route to hunt for.
Onto the main work: Correlation Power Analysis (CPA) on the first round of AES.

For plaintext byte `i`, each candidate key `k` gives one predicted intermediate value `S-box[pt_i ^ k]`.
If the chip leaks according to the Hamming model, the sample applying `HW(S-box[pt_i ^ k])` will correlate strongly with
the exact sample where that transformation happens, and only for the correct `k`.

Normalising the data:

```
traces     (500, 700) float32   mean 0.06, std ~1.0
plaintexts (500, 16)  uint8
```

With 500 traces, the correlation coefficient of pure noise has standard deviation `1/sqrt(500) = 0.045`;
projected over the number of trials (16 bytes × 256 keys × 700 samples) the largest random peak lands around 0.21.
That number is the yardstick for knowing when there is real signal - and it is exactly what makes this challenge
interesting, because my first run gave precisely 0.21 everywhere.

## Exploit Chain

**Step 1 - Reading the trace's time structure.** The energy spectrum per sample (`mean trace` and `variance profile`)
betrays a very clean sequential pattern: peaks at samples 30, 70, 110, ..., 630 - 16 peaks spaced 40 samples apart.
16 peaks = 16 bytes, i.e. the chip processes the state's bytes one after another, byte `i` sitting in slot `30 + 40*i`.
This tells us which samples to look at, and it is also how a wrong model gets detected: if there are 16 clearly active
slots yet the correlation still equals the floor, the problem is in the prediction function.

**Step 2 - Fixing the model, sweeping again per slot.** `analysis/sweep.py` tries 6 models × 16 bytes × 256 keys,
computing the vectorised Pearson correlation within each slot. The result separates decisively:

```
byte  0 HW(S[xor])  k=0xf9  sample  30  |r|=0.731
byte  6 HW(S[xor])  k=0xf6  sample 270  |r|=0.740
byte 13 HW(S[xor])  k=0x29  sample 550  |r|=0.736
...
```

Every other byte (15/16) also reaches 0.67-0.74, while each byte's runner-up falls back to ~0.20.
The time peaks match the slot formula exactly - proof that the model is right and not a statistical fluke.

**Step 3 - Assembling the key and decrypting.** The 16 bytes collected: `f937e70c f8f9f6f2 87a14b0d a829ba47`.
Decrypting `secret.enc` with AES-128-ECB using that key:

```
H7CTF{48333086-d56b-41f5-b24b-a1d53fb122ec}
```

The 48 B decode to a 43 B flag + a final 5 bytes of `0x05` (`pt[-5:] == 5*0x05`), i.e. valid PKCS#7 - one more layer
confirming the key, since a single wrong byte turns the 48 output bytes into garbage with no padding.

**Step 4 - Cross-verification.** The key is recovered without needing `secret.enc`; that file is only the final test.
So I keep two independent indicators: (a) 16/16 bytes at |r| ~0.7, absolutely separated from the runner-up,
and (b) the decrypted plaintext being an ASCII string with a UUID shape + valid padding. A key off by one byte would
give 48 garbage bytes and could not produce that structure.

## Flag
```bash
python exploit.py files/traces.npy files/plaintexts.npy files/secret.enc
```

```
    byte  0: k=0xf9  |r|=0.731  runner-up |r|=0.199
    ...
    byte 15: k=0x47  |r|=0.673  runner-up |r|=0.197
[+] AES-128 key: f937e70cf8f9f6f287a14b0da829ba47
[+] decrypted: 'H7CTF{48333086-d56b-41f5-b24b-a1d53fb122ec}'
[+] flag: H7CTF{48333086-d56b-41f5-b24b-a1d53fb122ec}
```

The whole run takes 0.35 s.
