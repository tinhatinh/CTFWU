# challenges/Exploit 4 - Read Me My Fortune/Dockerfile
# Container for EXP 200 — Read Me My Fortune.
#
# Runs a single xinetd-backed Python service on port 9000. One process
# is spawned per player connection. FLAG is NOT baked in — it's
# derived per-session from the session token via HMAC + build_marker.
#
# Required at run time (docker run -e):
#   FLAG_HMAC_SECRET  shared with the web server
#   CHALLENGE_ID      the challenges.id integer for this challenge
#
# Deploy:
#   docker build -t poctf/read-my-fortune .
#   docker run -d --name read-my-fortune \
#     -p <ext_port>:9000 \
#     -e FLAG_HMAC_SECRET="$FLAG_HMAC_SECRET" \
#     -e CHALLENGE_ID="$READ_MY_FORTUNE_CHALLENGE_ID" \
#     poctf/read-my-fortune

FROM debian:bullseye-slim

# Runtime deps: python3 + xinetd.
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        python3 xinetd ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# ── Unprivileged player-facing account ──────────────────────────────────────
# The service runs as this user. Nothing in this container is worth
# escalating to root over — the flag is per-session, and there's no
# other data. But we still avoid running the format-string service as
# root by principle.
RUN useradd -m -s /bin/bash -c "Madame Elara's client" seeker

# ── Challenge files ─────────────────────────────────────────────────────────
RUN mkdir -p /challenge
COPY service.py                   /challenge/service.py
COPY runner.sh                    /challenge/runner.sh
COPY read_my_fortune.xinetd       /etc/xinetd.d/read_my_fortune
COPY entrypoint.sh                /entrypoint.sh
COPY motd                         /etc/motd

RUN chmod 755 /challenge/runner.sh /entrypoint.sh /challenge/service.py && \
    chown root:root /challenge/service.py

# Harden runtime.
RUN chmod 700 /root

EXPOSE 9000
ENTRYPOINT ["/entrypoint.sh"]
