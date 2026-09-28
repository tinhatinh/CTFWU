import sys
from collections import Counter
from scapy.all import rdpcap, TCP, UDP, IP, ICMP, DNS, Raw

pkts = rdpcap(sys.argv[1])
print("packets:", len(pkts))
print("first ts:", pkts[0].time, "last ts:", pkts[-1].time, "span_sec:", float(pkts[-1].time - pkts[0].time))

layers = Counter()
for p in pkts:
    for L in (IP, TCP, UDP, ICMP, DNS):
        if p.haslayer(L):
            layers[L.__name__] += 1
    if p.haslayer(Raw):
        layers["Raw"] += 1
print("layers:", dict(layers))

proto = Counter()
for p in pkts:
    if p.haslayer(UDP):
        proto[("UDP", p[UDP].dport)] += 1
    elif p.haslayer(TCP):
        proto[("TCP", p[TCP].dport)] += 1
    elif p.haslayer(ICMP):
        proto[("ICMP", p[ICMP].type)] += 1
print("\ntop dest ports/types:")
for k, v in proto.most_common(18):
    print("  ", k, v)

conv = Counter()
for p in pkts:
    if p.haslayer(IP):
        conv[tuple(sorted([p[IP].src, p[IP].dst]))] += 1
print("\ntop conversations:")
for k, v in conv.most_common(10):
    print("  ", k, v)

sizes = Counter(len(p) for p in pkts)
print("\npacket size histogram (top 10):", sizes.most_common(10))

payl = Counter()
for p in pkts:
    if p.haslayer(Raw):
        payl[len(p[Raw].load)] += 1
print("raw payload length histogram (top 12):", sorted(payl.items())[:12])
print("max raw payload:", max(payl) if payl else 0)
