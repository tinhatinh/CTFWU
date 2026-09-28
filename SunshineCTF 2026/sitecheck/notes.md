# Decision log — SiteCheck

Target: `https://spaceship.web.2026.sunshinectf.games` (URL as supplied by the user). Flag prefix pinned from the challenge page: `sun{`.

| # | Observation | Test | Result |
| --- | --- | --- | --- |
| 1 | Express + server-rendered, no JS bundle | `GET /`, `/robots.txt` | 404 page is app-generated; routes: `/register /login /dashboard /scan /result/<uuid> /profile /logout /static /screenshots` |
| 2 | Register needs 3-24 chars `[A-Za-z0-9_-]` | POST `/register` with dots | 400 alert → account `h7tex_probe01` created |
| 3 | `POST /scan` → 302 `/result/<uuid>`; report = Status / Load time / Files fetched / **PNG snapshot at `/screenshots/<uuid>.png`** | scan `https://example.com/` | 200, 316 ms, 1 file → the snapshot is the content oracle, so the drone is a real browser |
| 4 | `127.0.0.1`, `localhost`, `LOCALHOST` blocked | scan | "For safety, SiteCheck will not inspect internal or local addresses." |
| 5 | IP *literals* are normalised before the check: `2130706433`, `0x7f000001`, `017700000001`, `127.1`, `0`, `example.com@127.0.0.1` | scan | all BLOCKED → parser-based check, string tricks on IPv4 are dead |
| 6 | `file://` | scan | BLOCKED by a separate protocol rule ("Only http:// and https://") |
| 7 | **`http://[::1]/` and `http://[::ffff:127.0.0.1]/` pass the filter** (Chromium reports `ERR_CONNECTION_REFUSED`, i.e. it actually reached loopback) | scan | ALLOWED → **IPv6 loopback is missing from the deny list** |
| 8 | `http://localtest.me/`, `http://127.0.0.1.nip.io/` also reach loopback | scan | ALLOWED → **hostnames are never resolved before the check**, second independent bypass |
| 9 | `host.docker.internal` → `ERR_NAME_NOT_RESOLVED` | scan | no docker DNS alias; no sidecar by that name |
| 10 | `http://[::1]:3000/` → **200, 10 files** | scan | the Express app itself listens on 3000; port 80 closed |
| 11 | Screenshot of `[::1]:3000/dashboard` renders **"Logged in as: admin — CLEARANCE: OMEGA"** | visual | app treats a loopback peer socket as an authenticated admin session (no cookie involved) |
| 12 | IP-spoof headers on our own session: `X-Forwarded-For`, `X-Real-IP`, `Client-Ip` = `127.0.0.1`/`::1` | GET `/profile` | still `h7tex_probe01` / REDACTED → trust is the real peer address, not a header |
| 13 | `/profile` has `.flag-plate` ("Restricted personnel token"), REDACTED for BRONZE; page ends with `<div class="spacer" style="height:1400px">` pushing the plate below 1280x800 | GET `/profile` | a plain screenshot of the admin profile shows only the top of the page |
| 14 | **URL fragment makes Chromium scroll the anchor into view before the shot** | scan `http://[::1]:3000/profile#clearance` | plate visible → `sun{fr4gm3nt3d_r3fl3ct10ns_1n_th3_futur3}` |

## Root cause

Two independent weaknesses chained: (a) the SSRF deny list normalises IPv4 literals but omits IPv6 loopback and never resolves hostnames; (b) the app authenticates by *peer IP*, so anything arriving from loopback is `admin` with OMEGA clearance. The last guardrail is purely visual (classified text below the fold) and is defeated by the URL fragment, which the report page echoes back verbatim. The flag wording ("fragmented reflections in the future") names the three links of the chain: fragment / screenshot-reflection / drone.
