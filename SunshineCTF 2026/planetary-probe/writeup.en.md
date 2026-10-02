# Planetary Probe — Web (Hard)

**Flag:** `sun{bl1nd_psqli_2_rc3_p4Nd0FyZt8k2}`
**URL:** `https://planetary.web.2026.sunshinectf.games/`, no files provided.

## Challenge

The planetary ledger of the "Galactic Federation". The console answers with exactly one bit:
"signal detected" or "no signal", no errors, no input echoed back.

The application has a blind SQL injection against PostgreSQL. The flag is not inside the database, but rather stored on the filesystem. By executing stacked statements, the application can use the `COPY (SELECT 1) TO PROGRAM '<cmd>'` feature to execute shell commands as the OS user `postgres`. The exit code of these commands can be used as a second oracle to infer filesystem contents and slowly extract the flag character by character.

## Initial Analysis

### Attack surface

The only form is `GET /probe?planet=<x>`, and responses come in just two shapes:

```html
<body class="is-carrier"> ... "Signal detected"
<body class="is-null">    ... "No signal"
```

Other routes return a Flask-style 404. Extra headers, cookies and parameters change nothing. The vulnerability is in the query string.

### SQL injection and the one-bit oracle

`MARS' OR 1=1-- ` returns carrier while `MARS' OR 1=1#` returns null, confirming PostgreSQL (`#` is not a comment) and direct concatenation:

```sql
SELECT id FROM planets WHERE name = '<payload>'
```

Normalised oracle: `MARS' AND (<expr>)-- ` returns carrier if and only if `<expr>` is true. 

The application lower-cases the entire payload. This means `ascii('A')=65` is evaluated as false, whereas `ascii('A')=97` and `ascii(chr(65))=65` are true. Therefore, no uppercase character may be typed in any pattern, and every comparison has to be reduced to numbers (`ascii`, `length`).

A full scan of the database schema (`pg_class`, `planets`, `zleak`) confirms the string `sun{` is not present in any column or description. The flag must reside on the filesystem.

## Exploit Chain

### Step 1 - The second oracle: the program's exit code

`MARS'; SELECT pg_sleep(3); -- ` delays the response by exactly 3.8s, demonstrating that stacked statements are supported. Because of a `psycopg2` driver requirement, the batch must end with a `SELECT` statement that returns rows; otherwise, psycopg2 throws an exception, causing the app to render "no signal".

`pg_auth_members` reveals that the user `probe` belongs to `pg_execute_server_program`. This enables running shell commands through:

```sql
MARS'; COPY (SELECT 1) TO PROGRAM '<cmd>'; SELECT 1; -- 
```

A command exiting non-zero causes PostgreSQL to raise an error, resulting in a "no signal" response. A successful exit code gives "signal detected". For example, `test -f /etc/passwd` gives carrier, `test -f /no.such` gives null. This oracle provides a way to infer filesystem contents.

The flag is found using the command: `find / -name "*flag*" -type f -exec grep -ls sun{ {} +`.

### Step 2 - Reading the file, one character per request

The pipeline to extract characters must fit inside one request and cannot rely on state between requests:

```bash
f=$(find / -name "*flag*" -type f -exec grep -ls sun{ {} + 2>/dev/null | grep -v /tmp/ | sort | head -1);
grep -aoE "sun[{][^}]*[}]" "$f" | head -1 | cut -c<K> | grep -qE "[class]"
```

Technical constraints to handle during extraction:
1. Replicas: The instance runs multiple containers. Saving state via `/tmp` fails because subsequent requests might hit a different container. Each probe must be entirely self-contained.
2. Timeouts: Slow probes (like running `grep -r` over the whole directory) trigger timeouts, which read as "no match". Pinning the file with `find -name` and reading one byte at a time using `cut -c<K>` solves this and allows parallelization.
3. Negative assumptions: Assuming a character is uppercase because a lowercase check `[d]` fails is unreliable due to timeouts acting as false negatives. Positive evidence using `[[:upper:]]` must be gathered first.

Each character is verified twice using bracket classes (`[s][u][n][{]...`) to avoid metacharacter interpretation.

## Flag

```
[*] exact string, end-anchored: True
[*] negative control (last char 3 instead of 2): False
[*] negative control (one uppercase where there is none): False
[*] length 35 and nothing more: True True
```

The measured flag length is 35. 

```
sun{bl1nd_psqli_2_rc3_p4Nd0FyZt8k2}
```

## Files in the folder

| file | contents |
| --- | --- |
| `exploit.py` | runs the whole chain: confirms both oracles, reads the flag, verifies |
| `extract.py` | SQL oracle + parallel reading helpers |
| `definitive.py` | the final character reader (`cut -c`, case by positive evidence) |
| `po.py`, `shell.py`, `flagpos.py`, `final_read.py` | intermediate scripts |
| `sweep3.py` | sweeps `sun{` across the whole catalog |
| `analysis/` | schema dump and logs |
| `flag.txt` | the flag |

## Reproduce

```bash
python exploit.py        # confirms both oracles, extracts and verifies the flag
```
