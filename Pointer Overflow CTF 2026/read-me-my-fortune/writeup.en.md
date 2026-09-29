# Read Me My Fortune - Exploitation

**Points:** 200 · **Wave:** 1 · **Flag:** `POCTF{127.612.IB2GGFAM2XGX6RDT.TEENFQ3KNWVEA3MCHJNFWFODQI}`

**Files provided:** `service.py` (`a1421668…`), `Dockerfile`, `runner.sh`, `entrypoint.sh`, `read_my_fortune.xinetd`, all matching the sha256 printed on the challenge card.

## Challenge

A netcat service at `read-my-fortune.pointeroverflowctf.com:9000`. Before the reading begins,
the service demands a session token issued specifically for the team, rotated on every page reload and
expiring after 15 minutes. The player enters a name, a zodiac sign and a `.format()` template of their
own making; Madame Elara renders that template and prints the result.

## Initial Analysis

The whole of `service.py` is public source, and it says outright where the hit lands:

```python
reading = template.format(
    name=name, sign=sign, date=date, elara=_greet,
)
```

`name`, `sign`, `date` are strings. `elara` is a **function object** (`_greet`). In Python 3, a format
string allows attribute traversal and subscripting right inside the field name (`{a.b[c]}`), so a function
object opens onto `__globals__`, that is the module namespace. The head of the file states plainly:

```python
# FLAG is a module-level global by design - the intended solve path
# uses Python's format-string attribute walk to reach it via a
# function's __globals__.
```

So this challenge has no hidden bug: the primitive is `.format()` with a live object as an argument,
and the job is only to write the right field, get past the token gate, and read back the output.

The two remaining constraints are worth noting but block nothing:

- `_read()` truncates input at `max_len`, and the template may be 2048 characters long, far more than the payload needs.
- The result is cut at `reading[:8000]`, but the payload prints a single field, so it fits inside the limit.
- Exceptions are printed together with their type and message (`print(f"({type(exc).__name__}: {exc})")`), so if
  any step goes wrong the service reports KeyError or IndexError itself, enough to correct the path without guessing.

## Hypotheses ruled out

- **Running `service.py` directly on Windows to test it**: it dies immediately at `signal.signal(signal.SIGALRM, ...)`
  because `SIGALRM` does not exist on this platform. No WSL or Docker is needed for this step, only a
  stub for exactly two symbols, `SIGALRM` and `alarm`, leaving every other code path untouched
  (`analysis/local_service.py`).
- **Skipping the token to test live**: `main()` calls `sys.exit(1)` if `_verify_token` returns `None`,
  and `_verify_token` checks the `EXP1` prefix, exactly 6 parts, `cid` matching `CHALLENGE_ID_ENV`, a
  well-formed nonce, not expired, and only then compares the HMAC. There is no way around it, so every
  live test has to use the team's real token.
- **Taking the `os.environ` route via `{elara.__globals__[...]}`**: technically workable but unnecessary,
  because `FLAG` sits directly in the globals of `_greet` itself. The service also leaves a comment
  about the 8000-character output cut, which is there to stop this kind of whole-environment dump.

## Exploit Chain

**Step 1 - Identify the primitive.** Read `main()`, see `template.format(elara=_greet)`, and remember
that a field name in `str.format` supports both attribute lookup and subscripting. There is no
sanitisation of `template` beyond the length limit.

**Step 2 - Build the payload.** `FLAG` is a global of the module containing `_greet`, so:

```text
{elara.__globals__[FLAG]}
```

This field resolves to `getattr(_greet, "__globals__")["FLAG"]`, that is exactly the flag string.

**Step 3 - Proof on the local machine.** Run the service through `analysis/local_service.py` with
`POCTF_DEV_MODE=1` (token step skipped, flag is a placeholder), feed in the payload, and get back
`POCTF{dev.flag.local.testing.only}`. This step confirms the conversation protocol and the payload
syntax without burning a live token, exactly as the challenge card advises.

Three places had to be patched for the local run to work on Windows, all of them harness problems rather
than challenge problems: the missing `signal.SIGALRM` (stubbed), the banner containing box-drawing characters
that killed the child with a cp1252 `UnicodeEncodeError` (set `PYTHONIOENCODING=utf-8` for the child), and
`os.read()` not working on a socket on Windows (use `sock.recv` for sockets, `os.read` for pipes).

**Step 4 - Hit it live.** Connect to port 9000, send a token still within its validity, answer the two questions
with arbitrary strings, then send the payload at the Template prompt. The service prints the flag in the Reading section.

## Flag

```text
POCTF{127.612.IB2GGFAM2XGX6RDT.TEENFQ3KNWVEA3MCHJNFWFODQI}
```

The flag structure matches `_build_marker()` exactly: `<cid>.<team_id>.<nonce>.<sig26>` with
`cid=127`, `team_id=612`, `nonce=IB2GGFAM2XGX6RDT` taken from the token, and 26 base32 characters of
HMAC-SHA256. `sig` cannot be recomputed on our side because it needs the server-side `FLAG_HMAC_SECRET`.

## Reproduce

```bash
cd read-me-my-fortune
python exploit.py --local
python exploit.py read-my-fortune.pointeroverflowctf.com 9000 "<token còn hạn trên trang đề>"
```
