# invisible-text - STEG (200 pts)

**Flag:** `POCTF{PIEMPAOSMHDLEGRT}` · **Files:** `invisible_text.py`, 4245 B, sha256 `f027442b37a521f4a775ec56d37336df446d83e7acd641042e28af030f745320`

## Challenge

The author says the file contains a secret message, and that you will see it if you "look in the right place". The challenge gives only `invisible_text.py`, generated specifically for the team (the server serves the file under the name `invisible_text_612.py`), no binary, no remote service. What has to be done: read out the message stored in the source file itself, then submit it.

## Initial Analysis

The file is plain Python, 4245 bytes, 81 lines, UTF-8. A byte inventory shows the whole file has exactly one character outside ASCII, the `-` in a comment. No Zero Width Space, no BOM, no NBSP, no lookalike characters.

The single remaining anomaly: **47/81 lines end in whitespace**. Concretely:

```
dòng 1   SSSTSTSSSS        (10 ký tự)
dòng 2   T                 (1 tab)
dòng 3   SSSSSTSSTTTT      (12 ký tự)
dòng 4   T
dòng 5   SSSSSTSSSSTT
...
dòng 45  SSSSSTTTTTST
dòng 46  T
dòng 47  SS                (2 ký tự)
```

Odd lines are 12 characters long (the very first line only 10), even lines are exactly one tab. The phrase "look closely" in the challenge points straight at this string.

The file's obvious content: `diary_reader.py` joins 46 base64 chunks into one string, `b64decode`s it, then `zlib.decompress`, and prints the result. Running it (you must write the output to a UTF-8 file because the Windows console is cp1252 and `print` would raise `UnicodeEncodeError`) yields 2145 braille characters over 33 lines.

## Directions ruled out

The full log is in `notes.md`. Summary:

1. **Invisible Unicode hidden inside the strings**: counting the frequency of U+200B-U+200F, U+FEFF, U+00A0 -> no character caught at all. Ruled out.
2. **The base64 + zlib payload being where the flag is kept**: it decodes to a braille picture, not to text. Ruled out.
3. **Braille hiding data in the dot count per cell**: the histogram gives 115 full 8-dot cells (255), 85 cells at 251, 79 cells at 253 -> that is a solid filled region of a picture, not an encoding. Ruled out.
4. **Trailing whitespace as continuous 8-bit binary**: concatenating the 299 characters and cutting them into 8-bit groups, trying both `space=0/tab=1` and `space=1/tab=0` plus bit-reversed -> all four variants give garbage bytes, no `POCTF`. Ruled out.
5. **The Whitespace language (esolang)**: Whitespace needs LF to terminate a number, but here no group contains an LF and the group length is fixed at 12. Ruled out.

## Exploit Chain

**Step 1 - Notice the fixed group length.** Every data line carries 12 whitespace characters, and the sixth position is **always a tab**. That is the signature of a 7-bit scheme: the first five spaces are column padding, the last seven characters are the code.

**Step 2 - Cut out the last seven characters, `tab = 1`, `space = 0`.** A printable ASCII character always has MSB equal to 1, so the 7-bit group beginning with 1 is precisely the region holding its own name - this is the anchoring point:

```python
for line in src.split("\n"):
    tail = line[len(line.rstrip()):]
    if len(tail) < 7:
        continue
    bits = tail[-7:].replace(" ", "0").replace("\t", "1")
    flag += chr(int(bits, 2))
```

The real output:

```
  line   1  TSTSSSS  =  80  'P'
  line   3  TSSTTTT  =  79  'O'
  line   5  TSSSSTT  =  67  'C'
  line   7  TSTSTSS  =  84  'T'
  line   9  TSSSTTS  =  70  'F'
  line  11  TTTTSTT  = 123  '{'
  ...
  line  45  TTTTTST  = 125  '}'
MESSAGE: POCTF{PIEMPAOSMHDLEGRT}
```

**Step 3 - Verify it is no coincidence.** Three matches: (a) 22/22 of the 12-character groups have the tab at exactly one position (the group's leading bit), (b) the number of data lines = 23 = the length of `POCTF{` + 16 + `}`, (c) the 16 uppercase flag body matches the event's flag format. The surplus leading spaces (5 spaces, only 3 on line 1 because that line starts earlier) are just column alignment and carry no information.

**Step 4 - Submit.**

```
POST /challenges/invisible-text/submit
{"flag":"POCTF{PIEMPAOSMHDLEGRT}"}
```

```
HTTP 200 :: {"correct":true,"message":"Correct."}
```

## Flag

```
POCTF{PIEMPAOSMHDLEGRT}
```

The server confirms it as correct and returns no other flag string, so this is the entire value obtained. The decisive idea: the message sits in the **trailing whitespace** of the source file, not in the script's output; and the whole base64 + zlib + braille layer is nothing but a redirecting lure.

## Reproduce

```bash
python exploit.py files/invisible_text.py
```
