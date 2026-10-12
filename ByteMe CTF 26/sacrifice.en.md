---
title: "Sacrifice"
category: "Forensics"
tags: ["pcap", "ftp-data", "jpeg-stego", "file-carving", "layered-compression"]
solve_date: "2026-10-09"
language: "en"
---

# Sacrifice

**Flag:** `OWASP{4_50u1_f0r_4_50u1_v0rm1r}`
**Artifact:** `s0ul.pcap` (227,553 B, sha256 `d08f3d1e01ddd3dea611653b2d1fcc1fd10f6e9db2577386ac983c71a27bb76c`, 669 packet). Author: Urvish Bharde.

## Challenge

The challenge title is taken from the platform's solved table; the description that was recorded for it reads:

```text
Exfiltrated communication was captured in a packet trace. Retrieve the hidden payload.
```

Easy, 100 points. The opening line of the accompanying bundle README:

```text
Two went down. Only one came back. Find the one who didn't.
```

## Analysis

### Trace scope

`capinfos` on the file shows the trace is only 669 packets and all traffic is loopback — every endpoint is a loopback address, no external host. The trace never crossed a network; it is a recording of a file-transfer session on a single machine.

### Protocol hierarchy

```console
$ tshark -r s0ul.pcap -q -z io,phs
```

The hierarchy was noted as a summary (figures kept as recorded, this is not the full `io,phs` output):

```text
FTP      : 138 packet
FTP-DATA : ~160 kB payload
```

Essentially the whole data volume of the trace sits in FTP and FTP-DATA: 138 control packets against roughly 160 kB of payload, meaning most bytes in the pcap are file contents rather than headers. The analysis direction is therefore to extract the FTP-DATA streams and rebuild the files, not to hunt for a single embedded payload in one packet.

### The FTP session

The extraction command actually used:

```console
$ tshark -r s0ul.pcap -Y "tcp.len>0" -T fields -e tcp.stream -e ip.src -e tcp.srcport -e tcp.payload
```

FTP control stream 3 carries the login pair and the `STOR` list:

```text
USER vormirkeeper
PASS S0ulK33per2014
```

followed by 22 `STOR` commands — 22 files pushed to the server during the session. The names taken from those 22 commands are `manifest_*.txt`, `fuel_request*.txt`, `sensor_dump*.bin` and `manifest_final_047.jpg`. `comms.bin` is not among the `STOR` names: it is a member of the ZIP appended behind the image, not a separately transferred file. The matching FTP-DATA streams hold the file contents, one data stream per file; the `tcp.payload` column is hex and must go through `binascii.unhexlify` before being written to disk.

Every figure used above (669 packets, 138 FTP packets, 22 `STOR` commands, 290 ICMP packets, a single `PK\x03\x04` block appended after the image, the COM-marker string present exactly once) was re-measured directly on `s0ul.pcap` at the time this writeup was written. The member names inside the tar are not re-measurable from the trace: they sit behind the compression layers, so they do not occur as raw strings in the pcap.

## Solution

### The JPEG and the embedded password

Among the `STOR` files is `manifest_final_047.jpg`. JPEG allows markers outside the image data; the `FFFE` marker (COM, comment) in this file carries a plaintext line:

```text
This password might be useful XD : th3_ult1m4t3_s4cr1f1s3
```

`th3_ult1m4t3_s4cr1f1s3` is the only password candidate appearing anywhere in the trace.

The same file also carries appended data starting at offset 150649, immediately after the image end marker `FFD9`. `binwalk` reports:

```text
Zip archive data, encrypted
```

The file is a valid JPEG with a ZIP appended behind it, and the ZIP is encrypted — matching the password read from the COM marker.

### Opening the ZIP and peeling the compression layers

```python
import binascii, bz2, gzip, io, pathlib, tarfile, zipfile

jpg = pathlib.Path("manifest_final_047.jpg").read_bytes()
blob = jpg[150649:]                       # ZIP appended after FFD9
print("carved magic:", blob[:4])

zf = zipfile.ZipFile(io.BytesIO(blob))
zf.set_password(b"th3_ult1m4t3_s4cr1f1s3")
name = zf.namelist()[0]
data = zf.read(name)
print("member:", name, "bytes:", len(data), "magic:", data[:4])

layer = gzip.decompress(data)             # gzip
print("after gzip  :", layer[:4])
layer = bz2.decompress(layer)             # BZh9 -> bzip2
print("after bzip2 :", layer[:4])
layer = gzip.decompress(layer)            # gzip again
print("after gzip2 :", layer[:4])

tf = tarfile.open(fileobj=io.BytesIO(layer))
for m in tf.getmembers():
    if m.isfile():
        print("%9d  %s" % (m.size, m.name))
```

The layer chain as recorded in the session, in peeling order:

```text
ZIP (encrypted)  -> comms.bin
comms.bin        -> gzip
gzip output      -> bzip2 (BZh9)
bzip2 output     -> gzip
gzip output      -> tar
tar members      -> comms/<hero>/comm.log
```

These four layers are not visible from a single `file` run on the original blob: each layer only becomes recognizable once the previous one has been decompressed and the next magic appears (`1f 8b` for gzip, `BZh9` for bzip2, `ustar` for tar).

### Picking the real comm.log and decoding the base64 line

The tar contains several `comms/<hero>/` directories, one `comm.log` each. The discriminator is size: seven `comm.log` files are exactly 300 B of unreadable random data, while Natasha's is 3,015 B of plain dialogue text. The README line "Find the one who didn't" points at this filtering step, and the 3,015 B log is the real one.

Inside the Red Skull / Natasha dialogue there is a base64 line:

```console
$ python -c "import base64; print(base64.b64decode('T1dBU1B7NF81MHUxX2Ywcl80XzUwdTFfdjBybTFyfQ=='))"
```

```text
b'OWASP{4_50u1_f0r_4_50u1_v0rm1r}'
```

The base64 string is embedded in spoken dialogue, so it does not stand out visually; the approach taken was to scan every `comm.log` in the tar for base64-shaped strings and try to decode them, so the selection does not depend on the directory name:

```python
import base64, glob, pathlib, re

for path in sorted(glob.glob("comms/*/comm.log")):
    raw = pathlib.Path(path).read_bytes()
    hits = []
    for cand in re.findall(r"[A-Za-z0-9+/]{40,}={0,2}", raw.decode("latin-1")):
        try:
            dec = base64.b64decode(cand, validate=True)
        except Exception:
            continue
        if all(32 <= b < 127 for b in dec):
            hits.append(dec)
    print("%6d B  %-28s printable_decodes=%d  %s" % (len(raw), path, len(hits), hits))
```

The selected file is Natasha's 3,015 B log; the 300 B logs yield no printable decode.

## Result

```text
OWASP{4_50u1_f0r_4_50u1_v0rm1r}
```

The flag was decoded from the base64 line in Natasha's `comm.log` (the 3,015 B file taken out of the tar), the file produced by the ZIP -> gzip -> bzip2 -> gzip -> tar chain after opening the ZIP with the password read from the COM marker of the JPEG carved out of FTP-DATA. The whole chain derives from the pcap artifact; there is no remote service. No submission response recorded.

## Reproduce

Requires `tshark`/`capinfos` and `binwalk` (Wireshark CLI), plus Python 3 stdlib for the layered decompression.

```console
$ capinfos s0ul.pcap
$ tshark -r s0ul.pcap -q -z io,phs
$ tshark -r s0ul.pcap -Y "tcp.len>0" -T fields -e tcp.stream -e ip.src -e tcp.srcport -e tcp.payload
$ tshark -r s0ul.pcap -Y "ftp" -T fields -e tcp.stream -e frame.number -e ftp-request -e ftp-request-arg
$ binwalk manifest_final_047.jpg
```

After rebuilding `manifest_final_047.jpg` from its FTP-DATA stream, save the script from the Solution section as `solve.py` in the same directory and run `python solve.py`. Writing files from hex payloads means running `binascii.unhexlify` over the `tcp.payload` column and concatenating per `tcp.stream` in packet order.

The member paths inside the tar (`comms/<hero>/comm.log`) depend on the directory names the author chose; the script prints every file member with its size so the 3,015 B selection does not depend on a name.
