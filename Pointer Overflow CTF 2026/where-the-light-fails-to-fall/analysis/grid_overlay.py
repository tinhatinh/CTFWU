import numpy as np
from PIL import Image, ImageDraw

im = Image.open("files/photo.png").convert("RGB")
W, H = im.size

# grid overlay every 250 px, labels every 500
g = im.copy()
d = ImageDraw.Draw(g)
for x in range(0, W, 250):
    col = (255, 0, 255) if x % 500 == 0 else (0, 200, 255)
    d.line([(x, 0), (x, H)], fill=col, width=3)
    if x % 500 == 0:
        d.text((x + 8, 40), str(x), fill=(255, 255, 0))
for y in range(0, H, 250):
    col = (255, 0, 255) if y % 500 == 0 else (0, 200, 255)
    d.line([(0, y), (W, y)], fill=col, width=3)
    if y % 500 == 0:
        d.text((8, y + 8), str(y), fill=(255, 255, 0))
g.resize((1050, 1400), Image.LANCZOS).save("analysis/grid_full.png")

# zoom on the bird + shadow
im.crop((900, 1500, 2600, 3000)).save("analysis/zoom_shadow.png")
# zoom on the arrow
im.crop((350, 2950, 2450, 3950)).save("analysis/zoom_arrow.png")
print("saved grid_full, zoom_shadow, zoom_arrow")
