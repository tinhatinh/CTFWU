"""Thong ke beacon cua implant (/tmp/.cache/.upd) tu audit.log + cron.log.

Chay: python analysis/beacons.py ../files/corpo_rat.zip
Hoac: python analysis/beacons.py <thu_muc_chua_log>
"""

import datetime as dt
import ipaddress
import re
import statistics
import sys
import zipfile
from pathlib import Path

SOCK = re.compile(r'type=SOCKADDR msg=audit\((\d+\.\d+):\d+\): saddr=([0-9A-F]+)')
CRON = re.compile(r'^(\w{3} +\d+ [\d:]+) \S+ CRON\[(\d+)\]: \(root\) CMD \((.*?)\)', re.M)
IMPLANT = "/tmp/.cache/.upd"


def read(source: Path, name: str) -> str:
    if source.is_dir():
        return (source / name).read_text(errors="replace")
    with zipfile.ZipFile(source) as zf:
        key = next(i.filename for i in zf.infolist() if Path(i.filename).name == name)
        return zf.read(key).decode(errors="replace")


def main() -> int:
    src = Path(sys.argv[1] if len(sys.argv) > 1 else "../files/corpo_rat.zip")
    audit = [(int(float(m.group(1))), m.group(2)) for m in SOCK.finditer(read(src, "audit.log"))]
    peers = {}
    for ts, s in audit:
        raw = bytes.fromhex(s)
        peers.setdefault((str(ipaddress.IPv4Address(raw[4:8])), int.from_bytes(raw[2:4], "big")), []).append(ts)
    for (ip, port), times in sorted(peers.items(), key=lambda kv: -len(kv[1])):
        gaps = [b - a for a, b in zip(times, times[1:])]
        print(f"{ip}:{port:<5} {len(times)} ket noi")
        if len(times) > 1 and gaps:
            f = lambda t: dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%b %d %H:%M:%S")
            print(f"  tu {f(times[0])} UTC -> {f(times[-1])} UTC")
            print(f"  gap min/median/max = {min(gaps)}/{statistics.median(gaps)}/{max(gaps)} s")

    cron = [m.groups() for m in CRON.finditer(read(src, "cron.log")) if IMPLANT in m.group(3)]
    print(f"\ncron.log: {len(cron)} lan cron root chay {IMPLANT}")
    print(f"  lan dau : {cron[0][0]} CRON[{cron[0][1]}]")
    print(f"  lan cuoi: {cron[-1][0]} CRON[{cron[-1][1]}]")
    print(f"  tong so SOCKADDR trong audit.log = {len(audit)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
