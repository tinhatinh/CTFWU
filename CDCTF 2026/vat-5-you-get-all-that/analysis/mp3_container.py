"""Kiem tra container MP3: ID3, appended data, frame structure.
Chay: python analysis/mp3_container.py
"""
from pathlib import Path

d = Path("files/captured_cred_call.mp3").read_bytes()
print(f"kich thuoc : {len(d)}")
print(f"head       : {d[:12]!r}")
if d[:3] == b"ID3":
    size = (d[6] << 21) | (d[7] << 14) | (d[8] << 7) | d[9]
    print(f"ID3v{d[3]}.{d[4]} flags={d[5]:#04x} size={size} (-> {size+10} byte header)")
    print(f"ID3 text   : {d[10:10+size]!r}")
    body = d[10 + size:]
else:
    body = d
print(f"sau tag    : {len(body)} byte, head={body[:8].hex()}")
# kich thuoc stream do bitrate danh duoc: 25.20 s @ 48 kbps
est = int(25.20 * 48000 / 8)
print(f"uoc luong stream = 25.20 s * 48000/8 = {est} byte; len(body) = {len(body)} byte; "
      f"chenh lech = {len(body) - est}")
print(f"toan bo file = ID3({10+size}) + stream({len(body)}) = {10+size+len(body)} vs {len(d)}")
for magic, name in [(b"PK", "zip"), (b"\x7fELF", "elf"), (b"ID3", "id3-lan-nua"),
                    (b"RIFF", "riff/wav"), (b"\x89PNG", "png")]:
    hits = [i for i in range(len(d) - 4) if d[i:i+len(magic)] == magic]
    if hits:
        print(f"  magic {name}: {hits[:5]}")
print("duoi 16 byte:", d[-16:].hex())
print(f"so byte 0x00 trong toan file: {d.count(0)}")
