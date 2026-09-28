"""you cut me off (forensics, Sunshine CTF) - khôi phục phần ảnh bị cắt khỏi PNG.

IHDR khai báo chiều cao nhỏ hơn số dòng scanline thật có trong IDAT, nên mọi trình xem
(PIL, trình duyệt) chỉ vẽ đúng số dòng đó và số dòng còn lại nằm im trong file.
"""
import sys, zlib, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path
from PIL import Image

src = Path(sys.argv[1] if len(sys.argv) > 1 else "files/hereyougo.png")
data = src.read_bytes()

pos, idat = 8, b""
while pos < len(data):
    ln = struct.unpack(">I", data[pos:pos + 4])[0]
    kind = data[pos + 4:pos + 8]
    if kind == b"IHDR":
        w, h, depth, ctype = struct.unpack(">IIBB", data[pos + 8:pos + 18])
    if kind == b"IDAT":
        idat += data[pos + 8:pos + 8 + ln]
    pos += 12 + ln

bpp = {0: 1, 2: 1, 3: 1, 4: 2, 6: 4}[ctype]
stride = 1 + w * bpp                       # 1 byte filter + 1 pixel row
raw = zlib.decompress(idat)
real_h = len(raw) // stride

print(f"IHDR: {w}x{h}  stride={stride}  IDAT giải nén={len(raw)} byte -> thực tế {real_h} dòng")
print(f"số dòng bị ẩn: {real_h - h}")
assert len(raw) % stride == 0, "buffer không chia hết cho stride, model sai"

rows = [raw[i * stride + 1:(i + 1) * stride] for i in range(real_h)]   # bỏ byte filter mỗi dòng
Image.frombytes("RGBA" if bpp == 4 else "RGB", (w, real_h), b"".join(rows)).save("analysis/full.png")
Image.frombytes("RGBA" if bpp == 4 else "RGB", (w, real_h), b"".join(rows)) \
    .convert("RGB").crop((0, h - 12, w, real_h)).resize(((w) * 3, (real_h - h + 12) * 3)).save("analysis/hidden.png")
print("đã ghi analysis/full.png và analysis/hidden.png")
