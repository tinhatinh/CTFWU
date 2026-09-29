#!/usr/bin/env python3
"""Dựng `_site_src/` (tieng Viet) va `_site_src_en/` (tieng Anh) cho Jekyll.

Kho writeup theo thu muc van la nguon duy nhat:
    <Event>/<slug>/writeup.md        ban tieng Viet
    <Event>/<slug>/writeup.en.md     ban tieng Anh (thieu thi bai do bi loai o cay en)

Ly do build 2 cay: Chirpy khong co i18n plugin, ma trang chu / categories / archive
cua no liet ke toan bo `site.posts`. De tron hai ngon ngu vung chung mot cay thi
nội dung VI va EN dong lan tren trang chu. Cach nay giu nguyen HTML cua Chirpy:
moi cay la mot site hoan chinh, nut ngon ngu chi doi mirror URL.

Chay:  python tools/build_site.py            # ca hai ngon ngu
        python tools/build_site.py --lang vi # mot cay
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
from urllib.parse import quote

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_TOP = {".git", ".github", "site", "tools", "_site_src", "_site_src_en",
            "_site", "assets", "node_modules", "_template", "_wip", "_de_raw", "docs"}
MAX_COPY = 4 * 1024 * 1024
# Nen pastel + muc dam, cung bang mau voi site/assets/css/campus.css
COLORS = ["#98ff98", "#add8e6", "#fdbcb4", "#e6e6fa"]
INK = "#2d3748"
CONTEST_TZ = dt.timezone(dt.timedelta(hours=7), "UTC+7")

UI = {
    "vi": {"competitions": "Các cuộc thi", "posts": "bài writeup", "view": "Xem writeup",
           "tagline": "Writeup CTF của tinhatinh, đội R3:TURИ",
           "description": "Writeup CTF của Danh Phan trong đội R3:TURИ: H7TEX, SunshineCTF, Pointer Overflow",
           "hint": "Mỗi cuộc thi là một mục. Bên trong là các bài giải, xếp theo chuyên mục."},
    "en": {"competitions": "Competitions", "posts": "writeups", "view": "Read writeups",
           "tagline": "CTF writeups by tinhatinh, team R3:TURИ",
           "description": "CTF writeups by Danh Phan of team R3:TURИ: H7TEX, SunshineCTF, Pointer Overflow",
           "hint": "One card per event. Inside each one, the solutions grouped by category.",
           "nottranslated": "This post has no English version yet."},
}

TEAM = "R3:TURИ"
MEMBERS = [
    ("minhduc26122913", "187061", ""),
    ("k4tpr02k5", "236179", ""),
    ("Tikilazada", "251074", "Tikilazada"),
    # CTFTime dang la "cu_kh1nh_b0_m4y_d1" (id 272628), doi ten hien thi theo yeu cau
    ("tinhatinh", "272628", "tinhatinh"),
    ("Lizamort1", "274020", "Lizamort1"),
]


MEMBER_UI = {
    "vi": {"head": "| Thành viên | CTFTime | GitHub |", "link": "hồ sơ", "me": "(mình)"},
    "en": {"head": "| Member | CTFTime | GitHub |", "link": "profile", "me": "(me)"},
}


def member_table(lang):
    ui = MEMBER_UI[lang]
    rows = [ui["head"], "|---|---|---|"]
    for handle, cid, gh in MEMBERS:
        me = " " + ui["me"] if gh == "tinhatinh" else ""
        github = "[@%s](https://github.com/%s)" % (gh, gh) if gh else "-"
        rows.append("| `%s`%s | [%s](https://ctftime.org/user/%s) | %s |"
                    % (handle, me, ui["link"], cid, github))
    return "\n".join(rows) + "\n"

ABOUT = {
    "vi": """Mình là **Phan Thành Danh** ([@tinhatinh](https://github.com/tinhatinh)), sinh viên Công
nghệ thông tin tại Học viện Bưu chính Viễn thông (PTIT), đang học thêm về kiểm thử bảo mật.

- Ngoại ngữ: tiếng Trung HSK 4 (262/300) kèm HSKK Trung cấp, tiếng Anh đang hướng tới TOEIC 850.
- Công cụ dùng hằng ngày: Python, C/C++, Java, Linux/Bash, Docker, Git.
- Liên hệ: [ptdanh007@gmail.com](mailto:ptdanh007@gmail.com),
  [Facebook](https://www.facebook.com/winterboyy), [TikTok](https://www.tiktok.com/@danh_pachirisu).

## Phạm vi

Mọi bài trên trang này là writeup do chính mình viết, tức phần của mình trong lời giải của đội
**{team}** ([CTFTime team 449538](https://ctftime.org/team/449538)). Lời giải của các thành viên
khác không nằm ở đây.

Mỗi đề là một thư mục trong repo [`tinhatinh/CTFWU`](https://github.com/tinhatinh/CTFWU) gồm
`de.md` (đề nguyên văn + metadata đã kiểm chứng), `writeup.md` (cách giải), `notes.md` (nhật ký giả
thuyết, kể cả hướng sai), `exploit.py` (script chạy lại được) và `files/` (artifact gốc đã đối
chiếu sha256).

Toàn bộ lời giải chỉ dựa vào artifact của chính đề bài, không tra writeup của người khác.
Flag là giá trị riêng theo team, nên copy từ đây về nộp sẽ không hợp lệ.

## Đội

{team} gồm năm thành viên. Ở POCTF 2026 đội đăng ký dưới số 612, nên thẻ đề và flag của các bài
POCTF mang số đó.

{members}
""",
    "en": """I'm **Phan Thành Danh** ([@tinhatinh](https://github.com/tinhatinh)), an IT student at the
Posts and Telecommunications Institute of Technology (PTIT), currently studying security testing.

- Languages: Chinese HSK 4 (262/300) with HSKK Intermediate, working towards TOEIC 850 in English.
- Daily tools: Python, C/C++, Java, Linux/Bash, Docker, Git.
- Contact: [ptdanh007@gmail.com](mailto:ptdanh007@gmail.com),
  [Facebook](https://www.facebook.com/winterboyy), [TikTok](https://www.tiktok.com/@danh_pachirisu).

## Scope

Every post here is a writeup I wrote myself, which is my share of what team
**{team}** ([CTFTime team 449538](https://ctftime.org/team/449538)) solved. Teammates publish
their own solutions elsewhere.

Each challenge is a folder in the [`tinhatinh/CTFWU`](https://github.com/tinhatinh/CTFWU) repo
holding `de.md` (the statement plus verified metadata), `writeup.md` (the solution), `notes.md`
(the hypothesis log, wrong turns included), `exploit.py` (a script that replays the solve) and
`files/` (original artifacts, sha256 checked).

Every solution comes from the challenge's own artifact only, with no outside writeups consulted.
Flags are per team, so copying one from here will not be accepted.

## Team

{team} has five members. At POCTF 2026 the team registered as number 612, which is why the POCTF
challenge cards and flags carry that id.

{members}
""",
}

LIQUID_SPAN = re.compile(r"\{\{.*?\}\}|\{%.*?%\}|\{\{.*$|\{%.*$", re.M)
SOLVE_TIMES = os.path.join(ROOT, "tools", "solve_times.json")


def event_dirs():
    for name in sorted(os.listdir(ROOT)):
        p = os.path.join(ROOT, name)
        if os.path.isdir(p) and name not in SKIP_TOP and not name.startswith((".", "_")):
            yield name


def slugify(s):
    return re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower() or "x"


def git_time(path):
    try:
        out = subprocess.run(["git", "-C", ROOT, "log", "-1", "--format=%cI", "--", path],
                             capture_output=True, text=True, timeout=30).stdout.strip()
        if out:
            return dt.datetime.fromisoformat(out)
    except Exception:
        pass
    return None


def flag_time(event, case):
    """Birthtime sớm nhất trong số flag.txt/flags.txt = lúc flag được ghi nhận trên máy."""
    best = None
    for dp, _, fs in os.walk(os.path.join(ROOT, event, case)):
        for n in fs:
            if n not in ("flag.txt", "flags.txt"):
                continue
            b = getattr(os.stat(os.path.join(dp, n)), "st_birthtime", 0)
            if b and (best is None or b < best):
                best = b
    return dt.datetime.fromtimestamp(best, CONTEST_TZ) if best else None


def solve_times():
    """`tools/solve_times.json`: thoi diem giai trong cuoc thi, <Event>/<case> -> ISO.

    Gia tri chi co ngay (YYYY-MM-DD, khong gio) du dung khi flag bi chep sang may hang
    loat: luc do mtime/birthtime khong con la bang chung ve phut.
    """
    raw = {}
    if os.path.isfile(SOLVE_TIMES):
        raw = json.load(open(SOLVE_TIMES, encoding="utf-8"))
    out = {}
    for key, val in raw.items():
        d = dt.datetime.fromisoformat(val)
        out[key] = (d if d.tzinfo else d.replace(tzinfo=CONTEST_TZ), "T" in val)
    return out


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


def protect_liquid(body):
    """Giup Liquid khong thuc thi payload SSTI/Jinja ma writeup chem lai.

    Mac dinh boc tung doan bang raw tag de excerpt (cat tu nguon chua render) van
    sach. Neu chinh noi dung chua raw tag thi khong long duoc, phai escape delimiter.
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


def cover_html(ev, base):
    """Khung cover cua su kien: `site/assets/competitions/<slug>.<ext>` that, khong
    co thi tile SVG sinh.

    Anh that phat qua `background-image`, KHONG dung the <img>: Chirpy boc moi
    <img> trong `a.popup.img-link` de mo lightbox, ma the card da la <a> -> nested
    anchor bi parser huy, anh nam ra ngoai card (phat hien khi do live, run #14).
    Duong dan co prefix baseurl vi khong co nao noi chuoi vao style.
    """
    for ext in ("png", "jpg", "jpeg", "webp", "svg"):
        f = "%s.%s" % (ev["slug"], ext)
        if os.path.isfile(os.path.join(ROOT, "site", "assets", "competitions", f)):
            return ('<span class="ctfw-cover" style="background-image:url(\'%s/assets/competitions/%s\')"></span>'
                    % (base, f))
    return '<span class="ctfw-cover">%s</span>' % cover_svg(ev["name"], ev["idx"])


def stamp(d, lang, exact=True):
    fmt = ("%d/%m/%Y" if lang == "vi" else "%b %d, %Y") + (" %H:%M" if exact else "")
    return d.strftime(fmt)


def initials(name):
    words = re.findall(r"[A-Za-z0-9]+", name)
    core = "".join(w[0] for w in words if w[0].isupper()) or (words[0][:2] if words else "CT")
    return (core[:4] or "CT").upper()


def cover_svg(name, i):
    """Tile du phong cho su kien chua lay duoc anh bìa that (xem cover_html)."""
    bg, fg = COLORS[i % len(COLORS)], INK
    year = re.search(r"(20\d\d)", name)
    label = re.sub(r"\s*(CTF|20\d\d).*", "", name).strip() or name
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 300" role="img" aria-label="{name}">
<rect width="600" height="300" fill="{bg}"/>
<g stroke="{fg}" stroke-width="14" opacity=".14">
{''.join(f'<line x1="{x}" y1="300" x2="{x+180}" y2="0"/>' for x in range(-180, 600, 60))}
</g>
<rect x="24" y="24" width="552" height="252" rx="20" fill="none" stroke="{fg}" stroke-width="8"/>
<text x="52" y="150" font-family="Fredoka,Nunito,Arial,sans-serif" font-size="86" font-weight="700" fill="{fg}">{initials(name)}</text>
<text x="52" y="212" font-family="Nunito,Arial,sans-serif" font-size="30" font-weight="700" fill="{fg}">{label[:26]}</text>
<text x="52" y="252" font-family="Nunito,Arial,sans-serif" font-size="20" letter-spacing="4" fill="{fg}">{year.group(1) if year else 'CTF'}</text>
</svg>
"""


def collect(lang):
    """Tra ve danh sach event -> bai viet cho mot ngon ngu."""
    events = []
    times = solve_times()
    seen = set()
    for i, event in enumerate(event_dirs()):
        fname = "writeup.md" if lang == "vi" else "writeup.en.md"
        catmap = readme_categories(event)
        posts = []
        for case in sorted(os.listdir(os.path.join(ROOT, event))):
            w = os.path.join(ROOT, event, case, fname)
            fallback = False
            if not os.path.isfile(w):
                # cay en: bai chua dich thi tam dung ban tieng Viet, co danh ngu
                if lang != "en":
                    continue
                w = os.path.join(ROOT, event, case, "writeup.md")
                if not os.path.isfile(w):
                    continue
                fallback = True
            text = open(w, encoding="utf-8").read()
            title = next((ln[2:].strip() for ln in text.split("\n")
                          if ln.startswith("# ")), "%s - %s" % (event, case))
            key = "%s/%s" % (event, case)
            seen.add(key)
            mod = git_time(w)
            solved, exact = times.get(key) or (flag_time(event, case), True)
            if not solved:
                solved = mod or dt.datetime.fromtimestamp(os.path.getmtime(w), CONTEST_TZ)
                exact = False
            posts.append({
                "case": case, "path": w, "text": text, "title": title,
                "date": solved, "exact": exact, "mod": mod,
                "key": "%s-%s" % (slugify(event), slugify(case)),
                "cat": (catmap.get(case) or "writeup").strip(), "fallback": fallback,
            })
        if posts:
            events.append({"name": event, "slug": slugify(event), "posts": posts, "idx": i})
    stale = sorted(set(times) - seen)
    if stale:
        print("  canh bao: solve_times.json thua %d key: %s"
              % (len(stale), ", ".join(stale[:3]) + ("..." if len(stale) > 3 else "")))
    return events


def write_post(stage, ev, p, lang, base):
    body = p["text"].split("\n")
    if body and body[0].startswith("# "):
        body = body[1:]
    body = "\n".join(body).strip() + "\n"

    def hold(m):
        alt, target = m.group(1), m.group(2).strip()
        if re.match(r"^(https?:|/|#)", target):
            return m.group(0)
        src = os.path.normpath(os.path.join(ROOT, ev["name"], p["case"], target.split("#")[0]))
        if not os.path.isfile(src) or os.path.getsize(src) > MAX_COPY:
            return m.group(0)
        dst_dir = os.path.join(stage, "assets", "writeups", ev["slug"], p["case"])
        os.makedirs(dst_dir, exist_ok=True)
        shutil.copyfile(src, os.path.join(dst_dir, os.path.basename(src)))
        return "![%s](%s/assets/writeups/%s/%s/%s)" % (
            alt, base, ev["slug"], p["case"], quote(os.path.basename(src)))

    body = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", hold, body)
    if p.get("fallback"):
        body = ("> %s\n{: .prompt-warning }\n\n" % UI["en"]["nottranslated"]) + body
    body = protect_liquid(body)

    d = p["date"]
    mod = p["mod"] or d
    fm = ["---", 'title: "%s"' % p["title"].replace('"', "'"),
          "date: %s %s" % (d.strftime("%Y-%m-%d %H:%M:%S"), d.strftime("%z")),
          "lastmod_at: %s" % mod.strftime("%Y-%m-%d %H:%M:%S %z"),
          "categories: [%s]" % p["cat"],
          "tags: [%s]" % ", ".join(dict.fromkeys([ev["slug"].replace("-ctf-", "-").replace("-2026", ""),
                                                  p["cat"].lower()])),
          "permalink: /posts/%s/" % p["key"]]
    desc = describe(p["text"])
    if desc:
        fm.append('description: "%s"' % desc.replace('"', "'"))
    preview = os.path.join(ROOT, ev["name"], p["case"], "files", "de.png")
    if os.path.isfile(preview) and os.path.getsize(preview) <= MAX_COPY:
        dst_dir = os.path.join(stage, "assets", "writeups", ev["slug"], p["case"])
        os.makedirs(dst_dir, exist_ok=True)
        shutil.copyfile(preview, os.path.join(dst_dir, "de.png"))
        fm += ["image:", "  path: /assets/writeups/%s/%s/de.png" % (ev["slug"], p["case"])]
    fm += ["---", ""]
    out_dir = os.path.join(stage, "_posts")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "%s-%s.md" % (d.strftime("%Y-%m-%d"), p["key"]))
    text_out = "\n".join(fm) + body
    if text_out.count("{% raw %}") != text_out.count("{% endraw %}"):
        raise SystemExit("the raw khong can doi o %s/%s" % (ev["name"], p["case"]))
    open(out, "w", encoding="utf-8", newline="\n").write(text_out)
    return out


def write_event_page(stage, ev, lang, base):
    ui = UI[lang]
    lines = ["---", 'title: "%s"' % ev["name"], "layout: page",
             "permalink: /events/%s/" % ev["slug"],
             'description: "%s"' % ("%d %s" % (len(ev["posts"]), ui["posts"])), "---", ""]
    for p in sorted(ev["posts"], key=lambda x: x["date"]):
        lines.append('- [%s](%s/posts/%s/) · `%s` · %s'
                     % (p["title"], base, p["key"], p["cat"],
                        stamp(p["date"], lang, p["exact"])))
    lines.append("")
    out = os.path.join(stage, "events")
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "%s.md" % ev["slug"]), "w", encoding="utf-8", newline="\n").write("\n".join(lines))


def write_competitions(stage, events, lang, base):
    ui = UI[lang]
    body = ["---", 'title: "%s"' % ui["competitions"], "icon: fas fa-trophy", "order: 1",
            "layout: page", "permalink: /competitions/", "---", ""]
    body.append("<p>%s</p>\n" % ui["hint"])
    body.append('<div class="ctfw-cards">')
    for ev in events:
        first = min(p["date"] for p in ev["posts"])
        last = max(p["date"] for p in ev["posts"])
        span = stamp(last, lang, False)
        if first.date() != last.date():
            span = "%s → %s" % (stamp(first, lang, False), span)
        cats = sorted({p["cat"] for p in ev["posts"]})
        cover = cover_html(ev, base)
        body.append(
            '<a class="ctfw-card" href="%s/events/%s/">'
            '%s'
            '<div class="ctfw-body"><span class="ctfw-kicker">CTF %s</span>'
            '<div class="ctfw-name">%s</div>'
            '<div>%s</div>'
            '<div class="ctfw-meta"><span>%d %s</span><span>%s</span>'
            '<span>%s &rarr;</span></div></div></a>'
            % (base, ev["slug"], cover, last.year, ev["name"],
               ", ".join(cats), len(ev["posts"]), ui["posts"], span, ui["view"]))
    body.append("</div>\n")
    out = os.path.join(stage, "_tabs")
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "competitions.md"), "w", encoding="utf-8", newline="\n").write("\n".join(body))


def write_about(stage, lang):
    out = os.path.join(stage, "_tabs")
    os.makedirs(out, exist_ok=True)
    fm = "---\nicon: fas fa-info-circle\norder: 5\n---\n\n"
    about = ABOUT[lang].replace("{team}", TEAM).replace("{members}", member_table(lang))
    if "{t" in about:
        raise SystemExit("placeholder ve trong about")
    open(os.path.join(out, "about.md"), "w", encoding="utf-8", newline="\n").write(fm + about)


def build(lang):
    stage = os.path.join(ROOT, "_site_src" if lang == "vi" else "_site_src_en")
    base = "/CTFWU" if lang == "vi" else "/CTFWU/en"
    if os.path.isdir(stage):
        shutil.rmtree(stage)
    shutil.copytree(os.path.join(ROOT, "site"), stage)
    cfg = os.path.join(stage, "_config.yml")
    t = open(cfg, encoding="utf-8").read()
    if lang == "en":
        t = t.replace('baseurl: "/CTFWU"', 'baseurl: "/CTFWU/en"').replace("lang: vi-VN", "lang: en")
    t = re.sub(r"^tagline:.*$", 'tagline: "%s"' % UI[lang]["tagline"], t, flags=re.M)
    t = re.sub(r"^description:.*$", 'description: "%s"' % UI[lang]["description"], t, flags=re.M)
    open(cfg, "w", encoding="utf-8", newline="\n").write(t)
    events = collect(lang)
    pending = [p["key"] for ev in events for p in ev["posts"] if p.get("fallback")]
    n = 0
    for ev in events:
        for p in ev["posts"]:
            write_post(stage, ev, p, lang, base)
            n += 1
        write_event_page(stage, ev, lang, base)
    write_competitions(stage, events, lang, base)
    write_about(stage, lang)
    total = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(stage) for f in fs)
    if pending:
        print("[warn] %d bai en dang dung ban tieng Viet: %s" % (len(pending), ", ".join(pending)))
    print("[%s] %d event, %d bai, %.1f MB -> %s"
          % (lang, len(events), n, total / 1e6, os.path.relpath(stage, ROOT)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=["vi", "en", "all"], default="all")
    a = ap.parse_args()
    for lang in (["vi", "en"] if a.lang == "all" else [a.lang]):
        build(lang)
