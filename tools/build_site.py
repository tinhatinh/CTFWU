#!/usr/bin/env python3
"""Dựng `_site_src/` (tieng Viet) va `_site_src_en/` (tieng Anh) cho Jekyll.

Kho writeup theo thu muc van la nguon duy nhat:
    <Event>/<slug>/writeup.md        ban tieng Viet
    <Event>/<slug>/writeup.en.md     ban tieng Anh (thieu thi dung VI kem nhan fallback)
    <Event>/Wave N/<slug>/          cau truc tuy chon cho cuoc thi chia wave

Hai cay doc lap giup trang chu / categories / archive chi liet ke bai cua ngon ngu
hien tai. Layout rieng trong site/_layouts dung chung metadata tu kho writeup;
nut ngon ngu doi mirror URL va giu lai bo loc tim kiem.

Chay:  python tools/build_site.py            # ca hai ngon ngu
        python tools/build_site.py --lang vi # mot cay
"""
import argparse
import datetime as dt
import json
import html
import hashlib
import os
import re
import shutil
import subprocess
import sys
from urllib.parse import quote, unquote

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_TOP = {".git", ".github", "site", "tools", "_site_src", "_site_src_en",
            "_site", "assets", "node_modules", "_template", "_wip", "_de_raw", "docs"}
MAX_COPY = 32 * 1024 * 1024
# Nen pastel + muc dam, cung bang mau voi site/assets/css/campus.css
COLORS = ["#98ff98", "#add8e6", "#fdbcb4", "#e6e6fa"]
INK = "#2d3748"
CONTEST_TZ = dt.timezone(dt.timedelta(hours=7), "UTC+7")

UI = {
    "vi": {"competitions": "Thành tích", "posts": "bài writeup", "view": "Xem writeup",
           "tagline": "Writeup CTF của tinhatinh, đội R3:TURИ",
           "description": "Writeup CTF của Danh Phan trong đội R3:TURИ: H7TEX, SunshineCTF, Pointer Overflow",
           "hint": "Mỗi cuộc thi là một mục. Bên trong là các bài giải, xếp theo chuyên mục.",
           "achievements": "Thành tích",
           "ach_hint": "Bảng dưới là kết quả của [{team}]({url}) trên CTFTime, số liệu lấy ngày {date}. "
                       "Chỉ những giải đăng ký trên CTFTime mới có trong bảng.",
           "place": "Hạng", "event": "Giải", "ctf_points": "Điểm CTF", "rating_points": "Điểm rating"},
    "en": {"competitions": "Achievements", "posts": "writeups", "view": "Read writeups",
           "tagline": "CTF writeups by tinhatinh, team R3:TURИ",
           "description": "CTF writeups by Danh Phan of team R3:TURИ: H7TEX, SunshineCTF, Pointer Overflow",
           "hint": "One card per event. Inside each one, the solutions grouped by category.",
           "nottranslated": "This post has no English version yet.",
           "achievements": "Achievements",
           "ach_hint": "The table below is the record of [{team}]({url}) on CTFTime, fetched on {date}. "
                       "Only events registered on CTFTime appear in it.",
           "place": "Place", "event": "Event", "ctf_points": "CTF points", "rating_points": "Rating points"},
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

Mỗi đề là một thư mục trong repo [`tinhatinh/CTFWU`](https://github.com/tinhatinh/CTFWU).
`de.md` lưu đề và metadata, các bản `writeup` trình bày lời giải. Nhật ký, script tái hiện và
artifact đi kèm được giữ trong `notes.md`, các file script và `files/` khi có dữ liệu.

Mỗi bài ghi lại dữ liệu đầu vào, thao tác và kết quả đã thu thập; nguồn tham khảo kỹ thuật
được dẫn khi cần. Một số cuộc thi dùng artifact hoặc flag riêng theo đội, nên kết quả
cần được đối chiếu với dữ liệu và định dạng của từng challenge.

## Đội

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

Each challenge is a folder in the [`tinhatinh/CTFWU`](https://github.com/tinhatinh/CTFWU) repo.
`de.md` records the statement and metadata; the writeup editions explain the solution.
Available investigation logs, reproduction scripts and artifacts are kept in `notes.md`,
script files and `files/`.

Each post records its inputs, operations and observed results, with technical references where needed.
Some events issue team-specific artifacts or flags, so results must be checked against the data
and format of the individual challenge.

## Team

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
    with open(p, encoding='utf-8') as source:
        rows = [ln for ln in source.read().split('\n') if ln.startswith('|')]
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
        mm = re.search(r"\]\(<?([^)>]+?)/writeup\.md>?\)", cells[0])
        if mm:
            m[unquote(mm.group(1)).replace('\\', '/')] = cells[ic]
    return m


def case_directories(event_root):
    """Enumerate direct cases and one Wave N level, excluding unfinished folders."""
    for name in sorted(os.listdir(event_root)):
        folder = os.path.join(event_root, name)
        if not os.path.isdir(folder) or name.startswith(('.', '_')):
            continue
        if re.fullmatch(r'Wave [1-9]\d*', name):
            for case in sorted(os.listdir(folder)):
                target = os.path.join(folder, case)
                if os.path.isdir(target) and not case.startswith(('.', '_')):
                    if os.path.commonpath([os.path.realpath(event_root), os.path.realpath(target)]) == os.path.realpath(event_root):
                        yield name + '/' + case
        elif os.path.commonpath([os.path.realpath(event_root), os.path.realpath(folder)]) == os.path.realpath(event_root):
            yield name


def challenge_key(event, case):
    # Wave 1 retains the previously published permalink and editor key.
    identity = case[len('Wave 1/'):] if case.startswith('Wave 1/') else case
    return slugify(event) + '-' + slugify(identity)


def challenge_categories(label):
    """Return separate, canonical labels in source order (primary first)."""
    aliases = {
        "cryptography": "Crypto", "crypto": "Crypto",
        "reverse engineering": "Reverse", "rev eng": "Reverse",
        "reverse": "Reverse", "re": "Reverse", "rev": "Reverse", "reve": "Reverse",
        "pwn": "Pwn", "web exploitation": "Web", "web": "Web",
        "forensics": "Forensics", "osint": "OSINT", "misc": "Misc",
        "log analysis": "Log Analysis", "password cracking": "Password Cracking",
        "scanning": "Scanning", "nta": "NTA", "steg": "Steg",
        "warm-up": "Warm-up", "web3": "Web3", "ai": "AI", "cloud": "Cloud",
        "hardware": "Hardware", "mobile": "Mobile", "exp": "EXP",
        "game hacking": "Game Hacking",
    }
    # Longest labels first also handles legacy strings without '+' delimiters.
    pattern = r"(?<!\w)(?:" + "|".join(re.escape(a) for a in sorted(aliases, key=len, reverse=True)) + r")(?!\w)"
    return list(dict.fromkeys(aliases[m.group().lower()] for m in re.finditer(pattern, label, re.I)))


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
    # Use an actual prose paragraph, never the flag / attachment metadata.
    body = re.sub(r"```[\s\S]*?```", "", body)
    for paragraph in re.split(r"\n\s*\n", body):
        s = paragraph.strip()
        if not s or s.startswith(("#", "!", ">", "|", "**", "-", "```")):
            continue
        s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
        s = re.sub(r"\s+", " ", re.sub(r"[*_`]", "", s))
        if len(s) > 45:
            return s[:197].rsplit(" ", 1)[0] + "…" if len(s) > 197 else s
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


def collect(lang, require_solve_dates=False):
    """Tra ve danh sach event -> bai viet cho mot ngon ngu."""
    events = []
    times = solve_times()
    seen = set()
    identities = set()
    for i, event in enumerate(event_dirs()):
        fname = "writeup.md" if lang == "vi" else "writeup.en.md"
        catmap = readme_categories(event)
        posts = []
        for case in case_directories(os.path.join(ROOT, event)):
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
            with open(w, encoding="utf-8") as source:
                text = source.read()
            title = next((ln[2:].strip() for ln in text.split("\n")
                          if ln.startswith("# ")), "%s - %s" % (event, case))
            category_label = catmap.get(case)
            if not category_label:
                heading_parts = re.split(r"\s[-–—]\s", title, maxsplit=1)
                category_label = heading_parts[1] if len(heading_parts) > 1 else ""
            categories = challenge_categories(category_label)
            if not categories:
                raise ValueError("Missing challenge category: %s/%s" % (event, case))
            key = "%s/%s" % (event, case)
            identity = challenge_key(event, case)
            if identity in identities:
                raise ValueError('Duplicate challenge permalink: ' + identity)
            identities.add(identity)
            seen.add(key)
            mod = git_time(w)
            legacy_key = event + '/' + case[len('Wave 1/'):] if case.startswith('Wave 1/') else key
            if legacy_key in times:
                seen.add(legacy_key)
            recorded = times.get(key) or times.get(legacy_key)
            if not recorded and require_solve_dates:
                raise ValueError("Missing declared solve date in tools/solve_times.json: " + key)
            solved, exact = recorded or (flag_time(event, case), True)
            if not solved:
                # Draft preview only. Editorial commits are never solve evidence.
                solved = dt.datetime.fromtimestamp(os.path.getmtime(w), CONTEST_TZ)
                exact = False
            posts.append({
                "case": case, "path": w, "text": text, "title": title,
                "date": solved, "exact": exact, "mod": mod,
                "key": identity,
                "cat": categories[0], "cats": categories, "fallback": fallback,
            })
        if posts:
            events.append({"name": event, "slug": slugify(event), "posts": posts, "idx": i})
    stale = sorted(set(times) - seen)
    if stale:
        print("  canh bao: solve_times.json thua %d key: %s"
              % (len(stale), ", ".join(stale[:3]) + ("..." if len(stale) > 3 else "")))
    return events


def write_post(stage, ev, p, lang, base):
    # Some source translations repeat the opening title + metadata verbatim.
    # Collapse that exact duplicate in the rendered copy, preserving the source.
    paragraphs = p["text"].split("\n\n")
    if len(paragraphs) >= 4 and paragraphs[:2] == paragraphs[2:4]:
        paragraphs = paragraphs[2:]
    body = "\n\n".join(paragraphs).split("\n")
    if body and body[0].startswith("# "):
        body = body[1:]
    body = "\n".join(body).strip() + "\n"

    case_root = os.path.realpath(os.path.join(ROOT, ev["name"], p["case"]))
    copied = {}

    def copy_image(target):
        target = unquote(target.strip().strip("<>"))
        if re.match(r"^(https?:|/|#)", target):
            return None
        src = os.path.realpath(os.path.join(case_root, target.split("#")[0]))
        if not os.path.isfile(src):
            src = os.path.realpath(os.path.join(case_root, "files", target.split("#")[0]))
        if os.path.commonpath([os.path.realpath(case_root), src]) != os.path.realpath(case_root) or not os.path.isfile(src):
            return None
        if os.path.splitext(src)[1].lower() not in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"):
            return None
        if src in copied:
            return copied[src]
        if os.path.getsize(src) > MAX_COPY:
            print("[warn] image over size limit: " + os.path.relpath(src, ROOT))
            return None
        relative = os.path.relpath(src, case_root).replace(os.sep, "/")
        dst = os.path.join(stage, "assets", "writeups", ev["slug"], p["case"], relative)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        url = "/assets/writeups/%s/%s/%s" % (ev["slug"], quote(p["case"], safe="/"), quote(relative, safe="/"))
        copied[src] = url
        return url

    inline_images = set()
    def hold(m):
        alt, target = m.group(1), m.group(2).strip()
        url = copy_image(target)
        if not url:
            return m.group(0)
        inline_images.add(url)
        return "![%s](%s)" % (alt, url)

    body = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", hold, body)
    def source_link(match):
        label, target = match.group(1), unquote(match.group(2).strip().strip('<>'))
        path, _, fragment = target.partition('#')
        if re.match(r'^(?:[a-z]+:|/|#)', target, re.I) or not path.endswith('.md'):
            return match.group(0)
        source = os.path.realpath(os.path.join(case_root, path))
        if os.path.commonpath([os.path.realpath(ROOT), source]) != os.path.realpath(ROOT) or not os.path.isfile(source):
            return match.group(0)
        relative = os.path.relpath(source, ROOT).replace(os.sep, '/')
        parts = relative.split('/')
        other_case = '/'.join(parts[1:-1])
        if len(parts) >= 3 and parts[-1] in ('writeup.md', 'writeup.en.md') and other_case in case_directories(os.path.join(ROOT, parts[0])):
            url = base + '/posts/' + challenge_key(parts[0], other_case) + '/'
        else:
            url = 'https://github.com/tinhatinh/CTFWU/blob/main/' + quote(relative, safe='/')
        if fragment:
            url += '#' + fragment
        return '[' + label + '](' + url + ')'
    # Keep Markdown examples and captured payloads inside fenced code unchanged.
    prose_parts = re.split(r'(```.*?```|`[^`\n]*`)', body, flags=re.S)
    for i in range(0, len(prose_parts), 2):
        prose_parts[i] = re.sub(r'(?<!!)\[([^\]]+)\]\(([^)]+)\)', source_link, prose_parts[i])
    body = ''.join(prose_parts)
    statement_images = []
    statement_path = os.path.join(case_root, "de.md")
    statement = ""
    if os.path.isfile(statement_path):
        with open(statement_path, encoding="utf-8") as source:
            statement = source.read()
    references = re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", statement)
    if not references and os.path.isfile(os.path.join(case_root, "files", "de.png")):
        references = [("", "files/de.png")]
    seen = set(inline_images)
    for alt, target in references:
        url = copy_image(target)
        if url and url not in seen:
            statement_images.append({"path": url, "alt": alt if alt and alt != "de" else ("Ảnh đề bài" if lang == "vi" else "Challenge screenshot")})
            seen.add(url)
    artifact_images = []
    for target in re.findall(r"`([^`\n]+\.(?:png|jpg|jpeg|webp|gif|bmp))`", p["text"], re.I):
        url = copy_image(target)
        if url and url not in seen:
            artifact_images.append({"path": url, "alt": target})
            seen.add(url)
    if p.get("fallback"):
        body = ("> %s\n{: .prompt-warning }\n\n" % UI["en"]["nottranslated"]) + body
    body = protect_liquid(body)

    d = p["date"]
    mod = p["mod"] or d
    fm = ["---", 'title: "%s"' % p["title"].replace('"', "'"),
          "date: %s %s" % (d.strftime("%Y-%m-%d %H:%M:%S"), d.strftime("%z")),
          "lastmod_at: %s" % mod.strftime("%Y-%m-%d %H:%M:%S %z"),
          "categories: " + json.dumps(p.get("cats", [p["cat"]]), ensure_ascii=False),
          "primary_category: " + json.dumps(p["cat"]),
          "tags: " + json.dumps([ev["slug"].replace("-ctf-", "-").replace("-2026", ""),
                                 p["cat"].lower()], ensure_ascii=False),
          "permalink: /posts/%s/" % p["key"],
          "challenge_key: " + json.dumps(p["key"]),
          "challenge_name: " + json.dumps(re.split(r"\s[-–—]\s", p["title"], maxsplit=1)[0], ensure_ascii=False),
          "event_name: " + json.dumps(ev["name"]),
          "event_slug: " + json.dumps(ev["slug"]),
          "source_directory: " + json.dumps(ev["name"] + "/" + p["case"], ensure_ascii=False),
          "difficulty: " + json.dumps(next(iter(re.findall(r"\b(?:Insane|Expert|Hard|Medium|Intermediate|Easy|Beginner)\b", p["title"], re.I)), "")),
          "source_url: " + json.dumps("https://github.com/tinhatinh/CTFWU/tree/main/" + quote(ev["name"]) + "/" + quote(p["case"])),
          "edit_url: " + json.dumps("https://github.com/tinhatinh/CTFWU/edit/main/" + quote(os.path.relpath(p["path"], ROOT).replace(os.sep, "/"))),
          "statement_images: " + json.dumps(statement_images, ensure_ascii=False),
          "artifact_images: " + json.dumps(artifact_images, ensure_ascii=False),
          "search_text: " + json.dumps(re.sub(r"\s+", " ", re.sub(r"```[\s\S]*?```", "", p["text"]))[:12000], ensure_ascii=False)]
    desc = describe(p["text"])
    if desc:
        fm.append('description: "%s"' % desc.replace('"', "'"))
    if statement_images:
        fm += ["image:", "  path: " + statement_images[0]["path"]]
    fm += ["---", ""]
    out_dir = os.path.join(stage, "_posts")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "%s-%s.md" % (d.strftime("%Y-%m-%d"), p["key"]))
    text_out = "\n".join(fm) + body
    if text_out.count("{% raw %}") != text_out.count("{% endraw %}"):
        raise SystemExit("the raw khong can doi o %s/%s" % (ev["name"], p["case"]))
    with open(out, "w", encoding="utf-8", newline="\n") as output:
        output.write(text_out)
    return out


def write_event_page(stage, ev, lang, base):
    ui = UI[lang]
    lines = ["---", 'title: "%s"' % ev["name"], "layout: event",
             'event_slug: "%s"' % ev["slug"],
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


def ctftime_team():
    """Thanh tich lay tu CTFTime, do tools/fetch_ctftime.py ghi ra."""
    p = os.path.join(ROOT, "tools", "ctftime_team.json")
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as source:
        return json.load(source)


def achievements(lang):
    ui = UI[lang]
    data = ctftime_team()
    if not data:
        print("[warn] thieu tools/ctftime_team.json -> bo qua muc thanh tich")
        return ""
    out = ["## %s\n" % ui["achievements"],
           ui["ach_hint"].format(
               team=data["team"],
               url=data["url"],
               date=stamp(dt.datetime.strptime(data["fetched"], "%Y-%m-%d"), lang, False),
           ), ""]
    for year in sorted(data["years"], reverse=True):
        out.append("### %s\n" % year)
        out.append("| %s | %s | %s | %s |" % (ui["place"], ui["event"], ui["ctf_points"], ui["rating_points"]))
        out.append("|---|---|---|---|")
        for r in data["years"][year]:
            out.append("| %s | [%s](%s) | %s | %s |"
                       % (r["place"], r["event"], r["event_url"], r["ctf_points"], r["rating_points"]))
        out.append("")
    text = "\n".join(out) + "\n"
    if "{" in text:
        raise SystemExit("placeholder ve trong muc thanh tich")
    return text


def write_competitions(stage, events, lang, base):
    ui = UI[lang]
    body = ["---", 'title: "%s"' % ui["competitions"], "icon: fas fa-trophy", "order: 1",
            "layout: competitions", "permalink: /competitions/", "---", ""]
    body.append("<p>%s</p>\n" % ui["hint"])
    body.append('<div class="ctfw-cards">')
    for ev in events:
        first = min(p["date"] for p in ev["posts"])
        last = max(p["date"] for p in ev["posts"])
        span = stamp(last, lang, False)
        if first.date() != last.date():
            span = "%s → %s" % (stamp(first, lang, False), span)
        cats = sorted({cat for p in ev["posts"] for cat in p.get("cats", [p["cat"]])})
        cover = cover_html(ev, base)
        cats_html = "".join("<span>%s</span>" % c for c in cats)
        body.append(
            '<a class="ctfw-card" href="%s/events/%s/">'
            '%s'
            '<div class="ctfw-body"><span class="ctfw-kicker">CTF %s</span>'
            '<div class="ctfw-name">%s</div>'
            '<div class="ctfw-cats">%s</div>'
            '<div class="ctfw-meta"><span>%d %s</span><span>%s</span>'
            '<span>%s &rarr;</span></div></div></a>'
            % (base, ev["slug"], cover, last.year, ev["name"],
               cats_html, len(ev["posts"]), ui["posts"], span, ui["view"]))
    body.append("</div>\n")
    body.append(achievements(lang))
    out = os.path.join(stage, "_tabs")
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "competitions.md"), "w", encoding="utf-8", newline="\n").write("\n".join(body))


def write_about(stage, lang):
    out = os.path.join(stage, "_tabs")
    os.makedirs(out, exist_ok=True)
    fm = "---\nlayout: about\ntitle: Phan Thành Danh\npermalink: /about/\nicon: fas fa-info-circle\norder: 5\n---\n\n"
    about = ABOUT[lang].replace("{team}", TEAM).replace("{members}", member_table(lang))
    if "{t" in about:
        raise SystemExit("placeholder ve trong about")
    open(os.path.join(out, "about.md"), "w", encoding="utf-8", newline="\n").write(fm + about)


def write_portfolio(stage, events, lang):
    """Event totals and team results derived from the archive."""
    records = []
    for ev in sorted(events, key=lambda e: max(p["date"] for p in e["posts"]), reverse=True):
        cover_dir = os.path.join(stage, "assets", "competitions")
        os.makedirs(cover_dir, exist_ok=True)
        cover = next((ev["slug"] + "." + ext for ext in ("png", "jpg", "jpeg", "webp", "svg")
                      if os.path.isfile(os.path.join(cover_dir, ev["slug"] + "." + ext))), None)
        if not cover:
            cover = ev["slug"] + ".svg"
            with open(os.path.join(cover_dir, cover), "w", encoding="utf-8") as image:
                image.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 300">'
                            '<rect width="600" height="300" fill="#171b17"/>'
                            '<text x="300" y="170" text-anchor="middle" font-family="monospace" '
                            'font-size="68" fill="#c0ec88">' + html.escape(initials(ev["name"])) + '</text></svg>')
        records.append({"name": ev["name"], "slug": ev["slug"], "count": len(ev["posts"]),
                        "categories": sorted({cat for p in ev["posts"] for cat in p.get("cats", [p["cat"]])}),
                        "date": max(p["date"] for p in ev["posts"]).strftime("%m / %Y"),
                        "cover": "/assets/competitions/" + cover})
    path = os.path.join(stage, "_data", "portfolio.json")
    with open(path, "w", encoding="utf-8", newline="\n") as out:
        assets = {}
        for key, relative in [("css", "assets/css/campus.css"), ("js", "assets/js/site.js"), ("editor", "assets/js/editor.js"), ("github_editor", "assets/js/github-editor.js")]:
            with open(os.path.join(stage, relative), "rb") as asset:
                assets[key] = hashlib.sha256(asset.read()).hexdigest()[:12]
        json.dump({"events": records, "results": ctftime_team(), "assets": assets}, out, ensure_ascii=False, indent=2)


def validate_certificates(stage):
    """Validate the extensible certificate catalog before publishing any assets."""
    path = os.path.join(stage, "_data", "certificates.json")
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as source:
        records = json.load(source)
    with open(os.path.join(stage, "_data", "certificate_types.json"), encoding="utf-8") as source:
        types = json.load(source)
    if not isinstance(records, list):
        raise ValueError("certificates.json must be an array")
    seen = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Each certificate must be an object")
        identifier = record.get("id", "")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", identifier) or identifier in seen:
            raise ValueError("Certificate IDs must be unique lowercase slugs")
        seen.add(identifier)
        for field in ("title", "issuer", "recipient"):
            if not isinstance(record.get(field), str) or not record[field].strip():
                raise ValueError("Certificate requires " + field)
        if record.get("type") not in types:
            raise ValueError("Unknown certificate type: " + str(record.get("type")))
        labels = types[record["type"]]
        if not all(isinstance(labels.get(lang), str) and labels[lang] for lang in ("vi", "en")):
            raise ValueError("Certificate type requires VI and EN labels")
        record.setdefault("date", "")
        record.setdefault("date_kind", "issued")
        if record["date_kind"] not in ("issued", "event", "exam"):
            raise ValueError("Certificate date_kind must be issued, event or exam")
        if record.get("event_period"):
            period = record["event_period"]
            if not isinstance(period, dict) or not all(isinstance(period.get(lang), str) and period[lang] for lang in ("vi", "en")):
                raise ValueError("Certificate event_period requires VI and EN labels")
        for field in ("date", "verified_on"):
            if record.get(field):
                dt.date.fromisoformat(record[field])
        for field in ("summary", "validity_note"):
            if record.get(field) and (not isinstance(record[field], dict) or not all(isinstance(record[field].get(lang), str) and record[field][lang] for lang in ("vi", "en"))):
                raise ValueError(field + " requires VI and EN text")
        for detail in record.get("score_details", []):
            if not isinstance(detail, dict) or any(not isinstance(detail.get(field), dict) or not all(isinstance(detail[field].get(lang), str) and detail[field][lang] for lang in ("vi", "en")) for field in ("label", "value")):
                raise ValueError("Certificate score details require bilingual labels and values")
        for field in ("image", "document"):
            if not record.get(field):
                continue
            asset = record[field]
            if not isinstance(asset, str) or not asset.startswith("/assets/certificates/"):
                raise ValueError("Certificate assets must be in /assets/certificates/")
            extensions = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp") if field == "image" else (".pdf",)
            if os.path.splitext(asset)[1].lower() not in extensions:
                raise ValueError("Certificate image must be raster; document must be PDF")
            target = os.path.realpath(os.path.join(stage, asset.lstrip("/")))
            folder = os.path.realpath(os.path.join(stage, "assets", "certificates"))
            if os.path.commonpath([target, folder]) != folder or not os.path.isfile(target):
                raise ValueError("Missing certificate asset: " + asset)
        if record.get("verification_url"):
            from urllib.parse import urlsplit
            url = urlsplit(record["verification_url"])
            if url.scheme != "https" or not url.netloc or url.username or url.password:
                raise ValueError("Certificate verification link must use HTTPS")
    with open(path, "w", encoding="utf-8", newline="\n") as output:
        json.dump(records, output, ensure_ascii=False, indent=2)


def build(lang, require_solve_dates=False):
    stage = os.path.join(ROOT, "_site_src" if lang == "vi" else "_site_src_en")
    base = "/CTFWU" if lang == "vi" else "/CTFWU/en"
    if os.path.isdir(stage):
        shutil.rmtree(stage)
    shutil.copytree(os.path.join(ROOT, "site"), stage)
    validate_certificates(stage)
    cfg = os.path.join(stage, "_config.yml")
    t = open(cfg, encoding="utf-8").read()
    if lang == "en":
        t = t.replace('baseurl: "/CTFWU"', 'baseurl: "/CTFWU/en"').replace("lang: vi-VN", "lang: en")
    t = re.sub(r"^tagline:.*$", 'tagline: "%s"' % UI[lang]["tagline"], t, flags=re.M)
    t = re.sub(r"^description:.*$", 'description: "%s"' % UI[lang]["description"], t, flags=re.M)
    open(cfg, "w", encoding="utf-8", newline="\n").write(t)
    events = collect(lang, require_solve_dates=require_solve_dates)
    pending = [p["key"] for ev in events for p in ev["posts"] if p.get("fallback")]
    n = 0
    for ev in events:
        for p in ev["posts"]:
            write_post(stage, ev, p, lang, base)
            n += 1
        write_event_page(stage, ev, lang, base)
    write_competitions(stage, events, lang, base)
    write_about(stage, lang)
    write_portfolio(stage, events, lang)
    total = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(stage) for f in fs)
    if pending:
        print("[warn] %d bai en dang dung ban tieng Viet: %s" % (len(pending), ", ".join(pending)))
    print("[%s] %d event, %d bai, %.1f MB -> %s"
          % (lang, len(events), n, total / 1e6, os.path.relpath(stage, ROOT)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=["vi", "en", "all"], default="all")
    ap.add_argument("--require-solve-dates", action="store_true",
                    help="Reject publication of writeups without declared solve dates")
    a = ap.parse_args()
    for lang in (["vi", "en"] if a.lang == "all" else [a.lang]):
        build(lang, require_solve_dates=a.require_solve_dates)
