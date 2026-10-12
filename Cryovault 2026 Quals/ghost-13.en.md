---
title: "GHOST - 13"
category: "Hardware"
tags: ["iot", "ecdsa", "forensics"]
solve_date: "2026-10-11T08:57:00+07:00"
language: "en"
---

# GHOST - 13

**Flag:** `isfcr{ghost13_dc8f84a256fa64108b6c75a151a1474d}`  
**Artifacts:** `plc_firmware.bin` (25,024), `plc_program.bin` (1,600), `plc_traffic.pcap` (5,473), `alarm_buzzer.wav` (93,964), `maintenance_update.ota` (726), `uart_log.txt` (778), `field_service_excerpt.txt` (3,817)

| Artifact | SHA-256 |
|---|---|
| `plc_firmware.bin` | `532395ef38016b0ef29981c7deb6dd3af07abc50af9268ce26a4d04083ae58f7` |
| `plc_program.bin` | `a0a145fe0ec9605ed3a2d9a338f1e66385eed6ac62011a3a9de43b520c8609f0` |
| `plc_traffic.pcap` | `a0de754f697df41db7bc2d3462a6fd9b89db9a763f22123873dfb4e17eab3b59` |
| `alarm_buzzer.wav` | `d9702ffce42d939be89250366cf782eb25b6bf6fa193fa29116ca5c7423bb769` |
| `maintenance_update.ota` | `e084621b293c7c34c51e80fefeffc3dc133bcac29f6db3ac45e58942d34e703d` |
| `uart_log.txt` | `643ce0ac86bfd45c5f2d221e04e2cbe396611618ee0b5055993e1f64514b9d18` |
| `field_service_excerpt.txt` | `6c11b6b0c551480fa44e6a2d3c431923f3e3d9239d0689d72a18f36f0dc99b88` |

## Challenge

The GHOST-13 line controller kept a manufacturing cell alive through a brief power failure. On restart, its maintenance gateway accepted two diagnostic writes that should never have looked alike. The hardware is gone; the plant retained a firmware image, an IEC-style program/configuration dump, a Modbus/TCP capture, a buzzer recording, an OTA update, a serial log and a damaged service manual excerpt. The task is to reconstruct the active configuration and the reboot sequence, then recover the diagnostic secret sealed inside the maintenance update.

## Initial Analysis

`field_service_excerpt.txt` is the specification for every other artifact, so the solve is a chain of format-conformant reconstructions in which each stage carries its own check (a CRC, a hash or a signature):

- `plc_firmware.bin` starts with `G13W`, version `3`, four directory entries: `VMBC` (offset 0xa0, 8234 B), `KDFD` (0x20d0, 78 B), `PUBK` (0x2120, 68 B), `RECV` (0x2170, 16462 B). `KDFD` holds `G13K` plus a 32-byte factory constant `bc2163b4…6bbaab74` and three marker strings; `PUBK` holds `P256` plus two big-endian coordinates. All four section CRC32 values verify.
- `plc_program.bin` starts with `G13L`: a 64-byte header whose offsets 16, 20, 22 give journal base 1088, count 8, size 64, then eight 128-byte `G13P` slots and eight 64-byte `G13J` commit journals. Slot `ID`, `salt` and `keypad_trim` sit at 8, 24 and 84.
- `plc_traffic.pcap` is Modbus/TCP traffic to `10.13.0.1:502` carrying FC16 writes of `G13C` diagnostic fragments.
- `alarm_buzzer.wav` is 8 kHz mono 16-bit, 5.87 s.
- `uart_log.txt` timestamps the sequence: `ROM … VM revision 3`, `PROGRAM: journal frontier restored after 16-bit rollover`, `DIAG fragment stream 0x41`, `watchdog exception 0x06; CPU brownout restart`, `DIAG fragment stream 0x42`, plus the buzzer-trim and legacy-key remarks.

The sealed record needs an ECDSA private scalar that is deliberately not present in any image ("the protected signing scalar is in slot 0x13, outside the image"). The description's two writes are the only way to obtain it: if the reboot reused a signature nonce, the scalar follows from the capture.

## Exploitation Chain

1. **Find the committed slot.** A slot is valid when `CRC32(slot[0:120])` equals the field at 120 and the commit word at 124 equals `CRC ^ 0x13c0ffee ^ (sequence<<16 | epoch)`. A journal is valid when `CRC32(journal[0:56])` equals the field at 56 and the commit word at 60 equals `CRC ^ 0xa91f0eed ^ (jseq<<16 | jseq)`, and it must also repeat the bound slot's sequence, epoch and CRC. Journal sequences run `65533, 65534, 65535, 0, 1, 2, 3, 4`, so they wrap. A plain maximum picks slot 2 (`R_TRIG_FEED`, jseq 65535); the newest journal under 16-bit serial arithmetic (`(a-b) & 0xffff < 0x8000`) is jseq 2. Journals 3 and 4 both fail their own checks:

   | jseq | slot | status |
   |---|---|---|
   | 65533…2 | 0…5 | valid, committed |
   | 3 | 6 `TON_WATCHDOG` | journal CRC32 field inconsistent (`0x8eb723c5` stored vs `0x8eb723c4` computed) |
   | 4 | 7 `R_TRIG_ALARM` | commit word `0xffffffff`, never committed; slot CRC32 field also inconsistent |

   The active configuration is **slot 5, `TON_WATCHDOG`, sequence 2, epoch 7**: `committed_ID = 75f83e16b7969d3985c35154de9fcb10`, `committed_salt = ac0c0f86d58bdde419cd50a98450c012`, `keypad_trim = [9,9,3,2,9,9,9,4]`.

2. **Reassemble the Modbus writes.** The client direction reassembles to 773 contiguous bytes; MBAP fields are big-endian and one request (tid 3) is split across two segments, so framing per packet instead of per stream misreads the MBAP length. Eleven FC16 writes carry `G13C` fragments (`magic, stream_id:u16, index:u8, data_count:u8, frame_len:u16, parity:u8, reserved:u8, payload[40], CRC16:u16`). CRC16/CCITT-FALSE over the first 52 bytes, combined with the address rule `0x4200+20*index` (or `0x4300` for the parity fragment), accepts 10 of 11: tid 14 is the damaged fragment (one byte of stream `0x43` index 1 differs from tid 11 although both carry the same CRC16), tid 10 is a byte-identical retransmission of tid 9. Three frames result, each from three 40-byte slices with `frame_len 118`:

   - stream `0x41`: index 1 missing, restored as `payload0 XOR payload2 XOR parity`
   - stream `0x42`: index 2 missing, restored the same way
   - stream `0x43`: all three data slices present, no parity fragment

   Each reassembled `G13F` frame is `magic, version=2, kind, sequence:u16, encrypted_length:u16=88, CTR_IV[16], body[88], CRC32`, and all three verify their trailing CRC32.

3. **Decrypt, and confirm the active slot.** `link_key = SHA256("G13/link/v2" || factory_constant || committed_ID || committed_salt)` = `c8017211…e7d24b97`. AES-256-CTR with the 16-byte `CTR_IV` as the initial counter block yields `state[24] || r[32] || s[32]`; the states read `PLC-G13/STATE/!`, `PLC-G13/STATE/"` and `PLC-G13/STATE/#`. Verifying ECDSA over `SHA256("G13/sign/v2" || G13F_header[26] || state || committed_ID || committed_salt[0:8])` against `PUBK` succeeds for all three frames using slot 5's ID and salt and for no other slot, which independently confirms step 1.

4. **Recover the scalar from the reused nonce.** Streams `0x41` and `0x42` share `r = 0x78dd7327…432c9765`; stream `0x43` uses a different one. With `s = k^-1(m + r·d)`:

   ```text
   k = (m1 - m2) / (s1 - s2)   = b467b40088e70a1c81902bcbf6d5bb3b1d571d56bcf58b2b96ef19628c05336a
   d = (s1·k - m1) / r         = 2f1945b86a823a5bffb808c0f5edc9bd981fb15481696d7c29bde45fb8e1a4cb
   d·G == PUBK                 True
   ```

   The recovered `d` also reproduces the `r` of stream `0x43`. The frames, the public key and the log agree on the mechanism: the brownout restart reset the signing VM's nonce state, so the pre-reset and post-reset writes were signed with the same `k`.

5. **Read the keypad code from the buzzer.** DTMF detection over 25 ms windows (rows 697/770/852/941, columns 1209/1336/1477/1850) finds sixteen digit bursts plus three 440 Hz carrier regions at 0.004–0.306 s, 2.557–2.974 s and 5.227–5.866 s, which separate the two eight-key groups:

   - power-on self-check: `70372720`
   - diagnostic wire code: `64658003`

   Adding each committed `keypad_trim` byte modulo 10 to the corresponding wire digit gives the eight ASCII digits used by the update: `53977997`.

6. **Build the target image.** The `G13U` v4 header verifies its own CRC32 at offset 60 and reports sealed length 111, nonce suffix `ba28ff2e`, `SHA256(target)[:16]` at bytes 24…39, manifest length 163 and patch length 388. The manifest names `GHOST-13`, `target: maintenance-4`, `base_crc32: 9b658883`, `target_crc32: 922823e4`. The six `G13X` v2 hunks (`image_offset:u32, length:u16, mode=1, replacement bytes`) change two regions and repair three bookkeeping fields: `0x000ca` rewrites 256 bytes of the `VMBC` signing program and `0x020d4` replaces the `KDFD` constant with `1b6213e5…f1add8cf`, while `0x00010` sets a header field, `0x0004c` and `0x00064` update the `VMBC` and `KDFD` directory CRC32 entries, and `0x0003c` updates the header CRC32 at offset 60. Applying them in order to a copy of the complete factory image gives a 25,024-byte target whose CRC32 is `0x922823e4`, whose SHA-256 begins `73842f3957f72613e4e61dda81dd1c0b`, and whose four section CRC32 values all revalidate. That target `KDFD` constant, not the factory one, is what the sealed record requires.

7. **Open the sealed record.** Using `IKM = d_be32 || committed_ID || committed_salt`, `salt = SHA256(target_KDF_constant || committed_salt)` and

   ```text
   info = "G13/diagnostic/v4" || committed_ID || firmware_version_le16 || keypad_digits_ascii
          || SHA256(target_image) || SHA256(raw_manifest) || SHA256(raw_delta)
   ```

   HKDF-SHA256 produces the AES-256-GCM key. The nonce is the eight ASCII digits followed by the four-byte suffix (`53977997` + `ba28ff2e`), and the AAD is `header[0:60] || raw_manifest || raw_delta`. Two readings of the excerpt were settled by the tag rather than assumed: `firmware_version_le16` is the patched image's header version (`3`, matching the log's "VM revision 3"), and the `G13/diagnostic/v4` marker enters the info string without the NUL that terminates it inside `KDFD`. Among the variants tried (both marker spellings × header versions 0, 1, 2, 3, 4), only that combination authenticated. Decryption yields `G13D` followed by a zlib stream:

   ```json
   {"diagnostic":"power-restoration","flag":"isfcr{ghost13_dc8f84a256fa64108b6c75a151a1474d}"}
   ```

## Eliminated Hypotheses

- **Reading the signing scalar out of the image.** `RECV` is the label `LEGACY-RECOVERY-KEY:` followed by 32 raw bytes (`7109d3c1…6ac43499`) and an embedded `CRC16_O…` table (16,462 B in total). The excerpt scopes it to v1 recovery images only, and no v2 or v4 step references it, so it was never used as a key. The `0x13` remarks (`secure slot 0x13 available`, repeated `retention tick=1729 ms`) point at storage outside the retained artifacts, and `SELFTEST: CRC16 legacy table OK (offline module)` matches the embedded offline CRC16 table in `RECV`, which is not needed once the correct CCITT-FALSE variant is identified.
- **Slot 6 or slot 7 as the active configuration.** Both look newer, and slot 6 duplicates the committed slot's name. Each fails one check in step 1, and only slot 5's `ID`/`salt` makes the ECDSA checks of step 3 pass: all eight slots were tried as link-key inputs, and only slot 5 yielded verifying signatures for the three frames.
- **Trusting packet order and packet boundaries.** Fragment payloads straddle TCP segments, and a `G13C`-less write from `10.13.0.88:49153` (unit-id `0x00`, register `0x1200`) joins no stream. Per-packet MBAP framing, or accepting that spoofed write, corrupts the reassembly.
- **Using the third write for the nonce-recovery step.** Only `0x41` and `0x42` share a nonce; `0x43` has its own `k` and serves as a cross-check of the recovered scalar.

## Flag

`isfcr{ghost13_dc8f84a256fa64108b6c75a151a1474d}`

Recovered offline from the supplied artifacts. The active configuration, the signing scalar and the keypad digits are each pinned by a cryptographic check (ECDSA verification against `PUBK`, `d·G == PUBK`, and the AES-256-GCM tag of the sealed record), so a wrong value at any stage would have failed authentication. The flag was not submitted to a CTF service, so acceptance is unconfirmed.

## Reproduce

Every stage below has its own integrity test, so a mistake surfaces immediately.

Parse `plc_firmware.bin` as a 64-byte `G13W` header plus 24-byte directory entries and confirm the section CRC32 values; take the factory constant from `KDFD[4:36]` and the coordinates from `PUBK[4:68]`. Parse `plc_program.bin` as eight 128-byte `G13P` slots at offset 64 and eight 64-byte `G13J` journals at the header's journal base, validate slots with `CRC ^ 0x13c0ffee ^ (seq<<16|epoch)` and journals with `CRC ^ 0xa91f0eed ^ (jseq<<16|jseq)` plus their stored CRC fields, then take the newest committed journal under 16-bit serial arithmetic; the result is slot 5 with its `ID`, `salt` and `keypad_trim`.

Reassemble the `10.13.0.13 → 10.13.0.1:502` direction by TCP sequence number, walk Modbus frames by big-endian MBAP length, keep FC16 writes whose `G13C` CRC16/CCITT-FALSE over bytes 0..51 matches and whose register equals `0x4200+20*index` or `0x4300`, drop the retransmission and the damaged write, XOR-restore the missing slice in streams `0x41` and `0x42`, and check each 118-byte `G13F` frame CRC32. Decrypt each body with AES-256-CTR keyed by `SHA256("G13/link/v2" || factory_constant || ID || salt)` and the frame's `CTR_IV`, then verify ECDSA over `SHA256("G13/sign/v2" || header[26] || state || ID || salt[0:8])` against `PUBK`. Recover `k = (m1-m2)/(s1-s2)` and `d = (s1·k-m1)/r` from the two frames sharing `r`, and confirm `d·G == PUBK`.

Decode the WAV as DTMF, split the sixteen digits at the 440 Hz carrier regions, take the second group `64658003`, and add `keypad_trim` modulo 10 to obtain `53977997`.

Apply the `G13X` hunks to a copy of the factory image, then revalidate the target CRC32 (`0x922823e4`), `SHA256(target)[:16]` against the `G13U` header, and the four section CRCs; read the target `KDFD` constant and the target header version as a little-endian u16. Derive the key with HKDF-SHA256 (`IKM = d_be32 || ID || salt`, `salt = SHA256(target_KDF || salt)`, `info = "G13/diagnostic/v4" || ID || version_le16 || "53977997" || SHA256(target) || SHA256(manifest) || SHA256(delta)`), decrypt the trailing 111 bytes with AES-256-GCM using nonce `"53977997" || ba28ff2e` and AAD `header[0:60] || manifest || delta`, and inflate the bytes after the `G13D` magic. The expected result is:

```text
FRONTIER (active/committed) -> slot 5 TON_WATCHDOG seq=2 epoch=7
stream 0x41 / 0x42 / 0x43  frame_crc32=OK  sig_verify=OK
NONCE REUSE (r identical for 0x41/0x42)  d*G == PUBK : True
DTMF groups: self-check=70372720  wire=64658003  -> keypad ascii 53977997
target image: ver=3 sections_ok=True crc32=0x922823e4
sealed plaintext magic: b'G13D'
{"diagnostic":"power-restoration","flag":"isfcr{ghost13_dc8f84a256fa64108b6c75a151a1474d}"}
```
