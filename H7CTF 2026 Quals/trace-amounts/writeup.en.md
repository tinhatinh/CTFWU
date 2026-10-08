# Trace Amounts - Hardware (Medium)

**Flag:** `H7CTF{48333086-d56b-41f5-b24b-a1d53fb122ec}` · The card's AES-128 key: `f937e70cf8f9f6f287a14b0da829ba47`

## Challenge

A contactless card runs AES-128 to approve each tap. A current probe is clipped onto the power line and 500 approvals
are recorded, together with the known plaintext challenge of each one. The key never leaves the chip - but its electrical
trace does. Three files are given: `traces.npy` (500×700), `plaintexts.npy` (500×16)
and `secret.enc` (48 B, exactly 3 AES-ECB blocks). The job: recover the key, then decrypt `secret.enc`.

## Analysis

The challenge page is a Python `SimpleHTTP` listing the three resources outright, so there is no route to hunt for.
Onto the main work: Correlation Power Analysis (CPA) on the first round of AES.

A leakage model predicts `HW(S-box[pt_i ^ k])` for each candidate `k`. Compare this with the measured traces and rank candidates by correlation. The highest-scoring candidates are checked against the ciphertext after recovering all sixteen bytes.

Normalising the data:

```
traces     (500, 700) float32   mean 0.06, std ~1.0
plaintexts (500, 16)  uint8
```
For 500 traces, the approximate standard deviation of a pure-noise correlation is `1/sqrt(500) = 0.045`. Across the tested combinations of 16 bytes, 256 keys and 700 samples, noise peaks were around 0.21. The initial sweep was near this level, so the analysis checked other leakage models and time windows.

## Solution

**Step 1 - Reading the trace's time structure.** The energy spectrum per sample (`mean trace` and `variance profile`)
betrays a very clean sequential pattern: peaks at samples 30, 70, 110,..., 630 - 16 peaks spaced 40 samples apart.
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
The correlation peaks fall within the predicted slots, supporting the selected model. Decrypting the ciphertext provides a separate check of the recovered key.

**Step 3 - Assembling the key and decrypting.** The 16 bytes collected: `f937e70c f8f9f6f2 87a14b0d a829ba47`.
Decrypting `secret.enc` with AES-128-ECB using that key:

```
H7CTF{48333086-d56b-41f5-b24b-a1d53fb122ec}
```
The plaintext contains a 43-byte flag followed by five `0x05` bytes (`pt[-5:] == 5*0x05`), which is valid PKCS#7 padding. Padding and flag format are additional checks of the CPA result; they are not by themselves a proof that every other key is impossible.

Two results are compared: all sixteen bytes have |r| around 0.7 versus about 0.20 for the next candidate, and the decrypted plaintext has a UUID-shaped flag with valid padding. These checks agree with the recovered key on the supplied data.

## Result
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
