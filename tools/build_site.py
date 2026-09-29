#!/usr/bin/env python3
"""Dựng `_site_src/` cho Jekyll (Chirpy) từ kho writeup, rồi mới tới lượt Jekyll.

Ly do co buoc nay: kho luu tru >1 GB artifact (snapshot website, disk image, pcap).
De Jekyll build thang tren repo thi toan bo artifact bi copy vao _site va
htmlproofer se di kiem tung link trong cac trang artifact ay. Stage chi giu lai
noi dung site + anh ma writeup thoc dung.

Chay:  python tools/build_site.py
"""
import datetime as dt
import os
import re
import shutil
import subprocess
import sys
from urllib.parse import quote

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_BASE = "/CTFWU"
STAGE = os.path.join(ROOT, "_site_src")
SKIP_TOP = {".git", ".github", "site", "tools", "_site_src", "_site", "assets",
            "node_modules", "_template", "_wip", "_de_raw", "docs"}
IMG_EXT = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp")
MAX_COPY = 4 * 1024 * 1024            # khong copy file > 4 MB vao site


def event_dirs():
    for name in sorted(os.listdir(ROOT)):
        p = os.path.join(ROOT, name)
        if os.path.isdir(p) and name not in SKIP_TOP and not name.startswith((".", "_")):
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
    m = {}
    p = os.path.join(ROOT, event, "README.md")
    if not os.path.exists(p):
        return m
    rows = [ln for ln in open(p, encoding="utf-8").read().split("\n") if ln.startswith("|")]
    hdr = next((r for r in rows if re.search(r"\bCategory\b", r)), None)
    if not hdr:
        return m
    cols = [c.strip().lower() for c in hdr.strip("|").split("|")]
    ic = cols.index("category")
    for r in rows:
        if r is hdr or set(r) <= {"|", "-", " "}:
            continue
        cells = [c.strip() for c in r.strip("|").split("|")]
        if len(cells) <= ic:
            continue
        mm = re.search(r"\]\(([^)/]+)/writeup\.md\)", cells[0])
        if mm:
            m[mm.group(1)] = cells[ic]
    return m


def slugify(s):
    return re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower() or "x"


LIQUID_SPAN = re.compile(r"\{\{.*?\}\}|\{%.*?%\}|\{\{.*$|\{%.*$", re.M)


def protect_liquid(body):
    """Giup Liquid khong thuc thi payload SSTI/Jinja ma writeup chem lai.

    Mac dinh boc tung doan bang {% raw %} de excerpt (cat tu nguon chua render)
    van sach. Neu chinh noi dung chua the raw nay thi khong dung cach do
    duoc - no se ket thuc som - nen doi thanh escape delimiter.
    """
    if "{% raw %}" in body or "{% endraw %}" in body:
        return re.sub(r"\{\{|\{%", lambda m: "{{ '%s' }}" % m.group(0), body)

    out = LIQUID_SPAN.sub(lambda m: "{%% raw %%}%s{%% endraw %%}" % m.group(0), body)
    stripped = re.sub(r"\{% raw %\}[\s\S]*?\{% endraw %\}", "", out)
    if "{{" in stripped or "{%" in stripped:
        raise SystemExit("con Liquid khong duoc bao ve")
    return out


def describe(body):
    for ln in body.split("\n"):
        s = ln.strip()
        if s and not s.startswith(("#", "!", ">", "|", "```", "---")):
            s = re.sub(r"[*_`]", "", s)
            return s[:157] + "..." if len(s) > 157 else s
    return ""


def copy_asset(src_abs, ev_slug, case_slug, name):
    dst_dir = os.path.join(STAGE, "assets", "writeups", ev_slug, case_slug)
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, os.path.basename(name))
    shutil.copyfile(src_abs, dst)
    return "/%s/assets/writeups/%s/%s/%s" % (SITE_BASE.strip("/"), ev_slug, case_slug,
                                             quote(os.path.basename(name)))


def build():
    if os.path.isdir(STAGE):
        shutil.rmtree(STAGE)
    shutil.copytree(os.path.join(ROOT, "site"), STAGE)
    posts, n_img = [], 0
    for event in event_dirs():
        ev_slug, catmap = slugify(event), readme_categories(event)
        for case in sorted(os.listdir(os.path.join(ROOT, event))):
            w = os.path.join(ROOT, event, case, "writeup.md")
            if not os.path.isfile(w):
                continue
            text = open(w, encoding="utf-8").read()
            title = next((ln[2:].strip() for ln in text.split("\n")
                          if ln.startswith("# ")), "%s - %s" % (event, case))
            d = case_date(w)
            key = "%s-%s" % (ev_slug, slugify(case))
            cat = (catmap.get(case) or "writeup").strip()
            tags = [t for t in dict.fromkeys([ev_slug.replace("-ctf-", "-").replace("-2026", ""),
                                              cat.lower()]) if t]

            body = text.split("\n")
            if body and body[0].startswith("# "):
                body = body[1:]
            body = "\n".join(body).strip() + "\n"

            def hold(m):
                nonlocal n_img
                alt, target = m.group(1), m.group(2).strip()
                if re.match(r"^(https?:|/|#)", target):
                    return m.group(0)
                src = os.path.normpath(os.path.join(ROOT, event, case, target.split("#")[0]))
                if not os.path.isfile(src) or os.path.getsize(src) > MAX_COPY:
                    return m.group(0)
                n_img += 1
                return "![%s](%s)" % (alt, copy_asset(src, ev_slug, case, target))

            body = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", hold, body)
            body = protect_liquid(body)
            fm = ["---", 'title: "%s"' % title.replace('"', "'"),
                  "date: %s +0700" % d.strftime("%Y-%m-%d %H:%M:%S"),
                  "lastmod_at: %s" % d.strftime("%Y-%m-%d %H:%M:%S %z"),
                  "categories: [%s]" % cat, "tags: [%s]" % ", ".join(tags)]
            desc = describe(text)
            if desc:
                fm.append('description: "%s"' % desc.replace('"', "'"))
            preview = os.path.join(ROOT, event, case, "files", "de.png")
            if os.path.isfile(preview) and os.path.getsize(preview) <= MAX_COPY:
                dst_dir = os.path.join(STAGE, "assets", "writeups", ev_slug, slugify(case))
                os.makedirs(dst_dir, exist_ok=True)
                shutil.copyfile(preview, os.path.join(dst_dir, "de.png"))
                n_img += 1
                fm += ["image:", "  path: /assets/writeups/%s/%s/de.png"
                       % (ev_slug, slugify(case))]
            fm += ["---", ""]
            os.makedirs(os.path.join(STAGE, "_posts"), exist_ok=True)
            out = os.path.join(STAGE, "_posts", "%s-%s.md" % (d.strftime("%Y-%m-%d"), key))
            open(out, "w", encoding="utf-8", newline="\n").write(
                "\n".join(fm) + protect_liquid(body))
            posts.append(out)
    total = sum(os.path.getsize(os.path.join(dp, f))
                for dp, _, fs in os.walk(STAGE) for f in fs)
    print("stage=%s  posts=%d  asset copied=%d  tong %.1f MB"
          % (os.path.relpath(STAGE, ROOT), len(posts), n_img, total / 1e6))


if __name__ == "__main__":
    build()
