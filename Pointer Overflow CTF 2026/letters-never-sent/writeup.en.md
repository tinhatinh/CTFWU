# Letters Never Sent - Crypto

**Points:** 95 · **Solves at solve time:** 248 · **Flag:** `POCTF{2.612.ORSMSQU6A7IQJGUC.PQ4FI6SPWLYJYQGBQK66AWTILP}`

**Files provided:** `files/letter.png` 1.150.873 byte, sha256 `907275df295c975e...`

## Challenge

Recovered from the estate of Dr. H. Aldous Whitmore, the letter was never sent. With it came
a strange message. The task: find the key the letter hides, then read the contents Whitmore
never intended to send. The ciphertext on the challenge card:

```text
PXYWN{2.612.QNTOXCK6E7DKGMKC.WK4KK6MPPPRJGOFZZI66EISSED}
```

## Initial Analysis

The handwritten letter is addressed to "Admiral Sir Francis Beaufort, K.C.B., Hydrographer to the
Navy", signed by Whitmore with the title Fellow of the Liminal Society for Spectral Fellowship,
dated November 1887. The decisive sentence is the one about the recipient's method: "that
reciprocal tableau which bears your name and which I have employed these many years in matters
requiring discretion". The Beaufort cipher is exactly such a self-inverse lookup table: encryption
and decryption use the same formula `c = k - p (mod 26)`.

Verify it right away with known data: the flag must start with `POCTF{`. Try the three
lookup-table cipher families over the 26-letter alphabet:

| Operation | Key implied by `PXYWN` -> `POCTF` |
| --- | --- |
| Beaufort `p = k - c` | `ELAPS` |
| Vigenère `p = c - k` | `AJWDI` |
| Variant Beaufort `p = c + k` | `AREXS` |

Only `ELAPS` opens something meaningful, and it matches the key taken from the border frame (Step 2). Porta
was eliminated early: with Porta, a ciphertext letter in the upper half of the table cannot be `P` if the plaintext is also `P`.

The border frame of the image carries 24 labels (6 per side) in English: flower names, bird names
and objects. Six labels are printed in dark red and have a red star next to them.

## Hypotheses ruled out

- Hidden data inside the image: no bytes after IEND, no tEXt/zTXt/iTXt chunks, the IDAT
  decompresses completely with no leftover byte, the three-channel low-bit ratios are
  0.4933 / 0.5036 / 0.4921 i.e. ordinary noise, `stegano.lsb.reveal` reports nothing.
- The running key being the letter itself: a Beaufort running key requires a key stream starting
  with `ELAPS`, and the letter text (607 letters, non-letters dropped) does not contain `ELA`.
- Autokey and progressive Beaufort with key `ELAPSE`: all three variants produce garbage.
- A transposition layer after decryption: the body has exactly 36 letters, so all 720 column permutations
  of a 6x6 grid were swept in both orders, rail fence at depths 2 to 12 for both encode and decode, spiral
  in four variants, grid transpose. No candidate stood out on quadgram score.
- A key from the unstarred labels: the 18 unstarred labels are exactly half of the 36 body
  letters, but `RFSTPHWMDOVYCRLFST` does not match the prefix pinned down above.
- A longer periodic Beaufort key: exhaustive sweep of every key of length 6, 7, 8, 9 with the 5
  first letters fixed at `ELAPS` (475k keys in total, scored with a quadgram model built from 370k
  English words) and hill-climbing for 10 to 16. No key produced English.

That last point turns out not to be a bad signal, see Step 4.

## Exploit Chain

**Step 1 - Fix the cipher.** Use the known `POCTF{` prefix to derive `key[0..4] = ELAPS`
for Beaufort over the 26-letter alphabet. Five letters agreeing between two independent sources
(the known prefix and the border frame) rule out every other cipher family.

**Step 2 - Read the key from the image by pixels, not by eye.** Filter on the colour deviation
`R - (G+B)/2 >= 45`, which separates exactly the red components (the stars and the marked labels),
while the cream paper scores 39 and is dropped. Cluster with `scipy.ndimage.label`, keep clusters
of area >= 40 px, assign each cluster to one of the 6 slots of its side based on the cluster
centroid. Unstarred labels are 6 to 10 px tall; starred labels are 11 to 22 px tall because the
star adds a vertical extent. The six slots above threshold: top 1, top 4, right 1, bottom 4, bottom 0, left 1.

**Step 3 - Order clockwise.** Going from the top-left corner: top left to right, right
top to bottom, bottom right to left, left bottom to top. The six labels met in that
order are Elder, Lily, Anchor, Poppy, Swan, Elder; taking their first letters gives `ELAPSE`.

**Step 4 - Accept that the flag body is unreadable.** Beaufort with `ELAPSE` and a key that only
advances on letters gives `POCTF{2.612.ORSMSQU6A7IQJGUC.PQ4FI6SPWLYJYQGBQK66AWTILP}`. The body
is not English, and every attempt to turn it into English (the ruled-out hypotheses)
failed. The read-me-my-fortune challenge later showed the reason: `_build_marker()` in the service
source generates flags from the template `POCTF{<cid>.<team_id>.<nonce>.<sig26>}`. Checked
against it, `2.612.ORSMSQU6A7IQJGUC.PQ4FI6SPWLYJYQGBQK66AWTILP` is exactly `cid=2`, `team_id=612`,
a 16-character nonce, and 26 base32 characters of HMAC. The flag body is therefore a per-team token
rather than prose, so "unreadable" is the correct result, not evidence of a wrong key.
Of the key-advance rules, only the "count only new letters" rule preserves the `POCTF{` prefix.

## Flag

```text
POCTF{2.612.ORSMSQU6A7IQJGUC.PQ4FI6SPWLYJYQGBQK66AWTILP}
```

Submitted and accepted. The lowercase form needed no further attempt.

## Reproduce

```bash
cd letters-never-sent
python exploit.py
```

The script measures the image itself to rebuild the key, prints `key from border: ELAPSE` and then the Beaufort
candidates, of which the `ELAPSE` line carries the `POCTF{` prefix. To run it against another team's challenge card:

```bash
python exploit.py files/letter.png "PXYWN{...}"
```
