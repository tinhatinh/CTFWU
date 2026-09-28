import re
import sys
from collections import Counter
from scapy.all import rdpcap, DNS, TCP, UDP, Raw, IP

pkts = rdpcap(sys.argv[1])

print("=== DNS answers for the exfil domain (any record type) ===")
seen = Counter()
for p in pkts:
    if not p.haslayer(DNS):
        continue
    d = p[DNS]
    if d.ancount:
        for i in range(d.ancount):
            try:
                rr = d.an[i]
                nm = rr.rrname.decode(errors="replace")
                rd = (rr.rdata.decode(errors="replace") if isinstance(rr.rdata, bytes) else str(rr.rdata))
            except Exception:
                continue
            seen[(nm.split(".")[-4] if nm.count(".") >= 3 else nm)] += 1
            if "cdn-telemetry" in nm or "lab" in nm:
                print(f"  {rr.type if hasattr(rr,'type') else '?'} {nm} -> {rd[:120]}")
print("  answer-name buckets:", dict(seen))

print("\n=== DNS answers carrying TXT for exfil queries ===")
for p in pkts:
    if p.haslayer(DNS) and p[DNS].qd and b"cdn-telemetry" in (p[DNS].qd.qname or b""):
        d = p[DNS]
        print("  Q", d.qd.qname.decode(), "| ancount", d.ancount, "| nscount", d.nscount, "| arcount", d.arcount)
        for i in range(d.ancount):
            try:
                rr = d.an[i]
                print("      AN", rr.type, (rr.rdata.decode(errors='replace') if isinstance(rr.rdata, bytes) else rr.rdata))
            except Exception as e:
                print("      AN parse fail", e)
        break

print("\n=== HTTP on 8080/8443: unique request lines ===")
reqs = []
for p in pkts:
    if p.haslayer(Raw) and p.haslayer(TCP) and p[TCP].dport in (8080, 8443):
        b = bytes(p[Raw].load)
        if b.startswith((b"GET", b"POST", b"PUT", b"HEAD")):
            reqs.append((float(p.time), p[TCP].dport, b))
paths = Counter((dp, l.split(b"\r\n")[0].decode(errors="replace")) for _, dp, l in reqs)
for k, v in paths.most_common(25):
    print("  ", v, k)

print("\n=== unique header blocks (normalized) ===")
hdrs = Counter()
for _, dp, b in reqs:
    head = b.split(b"\r\n\r\n")[0].decode(errors="replace")
    hdrs[head] += 1
for k, v in hdrs.most_common(12):
    print(f"  x{v} {k!r}")

print("\n=== response bodies from local servers (unique, len) ===")
resp = Counter()
for p in pkts:
    if p.haslayer(Raw) and p.haslayer(TCP) and p[TCP].sport in (8080, 8443):
        b = bytes(p[Raw].load)
        if b.startswith(b"HTTP"):
            body = b.split(b"\r\n\r\n", 1)[1] if b"\r\n\r\n" in b else b""
            resp[(len(b), body[:60])] += 1
for (ln, body), v in resp.most_common(14):
    print(f"  x{v} len={ln} body={body!r}")

print("\n=== any flag-looking token anywhere (case-insensitive, incl. decoded) ===")
pat = re.compile(rb"(?:flag|ctf|h7)\s*\{?[a-z0-9_]{0,60}\}?", re.I)
hits = set()
for p in pkts:
    raw = bytes(p[Raw].load) if p.haslayer(Raw) else b""
    for m in pat.findall(raw):
        hits.add(m)
    if p.haslayer(DNS) and p[DNS].qd:
        for m in pat.findall(p[DNS].qd.qname or b""):
            hits.add(m)
print("  ", sorted(hits)[:20] or "none in cleartext")
