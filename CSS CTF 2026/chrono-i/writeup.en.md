# Chrono I — Crypto (Beginner)

**Flag:** `CSSCTF{every_second_hides_a_secret}` · **Files:** none, every fact sits on the challenge card

## Challenge

The card gives one message and one ciphertext:

```text
Message:    2026-09-21 14:35:07 - "As always, The time is always the key to unlock it"
Ciphertext: ESUITO{gwfvb_xejqnf_nimgt_b_whhrlv}
```

The flag format is `CSSCTF{...}`, so the first six ciphertext characters correspond to
`CSSCTF`. That crib is handed to us, nothing to guess.

## Initial Analysis

Comparing the crib position by position:

| position | plain | cipher | shift mod 26 |
|---|---|---|---|
| 1 | C | E | 2 |
| 2 | S | U | 0 |
| 3 | S | I | 2 |
| 4 | C | T | 6 |
| 5 | T | O | 0 |
| 6 | F | O | 9 |

The shift sequence `2 0 2 6 0 9` is the first six digits of `20260921143507`, which is the
message timestamp with the separators removed: `2026-09-21 14:35:07`. When the card says "the
time is always the key" it means it literally: the key is that timestamp, the cipher is a
numeric Vigenère (Gronsfeld) with period 14.

## Approaches Ruled Out

Before settling on this, these channels were eliminated (full log in `notes.md`):

1. **Single-alphabet substitution**: the `S` at position 2 and 3 encrypts to `U` then `I`, which
   one alphabet cannot do. Ruled out.
2. **Pure transposition**: the multiset of `ESUITO` differs from `CSSCTF`, and permuting never
   changes a multiset. Ruled out.
3. **Beaufort and its variant**: with the same crib, Beaufort needs key `6 10 12 10 12 19` and
   the variant needs `24 0 24 20 0 17`; neither reads as anything time-related. Ruled out.
4. **Other ways to derive a key from a timestamp**: epoch seconds (UTC, UTC+7, AEST, EDT),
   cumulative digit sums, digit pairs, base 26, hex, each date/time field multiplied by its
   index. 95 sources were tried and only the raw digit string of `20260921...` matches the crib.
   All ruled out.

## Exploit Chain

**Step 1 — Take the key from the message.** Drop every non-digit character:

```python
key = re.sub(r"\D", "", "2026-09-21 14:35:07")   # '20260921143507'
```

**Step 2 — Confirm the crib.** Shift the first six ciphertext characters by the first six digits:

```
CSSCTF -> ESUITO : shift [2, 0, 2, 6, 0, 9]   # khop key[0:6]
```

**Step 3 — Decrypt the body with a counter that only advances on letters.** Counting `{` and `_`
as key positions yields garbage, so the key walks the letters only while the punctuation stays:

```python
for ch in text:
    if not ch.isalpha():
        out.append(ch)          # giu nguyên '{', '}', '_'
        continue
    k = int(key[i % len(key)]); i += 1
    base = 65 if ch.isupper() else 97
    out.append(chr((ord(ch) - base - k) % 26 + base))
```

This returns `CSSCTF{every_second_hides_a_secret}`, which is exactly the sentence the card hinted
at.

**Step 4 — Verify.** Both directions agree: re-encrypting the plaintext with the same key returns
the original ciphertext, and the body is plain `[a-z0-9_]*`. Three mutations were tried (last body
letter capitalised, the message hour changed to `15:35:07`, `ESUITO` changed to `XSUITO`) and the
script stops at the corresponding check, so this is not a self-confirming loop.

## Flag

```
$ python exploit.py
1) key = chu so cua message : 20260921143507 (14 chu so)
2) crib CSSCTF -> ESUITO : shift [2, 0, 2, 6, 0, 9]
   khop 100% so chu cai dau cua key -> Gronsfeld voi key = 20260921143507
3) giai ma toan bo : CSSCTF{every_second_hides_a_secret}
4) phep giai la nghich dao dung cua phep ma hoa
5) du dinh dang CSSCTF{...}, than co la snake_case

FLAG: CSSCTF{every_second_hides_a_secret}
```

## Reproduce

```bash
python exploit.py
```
