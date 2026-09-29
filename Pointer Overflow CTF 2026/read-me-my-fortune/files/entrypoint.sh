#!/bin/bash
# entrypoint.sh — POCTF container entrypoint for Read Me My Fortune.
#
# Verifies the required environment is set, then hands off to xinetd
# in foreground so Docker sees the service as the container's root
# process (correct SIGTERM handling, correct restart semantics).

set -e

MISSING=()
[ -z "$FLAG_HMAC_SECRET" ] && MISSING+=("FLAG_HMAC_SECRET")
[ -z "$CHALLENGE_ID" ]     && MISSING+=("CHALLENGE_ID")
if [ "${#MISSING[@]}" -gt 0 ]; then
    echo "[!] Missing required environment variables: ${MISSING[*]}" >&2
    echo "[!] Container refuses to start." >&2
    exit 1
fi

# xinetd inherits our env. Make it explicit so we can grep this
# variable's presence in container logs if the service ever complains
# it can't verify tokens.
export FLAG_HMAC_SECRET
export CHALLENGE_ID

echo "[entrypoint] starting xinetd on port 9000, CHALLENGE_ID=$CHALLENGE_ID"
exec /usr/sbin/xinetd -dontfork
