# Chrono II - Crypto (Intermediate)

**Flag:** `CSSCTF{th3_cl0ck_r3m3mb3rs_3very_s3c0nd}`
**Resources:** No attached files. The necessary data is extracted directly from an operating online service.

## Problem Description

The challenge provides a service at `http://34.116.80.78:8001`, along with information that the intercepted data segment has a "constantly changing" nature. The analyst's task is to collect ciphertexts from this service and reconstruct the original plaintext.
This problem is the sequel to "Chrono I". In the previous part, the cryptosystem was identified as a numeric Vigenère (Gronsfeld cipher with a period of 14) with a static key derived from a timestamp. In this upgraded version (Chrono II), the cryptographic model remains the same, but the encryption key is designed as a dynamic keystream that changes based on the progression of time (the clock).

## Initial Analysis

The service interface operates like a signal receiving station, displaying access ports. The `/api/feed` port responds with a list of 60 records structured as `{timestamp, ciphertext}` (equivalent to an update rate of one record per second). The `/capture.json` path statically stores an extracted 60-second data batch.

By randomly examining 60 data lines, two main technical characteristics were identified:

- The ciphertext maintains a fixed format: `UUUUUU{lll_lllll_lllllllll_lllll_llllll}`. Numeric characters alternately appear at the exact same positional system across all lines. It is assumed that if the plaintext were constantly changing, the probability of maintaining such a rigid structural pattern is zero. Deduction: The plaintext is a static constant, only the encryption key linearly changes per second.
- Separator characters such as `_`, `{`, and `}` appear intact and do not change positions. This proves the encryption stream is configured to ignore these characters.

The processing system is split into three data domains: Uppercase letters (modulo 26), lowercase letters (modulo 26), and digits (modulo 10).

Since the plaintext is a static value and the flag format is a known standard (`CSSCTF{...}`), the first six characters of all ciphertext lines are always the encrypted result of the `CSSCTF` prefix. This information serves as a crib, helping to accurately expose 6 characters of the keystream for each collected second.

## Exploitation Chain

In the recorded environment, requests with `curl` and Python sockets timed out, while the browser could load the page. The application stores its feed response in the `capture` variable, so the data was collected through the browser.

```javascript
capture.map(r => r.timestamp + ' ' + r.ciphertext).join('\n')
```

Attempting to call `fetch('/api/feed')` from the website's console will be blocked by the Content Security Policy (CSP). Navigating directly to `/capture.json` also returns an `ERR_FAILED` error. Directly extracting the value of the `capture` variable in the application's memory is the safest and most efficient data collection method.

**Step 2 - Determine the periodicity of the Keystream.** 
Perform cross-analysis on two collection timeframes: Window A (06:38:27 - 06:39:26) and Window B (07:00:51 - 07:01:50). The results show 43 identical ciphertexts overlapping completely between the two timeframes. The time delta of these ciphertexts falls into only two fixed values: 1309 seconds and 1386 seconds.

```text
1309 = 17 * 77
1386 = 18 * 77
Greatest common divisor: gcd(1309, 1386) = 77
```

Based on this result, the keystream position function is periodic: `o(t + 77) = o(t)`, confirming the system's period is 77. The number 77 also matches the statistical data: Within a 60-second collection window, there will be 17 lines with no corresponding subsequent data, because `77 - 60 = 17` gap offsets.

**Step 3 - Calculate the step size of the time translation function.** 
For every pair of data lines whose 6-character string can overlap with a certain shift offset `d` (between 1 and 5), run a linear regression model according to the formula `d == (g * dt) mod 77`, with the variable `g` running from 1 to 76.

```text
Optimal step size g = (43, 460)   # Result: 460/965 data pairs matched (Whereas random noise only achieved approximately 12.5)
```

Conclusion for the keystream's position function: `o(T) = (43 * T) mod 77`.

**Step 4 - Fully Reconstruct the Keystream.** 
Each data line provides 6 values (symbols) for the keystream at positions from `o(T)` to `o(T)+5`. Using a dataset of 120 lines collected from the two windows, the system is able to cover all 77 positions without recording any conflicts.

```python
K = {}
for T, ct in rows:
    base = (43 * T) % 77
    for j, (a, b) in enumerate(zip(ct[:6], "CSSCTF")):
        K[(base + j) % 77] = (ord(a) - 65 - (ord(b) - 65)) % 26
# Process complete: Recovered 77/77 symbols, conflict rate is 0
```

**Step 5 - Design the decryption algorithm.** 
The crux of the algorithm: The key index pointer only advances when the system processes a character that is actually encrypted. Characters like `_`, `{`, and `}` will be passed straight to the plaintext without consuming any characters from the keystream.

```python
def dec(T, ct):
    i = 0
    o = (43 * T) % 77
    out = []
    for ch in ct:
        if ch in "_{}":
            out.append(ch)
            continue          # Skip, do not advance the pointer i
        base, m = (65,26) if ch.isupper() else (97,26) if ch.islower() else (48,10)
        out.append(chr(base + (ord(ch) - base - K[(o+i) % 77]) % m))
        i += 1
    return "".join(out)
```

All 120 ciphertexts were successfully decrypted and converged to a single plaintext.

**Step 6 - Validate the model on an independent dataset.** 
To ensure the integrity of the decryption model, a new dataset (untrained) from the time window 07:09:46 - 07:10:45 (consisting of 60 lines) was collected. Apply the reconstructed keystream from the previous step to decrypt:

```text
Training set (train rows) = 120  | Testing set (held-out rows) = 60
Successful decryption result: n= 60/60 -> CSSCTF{th3_cl0ck_r3m3mb3rs_3very_s3c0nd}
```

The results did not incur any deviation. The period of 77 was also proven once more through visual comparison: The data line `HIWLWH{bp6_...}` at the 06:38:58 mark reappeared exactly at the 07:09:46 mark. The time difference is exactly 1848 seconds, equivalent to a multiplier of `24 x 77` seconds.

## Flag

Executing the decryption script:

```bash
python exploit.py analysis/rows.txt analysis/feed2.txt
```

```text
[*] 120 rows, 1 distinct plaintexts, best has 120
[flag] CSSCTF{th3_cl0ck_r3m3mb3rs_3very_s3c0nd}
```

Result:
```text
CSSCTF{th3_cl0ck_r3m3mb3rs_3very_s3c0nd}
```
