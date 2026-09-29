import sys
from PIL import Image

# usage: crop.py x0 y0 x1 y1 out.png [scale]
img = Image.open("../files/photo.png").convert("RGB")
x0, y0, x1, y1 = map(int, sys.argv[1:5])
out = sys.argv[5]
scale = float(sys.argv[6]) if len(sys.argv) > 6 else 1.0
c = img.crop((x0, y0, x1, y1))
if scale != 1.0:
    c = c.resize((int(c.width * scale), int(c.height * scale)), Image.LANCZOS)
c.save(out)
print(out, c.size)
