"""MPEG-TS structural survey: PIDs, PMT stream types, private payloads, stuffing, ID3 in ADTS."""

import re
import sys
from collections import Counter

PKT = 188
data = b"".join(open(p, "rb").read() for p in sys.argv[1:])
print(f"[*] {len(data)} bytes of TS")

if len(data) % PKT:
    # resync on the first 0x47 that repeats every 188
    for off in range(0, PKT):
        if all(data[i] == 0x47 for i in range(off, min(off + 5 * PKT, len(data)), PKT)):
            data = data[off:]
            print(f"[*] resynced at offset {off}")
            break

npkt = len(data) // PKT
pids = Counter()
ptys = {}
continuity = {}
payload_by_pid = Counter()
stuff_pkts = 0
id3 = []

for i in range(npkt):
    p = data[i * PKT:(i + 1) * PKT]
    if p[0] != 0x47:
        continue
    pid = ((p[1] & 0x1F) << 8) | p[2]
    pids[pid] += 1
    tsc = (p[3] >> 4) & 3
    if tsc >= 2:
        pl = p[4:]
        payload_by_pid[pid] += len(pl)
        if pid not in ptys and tsc == 1:
            pass
        if len(pl) > 4 and pl[0] == 0 and (pl[1] & 0xF0) == 0x30:      # PSI table
            tid = pl[0]
            pass
    if tsc == 1:
        adapt = (p[3] >> 4) & 3
        if adapt in (2, 3):
            stuff_pkts += 1
    for m in re.finditer(rb"ID3", p):
        id3.append((i, pid, m.start()))

print(f"\n[1] packets={npkt} with adaptation field={stuff_pkts}")
print("[2] PID histogram:")
for pid, c in pids.most_common(12):
    print(f"    PID 0x{pid:04x} ({pid:5d})  {c:6d} pkt  payload~{payload_by_pid[pid]} B")

print("\n[3] PMT decode (stream_type -> elementary PID):")
for i in range(npkt):
    p = data[i * PKT:(i + 1) * PKT]
    if p[0] != 0x47:
        continue
    pid = ((p[1] & 0x1F) << 8) | p[2]
    if (p[3] >> 4) & 3 < 2:
        continue
    pl = p[4:]
    ptr = pl[0]
    if ptr:
        pl = pl[1 + ptr:]
    if not pl or pl[0] != 0x02:      # PMT table id
        continue
    seclen = ((pl[1] & 0x0F) << 8) | pl[2]
    pnlen = ((pl[10] & 0x0F) << 8) | pl[11]
    k = 12 + pnlen
    while k + 5 <= 1 + seclen - 5 and k + 4 < len(pl):
        st = pl[k]
        elk = ((pl[k + 1] & 0x1F) << 8) | pl[k + 2]
        slen = ((pl[k + 3] & 0x0F) << 8) | pl[k + 4]
        desc = pl[k + 5:k + 5 + slen]
        print(f"    stream_type=0x{st:02x} ({'AUDIO' if st==0x0F else 'PRIVATE_DATA' if st==0x06 else 'SUBTITLE/other'}"
              f") elementary_PID=0x{elk:04x} descriptors={desc[:24].hex(' ')}")
        k += 5 + slen

print("\n[4] ID3 tags found:", len(id3))
for i, pid, off in id3[:5]:
    p = data[i * PKT:(i + 1) * PKT]
    print(f"    pkt {i} PID 0x{pid:04x} @{off}: {p[off:off+40]}")

print("\n[5] interesting strings in the raw TS:")
for kw in (b"H7CTF", b"flag", b"FLAG", b"stego", b"secret", b"MORSE", b"DTMF", b"txt", b"{", b"-----BEGIN"):
    hits = [m.start() for m in re.finditer(re.escape(kw), data)]
    if hits:
        print(f"    {kw!r}: {len(hits)} @ {hits[:4]}")
        for h in hits[:2]:
            print("        ctx:", re.sub(rb"[^\x20-\x7e]", b".", data[max(0, h-40):h+80]).decode())
