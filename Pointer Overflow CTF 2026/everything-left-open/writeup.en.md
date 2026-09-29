# Everything Left Open - Forensics

**Points:** 100 · **Wave:** 1 · **Flag:** `POCTF{109.612.I777LWHDFNCWRJ2S.JB6P5ZRASWPVYKKKHXKAPSQFWT}`

**Files provided:** `files/left-open-profile-team-612.zip` 3.486 byte, sha256 `faadae549b93f75a...` matching the challenge card.

## Challenge

A guest left a laptop at a hotel, unlocked, with the browser open in the middle of a form.
An outside IT firm repacked it into a zip. The task: find the flag in that session, and "pay
attention to the details". The zip is generated per team, so every team gets a different file.

## Initial Analysis

Inside is the Firefox profile `k-vance-profile` with five entries:

| File | Content read from it |
| --- | --- |
| `places.sqlite` | `moz_places` 8 rows (history) + `moz_bookmarks` 1 row |
| `formhistory.sqlite` | `moz_formhistory` 3 rows: `search` = "eighth session lssf redacted", `email` = "e.marchetti@hollis.edu", `search` = "halberd office hours wednesday" |
| `logins.json` | 2 logins, `encryptedUsername`/`encryptedPassword` are only plain base64 |
| `prefs.js` | `general.useragent.override` set to Firefox/119.0, `browser.startup.page=3`, `resume_from_crash=true` |
| `sessionstore-backups/recovery.jsonlz4` | 584 byte, container `mozLz40\0` |
| `README.txt` | Docket MARCHETTI/2026-14, "Find what she was about to submit." |

The phrases "data entered mid-form" and "what she was about to submit" point straight at the session store:
that is where Firefox keeps the contents of an unsent form. The sqlite files only hold investigative context.

## Recorded misdirections

Three things do not serve getting the flag but are worth writing down because they are exactly the kind of "pay attention to the details":

- The `moz_places` row id 99 has `url` as `https://catalog.spr.org.uk/apparatus/provenance/lssf`
  but `rev_host` is `moc.ftcwolfrevoretniop.nimda.`, which decodes to `admin.pointeroverflowctf.com`.
  `rev_host` is a column Firefox derives from `url` itself; the two columns contradict each other here, so this
  record was hand-assembled. It opens no direction either, the challenge being offline forensics with no service to reach.
- The only bookmark is named "flag draft (do not lose)", but its `fk=3` points at the Hollis Special
  Collections page, not at the page with the form. The bookmark name is bait.
- `logins.json` looks as though it holds encrypted credentials. In fact `ZS5tYXJjaGV0dGlAaG9sbGlzLmVkdQ==`
  and `TW5EYXlXM2RuZXNkQHk3` are just the base64 of `e.marchetti@hollis.edu` / `MnDayW3dnesd@y7`,
  and the second pair is `anon-analyst` / `hunter2`. There is no PKCS#11 or 3DES anywhere here.

## Exploit Chain

**Step 1 - Verify the artifact.** `sha256sum` on the zip matches the figure printed on the challenge
card before unpacking, then check the zip for anomalies: 6 entries, empty comment, no bytes after the
EOCD (3486 - 3464 = 22 byte, exactly the minimum EOCD size).

**Step 2 - Read the explicit sources.** `sqlite3` through Python for all of `moz_places`,
`moz_bookmarks`, `moz_formhistory`; `base64` for `logins.json`. No `POCTF{` string appears in
those four sources. A `grep -rao "POCTF{[^}]*}"` sweep over the whole extracted tree returns exactly
one hit, inside the still-compressed `recovery.jsonlz4`.

**Step 3 - Decode the jsonlz4 container.** The file begins with `6d 6f 7a 4c 7a 34 30 00`, that is
`mozLz40\0` (8 bytes), then 4 bytes of original size little-endian (`0x00000291` = 657), then a
plain LZ4 block. The easy mistake: guessing a 6-byte header and reading the size at offset 6 yields
`0x0291_0000` and `lz4.block` dies with "insufficient space in destination buffer":

```python
assert blob[:8] == b"mozLz40\x00"
size = struct.unpack("<I", blob[8:12])[0]
data = lz4.block.decompress(blob[12:], uncompressed_size=size)
```

`pip install lz4` has a Windows wheel for cp312, no build needed.

**Step 4 - Read the form data.** The decoded JSON is one window with one tab, the URL is the provenance
page `catalog.spr.org.uk/apparatus/provenance/lssf`, and `formdata.id` still holds the four fields the
user had typed but not submitted:

```json
"workstation":   "hollis-office-desktop-elena"
"analyst-name":  "K. Vance"
"artifact-flag": "POCTF{109.612.I777LWHDFNCWRJ2S.JB6P5ZRASWPVYKKKHXKAPSQFWT}"
"case-notes":    "Subject: E. Marchetti disappearance. Chain of custody initiated 2026-06-29..."
```

**Step 5 - Check the flag's validity.** The POCTF flag template is
`POCTF{<cid>.<team_id>.<nonce>.<sig26>}` where `sig26` is base32 of an HMAC-SHA256 truncated to 26
characters (taken from `_build_marker()` in the source of the read-me-my-fortune challenge). This string
fits: cid 109, team 612 which is the zip's own team, nonce `I777LWHDFNCWRJ2S` 16 alphanumeric
characters, sig 26 base32 characters. That is why the `artifact-flag` field was chosen rather than the
other three, and it is also a way to confirm without waiting for the server to answer.

## Flag

```text
POCTF{109.612.I777LWHDFNCWRJ2S.JB6P5ZRASWPVYKKKHXKAPSQFWT}
```

## Reproduce

```bash
cd everything-left-open
python exploit.py
```

The script verifies the sha256 on its own, dumps every sqlite and logins source, decodes the jsonlz4
and prints the field holding the flag. Run it with another team's zip: `python exploit.py <duong-dan-zip>`.
