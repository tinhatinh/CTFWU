"""In bang the cua crypto-cat-3 o hai chieu, lay truc tiep tu dict trong exploit.py."""

import re
from pathlib import Path

src = Path("exploit.py").read_text(encoding="utf-8")
body = re.search(r"MAP = \{(.*?)\n\}", src, re.S).group(1)
MAP = dict(re.findall(r'"(\w)": "(\w)"', body))
AL = "abcdefghijklmnopqrstuvwxyz"
INV = {v: k for k, v in MAP.items()}
assert len(MAP) == len(INV) == 22, (len(MAP), len(INV))

print("ma : " + " ".join(MAP.get(c, ".") for c in AL))
print("co : " + " ".join(AL))
print()
print("co : " + " ".join(INV.get(c, ".") for c in AL))
print("ma : " + " ".join(AL))
