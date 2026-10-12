---
title: "Mem-5 : The Last Trace"
category: "Forensics"
tags: ["memory-forensics", "memprocfs", "browser-cache", "edge-telemetry", "url-artifact"]
solve_date: "2026-10-09"
language: "en"
---

# Mem-5 : The Last Trace

**Flag:** `OWASP{soulstone_web_8b2d}`
**Artifact:** `soul.zip` 937,376,339 B (sha256 `94d15b80b78402ab027a6ab4f40d288babef7d938631766d25c1d5bcb6fd9ee0`) unpacking to the RAM image `soul.mem` 2,774,466,560 B (`0xa55f0000`, sha256 `617d69406e571bc6a80af9e4517cb2ecc3839c508e0e8374463e38f7f70014e6`).

## Challenge

"Someone was looking for something on web shortly before the machine was captured. The trail did not end on the filesystem, Instead in the web. Follow it." Medium, 200 points, 23 solves at the time of work.

## Analysis

### Shared context of the series

`soul.mem` is a raw physical memory dump of a VirtualBox guest, Windows 10 build **19041**, user `nightwatch`, captured with winpmem (`C:\Users\nightwatch\Downloads\winpmem_mini_x86.exe` is still present in the image's application-name cache). MemProcFS enumerates **111 processes**.

Process, PEB, VAD and registry analysis uses the MemProcFS Python module. Volatility 3 requires symbols for `ntkrnlmp.pdb`, GUID `F57E740B088E5056E8AF0772F1CC5BEB`, age 1:

```python
import sys
sys.path.insert(0, r"C:\Tools\ctf\memprocfs")
import vmmpyc

vmm = vmmpyc.Vmm(["-device", r"C:\path\to\soul.mem"])
for pr in sorted(vmm.process_list(), key=lambda p: p.pid):
    print(pr.pid, pr.ppid, pr.fullname)
```

The image also carries seven flags planted for other missions/challenges, recoverable by harvesting hex strings: `soulstone_cmd_741f` (25 copies), `soulstone_net_4d92` (10), `pr0c3ss_hunt_7f31` (33), `v0rm1r_clip_91a7` (4), `soulstone_web_8b2d` (290), `soulstone_note_3c91` (43), `soulstone_paint_52af` (1). Three later challenges in the series had wrong submissions caused by these values.

### Two readings of "a trail on the web"

The process list contains `msedge.exe` and several `msedgewebview2.exe`, so navigation history, browser network logs and window UIA text are all still in RAM. Two routes are distinguished:

- **Filesystem**: the record does not recover the corresponding history/cache database; the image-carving results in Mem-3 do not rule out every resident file.

## Solution

### Extracting the URL and its artifact parameter

```bash
python solve.py soul.mem
```

```text
== URLs with artifact= ==
   49 https://example.com/vormir?artifact=4f574153507b736f756c73746f6e655f7765625f386232647d
    9 https://example.com/vormir?artifact=4f574153507b736f756c73746f6e655f7765625f386232647d......
      4f574153507b736f756c73746f6e655f7765625f386232647d -> OWASP{soulstone_web_8b2d}
== bing queries ==
   18 q=winpmen
   17 q=ftk+imager
    6 q=dump+it
   11 q=Download+Free+FTK+Imager
```

The 54-character hex string in the `artifact=` parameter decodes to 27 bytes, `OWASP{soulstone_web_8b2d}`. The full URL appears **49 times** as UTF-16 and roughly **29 times** as ASCII, the ASCII copies usually truncated; every copy agrees on the `artifact=` value.

The same URL also appears in Edge telemetry logs:

```text
TopTrafficMiss.uri: https://example.com/vormir?artifact=4f574153507b736f756c73746f6e655f7765625f386232647d  browser_remotedata.cpp.150
CacheFilterHit.uri: https://example.com/vormir?artifact=4f574153507b736f756c73746f6e655f7765625f386232647d  browser_remotedata.cpp.188
```

`TopTrafficMiss` and `CacheFilterHit` are the two branches of the cache filter, so the browser really processed this URL rather than the string appearing by accident. `example.com` is a reserved placeholder domain; no request to it exists in the DNS logs, the trace only survives in browser cache/telemetry — matching "the trail did not end on the filesystem".

### Behaviour sequence matching the statement

The Bing queries still in RAM describe exactly "searching the web shortly before capture": `winpmem` (the RAM capture tool, string truncated to `winpmen`), `ftk imager` / `Download Free FTK Imager` (image readers), `dump it`. In parallel, PowerShell history holds `Get-Item C:\Users\nightwatch\Downloads\dump\memdump.mem | Select Name,Length` and `python -m pip install volatility3`, and `FTK Imager.exe` (PID 5960, `C:\Program Files\AccessData\FTK Imager\FTK Imager.exe`) was still running at capture time.

## Result

```text
OWASP{soulstone_web_8b2d}
```

The flag was read directly from the memory image (the `artifact=` parameter of the URL in Edge cache/telemetry) and the platform's solved table confirms it was accepted.

## Reproduce

Python 3 (`mmap`, `re`, `binascii`). Save the last `python` block as `solve.py` and run:

```bash
python solve.py soul.mem
```

The script scans the image in 16 MiB chunks, collects every URL containing `artifact=` (ASCII and UTF-16), decodes the hex parameter and aggregates the Bing `q=` queries.

```python
"""Trich vet web trong raw memory dump: URL co tham so artifact + tu khoa tim kiem.

Lich su/cache cua Edge (va UIA text) nam trong RAM duoi dang ASCII va UTF-16.
Script gom moi URL kieu

    https://example.com/vormir?artifact=<hex>

doi chieu ASCII/UTF-16, giai ma tham so hex, va liet ke cac truy van Bing
(`q=...`) de cho thay thuat toan da tim giuoc truc luc capture.

Chay:  python solve.py <anh-RAM>
"""
import sys
import mmap
import re
import binascii
import collections

PU = re.compile(rb"https?://[^\s\"'<>|]{10,300}")
PW = re.compile(rb"(?:[ -~]\x00){12,300}")
ART = re.compile(r"artifact=([0-9a-fA-F]{20,})")
QUERY = re.compile(r"[?&]q=([^&]{2,60})")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    with open(sys.argv[1], "rb") as fh:
        mm = mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ)
        total = len(mm)
        urls = collections.Counter()
        queries = collections.Counter()
        chunk = 1 << 24
        off = 0
        while off < total:
            blob = mm[off:min(off + chunk + 320, total)]
            for g in PU.finditer(blob):
                u = g.group().decode("latin-1", "ignore")
                if "artifact=" in u:
                    urls[re.sub(r"[^ -~]", ".", u)[:200]] += 1
                elif "bing.com/search" in u:
                    for q in QUERY.findall(u):
                        queries[q] += 1
            for g in PW.finditer(blob):
                s = g.group().decode("utf-16-le", "ignore")
                if s.startswith(("http://", "https://")):
                    if "artifact=" in s:
                        urls[re.sub(r"[^ -~]", ".", s)[:200]] += 1
                    elif "bing.com/search" in s:
                        for q in QUERY.findall(s):
                            queries[q] += 1
            off += chunk
        mm.close()

    print("== URLs with artifact= ==")
    seen = set()
    for u, n in urls.most_common(40):
        print("%5d %s" % (n, u[:150]))
        for m in ART.finditer(u):
            h = m.group(1)
            h = h[:len(h) // 2 * 2]
            try:
                d = binascii.unhexlify(h).decode("latin-1")
            except Exception:
                continue
            if d.startswith("OWASP{") and d not in seen:
                seen.add(d)
                print("      %s -> %s" % (h, d))
    print("== bing queries ==")
    for q, n in queries.most_common(25):
        print("%5d %s" % (n, q))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```
