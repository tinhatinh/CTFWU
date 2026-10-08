# Yummy Rat Toast - Password Cracking (500 points)

**Flag:** `cdctf{Alfredo Linguini01}` · **Points:** 500 · **Author:** alex
**Files:** `hash.txt` (33 B, sha256 `082b5ad8c25c7437967bbb2c0b10c434fb6a95a8529b9d6e7c3fa09aa139f1bb`)

## Challenge

The card gives one md5 digest, `3f1ebefc63dc39f3c9b934a30accb221`, and states the password is "based on the
name of a good friend of his". The narrator's friend is a rat called Remy, and Remy quotes "Anyone can cook"
by a wise friend. Both details point at the film Ratatouille: Remy, Alfredo Linguini, chef Auguste Gusteau.
Flag format for the event is `cdctf{...}`.

## Analysis

There is no artifact, the input is a 16-byte digest, so the first job was to measure how hard it actually is.
The gromweb reverse-md5 database (832,927,522 known sums) finds nothing:

```text
Provided MD5 hash could not be reversed into a string: no reverse string was found.
```

The queried database returned no match. Local mask attacks on an RTX 3050 (9.6 GH/s for `-m 0`) also found no preimage among lowercase strings of length 1..8 and digit strings of length 1..12. These results exclude only the tested sets:

```text
Exhausted  26/26              Exhausted  308915776/308915776
Exhausted  676/676            Exhausted  8031810176/8031810176
Exhausted  17576/17576        Exhausted  208827064576/208827064576
Exhausted  456976/456976
Exhausted  11881376/11881376
```

The Ratatouille clue motivates a wordlist of character names, including full names with spaces and numeric suffixes. The earlier masks do not exclude all other password formats.

## Approaches tried

1. **Common passwords**: 27.7M lines from xato-net-10M, Pwdb_top-10M, darkc0de, alleged-gmail,
   openwall.net-all and rockyou-75, plain and with `best64` (2,138,454,780 candidates, Exhausted) and
   `T0XlC`. No match.
2. **Personal names and the English dictionary**: 443,026 lines (names.txt, male/female/family top-1000,
   words_alpha, rockyou-75) times `dive.rule` (99,092 rules), `rockyou-30000`, `d3ad0ne`,
   `Incisive-leetspeak`. Exhausted.
3. **Joined names from big corpora**: 10M xato usernames and 2.4M Wikipedia en/fr/de words plus Brazilian,
   Indian and Danish name lists, plus combinator runs. Partly void at first: two batches called hashcat with
   the wrong positional order and therefore tested nothing (see `notes.md` H6). Re-run correctly, still no match.
4. **Not really md5**: the brief says "which is in md5, of course". Other 16-byte digests were attempted;
   only MD4 (`-m 3000`) accepts a bare 32-hex hashfile and it ran `theme.txt` to Exhausted. `-m 6000`,
   `-m 10` and `-m 2400` refuse to load the hash, so they are not valid tests.
5. **Encodings and double hashing**: 49,566,060 candidates through UTF-8, UTF-16, UTF-16LE/BE, UTF-32,
   latin-1, cp1252, with and without `\n` and `\r\n`; 26,405,190 forms of double hashing
   (md5(md5(x)) as hex and as raw digest), `cdctf{}`/`flag{}` wrappers, and `alex`/`rat` as prefix and suffix.
   No match.
6. **Lowercase strings of length 1-8 and digit strings 1-12**: fully Exhausted, so the password must contain
   something other than `a-z`. This removes every plain guess of the `linguini`, `ratatouille`,
   `anyonecancook` type.

## Solution

**Step 1 - Build a wordlist for the actual setting.** Take the cast and crew of Ratatouille (Remy, Alfredo
Linguini, Skinner, Django, Émile, Anton Ego, Auguste Gusteau, Colette Tatou, Horst, Lalo, Mustafa, Talon
Labarthe, Ambrister Minion, Brad Bird, Michael Giacchino, Patton Oswalt, Lou Romano, Ian Holm, Brian Dennehy,
Peter Sohn, Peter O'Toole, Janeane Garofalo, Will Arnett, John Ratzenberger), join every name with every other
using three separators (none, space, dot), then multiply by three case forms (lower, title, upper). The result
is 197,928 lines and it already contains the "Alfredo Linguini" shape that no rule can invent.

```python
SEPARATORS = ["", " ", "."]
CASES = [str.lower, str.title, str.upper]
for a in names:
    for b in names:
        if a != b:
            for sep in SEPARATORS:
                bases.append(a + sep + b)
```

**Step 2 - Let `dive.rule` handle the tail.** The wordlist only has to cover the name part; suffixes such as
`01`, `!` and leet variants come from `dive.rule` (99,092 rules). Run on the iGPU (44.98 MH/s because this is
a wordlist plus a long rule stack):

```bash
hashcat -m 0 -w 3 --backend-devices=3 --potfile-path=pot_3 --outfile=out_3.txt \
  -a 0 hc.txt theme3.txt -r rules/dive.rule
```

```text
Session..........: stheme3+dive3603
Status...........: Cracked
Hash.Mode........: 0 (MD5)
Speed.#3.........: 44977.2 kH/s (86.33ms) @ Accel:8 Loops:128 Thr:64 Vec:1
Progress.........: 4194304/19611893808 (0.02%)
Candidates.#3....: Alfredo -> GIACCHINO CHEESE!
```

```text
3f1ebefc63dc39f3c9b934a30accb221:Alfredo Linguini01
```

**Step 3 - Verify.** Recompute the md5 in Python, independent of hashcat, with a bounded search space inside
`exploit.py` so the result is reproducible without rules:

```bash
python exploit.py files/hash.txt
```

```text
candidates tried : 112500 in 0.2 s
password         : Alfredo Linguini01
FLAG             : cdctf{Alfredo Linguini01}
written          : C:\Users\Administrator\Downloads\CTFWU\CDCTF 2026\yummy-rat-toast\flag.txt
```

## Result

```
cdctf{Alfredo Linguini01}
```

## Reproduce

```bash
python exploit.py files/hash.txt
```

The script regenerates the cast names, joins them, tries three case forms and the numeric tails `""`,
`00`-`99`, `1900`-`2029`, prints the password and writes `flag.txt`. To repeat the exact path used during the
contest, run `theme3.txt` with `rules/dive.rule` as in Step 2; the answer sits at candidate 4,194,304 out of
19.6 billion.
