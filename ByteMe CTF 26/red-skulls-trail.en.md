---
title: "Red Skull's Trail"
category: "OSINT"
tags: ["github-history", "git-rename-trail", "png-trailer", "base64", "username-enumeration"]
solve_date: "2026-10-09"
language: "en"
---

# Red Skull's Trail

**Flag:** `OWASP{PhantomSoul}`
**Artifact:** `mr` — clone of `https://github.com/Vormir-616/Missing-Record` (21 commits, single author). Flag-bearing file: `RECORD6`, 1,917,594 B, sha256 `3ee355d92ebe3405dc0544aaf7ed9dc8e8375f81286939a50f1c826b288ce86f`. Author: Suyog Jadhav.

## Challenge

Easy, 100 points, 9 solves, challenge card created 09/10/2026. The attachment field of the card reads `File Attachments: No attachments available.` — the challenge ships no file; all data lives on GitHub.

The riddle text of the challenge was not preserved in the workspace. What was recorded is the direction it opens: the GitHub account `Vormir-616` and the repository `Missing-Record`. The repository figures below come from the clone itself and from the GitHub pages/JSON tables saved under `r/`; the creation timestamp `2026-09-20T17:34:17.000Z` specifically was read from the `repo.html` copy at `repo.html`.

## Analysis

### The repository

```console
$ git config --get remote.origin.url
https://github.com/Vormir-616/Missing-Record
$ git log --all --format='%an <%ae>' | sort -u
Vormir-616 <h3922457@gmail.com>
$ git log --all --oneline | wc -l
21
```

The repository holds six content files: `README.md` and `RECORD1`…`RECORD6`. `README.md` describes the Soul Stone going missing on Vormir and ends with "Only fragments remain".

`RECORD1`, `RECORD2`, `RECORD4` and `RECORD5` each name one user who returned the stone:

```text
RECORD1  -> soulkeeper
RECORD2  -> vormir_watcher
RECORD4  -> echoofvormir
RECORD5  -> soulbound
```

All four share one text template; `RECORD5` even carries the header line `SOUL STONE — RECORD 04` despite being file number 5, a sign of prefabricated filler rather than field data.

`RECORD3` is the file flagged as abnormal, verbatim from its 267 B form at HEAD:

```text
SOUL STONE — RECORD 03

Status: UNRECOVERED

The stone has not been returned.

This record appears to have been tampered with. Some information has been altered or removed from the original entry.
Find the user of the stone and prove your worthiness.

Record ends.
```

The line "Some information has been altered or removed" sets up the hypothesis that the stone's user was named in `RECORD3` and then deleted, so the history must be walked back.

### Testing the deletion hypothesis

The full history of `RECORD3` was taken with `git log --all --name-status` and by reading the blobs directly:

```console
$ git log --all --oneline -- RECORD3
14ab6ee Update RECORD3
b442da8 Create RECORD3
$ git cat-file -s b442da8:RECORD3
160
$ git cat-file -s 14ab6ee:RECORD3
267
$ git show --name-status --format='%h %s' 4d71aab
4d71aab Update RECORD3
$ git diff-tree --no-commit-id --name-only -r 4d71aab | wc -l
0
```

The `RECORD3` blob in the commit that created it (`b442da8`, 160 B) is:

```text
SOUL STONE — RECORD 03

Status: RECOVERED

The stone has been returned.

The price was paid.

The details of the recovery
have been classified.

Record ends.
```

Three decisive points, re-measured directly on the clone at the time this writeup was written:

- No version of `RECORD3` ever contained a username. The original 160 B form already had none — it differs from the current file only in the status line `RECOVERED`. There is therefore no "removed information" left to recover; strictly speaking, what changed was the status, not a deleted culprit name.
- Commit `4d71aab` has the subject `Update RECORD3` yet modifies exactly 0 files. The commit `885dfc1` with the same subject also prints no path line in `git log --all --name-status`.
- The number of username lines anywhere in `RECORD3`'s history is 0, which closes the "find the username in a diff" route.

This is the observation that redirected the solve: `RECORD3` is bait, and the real marker sits elsewhere in the history.

### Where the marker actually is

The same `git log --all --name-status` run shows a rename chain, every step `R100`, meaning the content did not change by a single byte:

```console
$ git log --all --follow --oneline -- RECORD6
16af270 Rename Nothing_suspicious to RECORD6
617ed85 Rename Nothing_suspicious.md to Nothing_suspicious
7ad8f4c Rename Nothing_suspicious.png to Nothing_suspicious.md
2f85701 Rename soul_stone.png to Nothing_suspicious.png
a28755b Add files via upload
```

The chain `soul_stone.png → Nothing_suspicious.png → Nothing_suspicious.md → Nothing_suspicious → RECORD6` shows that `RECORD6` at HEAD is the `soul_stone.png` image uploaded in `a28755b`, never edited. The author renamed it so it would read as an innocuous file, and its final name matches the template of the text `RECORD*` files, so it is easy to skip when only `README`/`RECORD1..5` are read.

## Solution

### Reading the tail of RECORD6

```console
$ file RECORD6
RECORD6: PNG image data, 1254 x 1254, ...
$ stat -c%s RECORD6
1917594
$ tail -c 40 RECORD6 | xxd
00000000: 28fe 1f12 2b12 3bfa f3e5 1e00 0000 0049  (...+.;........I
00000010: 454e 44ae 4260 8255 4768 6862 6e52 7662  END.B`.UGhhbnRvb
00000020: 564e 7664 5777 3d0a                      VNvdWw=.
```

`IEND` is the PNG end-of-image chunk; its 8 bytes are `49 45 4E 44 AE 42 60 82`. In a valid PNG nothing follows those 8 bytes. Here `IEND` sits at offset 1917569, so `1917569 + 8 = 1917577`, leaving exactly `1917594 - 1917577 = 17` appended bytes: `b'UGhhbnRvbVNvdWw=\n'`.

Those 17 bytes are a base64 string:

```console
$ tail -c 17 RECORD6
UGhhbnRvbVNvdWw=
$ tail -c 17 RECORD6 | base64 -d
PhantomSoul
```

The same check in Python, keeping the trailer byte-for-byte:

```python
import base64, pathlib

d = pathlib.Path("RECORD6").read_bytes()
i = d.rfind(b"IEND")
print("IEND at", i, "| size", len(d), "| trailing bytes", len(d) - (i + 8))
tail = d[i + 8:]
print(repr(tail))
print(base64.b64decode(tail.strip()))
```

```text
IEND at 1917569 | size 1917594 | trailing bytes 17
b'UGhhbnRvbVNvdWw=\n'
b'PhantomSoul'
```

`PhantomSoul` is decoded straight from the artifact; it is not an inference.

### From the decoded string to the flag

The event flag format is `OWASP{...}` (per the challenge card). The decoded string carries no braces, so wrapping it as `OWASP{PhantomSoul}` is an inference step, not data read from the file.

The limits of that inference matter: the player's notes list three candidates — `OWASP{PhantomSoul}`, `OWASP{phantomsoul}` and `OWASP{phantom_soul}` — and no submission response line was captured. This writeup therefore does not claim which casing variant the platform accepted; the event's solved table only records the challenge as solved.

## Result

```text
OWASP{PhantomSoul}
```

`PhantomSoul` decodes directly from the 11-character base64 string appended after `RECORD6`'s IEND chunk. The `OWASP{}` wrapper follows the event format, and because no submission response was recorded, the exact casing variant the platform accepted is not present in the player's files.

## Reproduce

Requires `git`, `xxd`, `base64` (coreutils) and Python 3 stdlib. The repository has to still be public at run time.

```console
$ git clone https://github.com/Vormir-616/Missing-Record mr
$ cd mr
$ git log --all --name-status
$ git cat-file -p b442da8:RECORD3
$ tail -c 17 RECORD6
UGhhbnRvbVNvdWw=
$ tail -c 17 RECORD6 | base64 -d
PhantomSoul
```

`git log --all --name-status` is the step that shapes the solve: it simultaneously shows that `RECORD3` never held a name and exposes the `R100` rename chain that ends at `RECORD6`. If the repository is later made private or deleted, the clone in the workspace still carries the full history needed to re-run every check above.
