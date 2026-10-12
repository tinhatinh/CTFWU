---
title: "Insanity Check"
category: "Misc"
tags: ["base64", "ascii85", "nested-encoding", "decoy", "stop-condition"]
solve_date: "2026-10-10T21:05:00+07:00"
language: "en"
points: 100
---

# Insanity Check

**Flag:**

```text
kBxAc{0k"i_?99W..Rc-]1/0&GF?<>U4@M:s:c2Bj;H5>,=Z0>F>ZslJ4^_hF0/Xn\=CF'NC.qAb?>qW#3bCB';_C'j6od1dEH5;@>;J!P6S'T@=%$Uo<A-$^6<meZFXAkd05NjL/jF;#AP=g33GCiB8LZAV/3@QJFYYX"5s[t(2`l"24^;\F2KM>391E#`=&h"'=BRg><%KD94=W`p7R1r?-"&ec5uC--?n5/l}
```

**Input:** one long Base64 string included directly in the challenge description; there is no downloadable attachment. It begins `VmpGYVYyRXhXWGxXYkdScVVteEtVMWx0...` and ends `...UmJFcFJWa1JCT1E9PQ==`. The normalized input contains 1,400 ASCII characters.

## Challenge

The task presents an apparently endless nested encoding. The title *Insanity Check* is meaningful: recognizing a supported encoding format is not enough. We must also identify the **correct stopping point**, even when the remaining text is syntactically valid input to another decoder.

## Analysis

The input uses the Base64 alphabet and ends in `==`. Repeatedly apply `From Base64` in CyberChef (or Python's `base64.b64decode`). The input/output sizes are:

| Layer | Input bytes | Output bytes |
|---|---:|---:|
| Base64 #1 | 1400 | 1048 |
| Base64 #2 | 1048 | 784 |
| Base64 #3 | 784 | 588 |
| Base64 #4 | 588 | 440 |
| Base64 #5 | 440 | 328 |
| Base64 #6 | 328 | 244 |


After **exactly six Base64 decodes**, the plaintext starts with an explicit marker:

```text
here is the flag : 0k"i_?99W..Rc-]1/0&GF?<>U4@M:s:c2Bj;H5>,=Z0>F>ZslJ4^_hF0/Xn\=CF'NC.qAb?>qW#3bCB';_C'j6od1dEH5;@>;J!P6S'T@=%$Uo<A-$^6<meZFXAkd05NjL/jF;#AP=g33GCiB8LZAV/3@QJFYYX"5s[t(2`l"24^;\F2KM>391E#`=&h"'=BRg><%KD94=W`p7R1r?-"&ec5uC--?n5/l
```

The text following `here is the flag : ` is the **flag body**. Its punctuation is intentional: preserve double quotes, backslashes, backticks, and all other ASCII characters exactly as they appear. The body resembles an ASCII85 blob, but this is the challenge's trap.

## Decoy and false flag

If we ignore the explicit marker and continue with **four ASCII85 decodings followed by one more Base64 decoding**, we get:

```text
HeHe_Haa_Hoo_HOO_you_got_the_wrong_flag_maybe_you_misread_something
```

Wrapping that last plaintext as a flag yields the following **rejected candidate**:

```text
kBxAc{HeHe_Haa_Hoo_HOO_you_got_the_wrong_flag_maybe_you_misread_something}
```

The phrase `you_got_the_wrong_flag_maybe_you_misread_something` is the decoy. The deeper decoding chain is technically valid, but it does not yield the flag accepted by the challenge.

## Solution

1. Copy the complete original Base64 challenge string into `insanity.txt` as a single line.
2. Apply **exactly six** standard Base64 decodings, either in CyberChef or with the Python script below.
3. Verify that the result begins with `here is the flag : `.
4. Preserve all **225 ASCII characters** after that prefix and wrap them in `kBxAc{...}`. **Do not** decode the apparent ASCII85 any further.

The confirmed flag is:

```text
kBxAc{0k"i_?99W..Rc-]1/0&GF?<>U4@M:s:c2Bj;H5>,=Z0>F>ZslJ4^_hF0/Xn\=CF'NC.qAb?>qW#3bCB';_C'j6od1dEH5;@>;J!P6S'T@=%$Uo<A-$^6<meZFXAkd05NjL/jF;#AP=g33GCiB8LZAV/3@QJFYYX"5s[t(2`l"24^;\F2KM>391E#`=&h"'=BRg><%KD94=W`p7R1r?-"&ec5uC--?n5/l}
```

## Result

This challenge deliberately punishes over-decoding. A further decoder can produce meaningful plaintext and still lead to a false submission. The correct stopping condition is the explicit `here is the flag : ` marker after **six Base64 layers**.

## Reproduction

Requires Python 3.9+. Save the original challenge string as `insanity.txt`, save this script as `solve_insanity.py`, and run:

```powershell
python solve_insanity.py insanity.txt
```

```python
#!/usr/bin/env python3
"""Stop after exactly six Base64 layers: do NOT decode the ASCII85 flag."""
import base64
from pathlib import Path
import sys

raw = Path(sys.argv[1]).read_text(encoding="ascii").strip().encode("ascii")
for i in range(6):
    decoded = base64.b64decode(raw, validate=True)
    assert base64.b64encode(decoded) == raw, f"Bad Base64 layer {i + 1}"
    raw = decoded
prefix = b"here is the flag : "
assert raw.startswith(prefix), "Unexpected layer-6 plaintext"
flag_body = raw[len(prefix):].decode("ascii")
print("kBxAc{" + flag_body + "}")
```

**Expected output:**

```text
kBxAc{0k"i_?99W..Rc-]1/0&GF?<>U4@M:s:c2Bj;H5>,=Z0>F>ZslJ4^_hF0/Xn\=CF'NC.qAb?>qW#3bCB';_C'j6od1dEH5;@>;J!P6S'T@=%$Uo<A-$^6<meZFXAkd05NjL/jF;#AP=g33GCiB8LZAV/3@QJFYYX"5s[t(2`l"24^;\F2KM>391E#`=&h"'=BRg><%KD94=W`p7R1r?-"&ec5uC--?n5/l}
```

