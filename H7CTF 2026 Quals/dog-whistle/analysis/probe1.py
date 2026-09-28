import sys
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import enc, client

a = client.Aria()
print("banner:", a.hello()[:60])
tests = [
    ("direct ping      ", bytes([0x10, 0x00]), "direct"),
    ("whistle ping     ", bytes([0x10, 0x00]), "whistle"),
    ("direct select 0E ", bytes([0x01, 0x01, 0x0E]), "direct"),
    ("whistle select 0E", bytes([0x01, 0x01, 0x0E]), "whistle"),
]
for name, pl, mode in tests:
    wav, fr = enc.capture(pl, mode=mode)
    print("== %s  frame=%s  %.2fs ==" % (name, fr.hex(), (len(wav) - 44) / 3 / 96000))
    print(a.send_line(wav).decode(errors="replace"))
a.close()
