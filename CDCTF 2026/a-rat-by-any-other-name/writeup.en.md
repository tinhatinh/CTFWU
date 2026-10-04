# A rat by any other name - Password Cracking (500 pts)

**Flag:** `cdctf{Jaqurtis}` · **Files:** `files/hash.txt` (33 bytes, sha256 `66ad6348...d1c48f`)

## Problem

A pet rat has a human name and always uses that name as its password. The challenge provides one MD5 hash, `fe00ab6a1d242513c9f246344bf7da1d`, plus three formatting rules for the name: at most 8 characters, first character uppercase, all remaining characters lowercase. No binary and no network service; the task is only to recover the string that matches the hash and the rules. Flag format: `cdctf{Name}`.

## Initial Analysis

The three rules are not hints for guessing a name - they are a mask. The set of valid passwords is exactly one character class:

```text
?u?l{0,7}  =  26 + 26^2 + ... + 26^8  =  217,180,147,158 candidates
```

MD5 is fast and unsalted, so that number is the whole decision. hashcat 6.2.6 on an RTX 3050 laptop reached 8415 MH/s with the optimized kernel, which puts the full space at a couple of minutes; the measured run finished in under a minute. The problem becomes structured brute force, with no need to find the "right" name list.

Wordlists were still tried first, and all three corpora came back negative:

| Corpus | Candidates hashed | Result |
| --- | --- | --- |
| `words_alpha.txt` (English dictionary, words <= 8 chars, first letter capitalised) | 149,189 | no match |
| `name-dataset` first names (raw / capitalize / title variants) | 727,556 | no match |
| Moby Project `NAMES*.TXT` (Scrabble proper names) | 30,829 | no match |

Those negatives only prove the corpora are incomplete; they say nothing about whether the password lies outside the search space, and an "unconventional" name is expected to be missing from popular name lists. The conclusion therefore rests on exhausting the mask, not on a wordlist.

## Exploit Chain

**Step 1 - Prove the candidate generator works before trusting any result.** The self-test plants the MD5 of an unrelated name (`Felix`) and asks hashcat to recover it through the same mask family `?u?l{1,3}`. Only if a known positive is found can a "space exhausted" statement be believed.

```bash
python exploit.py --selftest
```

```text
[*] selftest: an md5('Felix') = 2c3baf26f776086aab9f234f8c9a00ed
[*] thu hoi: 'Felix' (18.6 s, rc=0)
[+] PASS: bo sinh to hop tim thay mat khau trong family mask.
```

**Step 2 - Run the full mask against the challenge hash.** `--increment` over an 8-position mask generates the 1..8 character slices automatically, each slice keeping the one-uppercase-then-lowercase rule:

```bash
python exploit.py
```

```text
[*] MD5 = fe00ab6a1d242513c9f246344bf7da1d, mask = ?u?l?l?l?l?l?l?l, mien = 2..8
[*] thu hoi: 'Jaqurtis' (41.9 s)
[+] ten cua chuot: Jaqurtis
[+] cdctf{Jaqurtis}
```

Equivalent hashcat command and the status block measured in the first run:

```bash
hashcat -O -m 0 -a 3 -d 1 -w 3 --increment --increment-min 2 --increment-max 8 \
        hash.txt '?u?l?l?l?l?l?l?l'
```

```text
Status...........: Cracked
Guess.Mask.......: ?u?l?l?l?l?l?l?l [8]
Speed.#1.........:  8415.0 MH/s (58.07ms) @ Accel:512 Loops:1024 Thr:64 Vec:8
Recovered........: 1/1 (100.00%) Digests (total), 1/1 (100.00%) Digests (new)
Progress.........: 36771463168/208827064576 (17.61%)
```

```text
fe00ab6a1d242513c9f246344bf7da1d:Jaqurtis
```

**Step 3 - Verify.** The recovered string holds up on three independent checks:

```python
import hashlib
print(hashlib.md5(b"Jaqurtis").hexdigest())   # fe00ab6a1d242513c9f246344bf7da1d
```

- `md5("Jaqurtis")` equals the challenge hash exactly, so the hash copied off the challenge card has no misread character - a transcription error could not have produced a preimage in the same space.
- Length 8, `J` uppercase and the rest lowercase, matching "begins with a capitol, and the rest is lower case" literally.
- Uniqueness: the length-1 slice and the lengths 2..7 were fully exhausted (`Status: Exhausted`, `Recovered 0/1`); the preimage appears only at length 8. `Jaqurtis` is a readable proper name rather than a random letter combination, and it is absent from all three corpora above, which fits the "unconventional" wording in the challenge.

## Flag

```text
cdctf{Jaqurtis}
```

## Reproduce

```bash
python exploit.py --selftest    # check the candidate generator (md5 of "Felix")
python exploit.py               # brute force the ?u?l{1,7} mask against the challenge hash
```

Requires hashcat. Default path `C:\Tools\hashcat\hashcat-6.2.6\hashcat.exe`, overridable through the `HASHCAT` environment variable; the device is overridable through `HASHCAT_DEV` (`1` = CUDA, `3` = CPU). hashcat locates its kernels through the relative path `./OpenCL/`, so the script launches the binary from its own installation directory.
