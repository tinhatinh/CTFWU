"""Dem hinh hoc trong SVG de: duong kinh -> so luong -> kieu, va toa do den theo hang.

Dung de kiem tra khong con noi dung nao an trong file (layer khong hien thi,
path khong phai hinh tron, ...).

  python analysis/dump_svg.py files/lampDrill.svg
"""
import re
import sys
from collections import Counter, defaultdict


def paths(svg):
    for p in re.findall(r"<path([^>]*?)/?>", svg, re.S):
        st = re.search(r'style="([^"]*fill:[^"]*)"', p)
        d = re.search(r'\bd="([^"]*)"', p, re.S)
        if not (st and d):
            continue
        f = re.search(r"fill:\s*(#\w+|\w+)", st.group(1))
        n = [float(x) for x in re.findall(r"-?\d+\.?\d*(?:e-?\d+)?", d.group(1))]
        xs, ys = n[0::2], n[1::2]
        if not xs:
            continue
        yield dict(cx=(min(xs) + max(xs)) / 2, cy=(min(ys) + max(ys)) / 2,
                   w=max(xs) - min(xs), h=max(ys) - min(ys),
                   fill=f.group(1) if f else "?", bez=d.group(1).count("C"))


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    src = sys.argv[1] if len(sys.argv) > 1 else "files/lampDrill.svg"
    svg = open(src, encoding="utf-8", errors="replace").read()
    ps = list(paths(svg))
    print("path co fill: %d" % len(ps))
    print("duong kinh :", Counter(round(p["w"], 1) for p in ps).most_common(8))
    print("mau fill   :", Counter(p["fill"] for p in ps).most_common(8))
    print("so bezier  :", Counter(p["bez"] for p in ps).most_common(4))
    print("text/layer : <text=%d  <use=%d  display:none=%d  visibility=hidden=%d"
          % (svg.count("<text"), svg.count("<use"),
             svg.count("display: none") + svg.count("display:none"),
             svg.count("visibility: hidden") + svg.count("visibility:hidden")))
    lamps = [p for p in ps if 22 < p["w"] < 24]
    rows = defaultdict(list)
    for p in lamps:
        rows[round(p["cy"])].append(p)
    print("\nden theo hang: %d hang, tong %d" % (len(rows), len(lamps)))
    for y in sorted(rows):
        r = sorted(rows[y], key=lambda p: p["cx"])
        print("  y=%-5d n=%2d  %s" % (y, len(r),
              "".join("#" if p["fill"] == "#1c1915" else "." for p in r)))
        print("           x: %s" % " ".join("%.0f" % p["cx"] for p in r))


if __name__ == "__main__":
    main()
