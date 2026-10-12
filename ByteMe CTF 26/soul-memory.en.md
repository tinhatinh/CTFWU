---
title: "Soul Memory"
category: "Forensics"
tags: ["memory-artifact", "key-value-parsing", "plaintext-flag", "field-locator"]
solve_date: "2026-10-09"
language: "en"
---

# Soul Memory

**Flag:** `OWASP{s0ul_m3m0ry_n3v3r_d13s}`
**Artifact:** `memory_dump.txt` (148 B as recorded).

## Challenge

Statement (Easy, 100 points, 25 solves on the platform): a cache record extracted from a Soul Vault "memory dump", where one hint line states how to locate the field holding the answer.

The artifact's whole content is six `key=value` fields:

```text
pid=4041
module=soul-cache
user=keeper
cache_key=MEMORY_7
vault_hint=look_after_after_cache_key
data=OWASP{s0ul_m3m0ry_n3v3r_d13s}
```

## Analysis

The first four fields are record metadata: `pid=4041`, `module=soul-cache`, `user=keeper` (the same `keeper` user that appears in the Soul Vault group of challenges), `cache_key=MEMORY_7`. The remaining two carry the locator information.

`vault_hint` holds `look_after_after_cache_key`. The string repeats `after` twice; the meaningful reading is `look_after_cache_key` — "look at what comes after the cache key". The hint does not contain the answer itself, it only supplies the field-selection rule.

Applying that rule to the recorded field order: going forward from `cache_key=MEMORY_7` there are two fields, `vault_hint` and `data`. `vault_hint` contains only the instruction, no payload; `data` is the first field after the cache key whose value is actual payload data. That value is already plaintext and already carries the flag shape:

```text
data=OWASP{s0ul_m3m0ry_n3v3r_d13s}
```

There is no decoding step: the value is not hex, not base64, not XORed and not compressed. This is a read-and-select challenge, not a transformation challenge.

The solve uses captured text; the original file bytes and size were not independently checked.

## Solution

Pulling the `data` field out of the record:

```console
$ python -c "import pathlib,re; t=pathlib.Path('memory_dump.txt').read_text(); print(re.search(r'^data=(\S+)', t, re.M).group(1))"
```

```text
OWASP{s0ul_m3m0ry_n3v3r_d13s}
```

Working from the captured text alone, the equivalent operation is simply reading the value that follows `data=`.

The script demonstrates reading the `data` field. Reading the same value directly is sufficient.

```python
import re

record = (
    "pid=4041\n"
    "module=soul-cache\n"
    "user=keeper\n"
    "cache_key=MEMORY_7\n"
    "vault_hint=look_after_after_cache_key\n"
    "data=OWASP{s0ul_m3m0ry_n3v3r_d13s}"
)

fields = [line.split("=", 1) for line in record.splitlines()]
keys = [k for k, _ in fields]
i = keys.index("cache_key")
print("cache_key value :", fields[i][1])
for k, v in fields[i + 1:]:
    print("after cache_key : %-10s -> %r" % (k, v))
```

```text
cache_key value : MEMORY_7
after cache_key : vault_hint -> 'look_after_after_cache_key'
after cache_key : data       -> 'OWASP{s0ul_m3m0ry_n3v3r_d13s}'
```

Of the two listed fields only `data` is payload; `vault_hint` just repeats the instruction.

## Result

```text
OWASP{s0ul_m3m0ry_n3v3r_d13s}
```

The flag is the value of `data`; no decoding is needed. No submission response was preserved.

## Reproduce

Python 3 only (`pathlib`, `re`). With `memory_dump.txt` available, run the single-field extraction command above. Working from the captured text only, save the `record` snippet from the Solution section as `solve.py` and run:

```console
$ python solve.py
```

That script reads no file, so it reproduces independently of whether the original artifact still exists.
