from pathlib import Path
import re
b = Path("files/network_traffic_with_a_flag_in_there.pcapng").read_bytes()
found = [s for s in re.findall(rb"[\x20-\x7e]{6,}", b)
         if any(word in s.lower() for word in [b"flag", b"cdctf", b"cat", b"net"])]
for s in found:
    print(repr(s))
print(f"Matching printable strings: {len(found)}")
