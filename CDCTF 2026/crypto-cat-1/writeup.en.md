# The Epic Adventures of Crypto Cat Caticus Catanius (1/5) - Crypto (Easy)

**Flag:** `cdctf{atbash1n_it_up_in_h3re}`
**Files:** `files/ciphertext.txt` (29 cipher characters, sha256 `901d528d70490f20879dbbf29865c48c3440647a156e57ae261201f0db39cf99`)

## Challenge

Part 1 of a five-part series set in the village of Caterie. The challenge text is
a taunting message from the cat wizard Dericat followed by a single ciphertext
line:

```text
xwxgu{zgyzhs1m_rg_fk_rm_s3iv}
```

That string is the first of four minor dungeon keys. The title mentions "xor with
many keys", but the story says clearly that XOR-with-many-keys protects the master
key, and all four part flags are needed in part 5. Each part is therefore a
standalone cipher.

## Initial Analysis

- 29 characters, lowercase letters, digits, `_`, `{`, `}` only.
- Special character positions: `{` at index 5, four `_` at 14, 17, 20, 23, `}` at
  the last index. That is exactly the skeleton of a flag
  (`prefix{word_word_word_word}`), which suggests the transform preserves special characters; a byte-wide XOR would have moved `{`, `}` and `_` as well.
- The challenge never states the flag prefix, so each candidate cipher was judged
  on whether the 5 leading characters (`xwxgu`) turn into a readable tag.

## Routes Ruled Out

1. **Single-byte XOR** (the name of the series): all 256 keys tested over the
   whole string. 16 keys give output inside the printable ASCII range, but only
   `0x00` (no encryption at all) keeps `{` at index 5. The rest is garbage such as
   `yvyftz{fx{ir0l^sf^gj^sl^r2hw|`. Rejected.
2. **Caesar / fixed alphabet shift**: all 25 shifts printed by `analysis/triage.py`
   are checked, and none produces a meaningful 5-char tag; `zgyzhs` does not become
   a word under any of the 25 shifts. Rejected.
3. **Vigenere/Beaufort keyed on a character name** (`caticus`): yields
   `lmuoi{xuowpg1k_hd_tg_fc_a3et}` and `edvbh{svbtaj1f_im_wj_kn_p3lw}`. Rejected.

The remaining candidate, Atbash (a<->z), maps `xwxgu` to `cdctf` on the first try
and is the solution below.

Full log in `notes.md`.

## Exploit Chain

**Step 1 - Read the ciphertext skeleton.** Counting the positions of `{`, `}` and
`_` identifies the flag structure; `analysis/triage.py` then prints the 25
Caesar shifts and the 256 single-byte XOR candidates so the first two routes can be
eliminated in one run:

```bash
python analysis/triage.py
```

**Step 2 - Atbash.** For a lowercase letter, Atbash is `chr(219 - ord(c))`, because
`ord('a') + ord('z') = 97 + 122 = 219`. Applied to the whole string:

```python
ALPHABET = "abcdefghijklmnopqrstuvwxyz"


def atbash(s):
    return "".join(chr(219 - ord(c)) if c in ALPHABET else c for c in s)


print(atbash("xwxgu{zgyzhs1m_rg_fk_rm_s3iv}"))
```

```text
cdctf{atbash1n_it_up_in_h3re}
```

**Step 3 - Verification.** Atbash is an involution: applying it to the plaintext
must return the original ciphertext, and `exploit.py` asserts that. The tag `cdctf`
matches the event's flag format, the body contains only lowercase letters, digits
and underscores, and the decoded body describes the Atbash transformation.

## Flag

```bash
python exploit.py files/ciphertext.txt
```

```text
[*] ciphertext.txt: 29 ky tu
[*] vi tri cua ngoac va gach duoi: [5, 14, 17, 20, 23, 28]
[*] XOR 1 byte: 16/256 khoa cho output in duoc; cac khoa con giu duoc '{' o vi tri 5: ['0x0'] (k=0 la khong ma hoa)
[*] Atbash: xwxgu{zgyzhs1m_rg_fk_rm_s3iv} -> cdctf{atbash1n_it_up_in_h3re}
[+] kiem chung: atbash(atbash(ciphertext)) == ciphertext
[+] flag: cdctf{atbash1n_it_up_in_h3re}
[+] da luu flag.txt
```

## Reproduce

```bash
python exploit.py files/ciphertext.txt
```

## Note for the following parts

Keep the part 1 flag. The statement says all four minor keys are required for part
5, where the master key is protected by "xor with many keys", The combination used in part 5 is not established here.
