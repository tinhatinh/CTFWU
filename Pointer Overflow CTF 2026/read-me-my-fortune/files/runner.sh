#!/bin/bash
# /challenge/runner.sh — per-connection wrapper invoked by xinetd.
#
# xinetd inherits the container environment for us (including
# FLAG_HMAC_SECRET and CHALLENGE_ID as set by entrypoint.sh), so we
# just exec the Python service directly. Stdout/stderr flow through
# the socket that xinetd handed us.

# unbuffered — the service prompt-and-read loop is interactive
export PYTHONUNBUFFERED=1

# Belt-and-suspenders: umask so any tempfile the service accidentally
# writes isn't world-readable.
umask 077

exec /usr/bin/python3 /challenge/service.py
