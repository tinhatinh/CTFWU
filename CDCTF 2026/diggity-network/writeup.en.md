# Diggity Network - Forensics (500 points)

**Flag:** `cdctf{file_over_http}` · **Files:** `network_traffic_with_a_flag_in_there.pcapng`, 104320 bytes, sha256 `2b77a67c14d61cbabd48ca338cbe86188f5bd5c5ff700e00546fe9b6bbd67fa3`

## Challenge

The challenge provides a network capture and says a friend used `cat` to send a file containing the flag into netcat. Recover the transmitted data and find a flag in the form `cdctf{...}`. The supplied point value is 500; Forensics is inferred from the artifact.

## Analysis

The file is PCAPNG. tshark reports 59 frames, totaling 101971 bytes at the frame layer, containing only Ethernet/IP/TCP. There is one connection: `172.21.0.3:34012 → 172.21.0.2:8080`, TCP stream 0.

Frame 4 contains the first payload, with relative sequence number 1 and 2048 bytes. Its first eight bytes are `89 50 4e 47 0d 0a 1a 0a`, the PNG signature. Since netcat sends file bytes directly over TCP, reassemble the sender's payloads in sequence order and open the image.

## Approaches tried

1. **Searching for an ASCII flag in the capture:** scanning printable strings containing `flag`, `cdctf`, `cat`, or `net` returned no matches. This direct search did not recover a flag; the PNG payload explains why handwritten text does not appear as plaintext.
2. **Treating the transfer as HTTP or TLS:** protocol statistics contain no HTTP/TLS layer, and the payload starts directly with PNG magic. Reassembling the file from TCP is sufficient; decryption or HTTP object export is unnecessary.

Commands and evidence for each approach are recorded in `notes.md`.

## Solution

**Step 1 - Identify the connection and file signature.** Run from the challenge directory:

```powershell
tshark -n -r files/network_traffic_with_a_flag_in_there.pcapng -q -z io,phs -z conv,tcp
tshark -n -r files/network_traffic_with_a_flag_in_there.pcapng -Y "tcp.len > 0" -T fields -e frame.number -e tcp.stream -e ip.src -e tcp.srcport -e tcp.seq -e tcp.len -e tcp.payload
```

The full statistics output is saved in `analysis/triage.txt`. The sender is `172.21.0.3` in stream 0.

**Step 2 - Reassemble the payloads.** `exploit.py` uses tshark to extract sequence numbers and payloads in the sending direction. It sorts by sequence number, detects gaps, checks overlapping retransmission bytes, and writes `analysis/recovered_flag.png`. The key reassembly code is:

```python
base = parts[0][0]
data = bytearray()
for seq, payload in parts:
    offset = seq - base
    if offset > len(data):
        raise SystemExit(f"Missing TCP bytes at offset {len(data)}.")
    overlap = min(len(data) - offset, len(payload))
    if data[offset:offset + overlap] != payload[:overlap]:
        raise SystemExit("Conflicting retransmission.")
    data.extend(payload[overlap:])
```

**Step 3 - Verify and read the image.** The reconstructed file contains 98061 bytes from 30 payloads. The PNG measures 724×390 pixels and contains 14 chunks: IHDR, 12 IDAT chunks, and IEND. All chunk CRCs are valid, with no trailing bytes after IEND.

![Flag image reconstructed from TCP](analysis/recovered_flag.png)

Read the handwritten flag directly from the image. The script reconstructs and validates the PNG, then accepts a manual flag transcription. The flag contains `http`, but the capture carries the file directly over TCP.

## Result

```powershell
python exploit.py files/network_traffic_with_a_flag_in_there.pcapng
```

After opening the image and entering the observed flag, the actual output is:

```text
TCP stream 0: 30 payloads, 98061 bytes
PNG: 724x390, 14 chunks, all CRCs valid
Saved: analysis/recovered_flag.png
Manual visual step: open the PNG and transcribe its handwritten flag.
[+] flag (manual transcription): cdctf{file_over_http}
```

The flag is saved in `flag.txt`. No accepted submission is recorded.

## Reproduce

Requirements: Python 3 and Wireshark/tshark on PATH. Run from `diggity-network`, open `analysis/recovered_flag.png`, then enter the flag at the script's prompt. On Windows, use `--open-image` to open the image in the default application.

```powershell
python exploit.py files/network_traffic_with_a_flag_in_there.pcapng --open-image
```

To recover it manually in Wireshark, filter on `tcp.stream == 0`, select **Follow → TCP Stream**, choose `172.21.0.3:34012 → 172.21.0.2:8080`, select **Raw**, and save as PNG.
