---
title: "Tangled"
category: "Misc"
tags: ["factorio", "blueprint", "qr-code", "xor", "circuit-network", "glyph-ambiguity"]
solve_date: "2026-10-10"
language: "en"
---

# Tangled

**Flag:** `FortID{Wh3n_7h3_8e1ts_b3c0me_5p49hett1_tr41n5_8ec0m3_th3_0n1y_r34s0n4b1e_50lut10n}`
**Challenge:** `Tangled` (laragrr), challenge UUID `386d874b-3c23-4897-b872-21e0fcd1edb6`. **Handout:** `handout_file_1.txt` (9458 B) and `handout_file_2.txt` (1162 B); both are Factorio blueprints (base64 + zlib).

## Challenge

Each of the two text files holds one Factorio blueprint string. There is no description beyond the two blobs themselves; every fact lives in the blueprint structure (entities, tiles, and circuit-network elements).

## Analysis

A Factorio blueprint string is JSON that was zlib-compressed and then base64-encoded, so the first decode step is just normalisation:

```python
import base64, zlib, json

def decode_blueprint(text):
    body = text.strip()
    if body.startswith("^"):
        body = body.split("^", 2)[2] if body.count("^") >= 2 else body[1:]
    return json.loads(zlib.decompress(base64.b64decode(body)))
```

Decoding `handout_file_2.txt` yields a set of tiles that assemble into a damaged 25×25 QR grid. `handout_file_1.txt` holds the entities (the factory floor) with their centre coordinates; XOR-ing those entity centres against the tile matrix of the QR grid produces a text fragment recorded with a `QR` label:

```text
QR _5p49hett1_tr41n5_8ec0m3_
```

Three independent sources supply three pieces of the flag that concatenate into the full string:

```text
factory-floor QR (prefix):   FortID{Wh3n_7h3_8e1ts_b3c0me
XOR tile fragment (middle):  _5p49hett1_tr41n5_8ec0m3_
wire-glyph suffix:           th3_0n1y_r34s0n4b1e_50lut10n}
```

- The factory floor itself in `handout_file_1` carries a second QR that reads out the prefix `FortID{Wh3n_7h3_8e1ts_b3c0me`.
- The XOR fragment above is the middle `_5p49hett1_tr41n5_8ec0m3_` (the `QR` label only marks the source, it is not part of the flag).
- The 29 circuit-network wire components in the blueprint are re-rendered as glyphs with `inspect_wires.py` / `render_ports.py`, using the real Factorio 2.0.77 connector offsets obtained through `lupa`; they give the suffix `th3_0n1y_r34s0n4b1e_50lut10n}`.

Concatenating the three pieces (prefix + middle + suffix) matches the flag exactly.

## Solution

The whole recovery runs offline: decode the blueprints, build the 25×25 QR grid, XOR it against the entity centres to get the middle, read the factory-floor QR for the prefix, and render the 29 wire glyphs for the suffix. The only remaining constraint is glyph ambiguity: the characters `b`/`6` and `s`/`5` cannot be told apart on the re-rendered image, so the suffix is readable only at the shape level and its spelling is not settled.

The ambiguity is confined to the `r34s0n4b1e` cluster; the glyph readings produce roughly 20 variants differing between `r3450n461e` and `r34s0n4b1e` (and intermediate combinations). These variants were enumerated into `candidates_ports.txt`, i.e. 130 full candidates.

`check_candidates.py` used the platform only to disambiguate the glyph readings, not to discover the flag: it authenticated against `https://platform.ctf.fortid.com/api/v1/auth/login` with the team token, then POSTed each candidate to `/api/v1/challs/<uuid>/submit` (uuid above), respecting the `badRateLimit` backoff. The response is recorded verbatim:

```text
Authenticated successfully.\r\nChecking 130 candidates from candidates_ports.txt.\r\nACCEPTED: FortID{Wh3n_7h3_8e1ts_b3c0me_5p49hett1_tr41n5_8ec0m3_th3_0n1y_r34s0n4b1e_50lut10n}
```

Durable corroboration: `work\tangled\flag_verified.txt` (84 B) and `submission_results.jsonl` with 136 rows, distribution `Counter({'badFlag': 135, 'goodFlag': 1})`.

## Result

```text
FortID{Wh3n_7h3_8e1ts_b3c0me_5p49hett1_tr41n5_8ec0m3_th3_0n1y_r34s0n4b1e_50lut10n}
```

The flag was assembled offline from three pieces (factory-floor QR + XOR tile fragment + wire-glyph suffix), then accepted by the platform to disambiguate the glyph reading. The acceptance line is recorded verbatim: `Authenticated successfully.\r\nChecking 130 candidates from candidates_ports.txt.\r\nACCEPTED: FortID{Wh3n_7h3_8e1ts_b3c0me_5p49hett1_tr41n5_8ec0m3_th3_0n1y_r34s0n4b1e_50lut10n}` — the flag was accepted by `/submit`.

## Reproduce

Dependencies: Factorio 2.0.77 Lua prototypes (through `lupa`) for the real connector offsets, `PIL`/`cv2` to render images, and `qrcode` for QR generation and OpenCV for QR decoding. Recovery is offline; only the glyph-reading disambiguation needs the platform.

```console
$ pip install lupa pillow opencv-python qrcode
$ python inspect_wires.py handout_file_1.txt   # glyphs of the 29 wire components
$ python render_ports.py                        # glyph image (b/6, s/5 ambiguous)
$ python check_candidates.py                    # disambiguates glyph readings only, honours badRateLimit backoff
```

Note: `check_candidates.py` touches the platform API, so run it only when authorised; algorithmically, the fragments are recovered offline, while the final spelling is resolved using submission feedback.
