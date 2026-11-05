---
title: "Discord"
category: "OSINT"
tags: ["osint", "discord", "linktree", "invite-api", "curl", "social-media"]
solve_date: "2026-10-07T09:36:00+07:00"
language: "en"
points: 4
---

# Discord — Flag in the pinned rules post

**Flag:** `CTF{OffWeGo}` (submitted and accepted) · **Solves:** 114 · **Challenge image:** `challenge-modal.png`, 17 864 byte, sha256 `54b31508c1a100edd2dedf2434ca1b0a6fed3d83d2a52a9252b13c5c0eadc1aa`

## Challenge

The card on `ctf.bugpwn.com` carries nothing but the title **Discord**, 4 points, no description, no
file, no service. The title and the flag input box are the entire statement; `challenge-modal.png`
captures the card exactly as it opened. The objective therefore is to locate the battleCTF 2026
Qualifier Discord on your own and read the flag from inside it.

## Analysis

The platform footer links to `linktr.ee/bugpwn`, which lists the Discord invite. The public invite API identifies the server and destination channel. Other lookup attempts are recorded in `notes.md`.

## Solution

**Step 1 - From the card to the official link source.** CTFtime describes the event as "A technical CTF by
BUG|PWN" and gives the website `ctf.bugpwn.com`. Read every outbound link on the platform page:

```bash
curl -sL -A "Mozilla/5.0" https://ctf.bugpwn.com/ | grep -oiE 'href="[^"]+"' | sort -u | grep -viE 'static|assets'
```

```text
href="/"
href="/challenges"
href="/confirm?flow=init"
href="/login"
href="/register"
href="/rules"
href="/scoreboard"
href="/users"
href="https://ctfd.io"
href="https://linktr.ee/bugpwn"
```

The `linktr.ee/bugpwn` footer link provides the organiser’s invite source.

**Step 2 - Read the Linktree when the local connection is reset.** `linktr.ee` is unreachable from the
solving environment: `curl` returns HTTP `000` and the headless browser reports `ERR_CONNECTION_RESET`,
while other domains still work, so the failure is on the path to linktr.ee rather than in the page. Use a
text proxy to fetch the static content:

```bash
curl -sL "https://r.jina.ai/https://linktr.ee/bugpwn" | grep -n -i -B6 -A6 "discord"
```

```text
8-# BUG|PWN Team
14:[My community Discord Server • Free to join](https://discord.gg/WvUrypNDv)
```

**Step 3 - Validate the invite before trusting it.** The label "My community Discord Server" is generic,
and the proxy output mixes in dozens of unrelated Linktree profiles injected by Linktree's suggestion
block. So resolve the invite code through Discord's public API — this endpoint needs no token:

```bash
curl -s -A "Mozilla/5.0" "https://discord.com/api/v9/invites/WvUrypNDv?with_counts=true&with_expiration=true"
```

```json
{
    "code": "WvUrypNDv",
    "inviter": { "username": "weird.raven", "global_name": "WEIRD RAVEN" },
    "expires_at": "2026-10-28T14:30:16+00:00",
    "guild": { "id": "1082707709004095658", "name": "BattleCTF" },
    "channel": { "id": "1115911426003980318", "name": "announcements" },
    "profile": { "name": "BattleCTF", "member_count": 399, "online_count": 32 }
}
```

The server is named `BattleCTF` and the channel the invite opens on is `#announcements`. Right event, and
the API also names the channel worth reading.

**Step 4 - Read `#announcements`.** After joining with a Discord account, `#announcements` holds a single
pinned post, "battleCTF Qualifier Rules" by RAVEN. Under **Scoring**, the first bullet reads:

> Flags follow the `CTF{OffWeGo}` format. Submit exactly what the challenge gives you, nothing added or
> stripped.

Read the pinned post directly and copy the example flag string. The channel being read-only does not prevent reading or searching its messages.

*Screenshot: the flag inside the Scoring section of the rules post (discord-announcements.png).*

**Step 5 - Verification.** Cross-check the invite and post: the invite resolves to the
`BattleCTF` guild rather than some community server; the post sits in `#announcements`, exactly the
`channel.name` returned by the API; and the platform itself already records a `CTF{...}` prefix for some
challenges of this event (see the flag format note in the [event README](README.md)), so a
`CTF{OffWeGo}` flag does not break the stated convention.

## Result

```text
CTF{OffWeGo}
```

Recovered by reading the rules post directly in `#announcements` of the BattleCTF server
(`discord.gg/WvUrypNDv`); screenshot in `discord-announcements.png`. The flag was submitted to
`ctf.bugpwn.com` and accepted; `challenge-modal.png` shows the card **before** the flag was entered.

## Reproduce

Requires: Git Bash on Windows, `curl`, and a Discord account that has joined the server. The invite is
time-limited — code `WvUrypNDv` expires at `2026-10-28T14:30:16+00:00`; after that, pull a fresh code from
`linktr.ee/bugpwn` following Step 2.

```bash
cd "discord"
bash repro.sh
```

Or manually, three commands:

```bash
curl -sL -A "Mozilla/5.0" https://ctf.bugpwn.com/ | grep -oiE 'href="[^"]+"' | sort -u
curl -sL "https://r.jina.ai/https://linktr.ee/bugpwn" | grep -n -i "discord"
curl -s -A "Mozilla/5.0" "https://discord.com/api/v9/invites/WvUrypNDv?with_counts=true" | head -c 400
```

The last step — reading `#announcements` — is a manual action with no corresponding command.
