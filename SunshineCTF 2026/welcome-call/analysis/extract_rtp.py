#!/usr/bin/env python
"""Welcome Call: pull every RTP voice stream out of welcomecall.pcap and rebuild WAV.

The capture is a SIP session between 192.0.2.10 (caller) and 192.0.2.20 (the "board").
Each INVITE/200-OK carries an SDP naming the RTP port and payload type (0 = PCMU
mu-law, 8 = PCMA a-law, 101 = telephone-event/DTMF). RTP payloads are grouped per
4-tuple, expanded to 16-bit PCM and written as 8 kHz mono WAV for analysis.
"""
import collections
import os
import struct
import sys
import wave

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from scapy.all import IP, Raw, UDP, rdpcap

PCAP = sys.argv[1] if len(sys.argv) > 1 else "files/welcomecall.pcap"
OUT = "analysis"


def ulaw2lin(c):
    c = ~c & 0xFF
    seg, q = (c >> 4) & 7, c & 0xF
    s = ((q << 4) + 8) << (seg + 2) if seg else (q << 4) + 8
    s -= 33
    return -s if c & 0x80 else s


def alaw2lin(c):
    c ^= 0xD5
    seg, q = (c >> 4) & 7, c & 0xF
    s = ((q << 4) + 8) << (seg + 1) if seg else (q << 4) + 8
    return -s if c & 0x80 else s


DEC = {0: ulaw2lin, 8: alaw2lin}


def parse_sdp(t):
    d = {}
    for line in t.split("\r\n"):
        if line.startswith("m=audio"):
            f = line.split()
            d["port"], d["fmt"] = int(f[1]), f[3]
        elif line.startswith("a=rtpmap"):
            d["codec"] = line.split(":", 1)[1].split(" ", 1)[1].split("/")[0]
        elif line.startswith("a=") and line[2:] in ("sendrecv", "sendonly", "recvonly", "inactive"):
            d["dir"] = line[2:]
        elif line.startswith("s="):
            d["session"] = line[2:]
    return d


pkts = rdpcap(PCAP)
print("[*] %d packets" % len(pkts))

print("\n[*] SIP media announcements:")
for p in pkts:
    if UDP in p and Raw in p:
        t = bytes(p[Raw].load).decode("latin-1", "replace")
        if "m=audio" in t:
            d = parse_sdp(t)
            print("    %s:%-5s -> %s:%-5s  %s" % (p[IP].src, p[UDP].sport, p[IP].dst, p[UDP].dport,
                                                  t.split("\r\n")[0][:38]))
            print("        port=%s fmt=%s codec=%s %s session=%r"
                  % (d.get("port"), d.get("fmt"), d.get("codec"), d.get("dir"), d.get("session")))

streams = collections.OrderedDict()
for p in pkts:
    if UDP not in p or Raw not in p:
        continue
    b = bytes(p[Raw].load)
    if len(b) < 13 or (b[0] >> 6) != 2:
        continue
    pt = b[1] & 0x7F
    if pt not in DEC and pt != 101:
        continue
    if p[UDP].sport == 5060 or p[UDP].dport == 5060:
        continue
    streams.setdefault((p[IP].src, p[UDP].sport, p[IP].dst, p[UDP].dport), []).append(
        (float(p.time), pt, b[12:], b[1] & 0x80, struct.unpack(">H", b[2:4])[0]))

os.makedirs(OUT, exist_ok=True)
print("\n[*] RTP streams:")
for key, chunks in streams.items():
    s_ip, s_p, d_ip, d_p = key
    pts = collections.Counter(pt for _, pt, _, _, _ in chunks)
    audio = {pt: n for pt, n in pts.items() if pt in DEC}
    main = max(audio, key=audio.get) if audio else None
    print("    %s:%s -> %s:%s  pkts=%d types=%s" % (s_ip, s_p, d_ip, d_p, len(chunks), dict(pts)))
    ev = [(t, pl[0] & 0x0F) for t, pt, pl, m, _ in chunks if pt == 101 and pl]
    if ev:
        print("        DTMF: %s" % "".join("0123456789ABCD*#"[c] for _, c in ev))
    if main is None:
        continue
    pcm = bytearray()
    for t, pt, pl, m, seq in sorted(chunks):
        if pt != main:
            continue
        f = DEC[pt]
        for byte in pl:
            pcm += struct.pack("<h", f(byte))
    name = "%s-%s_%s-%s_pt%d.wav" % (s_ip, s_p, d_ip, d_p, main)
    with wave.open(os.path.join(OUT, name), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(8000)
        w.writeframes(bytes(pcm))
    print("        wrote %-40s %.2f s  (%d samples)" % (name, len(pcm) / 2 / 8000, len(pcm) // 2))
