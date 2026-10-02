# SiteCheck - Web (Hard)

Points: 498 · **Flag:** `sun{fr4gm3nt3d_r3fl3ct10ns_1n_th3_futur3}`
**Instance:** `https://spaceship.web.2026.sunshinectf.games` (no source files provided)

## Challenge

SiteCheck is a website inspection service. Register an inspector account and submit a URL, and SiteCheck's "drone" goes to that address itself, measures the load time, counts the files downloaded, then returns a viewport screenshot. The drone refuses internal and local addresses. The problem is getting past that refusal in order to read something the site never hands back directly.

## Recon

Server-side-rendered Express app, no JS bundle. Routes recovered from the HTML: `/register`, `/login`, `/dashboard`, `POST /scan`, `/result/<uuid>`, `/profile`, `/logout`, `/static/`, `/screenshots/`.

The scan flow is: `POST /scan` → 302 → `/result/<uuid>`. The report page shows Status, Load time, Files fetched and an `<img src="/screenshots/<uuid>.png">` tag.

Those three numbers are only side oracles. The snapshot image is the real content-reading channel, and the very existence of an image also shows the drone is an actual browser (Playwright/Chromium headless, 1280x800 viewport), not `requests.get` plus a blind count.

## What the SSRF filter blocks and what it does not

Every row below is one test; the details are in `notes.md`.

| Tried with the drone | Result |
| --- | --- |
| `http://127.0.0.1/`, `http://localhost/`, `http://LOCALHOST/` | blocked |
| `http://2130706433/`, `http://0x7f000001/`, `http://017700000001/`, `http://127.1/`, `http://0/` | blocked |
| `http://example.com@127.0.0.1/` | blocked |
| `file:///etc/passwd` | blocked by a dedicated protocol rule |
| `http://[::1]/`, `http://[::ffff:127.0.0.1]/` | gets through |
| `http://localtest.me/`, `http://127.0.0.1.nip.io/` | gets through |

The first four rows show they do not compare strings. The code parses the IP literal into a number and only then checks ranges, so tricks such as writing `127.0.0.1` in decimal, hexadecimal, octal, or hiding it behind an `@` are killed before they start.

The last two rows do get through, and for two completely different reasons: IPv6 loopback was left off the deny list, while hostnames are never resolved for the check at all. The proof is the drone returning `ERR_CONNECTION_REFUSED` for all four of those names, meaning it did open a real TCP connection, there is simply nobody listening on port 80.

## Exploit Chain

**Step 1: find an open port on loopback.** `http://[::1]:3000/` returns Status 200, Files fetched 10, with a snapshot. Ports 80, 8080, 3001 all give `ERR_CONNECTION_REFUSED`. 3000 is the SiteCheck app; the nginx in front only forwards traffic arriving from outside.

**Step 2: the app trusts the socket address.** The snapshot of `http://[::1]:3000/dashboard` plainly shows `Logged in as: admin - CLEARANCE: OMEGA`, while the drone sends its request with no cookies at all. That means a connection arriving from loopback is treated as an admin session.

Checked the other way: attaching `X-Forwarded-For`, `X-Real-IP`, `Client-Ip` set to `127.0.0.1` or `::1` to my own session still gives `h7tex_probe01`, still `REDACTED`. So this is the real socket address, not a header.

**Step 3: read `/profile`.** The Personnel File page has a `#clearance` section with the `.flag-plate` element, labeled "Restricted personnel token - visible only to holders of this file". On my BRONZE account the plate only reads `REDACTED · insufficient clearance`.

**Step 4: the plate lies outside the viewport.** The top of the page has `<div class="spacer" style="height:1400px">` and another `.spacer.tall` as well, so even the admin rendering with the real token gets pushed below the 1280x800 cut-off. The screenshot only captures the top of the page.

This is the easiest part of the challenge to miss. The SSRF chain was fully working, admin was in hand, and the flag was still nowhere in sight.

**Step 5: use a fragment to make Chromium scroll itself.** `page.goto()` with a fragment scrolls the element carrying that id into the viewport before the capture, and the `/result/<uuid>` page echoes TARGET verbatim, including `#clearance`. Final payload:

```
POST /scan   url=http://[::1]:3000/profile#clearance
```

The image returned shows the plate in full. Crop and zoom it to read one character at a time, because the `0` in `ct10ns` is a digit without a slash rather than the letter O.

## Flag
```
sun{fr4gm3nt3d_r3fl3ct10ns_1n_th3_futur3}
```

Re-run `python exploit.py` from the start to confirm:

```
[*] /register said: That callsign is already taken.
[+] 201352-byte viewport snapshot -> flag_shot.png
```

The fresh image still gives exactly that flag string.
