"""Lay bang "Participated in CTF events" cua doi tren CTFTime ve file JSON
duoc commit, de tools/build_site.py ve thanh muc "Thanh tich" duoi trang
"Cac cuoc thi".

Chay khi muon cap nhat:  python tools/fetch_ctftime.py
Mang chi duoc dung o day, luc build site khong bao gio truy cap CTFTime.
"""

import datetime as dt
import json
import os
import re
import sys
import urllib.request

TEAM_ID = 449538
URL = "https://ctftime.org/team/%d" % TEAM_ID
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ctftime_team.json")
UA = "Mozilla/5.0 (compatible; CTFWU site builder; https://github.com/tinhatinh/CTFWU)"

YEAR_TAB = re.compile(r'href="#rating_(\d{4})"[^>]*>\s*(\d{4})\s*<')
PANE = re.compile(r'id="rating_(\d{4})"([^>]*)>(.*?)</div>', re.S)
ROW = re.compile(
    r'(?:<td class="place_ico">.*?</td>)?\s*'
    r'<td class="place">\s*(.*?)\s*</td>'
    r'<td><a href="(/event/\d+)">(.*?)</a></td>'
    r"<td>([\d.]+)</td>"
    r"<td>([\d.]+)</td>",
    re.S,
)


def fetch():
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")


def parse(html):
    name = re.search(r"<title>CTFtime\.org / (.*?)</title>", html)
    if not name:
        raise SystemExit("khong doc duoc ten doi: trang thay doi cau truc")
    years = {}
    for m in PANE.finditer(html):
        year, body = m.group(1), m.group(3)
        rows = []
        for r in ROW.finditer(body):
            place, href, event, ctf, rating = r.groups()
            rows.append({
                "place": place.strip() or "-",
                "event": re.sub(r"\s+", " ", event).strip(),
                "event_url": "https://ctftime.org" + href,
                "ctf_points": "%.2f" % float(ctf),
                "rating_points": "%.3f" % float(rating),
            })
        if rows:
            years[year] = rows
    tabs = {y for y, _ in YEAR_TAB.findall(html)}
    missing = sorted(tabs - set(years))
    if missing:
        raise SystemExit("khong parse duoc nam nao trong so: %s" % ", ".join(missing))
    if not years:
        raise SystemExit("trang khong tra hang nao - dung ghi de file cu")
    return {"team": name.group(1).strip(), "team_id": TEAM_ID, "url": URL, "years": years}


def main():
    if "--stdin" in sys.argv:
        html = sys.stdin.read()
    else:
        html = fetch()
    data = parse(html)
    data["fetched"] = dt.date.today().isoformat()
    total = sum(len(v) for v in data["years"].values())
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    print("%s: %d su kien (%s) -> %s" % (
        data["team"], total,
        ", ".join("%s=%d" % (y, len(r)) for y, r in sorted(data["years"].items())),
        os.path.basename(OUT)))


if __name__ == "__main__":
    main()
