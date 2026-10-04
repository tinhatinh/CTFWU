# Best of Friends - Crypto (500 points)

**Flag:** `cdctf{friendshipisalotlikecheese}`
**Files:** `files/bestfriends.txt`, 107 bytes, sha256 `24d05085a4c80d16f3110682536ec0d314ae49412ebe0b4a7285f0a98c537269`

## Challenge

adlee7 ships a single ciphertext file and a Tom & Jerry hint, the cat-and-mouse pair
"stuck in an endless loop of chasing each other since 1940". The flag format is
`cdctf{plaintextgoeshere}`, so the decoded output has to be a lowercase letter string
with no spaces.

## Initial Analysis

```text
//\ /\// /\\\ /\ \/// //// \/\ /\\ /\\\ //\/ /\\\ \/\ / \\\/ /\/ \\/\ \\\/ /\\\ \\/ /\ /// /\\ /\ /\ \/\ /\
```

- 107 bytes = 82 symbols + 25 spaces. Nothing outside `/`, `\` and space occurs in
  the file: no BOM, no trailing newline, no hidden byte, no additional byte-level data was found.
- 26 groups but only 15 distinct shapes. Groups repeat as whole shapes: `/\` 5 times,
  `/\\\` 4 times, `\/\` 3 times, `\\\/` and `/\\` twice each.
- Group lengths run 1 to 4 (histogram 1/5/9/11). Equal symbol counts in a different
  order are still different shapes: `(3 slashes, 1 backslash)` is `\///`, `//\/` and
  `/\//`; `(1 slash, 2 backslashes)` is `/\\`, `\/\` and `\\/`. The unit of the code is
  the shape, not the counts.
- That whole-shape repetition is the signature of a one-to-one substitution alphabet
  (shape = letter), not of a positional bit code.

## Directions Tried and Ruled Out

Numbers quoted here are reproduced by `python analysis/triage.py` (log kept in
`analysis/triage.txt`).

1. **Morse, one group per letter**: 24 of 26 groups are valid Morse codes with
   `/` = dit (the two `\\\/` groups, `---.`, are not in the table), 25 of 26 with
   `\` = dit (the `////` group, `----`, is not). The recovered strings
   `ULJABHKWJFJKE?RQ?JGASWAAKA` and `GYBNJ?RDBQBRTVKFVBUNODNNRN` stay meaningless
   after all 25 Caesar shifts and Vigenère/Beaufort/autokey under theme keys (TOM,
   JERRY, TOMANDJERRY, BESTFRIENDS, 1940, CAT, MOUSE, CHASE, LOOP). Rejected.
2. **Groups as numbers**: group length (1..4), slash count (0..4), backslash count
   (0..3), their difference, the group read as binary (0..14), and the number of
   direction changes. Each was read directly as A1Z26, as a running sum mod 26, and
   as two consecutive groups forming a coordinate in bases 4, 5, 6, 7, 8, 10, 16,
   26, 27. No combination produced a string containing an English word or `cdctf`.
   Rejected.
3. **Drop the spaces, read the 82 symbols as a bit stream**: 82 = 10 bytes + 2 bits of
   remainder, and reading group lengths as run-lengths of an alternating bit stream
   gives `1e 18 78 e1 e1 de 3c 3c 63 98` (4 of 10 bytes printable), or
   `e1 e7 87 1e 1e 21 c3 c3 9c 67` with the first bit inverted (2 of 10). Rejected.

## Exploit Chain

**Step 1 - Recognise the Tom-Tom alphabet.** Two symbols split into variable-length
groups separated by spaces is the structure of a two-symbol substitution alphabet.
Code Tom-Tom assigns each letter A-Z a fixed pattern of `/` and `\`. All 15 shapes in
the file match 15 letters of that table, and no two table entries collide, so the
grouping is unambiguous:

| Pattern | Letter | Pattern | Letter | Pattern | Letter | Pattern | Letter |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `/` | A | `/\` | E | `///` | C | `////` | D |
| `//\` | F | `/\\` | H | `/\\\` | I | `\\/` | K |
| `\/\` | S | `\///` | N | `/\//` | R | `//\/` | P |
| `/\/` | O | `\\\/` | L | `\\/\` | T | | |

**Step 2 - Decode and verify by round-trip.** `exploit.py` maps the 26 groups through
the table, re-encodes the resulting letters with the same table and compares the
output byte for byte with the original file:

```bash
python exploit.py files/bestfriends.txt
```

```text
groups    : 26
characters: 82
plaintext : FRIENDSHIPISALOTLIKECHEESE
round-trip: OK (re-encode khop tung byte voi file goc)
flag      : cdctf{friendshipisalotlikecheese}
```

Verification checks: all 26 groups resolve through a 1-to-1 table; the
re-encode matches all 107 bytes of the file; and the 26 letters read as the English
sentence "Friendship is a lot like cheese", which is the direction the hint points to.

## Flag

```text
cdctf{friendshipisalotlikecheese}
```

The flag is derived from the artifact; it has not been confirmed by a submission to the
platform yet.

## Reproduce

```bash
cd "CDCTF 2026/best-of-friends"
python analysis/triage.py                  # analysis data and the 3 rejected routes
python exploit.py files/bestfriends.txt    # decode plus round-trip check
```
