"""Doc the literal X-Resolver value va route fetch ra tu bundle SvelteKit.

Chay: python analysis/bundle_route.py files/2.CftUi-UM.js
"""

import base64
import re
import sys
from pathlib import Path

src = Path(sys.argv[1] if len(sys.argv) > 1 else "files/2.CftUi-UM.js").read_text(
    encoding="utf-8", errors="replace"
)

route = re.search(r'fetch\(`([^`]+)`\s*,\s*\{headers:(\{[^}]*\})', src)
print("route :", route.group(1) if route else "khong tim thay")
print("header:", route.group(2) if route else "")

for lit in re.findall(r'"(X[A-Za-z0-9+/=]{20,})"', src):
    body = base64.b64decode(lit[1:]).decode()
    print("X-Resolver literal:", lit[:24] + "...")
    print("  prefix  :", lit[0])
    print("  decoded :", body)
    print("  rebuild : X + base64(json) =", "X" + base64.b64encode(body.encode()).decode() == lit)
