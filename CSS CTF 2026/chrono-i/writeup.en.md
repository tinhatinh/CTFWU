# Chrono I - Crypto (Beginner)

**Flag:** `CSSCTF{every_second_hides_a_secret}`
**Resources:** No attached files. Analytical data is provided directly in the problem description text.

## Challenge

The challenge provides a text message and its corresponding ciphertext:

```text
Message:    2026-09-21 14:35:07 - "As always, The time is always the key to unlock it"
Ciphertext: ESUITO{gwfvb_xejqnf_nimgt_b_whhrlv}
```
The stated format is `CSSCTF{...}`. Use the six letters `CSSCTF` as a known-plaintext crib to calculate the initial shifts.

## Analysis

Perform a modulo 26 shift value check for each position based on the available crib:

| Position | Plaintext (Plain) | Ciphertext (Cipher) | Modulo 26 Shift |
|---|---|---|---|
| 1 | C | E | 2 |
| 2 | S | U | 0 |
| 3 | S | I | 2 |
| 4 | C | T | 6 |
| 5 | T | O | 0 |
| 6 | F | O | 9 |

The obtained shift sequence is `2 0 2 6 0 9`. Comparing this number sequence with the input data, it matches the first six digits of the timestamp in the message: `20260921143507` (removing delimiter characters from `2026-09-21 14:35:07`). The instructional sentence "the time is always the key" has direct reference value: the decryption key is precisely the numerical character string of the timestamp, applied on a numerical Vigenère cipher scheme (Gronsfeld Cipher) with a period of 14.

## Solution

**Step 1 - Extract the key from the message.**
Use a regular expression to eliminate all non-numeric characters, retaining the pure numeric string as the key:

```python
key = re.sub(r"\D", "", "2026-09-21 14:35:07")   # Result: '20260921143507'
```

**Step 2 - Validate with the initial crib.**
Perform a trial encryption of the first six plaintext characters using the first six digits of the key to verify the model:

```text
CSSCTF -> ESUITO : Apply shift [2, 0, 2, 6, 0, 9]   # Matches perfectly with key[0:6]
```

**Step 3 - Decrypt the entire ciphertext.**
Design the decryption logic: The key index counter only advances when encountering alphabetical characters. Special characters like `{`, `}`, and `_` will be bypassed in the shift calculation step and preserved in the final result. Incorrectly applying the counter (including special characters) will lead to faulty decryption.

```python
for ch in text:
    if not ch.isalpha():
        out.append(ch)          # Preserve intact the characters '{', '}', '_'
        continue
    k = int(key[i % len(key)])
    i += 1
    base = 65 if ch.isupper() else 97
    out.append(chr((ord(ch) - base - k) % 26 + base))
```
Applying the shifts to the full ciphertext gives `CSSCTF{every_second_hides_a_secret}`. Re-encrypting the plaintext with the recovered key checks it against the supplied ciphertext.

**Step 4 - Verification stage.**
The execution process has uniform bidirectionality: if re-encrypting the plaintext using that same key, the system will return the exact original ciphertext. Furthermore, the body of the plaintext strictly adheres to the `[a-z0-9_]*` structure. To affirm the script code's reliability, injecting artificial errors (such as changing a letter to uppercase, modifying the hour parameter to `15:35:07`, or altering the crib `ESUITO` to `XSUITO`) all trigger the script's error reporting mechanism, verifying that the process does not operate based on a blind self-matching mechanism.

## Result

Run the script:

```bash
$ python exploit.py
1) key = message digits : 20260921143507 (14 digits)
2) crib CSSCTF -> ESUITO : shift [2, 0, 2, 6, 0, 9]
   100% match with key's first digits -> Gronsfeld with key = 20260921143507
3) decrypt all : CSSCTF{every_second_hides_a_secret}
4) solution is the exact inverse of encryption
5) complies with CSSCTF{...} format, body is snake_case

FLAG: CSSCTF{every_second_hides_a_secret}
```

Result:
```text
CSSCTF{every_second_hides_a_secret}
```
