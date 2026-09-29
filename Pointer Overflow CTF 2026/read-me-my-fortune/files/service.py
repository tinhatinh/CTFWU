#!/usr/bin/env python3
"""
service.py — Madame Elara's Personalized Fortune Reading Service.

Runs on the util server, one process per xinetd connection. Verifies
the player's session token (issued by the web server), computes their
team's per-team FLAG, then enters an interactive loop where the player
provides a custom .format() template that Madame Elara renders.

THIS SOURCE FILE IS INTENTIONALLY PLAYER-VISIBLE. The flag is NOT
baked into the source — it's derived per-session from the token
signature over (team_id, cid, nonce, secret). Everything you need to
solve is here; nothing about your team's flag is here.

── For local development ────────────────────────────────────────────
Set POCTF_DEV_MODE=1 and the token step is skipped. FLAG defaults to
"POCTF{dev.flag.local.testing}" so you can craft and test exploits
against your own copy. Bring-your-own-format-string.

    export POCTF_DEV_MODE=1
    python3 service.py

The remote server (in production) does NOT set this env var; you must
provide a valid token issued to your team by the POCTF website.

── Environment (production) ────────────────────────────────────────
    FLAG_HMAC_SECRET  — shared with web server, used to verify token
    CHALLENGE_ID      — challenges.id (int), used to reject cross-
                        challenge token reuse
    POCTF_DEV_MODE    — unset in prod; set to "1" for local testing
"""

from __future__ import annotations

import base64
import datetime
import hashlib
import hmac
import os
import signal
import sys


# ── Config ─────────────────────────────────────────────────────────────────

DEV_MODE = os.environ.get("POCTF_DEV_MODE") == "1"
FLAG_HMAC_SECRET = os.environ.get("FLAG_HMAC_SECRET", "")
CHALLENGE_ID_ENV = os.environ.get("CHALLENGE_ID", "0")

# xinetd doesn't line-buffer per default; force us to flush after every write.
sys.stdout.reconfigure(line_buffering=True)

# Hard per-connection timeout so a wedged client doesn't tie up an xinetd slot.
CONNECTION_TIMEOUT_SEC = 120
def _timeout(_sig, _frame):
    print("\n\nMadame Elara has other clients waiting. Farewell.\n")
    sys.exit(0)
signal.signal(signal.SIGALRM, _timeout)
signal.alarm(CONNECTION_TIMEOUT_SEC)


# ── Token verification (self-contained; mirrors api/session_token.verify) ──

_NONCE_MIN_LEN = 8
_NONCE_MAX_LEN = 48
_TOKEN_PREFIX = "EXP1"


def _valid_wire_nonce(nonce):
    if not isinstance(nonce, str):
        return False
    if len(nonce) < _NONCE_MIN_LEN or len(nonce) > _NONCE_MAX_LEN:
        return False
    return nonce.replace("_", "").isalnum()


def _sign(payload, secret):
    mac = hmac.new(secret.encode("utf-8"),
                   payload.encode("utf-8"),
                   hashlib.sha256).digest()
    return base64.b32encode(mac).decode("ascii").rstrip("=")[:26]


def _verify_token(token, expected_cid):
    """Return (team_id, cid, nonce) on success, or None on any failure.
    Silent on failure — caller shows a generic 'unrecognized' message."""
    import time
    if not token or len(token) > 512:
        return None
    parts = token.strip().split(".")
    if len(parts) != 6:
        return None
    prefix, team_id_s, cid_s, nonce, expires_s, sig = parts
    if prefix != _TOKEN_PREFIX:
        return None
    try:
        team_id = int(team_id_s)
        cid = int(cid_s)
        expires = int(expires_s)
    except ValueError:
        return None
    if cid != int(expected_cid):
        return None
    if not _valid_wire_nonce(nonce):
        return None
    if int(time.time()) > expires:
        return None
    payload = f"{prefix}.{team_id}.{cid}.{nonce}.{expires}"
    if not hmac.compare_digest(sig, _sign(payload, FLAG_HMAC_SECRET)):
        return None
    return team_id, cid, nonce


def _build_marker(cid, team_id, nonce):
    """Mirrors api/flags.build_marker on the web server."""
    msg = f"{cid}:{team_id}:{nonce}".encode()
    mac = hmac.new(FLAG_HMAC_SECRET.encode(), msg, hashlib.sha256).digest()
    sig = base64.b32encode(mac).decode("ascii").rstrip("=")[:26]
    return f"POCTF{{{cid}.{team_id}.{nonce}.{sig}}}"


# ── I/O helpers ────────────────────────────────────────────────────────────

def _read(prompt, max_len=1024):
    sys.stdout.write(prompt)
    sys.stdout.flush()
    try:
        line = sys.stdin.readline()
    except Exception:
        sys.exit(0)
    if not line:
        sys.exit(0)
    return line.rstrip("\r\n")[:max_len]


# ── Presentation ───────────────────────────────────────────────────────────

BANNER = r"""
     ╭──────────────────────────────────────────────────────╮
     │                                                      │
     │       M A D A M E   E L A R A ' S                    │
     │       Personalised Fortune Reading Service           │
     │                                                      │
     │       ~ Astrology · Numerology · Custom Divination ~ │
     │                                                      │
     ╰──────────────────────────────────────────────────────╯

  Enter, seeker. The threads of fate are ready to be read.
"""


def _greet():
    """Madame Elara's opening incantation. Present for atmosphere."""
    return "Welcome, seeker. The candles are lit; the tea is steeping."


# ── Main flow ──────────────────────────────────────────────────────────────
# FLAG is a module-level global by design — the intended solve path
# uses Python's format-string attribute walk to reach it via a
# function's __globals__.

FLAG = None


def main():
    global FLAG

    print(BANNER)

    # ── Token step (skipped in dev mode) ──
    if DEV_MODE:
        FLAG = "POCTF{dev.flag.local.testing.only}"
        print("  [POCTF_DEV_MODE=1] Token step skipped. Using local dev flag.")
        print()
    else:
        if not FLAG_HMAC_SECRET or CHALLENGE_ID_ENV == "0":
            print("  [!] Service is misconfigured. Contact operator.")
            sys.exit(1)
        print("  Present your session token to prove you are one of my expected")
        print("  guests. The token is on your challenge page at pointeroverflowctf.com.")
        print()
        tok = _read("  Token: ", max_len=512)
        result = _verify_token(tok, CHALLENGE_ID_ENV)
        if not result:
            print()
            print("  The stars do not recognize you. Session token is invalid or expired.")
            print("  Return to the challenge page for a fresh token.")
            sys.exit(1)
        team_id, cid, nonce = result
        FLAG = _build_marker(cid, team_id, nonce)
        print()
        print(f"  Welcome, member of team #{team_id}. Your consultation is confirmed.")
        print()

    # ── Reading step ──
    print("  Madame Elara offers PERSONALISED readings. First, tell me about")
    print("  yourself, then compose the format of your desired reading. I")
    print("  shall fill in the placeholders you provide.")
    print()
    name = _read("  What is your name? ", max_len=200)
    sign = _read("  What is your star sign? ", max_len=60)
    print()
    print("  Now, seeker: your reading TEMPLATE. Available placeholders are")
    print("  {name}, {sign}, {date}, and {elara} (my presence).")
    print()
    print("  Example:")
    print("    'Dear {name}, on this {date} the {sign} within you shall...'")
    print()
    template = _read("  Template: ", max_len=2048)

    date = datetime.datetime.utcnow().strftime("%B %d, %Y")

    print()
    print("  ── Your Reading ─────────────────────────────────────────────")
    try:
        reading = template.format(
            name=name, sign=sign, date=date, elara=_greet,
        )
        # Cap the output size to avoid a runaway leak of, say, the entire
        # os.environ dict formatted through str().
        print("  " + reading[:8000].replace("\n", "\n  "))
    except Exception as exc:
        # Reveal exception TYPE and MESSAGE — this is intentional; it's
        # how a good player learns their walk failed and adjusts.
        print(f"  ({type(exc).__name__}: {exc})")
    print("  ─────────────────────────────────────────────────────────────")
    print()
    print("  The candles gutter. Our consultation is complete.")
    print()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:
        # Never leak a traceback in prod — but do give the operator a
        # log line via stderr.
        sys.stderr.write(f"[service] uncaught: {type(exc).__name__}: {exc}\n")
        print("\n  Something has disturbed the veil. Try again.\n")
        sys.exit(1)
