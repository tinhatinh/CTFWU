#!/usr/bin/env bash
# Tải tranh hero của trang tham chiếu và cắt hai kích thước dùng trong preview.
# Tranh có bản quyền: chỉ dùng cục bộ để duyệt thiết kế, không commit, không deploy.
set -euo pipefail
cd "$(dirname "$0")/assets"

curl -sS -A "Mozilla/5.0" -o raw-gate.jpg \
  "https://ossstatic.leiting.com/static/xian/202012/images/index-bg7.jpg"

python3 - <<'PY'
from PIL import Image
import os
im = Image.open("raw-gate.jpg")
im.resize((1600, 900), Image.LANCZOS).save(
    "hero-desktop.jpg", quality=82, optimize=True, progressive=True)
w, h = im.size
cw = int(h * 0.8)
x = 960 - cw // 2
im.crop((x, 0, x + cw, h)).resize((1080, 1350), Image.LANCZOS).save(
    "hero-mobile.jpg", quality=80, optimize=True, progressive=True)
for f in ("hero-desktop.jpg", "hero-mobile.jpg"):
    print(f, round(os.path.getsize(f) / 1024), "KB")
PY

rm -f raw-gate.jpg
