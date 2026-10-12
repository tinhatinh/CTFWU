---
title: "Phantom Mesh"
category: "Forensics"
tags: ["side-channel", "cpa", "aes-ccm"]
solve_date: "2026-10-11T04:12:00+07:00"
language: "en"
---

# Phantom Mesh

**Flag:** `isfcr{ph4nt0m_m3sh_h4rm0n1cs_un14sk_th3_tc_l1nk_k3y}`  
**Artifacts:** `mesh.pcap`, `traces/iq.npz`, `traces/nonces.csv`, `docs/LMP-protocol.md`, `docs/sdr-capture.md` (supplied in `phantom-mesh.zip`)

| Artifact | SHA-256 |
|---|---|
| `mesh.pcap` | `fc21e8e8e7c33013e6232bd1152e133ab4cb67b6d248bbac4e8b32ce91145a53` |
| `traces/iq.npz` | `1ef310df2b4b3e4c3d2d34180316511a1593d30b533d66320ad320c8041383ec` |
| `traces/nonces.csv` | `6ac10e271a62937aadfd20408f767a0a78e46e2cc6596d201efb5250ee71b182` |
| `docs/LMP-protocol.md` | `137e2f850157c86a9a0a8a6c1cdfba7526413873e1e9e290a9420ce53235a13b` |
| `docs/sdr-capture.md` | `b65b72e5e6531037e5d916b42e821323e1c748eba69431ed25780f3d95444ca9` |

## Challenge

A smart-lighting mesh contains an unauthorized device that sends a daily diagnostics report. We are given an over-the-air IEEE 802.15.4 capture, synchronized complex I/Q traces from the coordinator, the nonces transmitted during those traces, and vendor documentation for the Lumeta Mesh Protocol (LMP). The network key is unknown. Our goal is to recover and decrypt the report containing the flag.

## Initial Analysis

`mesh.pcap` uses link type **195 (IEEE 802.15.4)**. The LMP payloads begin with `1c 03`, followed by a command byte. The vendor's `LMP-protocol.md` identifies the important commands:

| Command | Meaning | Protection |
|---|---|---|
| `0x11` | `TRANSPORT_KEY` | Fleet-wide Trust Center (TC) Link Key |
| `0x12` | `KEY_CONFIRM` | Plaintext challenge/response using the TC Link Key |
| `0x21` | `SECURE_REPORT` | Per-site Network (NWK) Key |
| `0x30` | `BEACON` | Plaintext |

All encrypted commands use **AES-128-CCM with a 4-byte authentication tag** (CCM `M=4`, `L=2`). Crucially, the vendor deliberately uses different EUI-64 byte orders in the nonce and associated data:

```text
nonce = src_eui64 (big-endian, 8 bytes)
      || frame_counter (little-endian, 4 bytes)
      || sec_ctl (1 byte)

aad   = sec_ctl (1 byte)
      || frame_counter (little-endian, 4 bytes)
      || src_eui64 (little-endian, 8 bytes)
```

The capture contains eight consecutive `KEY_CONFIRM` packets (packets **32–39**) followed by a `TRANSPORT_KEY` to short address `0x1040` (packet **40**). Packet **81** is a long `SECURE_REPORT` sent from `0x1040` to the coordinator. These provide an attack chain: recover the TC Link Key, decrypt the NWK Key, and decrypt the report.

The side-channel files are especially useful. According to `docs/sdr-capture.md`, `traces/iq.npz` contains **2,500 aligned traces of 2,500 complex64 samples each**. Each trace corresponds to a `KEY_CONFIRM` generated with a known 16-byte nonce in `traces/nonces.csv`. The coordinator implements AES in software, and a poorly decoupled RF power amplifier leaks variations in the transmitted signal envelope. This gives us a correlation power analysis (CPA) target despite not having the key.

## Exploitation Chain

1. **Convert I/Q traces into a leakage signal.** Load the `iq` matrix and compute `abs(iq)` for each complex sample. Center and normalize every time sample across the 2,500 traces. The RF amplitude provides a usable proxy for AES-dependent power consumption.

2. **Recover the fleet-wide TC Link Key with CPA.** The `KEY_CONFIRM` calculation is the first eight bytes of `AES-128-ECB(TC_Link_Key, nonce)`. For each key byte position `i` and candidate byte `k`, predict the first-round AES S-box output `SBOX[nonce[i] XOR k]`, convert it to Hamming weight, and correlate that prediction against all amplitude samples. Choose the candidate with the largest absolute Pearson correlation. The 16 bytewise winners form:

   ```text
   TC Link Key = 7cf8b0b78be9f36a225c1e70692e1e1c
   ```

   The leakage peaks occur sequentially around sample **1051** for byte 0 through **1771** for byte 15, spaced approximately 48 samples apart. The correct key byte ranks first for each position. Independently validate the recovered key using the eight on-air `KEY_CONFIRM` tags:

   ```text
   confirm_tag == AES-128-ECB(TC_Link_Key, nonce)[:8]
   ```

   **All eight tags match.** This confirms the AES construction and the recovered TC Link Key, without relying on the CPA correlation score alone.

3. **Decrypt `TRANSPORT_KEY` in packet 40.** Read the `0x11` body as `sec_ctl (1) || frame_counter (4) || src_eui64_LE (8) || ciphertext (16) || MIC (4)`. The security control is `05`, the frame counter is `64000000`, and the source EUI-64 is `0100aa25004b1200` in little-endian order. Build the 13-byte CCM nonce and AAD exactly as documented:

   ```text
   nonce = 00124b0025aa00016400000005
   aad   = 05640000000100aa25004b1200
   ```

   AES-CCM decryption using the TC Link Key authenticates the four-byte MIC and yields the 16-byte site key:

   ```text
   NWK Key = ffa0be732cd8f56eae8caa21359baf06
   ```

4. **Decrypt the unauthorized device's report in packet 81.** This `0x21` message originates from short address `0x1040`. For its security header, the frame counter is `ad0d0000` and the EUI-64 is `4000aa25004b1200` in little-endian order. Thus:

   ```text
   nonce = 00124b0025aa0040ad0d000005
   aad   = 05ad0d00004000aa25004b1200
   ```

   Decrypt the ciphertext and verify its MIC with the newly recovered NWK Key. The plaintext begins with the six-byte ZCL-like attribute header:

   ```text
   cluster_id   = 0xFC01
   attribute_id = 0x0042
   vlen         = 0x0034 = 52 bytes
   ```

   The following 52 ASCII bytes contain:

   ```text
   isfcr{ph4nt0m_m3sh_h4rm0n1cs_un14sk_th3_tc_l1nk_k3y}
   ```

## Flag

`isfcr{ph4nt0m_m3sh_h4rm0n1cs_un14sk_th3_tc_l1nk_k3y}`

The flag was recovered directly from the authenticated AES-CCM plaintext in packet 81. The TC Link Key was independently validated against eight `KEY_CONFIRM` packets, and both AES-CCM decryption steps passed authentication. The flag was not submitted to the CTF service, so acceptance is unconfirmed.

## Reproduce

Extract `phantom-mesh.zip` and run the following code from the directory containing the extracted `phantom-mesh/` folder. Install Python packages `numpy` and `cryptography` if necessary. The code recovers the TC Link Key from the **actual radio traces**, verifies the eight challenge/response tags, extracts the NWK Key from the PCAP, and decrypts the flag-bearing report. No key is hard-coded.

```python
import csv
import struct
from pathlib import Path

import numpy as np
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESCCM

root = Path("phantom-mesh")

# Standard AES substitution box.
sbox = np.frombuffer(bytes.fromhex("""
637c777bf26b6fc53001672bfed7ab76
ca82c97dfa5947f0add4a2af9ca472c0
b7fd9326363ff7cc34a5e5f171d83115
04c723c31896059a071280e2eb27b275
09832c1a1b6e5aa0523bd6b329e32f84
53d100ed20fcb15b6acbbe394a4c58cf
d0efaafb434d338545f9027f503c9fa8
51a3408f929d38f5bcb6da2110fff3d2
cd0c13ec5f974417c4a77e3d645d1973
60814fdc222a908846eeb814de5e0bdb
e0323a0a4906245cc2d3ac629195e479
e7c8376d8dd54ea96c56f4ea657aae08
ba78252e1ca6b4c6e8dd741f4bbd8b8a
703eb5664803f60e613557b986c11d9e
e1f8981169d98e949b1e87e9ce5528df
8ca1890dbfe6426841992d0fb054bb16
"""), dtype=np.uint8)
hw = np.array([n.bit_count() for n in range(256)], dtype=np.float32)

# The aligned RF envelope acts as a power-analysis trace.
iq = np.load(root / "traces/iq.npz")["iq"]
with (root / "traces/nonces.csv").open(newline="") as f:
    rows = list(csv.DictReader(f))
nonces = np.array(
    [list(bytes.fromhex(r["nonce_hex"])) for r in rows],
    dtype=np.uint8,
)
assert iq.shape == (2500, 2500) and nonces.shape == (2500, 16)

signal = np.abs(iq).astype(np.float32)
signal -= signal.mean(axis=0)
signal /= np.maximum(np.linalg.norm(signal, axis=0), 1e-9)

# Recover each AES key byte by Pearson-correlation CPA.
keys = np.arange(256, dtype=np.uint8)
recovered = bytearray()
for i in range(16):
    # h: 256 candidate predictions x 2500 traces
    h = hw[sbox[nonces[:, i, None] ^ keys[None, :]]].T.copy()
    h -= h.mean(axis=1, keepdims=True)
    h /= np.maximum(np.linalg.norm(h, axis=1, keepdims=True), 1e-9)
    corr = h @ signal
    scores = np.max(np.abs(corr), axis=1)
    recovered.append(int(np.argmax(scores)))
tc_key = bytes(recovered)
print("TC Link Key:", tc_key.hex())

# Read little-endian PCAP records; linktype 195 is raw IEEE 802.15.4.
raw = (root / "mesh.pcap").read_bytes()
assert raw[:4] == bytes.fromhex("d4c3b2a1")
assert struct.unpack_from("<I", raw, 20)[0] == 195
packets = []
offset = 24
while offset < len(raw):
    _, _, caplen, _ = struct.unpack_from("<IIII", raw, offset)
    packets.append(raw[offset + 16:offset + 16 + caplen])
    offset += 16 + caplen

# Captured frames have a 9-byte 802.15.4 MAC header and 2-byte FCS.
def lmp(packet_number):
    pdu = packets[packet_number - 1][9:-2]
    assert pdu[:2] == b"\x1c\x03"
    return pdu

def aes_block(key, data):
    enc = Cipher(algorithms.AES(key), modes.ECB()).encryptor()
    return enc.update(data) + enc.finalize()

# The eight KEY_CONFIRM packets must match AES-ECB, truncated to 8 bytes.
for packet_number in range(32, 40):
    pdu = lmp(packet_number)
    assert pdu[2] == 0x12
    assert aes_block(tc_key, pdu[3:19])[:8] == pdu[19:27]
print("KEY_CONFIRM: 8/8 verified")

def decrypt_lmp(pdu, key):
    body = pdu[3:]
    ctl, counter, eui_le = body[:1], body[1:5], body[5:13]
    nonce = eui_le[::-1] + counter + ctl
    aad = ctl + counter + eui_le
    return AESCCM(key, tag_length=4).decrypt(nonce, body[13:], aad)

transport = lmp(40)
assert transport[2] == 0x11
nwk_key = decrypt_lmp(transport, tc_key)  # Verifies CCM MIC.
assert len(nwk_key) == 16
print("NWK Key:    ", nwk_key.hex())

report = lmp(81)
assert report[2] == 0x21
plaintext = decrypt_lmp(report, nwk_key)  # Verifies CCM MIC.
cluster, attribute, value_length = struct.unpack_from("<HHH", plaintext)
value = plaintext[6:]
assert (cluster, attribute) == (0xFC01, 0x0042)
assert len(value) == value_length == 52
flag = value.decode("ascii")
assert flag.startswith("isfcr{") and flag.endswith("}")
print("FLAG", flag)
```

Expected output:

```text
TC Link Key: 7cf8b0b78be9f36a225c1e70692e1e1c
KEY_CONFIRM: 8/8 verified
NWK Key:     ffa0be732cd8f56eae8caa21359baf06
FLAG isfcr{ph4nt0m_m3sh_h4rm0n1cs_un14sk_th3_tc_l1nk_k3y}
```
