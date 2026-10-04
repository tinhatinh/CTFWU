"""Quet ky tu an trong toan bo repo: working tree, moi blob trong lich su, moi commit message.

Chay: python analysis/scan_hidden_unicode.py ../notekeeper
Can mot clone cua repo. In ra so luong ky tu Unicode Tag (U+E0000-U+E0FFF, nhom vo hinh
trong hau het editor) va cac ky tu zero-width/bidi thong thuong (U+200B-U+200F,
U+202A-U+202E, U+2060, U+FEFF), kem commit da sinh ra blob nhiem.
"""

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
TAG = re.compile(r"[\U000E0000-\U000E0FFF]")
ZW = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff\u061c]")


def report(label: str, data: bytes) -> tuple[int, int]:
    text = data.decode("utf-8", "replace")
    tags, zws = TAG.findall(text), ZW.findall(text)
    if tags or zws:
        print(f"{label}: tag={len(tags)} zw={len(zws)}")
        if tags:
            print(f"    len {len(''.join(chr(ord(c) - 0xE0000) for c in tags))} ky tu tai lap")
    return len(tags), len(zws)


print("### working tree")
for p in sorted(REPO.rglob("*")):
    if p.is_file() and ".git" not in p.parts:
        report(str(p.relative_to(REPO)), p.read_bytes())

print("### moi blob trong lich su")
check = subprocess.run(
    ["git", "-C", str(REPO), "cat-file", "--batch-all-objects", "--batch-check"],
    capture_output=True, text=True, check=True).stdout.split()
for i in range(0, len(check), 3):
    sha, typ = check[i], check[i + 1]
    if typ != "blob":
        continue
    blob = subprocess.run(["git", "-C", str(REPO), "cat-file", "blob", sha],
                          capture_output=True).stdout
    if report(f"blob {sha}", blob)[0]:
        who = subprocess.run(["git", "-C", str(REPO), "log", "--all",
                              "--format=%h %ad %s", "--find-object=" + sha],
                             capture_output=True, text=True).stdout.strip()
        print(f"    xuat hien trong: {' / '.join(who.splitlines())}")

print("### commit message, author, committer")
for c in subprocess.run(["git", "-C", str(REPO), "rev-list", "--all"],
                        capture_output=True, text=True, check=True).stdout.split():
    meta = subprocess.run(["git", "-C", str(REPO), "log", "-1",
                           "--format=%B%n%an%n%ae%n%cn", c],
                          capture_output=True).stdout
    report(f"commit {c[:8]}", meta)

print("### refs va object loi lac")
print(subprocess.run(["git", "-C", str(REPO), "for-each-ref"], capture_output=True,
                     text=True).stdout.strip() or "(chi co main)")
print(subprocess.run(["git", "-C", str(REPO), "fsck", "--full", "--no-progress",
                      "--dangling"], capture_output=True, text=True).stdout.strip()
      or "(fsck: khong co dangling object)")
