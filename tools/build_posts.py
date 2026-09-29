#!/usr/bin/env python3
"""Sinh `_posts/*.md` cho site Jekyll (Chirpy) từ kho writeup theo thư mục.

Nguồn sự thật vẫn là "<Event>/<slug>/writeup.md". Script này chỉ thêm front matter,
dịch link tương đối sang đường dẫn tuyệt đối của site, và đặt tên file theo kiểu
Jekyll để trang chủ / categories / tags của Chirpy liệt kê được.

Chạy:  python tools/build_posts.py [--dry]
"""
import datetime as dt
import os
import re
import subprocess
import sys
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_BASE = "/CTFWU"
CAT_WORDS = ["crypto", "web", "pwn", "reverse", "rev", "forensics", "osint",
             "steg", "stego", "misc", "hardware", "blockchain", "ai", "game hacking"]
SKIP_TOP = {".git", ".github", "_data", "_plugins", "_tabs", "_template",
            "_wip", "_de_raw", "tools", "assets", "node_modules"}


def event_dirs():
    for name in sorted(os.listdir(ROOT)):
        p = os.path.join(ROOT, name)
        if os.path.isdir(p) and name not in SKIP_TOP and not name.startswith("."):
            yield name


def case_date(path):
    try:
        out = subprocess.run(["git", "-C", ROOT, "log", "-1", "--format=%cI", "--", path],
                             capture_output=True, text=True, timeout=30).stdout.strip()
        if out:
            return dt.datetime.fromisoformat(out)
    except Exception:
        pass
    return dt.datetime.fromtimestamp(os.path.getmtime(path))


def readme_categories(event):
    """Đọc bảng 'Solved Challenges' trong README của event: slug -> (category, difficulty)."""
    map_ = {}
    p = os.path.join(ROOT, event, "README.md")
    if not os.path.exists(p):
        return map_
    rows = [ln for ln in open(p, encoding="utf-8").read().split("\n") if ln.startswith("|")]
    hdr = next((r for r in rows if re.search(r"\bCategory\b", r)), None)
    if not hdr:
        return map_
    cols = [c.strip().lower() for c in hdr.strip("|").split("|")]
    ic = cols.index("category")
    idif = cols.index("difficulty") if "difficulty" in cols else None
    for r in rows:
        if r is hdr or set(r) <= {"|", "-", " "}:
            continue
        cells = [c.strip() for c in r.strip("|").split("|")]
        if len(cells) <= ic:
            continue
        m = re.search(r"\]\(([^)/]+)/writeup\.md\)", cells[0])
        if m:
            map_[m.group(1)] = (cells[ic], cells[idif] if idif is not None else "")
    return map_


def guess_category(text, known):
    for w in CAT_WORDS:
        if re.search(r"(?i)\b%s\b" % w, known):
            return w
    m = re.search(r"(?i)^#\s+.*?[—-]\s*([A-Za-z ]{3,20})\s*\(", text.split("\n")[0])
    return m.group(1).strip().lower() if m else "writeup"


def slugify(s):
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s or "x"


FILE_EXT = r"\.(md|png|jpg|jpeg|gif|svg|py|txt|json|zip|sav|pcap|cap|bin|elf|yml|yaml|html|csv|tsv|7z|tar|gz|xz|wav|mp3|pdf|xlsx?|docx?|pptx?)$"


def looks_like_path(target):
    return bool(re.search(FILE_EXT + r"$", target.split("#")[0], re.I) or "/" in target)


def fix_links(body, event, slug, post_names):
    case_prefix = "%s/%s/%s" % (SITE_BASE, quote(event), quote(slug))
    # Link trong code span / fenced block la vi du, khong phai link that -> giu nguyen
    stash = []

    def hold(m):
        stash.append(m.group(0))
        return "\x00%d\x00" % (len(stash) - 1)

    body = re.sub(r"```[\s\S]*?```", hold, body)
    body = re.sub(r"`[^`\n]*`", hold, body)

    def repl(m):
        target = m.group(1).strip()
        if re.match(r"^(https?:|mailto:|#|/)", target) or not looks_like_path(target):
            return m.group(0)
        if target.endswith("/writeup.md") or target == "writeup.md":
            other = os.path.normpath(os.path.join(event, slug, target)).replace("\\", "/")
            key = other.split("/")[-2]
            if key in post_names:
                return "](%s/posts/%s/" % (SITE_BASE, post_names[key])
        clean = target.split("#")[0]
        if not clean:
            return m.group(0)
        if clean.endswith(".md"):                      # Jekyll xuat page dang .html
            target = clean[:-3] + ".html" + target[len(clean):]
        return "](%s/%s)" % (case_prefix, quote(target))

    body = re.sub(r"\]\(([^)]+)\)", repl, body)
    return re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], body)


def protect_liquid(body):
    """Writeup co the chua cú pháp Liquid that (`{{7*7}}`, `{% ... %}` tu payload
    SSTI). Jekyll render noi dung qua Liquid nen phai bao ve, neu khong build fail
    hoac noi dung bi an mot."""
    if "{% raw %}" in body or "{% endraw %}" in body:
        raise SystemExit("writeup chua the '{%% raw %%}' -> khong boc duoc; sua nguon truoc")
    return "{% raw %}\n" + body + "\n{% endraw %}\n"


def build(dry=False):
    posts_dir = os.path.join(ROOT, "_posts")
    post_names, out_files = {}, []
    for event in event_dirs():
        catmap = readme_categories(event)
        for slug in sorted(os.listdir(os.path.join(ROOT, event))):
            w = os.path.join(ROOT, event, slug, "writeup.md")
            if not os.path.isfile(w):
                continue
            text = open(w, encoding="utf-8").read()
            title = next((ln[2:].strip() for ln in text.split("\n")
                          if ln.startswith("# ")), "%s - %s" % (event, slug))
            d = case_date(w)
            key = "%s-%s" % (slugify(event), slugify(slug))
            post_names[slug] = key
            known = catmap.get(slug, ("", ""))[0]
            cat = (known or guess_category(text, known)).strip()
            tags = [slugify(event).replace("-ctf-", "-").replace("-2026", ""), cat]
            img = os.path.join(ROOT, event, slug, "files", "de.png")
            fm = ["---",
                  'title: "%s"' % title.replace('"', "'"),
                  "date: %s +0700" % d.strftime("%Y-%m-%d %H:%M:%S"),
                  "lastmod_at: %s" % d.strftime("%Y-%m-%d %H:%M:%S %z"),
                  "categories: [%s]" % cat,
                  "tags: [%s]" % ", ".join(t for t in dict.fromkeys(tags) if t),
                  ]
            if os.path.exists(img):
                fm += ["image:",
                       "  path: %s/%s/%s/files/de.png" % (SITE_BASE, quote(event), quote(slug))]
            fm += ["---", ""]
            body = text.split("\n")
            if body and body[0].startswith("# "):
                body = body[1:]
            body = fix_links("\n".join(body).strip() + "\n", event, slug, post_names)
            body = protect_liquid(body)
            rel = os.path.join("_posts", "%s-%s.md" % (d.strftime("%Y-%m-%d"), key))
            out_files.append((rel, "\n".join(fm) + body))
    if dry:
        for rel, _ in out_files:
            print("  would write", rel)
    else:
        os.makedirs(posts_dir, exist_ok=True)
        for old in os.listdir(posts_dir):
            if old.endswith(".md"):
                os.remove(os.path.join(posts_dir, old))
        for rel, content in out_files:
            open(os.path.join(ROOT, rel), "w", encoding="utf-8", newline="\n").write(content)
    print("da sinh %d bai vao _posts/" % len(out_files))


if __name__ == "__main__":
    build("--dry" in sys.argv)
