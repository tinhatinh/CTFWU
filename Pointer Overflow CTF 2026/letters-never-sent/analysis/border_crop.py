import os
from PIL import Image

CASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
p = os.path.join(CASE, "files", "letter.png")
data = open(p, "rb").read()
iend = data.rfind(b"IEND")
print("png len", len(data), "IEND at", iend + 8, "appended bytes:", len(data) - (iend + 8))
if len(data) - (iend + 8) > 0:
    tail = data[iend + 8:]
    print("tail head:", tail[:200])

im = Image.open(p)
W, H = im.size
crops = {
    "top": (0, 0, W, 70),
    "bottom": (0, H - 70, W, H),
    "left": (0, 0, 70, H),
    "right": (W - 70, 0, W, H),
}
out = os.path.join(CASE, "analysis")
os.makedirs(out, exist_ok=True)
for name, box in crops.items():
    c = im.crop(box)
    scale = 3 if name in ("top", "bottom") else 2
    c = c.resize((c.width * scale, c.height * scale), Image.LANCZOS)
    fp = os.path.join(out, f"border_{name}.png")
    c.save(fp)
    print("saved", fp, c.size)
