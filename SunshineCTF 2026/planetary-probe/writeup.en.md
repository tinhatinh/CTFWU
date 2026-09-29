# Planetary Probe — Web (Hard)

**Flag:** `sun{bl1nd_psqli_2_rc3_p4Nd0FyZt8k2}`
**URL:** `https://planetary.web.2026.sunshinectf.games/`, no files provided.

## Challenge

The planetary ledger of the "Galactic Federation". The console answers with exactly one bit:
"signal detected" or "no signal", no errors, no input echoed back.

That bit is first used as the oracle for a blind SQL injection against PostgreSQL, but the flag
is not in the database: the only two tables were dumped in full and no other object contains the
string `sun{`. The second bit comes from somewhere else. The `planet` parameter allows stacked
statements, and the user `probe` is a member of `pg_execute_server_program`, so
`COPY (SELECT 1) TO PROGRAM '<cmd>'` runs shell commands as the OS user `postgres`, and the exit
code of the command itself becomes a yes/no question about the filesystem. The flag is read one
character at a time through that oracle.

## Initial Analysis

### Attack surface

The only form is `GET /probe?planet=<x>`, and responses come in just two shapes:

```html
<body class="is-carrier"> ... "Signal detected"
<body class="is-null">    ... "No signal"
```

Other routes return a Flask-style 404 (207 bytes). `OPTIONS /probe` gives `Allow: HEAD, OPTIONS, GET`;
extra headers, cookies and parameters change nothing. The HTTP layer is a dead end, the challenge
lives in the query string.

### SQL injection and the one-bit oracle

`MARS' OR 1=1-- ` returns carrier while `MARS' OR 1=1#` returns null, so this is PostgreSQL (`#` is
not a comment) and the string is concatenated directly:

```sql
SELECT id FROM planets WHERE name = '<payload>'
```

Normalised oracle: `MARS' AND (<expr>)-- ` returns carrier if and only if `<expr>` is true. MARS is a
real row, so a condition can never come out false because of a bad anchor.

First trap: the app lower-cases the entire payload. `ascii('A')=65` is false while `ascii('A')=97` is
true and `ascii(chr(65))=65` is true. Consequences: no uppercase character may be typed in any
pattern, and every comparison has to be reduced to numbers (`ascii`, `length`), otherwise a "no match"
is just an uppercase letter folded to lowercase.

## Approaches Ruled Out

### The flag is not in the database

Schema dumped through `pg_class`/`pg_attribute` (`information_schema` is not used for the question "is
there a foreign schema", because that view hides whatever one has no rights on):

* `planets(id, name, diameter_km, description)`: 8 rows, every diameter is a real number, `string_agg`
  over all 337 characters, no `{` anywhere (`p::text LIKE '%{%'` is false), no control characters
  (comparing `octet_length` with `length`, and `[[:cntrl:]]`).
* `zleak(v)`: exactly 1 row, its value being the string `select v from zleak`. This is a bait table,
  confirming the DB is readable, not a flag.
* Sweeping for `sun{` (built with `chr()` so it does not get lower-cased) over `pg_proc.prosrc`,
  `pg_description`, `pg_shdescription`, `pg_seclabel`, `pg_enum`, `pg_indexes.indexdef`, `pg_views`,
  `pg_rules`, `pg_attribute` (including `attmissingval`), `pg_policies`, `pg_foreign_*`,
  `pg_subscription`, `pg_largeobject`, `pg_statistic` (stavalues 1..4), `pg_auth_members`: all false,
  and each test came with a positive control (the same test on a string containing `sun{` must be true).
* Two places that first reported true turned out to be false positives: `pg_db_role_setting` and
  `reloptions`, only because casting an array prints `{...}`. Searching for `{` is meaningless, the
  whole `sun{` has to be searched with `position()`.
* `pg_stat_activity` also once reported containing `sun{`, that was the test's own query. It has to be
  excluded with `pid<>pg_backend_pid()` and the pattern built with `chr()`.

## Exploit Chain

### Step 1 - The second oracle: the program's exit code

`MARS'; SELECT pg_sleep(3); -- ` is slower by exactly 3.8 s, so stacked statements really do run. The
earlier conclusion "every extra statement is blocked" was wrong, and the cause is a driver requirement:
the batch must end with a SELECT that returns rows, psycopg2 raises otherwise, and a raise renders as
"no signal", identical to a false condition.

`pg_auth_members` shows `pg_execute_server_program -> probe`, even though `has_privs_of_role()` returns
false: the membership exists, it is just not inherited automatically. With that privilege:

```sql
MARS'; COPY (SELECT 1) TO PROGRAM '<cmd>'; SELECT 1; -- 
```

`<cmd>` runs through `/bin/sh -c` as the OS user postgres (`id -un | grep -q ^postgres` confirms it).
A command exiting non-zero makes PostgreSQL raise, and the app answers "no signal". Controls:
`test -f /etc/passwd` gives carrier, `test -f /no.such` gives null. This is a new oracle, one that can
ask about the filesystem and not only about the DB.

Some things are missing from the image (`cat`, `python3`, `md5sum`, and `grep -qiF` does not work), so a
test returning false only means false when the tool is known to exist; quite a few "false" results were
really a command that does not exist.

Locating the flag: `/flag.txt` exists but is empty (`test -s` false).
`find / -name "*flag*" -type f -exec grep -ls sun{ {} +` is what points at the real file; the two paths
found point to the same content, `cmp -s` confirms it.

### Step 2 - Reading the file, one character per request

The pipeline fits inside one request, with no state kept between two requests:

```
f=$(find / -name "*flag*" -type f -exec grep -ls sun{ {} + 2>/dev/null | grep -v /tmp/ | sort | head -1);
grep -aoE "sun[{][^}]*[}]" "$f" | head -1 | cut -c<K> | grep -qE "[class]"
```

Three hidden costs spoiled several reading rounds:

1. Replicas. The instance runs more than one container. The first version wrote results to `/tmp` and
   read them in the next request, but that next request landed in a different container so the file was
   gone. Worse, the junk `/tmp` file also contains `sun{`, so `grep -rl` returned two results and the
   read consumed data generated by myself. Fix: each probe carries the whole pipeline by itself, and
   `/tmp/` is excluded from the find results.
2. A slow probe counts as a wrong probe. `grep -r` over the PostgreSQL data directory sometimes exceeds
   the timeout, and a timeout reads as "no match", corrupting the bisection; once it reported the flag
   starting with `0` while `^sun[{]` was still true. Fix: pin the file by name with `find -name`, and
   read only one byte at a time with `cut -c<K>`. This way is fast and the positions become independent,
   so they can be parallelized.
3. Inferring uppercase from a negative is wrong. The old rule "test `[d]` case-sensitively and if it
   fails it must be `D`" breaks because a timeout also yields a failure, so `d` became `D` at random.
   Fix: positive evidence is required, `[[:upper:]]` (punctuation only, so it never gets lower-cased)
   must be true and `[d]` must be false before concluding `D`.

Each character is read twice and the two reads must agree. The pattern is a chain of bracket classes
(`[s][u][n][{]...`) so that `{`, `}` and `.` can never be reinterpreted as metacharacters.

## Flag

```
[*] exact string, end-anchored: True
[*] negative control (last char 3 instead of 2): False
[*] negative control (one uppercase where there is none): False
[*] length 35 and nothing more: True True
```

The measured length is 35 (`wc -c` gives 36 including the newline), nothing is left at position 36, and
both negative controls are false.

```
sun{bl1nd_psqli_2_rc3_p4Nd0FyZt8k2}
```

## Files in the folder

| file | contents |
| --- | --- |
| `exploit.py` | runs the whole chain: confirms both oracles, reads the flag, verifies |
| `extract.py` | SQL oracle + parallel reading helpers |
| `definitive.py` | the final character reader (`cut -c`, case by positive evidence) |
| `po.py`, `shell.py`, `flagpos.py`, `final_read.py` | intermediate rounds, kept to review the history |
| `sweep3.py` | sweeps `sun{` across the whole catalog, with controls |
| `analysis/` | per-round logs, the dumped schema |
| `flag.txt` | the flag |

## Reproduce

```bash
python exploit.py        # xác nhận cả hai oracle, đọc lại cờ và verify toàn chuỗi
```
