---
title: "Signed, But Which Original?"
category: "Forensics"
tags: ["transparency-log", "ed25519"]
solve_date: "2026-10-10T16:44:00+07:00"
language: "vi"
---

# Signed, But Which Original?

**Flag:** `isfcr{29336738f5f44f4d2d1e3ac2}`  
**Artifact:** `case.json`, `entries.bin` (extracted from `handout (23).zip`)
| Artifact | SHA-256 |
|---|---|
| `case.json` | `75c062301993c6f58ede6c941ed06346d1fa4e6e9aa5843e256c341085871cf8` |
| `entries.bin` | `2eb1ce3bdaaf0d746c91db7a62114c7896938a20321b725bba391ba9b113a33e` |

## Đề bài

Khôi phục derivative đúng policy và authenticated ancestry từ transparency log. Sáu ASCII evidence field dùng để dựng key và decrypt flag; chữ ký hợp lệ chưa đủ nếu key không được phép hoặc checkpoint sai.

## Phân tích

case.json quy định trusted root, principal `capture-north`, incident `incident-d7be9442cb`, chain `capture→crop→resize→redact`, tối đa bốn manifest và largest valid checkpoint. JSON phải canonical RFC 8785; parent phải được log trước child.

entries.bin có magic ISFCRLOG, length big-endian 4 byte và record TLV. Key declaration/revocation xác định authorization theo vị trí. Checkpoint cần cả Merkle root đúng, signature đúng và signer đang authorized.

## Lời giải

1. Dựng Merkle root kiểu RFC 6962: leaf SHA256(0x00||record), node SHA256(0x01||left||right). Check root/signature/authorization của từng checkpoint. Chọn size 46; chỉ record 0…45 thuộc snapshot. Size 50 sai root, 52 dùng key chưa active, 55 sai signature; size 33 hợp lệ nhưng nhỏ hơn.
2. Xác minh root-signed key timeline. editor-desk key cũ bị revoke tại position 15; replacement bắt đầu ở vị trí đó. Kiểm tra signer tại record position và reject manifest không canonical.
3. Capture manifest `mf-326c47df321e` ở index 6 do principal đúng ký; ingest record index 7 nối asset digest tới incident.
4. Theo `parent_asset_sha256` và thứ tự log để nối capture, crop, resize, redact. Chain manifest lần lượt kết thúc `321e`, `da36`, `846e`, `8137`; dùng đầy đủ digest trong bảng.
5. Dựng sáu field đúng thứ tự, compact ASCII JSON. Prefix `isfcr-forensics` và NUL, dùng scrypt rồi AES-GCM với AAD `signed-but-which-original`.

   | Tree size | Assessment |
   |---:|---|
   | 33 | Valid root and authorized signature, but not the largest valid checkpoint |
   | **46** | **Valid root, authorized log key, and valid signature — selected** |
   | 50 | Signature verifies, but the advertised Merkle root does not match the 50 logged entries |
   | 52 | Root and signature verify, but the secondary log key is not active until position 62 |
   | 55 | Merkle root matches, but the checkpoint signature is invalid |

   | Step | Action | Manifest ID | Asset SHA-256 |
   |---:|---|---|---|
   | 1 | capture | `mf-326c47df321e` | `5fe33137c48b34086ca6c2c19723b4916fb13732e465759be10b96dcef825bcf` |
   | 2 | crop | `mf-95efb978da36` | `9293fe403504fdf7fb149bafa4e7c1780cf0cab25ab8475773bdc0261da29215` |
   | 3 | resize | `mf-57d2452e846e` | `39b82b8f3aa9d390b46c357fade09158749847fe0e10784a3fbfed0ab3542201` |
   | 4 | redact | `mf-ee2392778137` | `c40ac4a3268f0b30aac5a1e344e1e4016b82fbfb1171e86330a64c69e73d6cff` |

## Evidence

Evidence array trong block dưới đây phải giữ nguyên cả sáu string; tree size là string `46`. Scrypt dùng n=131072, r=8, p=1, dklen=32, maxmem=2**28. Salt, nonce và AAD được giữ trong code tái hiện.

```json
[
  "c40ac4a3268f0b30aac5a1e344e1e4016b82fbfb1171e86330a64c69e73d6cff",
  "mf-ee2392778137",
  "mf-326c47df321e>mf-95efb978da36>mf-57d2452e846e>mf-ee2392778137",
  "5fe33137c48b34086ca6c2c19723b4916fb13732e465759be10b96dcef825bcf",
  "incident-d7be9442cb",
  "46"
]
```

## Kết quả

Flag được đọc sau khi GCM tag xác thực evidence đã dựng.

`isfcr{29336738f5f44f4d2d1e3ac2}`

## Tái hiện

Đặt case.json và entries.bin trong working directory. Cài cryptography, lưu Python block thành `reproduce.py` rồi chạy. Script đầy đủ ở đây thay cho một file script phụ; output cuối đối chiếu evidence và flag.

```bash
python -m pip install cryptography
python reproduce.py
```

```python
#!/usr/bin/env python3
"""Standalone CTF reproduction: run beside case.json and entries.bin."""
import hashlib
import json
import struct
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

H = lambda value: hashlib.sha256(value).digest()
canon = lambda obj: json.dumps(obj, ensure_ascii=True, sort_keys=True,
                               separators=(',', ':')).encode('ascii')
case = json.loads(Path('case.json').read_text())
blob = Path('entries.bin').read_bytes()
assert blob[:8] == b'ISFCRLOG'
entries = []
position = 8
while position < len(blob):
    n = int.from_bytes(blob[position:position + 4], 'big')
    entries.append(blob[position + 4:position + 4 + n])
    position += 4 + n
assert position == len(blob)


def fields(record):
    fields = {}
    offset = 1
    while offset < len(record):
        tag = record[offset]
        size = int.from_bytes(record[offset + 1:offset + 3], 'big')
        fields[tag] = record[offset + 3:offset + 3 + size]
        offset += 3 + size
    assert offset == len(record)
    return fields


def verify(key, signature, message):
    try:
        Ed25519PublicKey.from_public_bytes(key).verify(signature, message)
        return True
    except Exception:
        return False


def merkle(records):
    if len(records) == 1:
        return H(b'\x00' + records[0])
    split = 1 << ((len(records) - 1).bit_length() - 1)
    return H(b'\x01' + merkle(records[:split]) + merkle(records[split:]))


root_key = bytes.fromhex(case['root_key'])
keys = {}
for index, record in enumerate(entries):
    if record[0] != 1:
        continue
    f = fields(record)
    if not verify(root_key, f[127], record[:-67]):
        continue
    keys[f[1].decode()] = {
        'pub': f[4], 'role': f[2].decode(),
        'from': int.from_bytes(f[5], 'big'), 'issued': index
    }


def signed_by(name, index):
    k = keys.get(name)
    return (k is not None and k['issued'] < index
            and k['from'] <= index
            and (name not in revoked or index < revoked[name]))


# Use signed root-key revocation events, excluding events after the checkpoint.
def revocations(count):
    result = {}
    for record in entries[:count]:
        if record[0] == 2:
            f = fields(record)
            if verify(root_key, f[127], record[:-67]):
                key_id = f[1].decode()
                epoch = int.from_bytes(f[7], 'big')
                result[key_id] = min(result.get(key_id, epoch), epoch)
    return result


valid_cps = []
for cp in case['checkpoints']:
    n = cp['tree_size']
    revoked = revocations(n)
    name = cp['key_id']
    if n > len(entries) or not signed_by(name, n):
        continue
    if keys[name]['role'] not in ('log-primary', 'log-secondary'):
        continue
    checkpoint_message = canon({k: cp[k] for k in ('key_id', 'root_hash', 'tree_size')})
    sig_ok = verify(keys[name]['pub'], bytes.fromhex(cp['sig']), checkpoint_message)
    root_ok = merkle(entries[:n]).hex() == cp['root_hash']
    if sig_ok and root_ok:
        valid_cps.append(cp)
assert valid_cps
checkpoint = max(valid_cps, key=lambda x: x['tree_size'])
limit = checkpoint['tree_size']
revoked = revocations(limit)

manifests = {}
incident_assets = set()
for index, record in enumerate(entries[:limit]):
    f = fields(record)
    if record[0] not in (3, 4):
        continue
    signer = f[126].decode()
    if not signed_by(signer, index):
        continue
    if record[0] == 3:
        raw_json = f[8]
        try:
            obj = json.loads(raw_json)
        except ValueError:
            continue
        if raw_json != canon(obj):  # RFC8785 for these ASCII JSON records
            continue
        if not verify(keys[signer]['pub'], f[127], raw_json):
            continue
        obj['_index'] = index
        obj['_signer'] = signer
        manifests[obj['asset_sha256']] = obj
    else:
        if not verify(keys[signer]['pub'], f[127], record[:-67]):
            continue
        if keys[signer]['role'] != 'ingest-desk':
            continue
        if f[9].decode() == case['target_incident_id']:
            incident_assets.add(f[10].hex())

candidates = []
for obj in manifests.values():
    if obj['action'] != case['final_action']:
        continue
    chain = [obj]
    while chain[0]['parent_asset_sha256'] is not None:
        parent = manifests.get(chain[0]['parent_asset_sha256'])
        if parent is None or parent['_index'] >= chain[0]['_index']:
            break
        chain.insert(0, parent)
        if len(chain) > case['max_chain']:
            break
    if len(chain) != 4 or chain[0]['parent_asset_sha256'] is not None:
        continue
    if [x['action'] for x in chain] != ['capture'] + case['intermediate_actions'] + [case['final_action']]:
        continue
    if keys[chain[0]['_signer']]['role'] not in case['capture_principals']:
        continue
    if chain[0]['asset_sha256'] not in incident_assets:
        continue
    candidates.append(chain)

assert len(candidates) == 1, f'Expected one valid derivative, found {len(candidates)}'
chain = candidates[0]
evidence = [chain[-1]['asset_sha256'], chain[-1]['manifest_id'],
            '>'.join(x['manifest_id'] for x in chain), chain[0]['asset_sha256'],
            case['target_incident_id'], str(limit)]
key = hashlib.scrypt(
    b'isfcr-forensics\x00' + json.dumps(evidence, ensure_ascii=True,
                                         separators=(',', ':')).encode('ascii'),
    salt=bytes.fromhex('df2fd39adb32a812294cfe264c4a0ddc'),
    n=131072, r=8, p=1, maxmem=2**28, dklen=32)
flag = AESGCM(key).decrypt(
    bytes.fromhex('d2705557b11d25f6a1607cfd'),
    bytes.fromhex('7bad7e996d62c88b017ef105997ca1235e513b8b24a724eb88a5204d1771614af735db56d5d02cc8177133b8d79101'),
    b'signed-but-which-original').decode('ascii')
print('Trusted checkpoint:', limit)
for item in chain:
    print(f"{item['action']:7}  {item['manifest_id']}  {item['asset_sha256']}")
print('Evidence:', json.dumps(evidence, separators=(',', ':')))
print('FLAG', flag)
```

```text
Trusted checkpoint: 46
capture  mf-326c47df321e  5fe33137c48b34086ca6c2c19723b4916fb13732e465759be10b96dcef825bcf
crop     mf-95efb978da36  9293fe403504fdf7fb149bafa4e7c1780cf0cab25ab8475773bdc0261da29215
resize   mf-57d2452e846e  39b82b8f3aa9d390b46c357fade09158749847fe0e10784a3fbfed0ab3542201
redact   mf-ee2392778137  c40ac4a3268f0b30aac5a1e344e1e4016b82fbfb1171e86330a64c69e73d6cff
FLAG isfcr{29336738f5f44f4d2d1e3ac2}
```
