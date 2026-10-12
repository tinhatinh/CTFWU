---
title: "The Image That Forgot"
category: "Forensics"
tags: ["oci", "container-forensics"]
solve_date: "2026-10-10T16:45:00+07:00"
language: "en"
---

# The Image That Forgot

**Flag:** `isfcr{57cfd556fca281af64d920ef}`  
**Artifacts:** `events.jsonl`, `images.tar`, `vault.json` (from `handout (24).zip`)

| Artifact | Size (bytes) | SHA-256 |
|---|---:|---|
| `events.jsonl` | 4,471 | `9589cd02c81aefcbe93f5e6201802ba446bdf0645d711b38286cbdf3637f38a8` |
| `images.tar` | 501,760 | `a5d1270c9414365304b6ee75420c7f0a26a2fbc71ffc36634b1b00eef45547a6` |
| `vault.json` | 35,814 | `311320c8a1de73c2562f1a7518ee439ca071f7a173796cab5cafdbebfbb8e021` |

## Challenge

Recover the incident token of the container instance serving `dispatch-ac1af5608a` at `2026-08-14T10:10:08.555+05:30`. The evidence consists of container lifecycle events, an OCI image archive, and a vault of AES-256-GCM-encrypted notes. The five evidence fields must be supplied in this exact order: `event_id`, `manifest_digest`, `service_id`, `key_version`, and `token`. These fields are then used as input to a specified scrypt/AES-GCM flag decryption.

## Initial Analysis

`events.jsonl` contains interleaved events for multiple services, timestamp formats, deployment actions, and mutable image tags. `images.tar` is an OCI image layout, including multi-platform image indexes and historical filesystem layers; it is not simply a single Docker filesystem. `vault.json` contains **4** AES-256 keys and **203** notes. Each note has a 12-byte nonce and ciphertext with an appended 16-byte authentication tag.

The target timestamp converts to **`2026-08-14T04:40:08.555Z`**. Sorting the `dispatch-ac1af5608a` records by actual UTC time is essential: choosing the latest `dispatch:stable` tag, the most recent attempted deployment, or the most recent image index would select the wrong evidence.

## Exploitation Chain

1. **Reconstruct the instance timeline.** Normalize all ISO-8601 timestamps and millisecond-epoch tag updates to UTC, then filter for the target service. The important sequence is:

   | UTC time on 2026-08-14 | Event | Interpretation |
   |---|---|---|
   | `03:56:28.858` | `dispatch:stable` points to `sha256:30062144...` | Image index used by the successful `03:56:28.933` activation |
   | `04:16:07.672` | Successful activation `deploy-6d1373b389` | Uses the newly updated image index `sha256:6dae20c6...` |
   | `04:25:54.376` | Rollback `deploy-81aa644580` | Reverts the serving instance to the previous successful image |
   | `04:31:26.759` | `dispatch:stable` retargeted to `sha256:1e6f1acb...` | Tag movement does **not** change the already-running container image |
   | `04:36:41.756` | Migration `deploy-9d1a1fd93d` | Starts the relevant instance on `node-3dfc02`, `linux/amd64`, retaining the rolled-back image |
   | `04:38:01.936` | Activation `deploy-ac1c2df5f4` | **Failed**; does not replace the migrated instance |
   | `04:40:08.555` | Requested snapshot | The migrated instance is still serving the service |

   Consequently, the instance-starting **event ID** is `deploy-9d1a1fd93d`, while its retained image comes from the earlier image index `sha256:30062144e4a7cfc95730fe76cfe8d3a9ccb20434dfee8d8c55c8e7349227981a`.

2. **Resolve the correct OCI manifest, not the image index.** Read `blobs/sha256/30062144...` inside `images.tar`; it is a multi-platform OCI index. The migration specifies `linux/amd64`, so select that platform's *image manifest*:

   ```text
   sha256:154d6f1fa75464d02b6245a4e536f6efb187af4bf7266aff8ac9e2e21d4538f8
   ```

   This is the `manifest_digest` required by both the vault associated data and the final evidence. Substituting the parent OCI index digest would fail AES-GCM authentication.

3. **Recover the historical key version through OCI layers.** Inspect the five layers in the selected `linux/amd64` manifest in order. The first layer contains `/etc/service/key-version.json` with a decoy/older version `key-3de4b6b00b`. The second layer replaces that path with a **hardlink** to `opt/dispatch/.state/b97e8564`; the target file contains:

   ```json
   {"key_version":"key-e52be7cc57","service_id":"dispatch-ac1af5608a"}
   ```

   A later layer contains the opaque whiteout `etc/service/.wh..wh..opq`, hiding earlier entries under `/etc/service`. Another layer has a misleading `/etc/service.bak/key-version.json` containing `key-90a623d0c2`. Neither the old value nor the backup is the right choice. Following the historical hardlink to its stored target reveals the required `key-e52be7cc57` despite the later whiteout.

4. **Authenticate and decrypt the vault note.** Build the associated data as ASCII compact JSON in the prescribed *vault* order: `[service_id,key_version,manifest_digest,event_id]`:

   ```json
   ["dispatch-ac1af5608a","key-e52be7cc57","sha256:154d6f1fa75464d02b6245a4e536f6efb187af4bf7266aff8ac9e2e21d4538f8","deploy-9d1a1fd93d"]
   ```

   Test the four 32-byte keys against the notes with each note's `nonce` and `data`. **Only key index 2 and note index 92 (both zero-based)** authenticate with this AAD. The recovered incident token is:

   ```text
   e411af706f77101364ccdf6b0cb59e75eb8b3cc34342a94c
   ```

5. **Derive and decrypt the final flag.** Arrange the *flag* evidence in its different, specified order:

   ```json
   ["deploy-9d1a1fd93d","sha256:154d6f1fa75464d02b6245a4e536f6efb187af4bf7266aff8ac9e2e21d4538f8","dispatch-ac1af5608a","key-e52be7cc57","e411af706f77101364ccdf6b0cb59e75eb8b3cc34342a94c"]
   ```

   Serialize with `json.dumps(..., ensure_ascii=True, separators=(",", ":"))`, prepend `b"isfcr-forensics\x00"`, and run scrypt with the challenge-provided salt and `n=131072, r=8, p=1, dklen=32`. AES-256-GCM decryption with the supplied nonce, ciphertext/tag, and AAD `the-image-that-forgot` succeeds and returns the flag.

## Flag

`isfcr{57cfd556fca281af64d920ef}`

The token and final flag were **independently reproduced from the supplied artifacts**, with successful AES-GCM authentication for both decryption stages. Acceptance on the CTF server was not checked.

## Reproduce

Extract the ZIP so that `the-image-that-forgot/` contains the three artifacts. Install the Python `cryptography` package and run the following script from the directory containing that folder (for example, save it as `solve.py`). The timeline analysis above explains the two fixed identifiers used to select the correct migrated event and rolled-back OCI index.

```python
import hashlib
import io
import json
import tarfile
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

root = Path("the-image-that-forgot")
service_id = "dispatch-ac1af5608a"
event_id = "deploy-9d1a1fd93d"
image_index_digest = (
    "sha256:30062144e4a7cfc95730fe76cfe8d3a9ccb20434dfee8d8c55c8e7349227981a"
)

# Verify that the chosen event is the amd64 migration before the snapshot.
events = [json.loads(line) for line in (root / "events.jsonl").read_text().splitlines()]
start = next(e for e in events if e.get("event_id") == event_id)
assert start["service_id"] == service_id
assert start["action"] == "migrate" and start["platform"] == "linux/amd64"

with tarfile.open(root / "images.tar") as oci:
    def blob(digest):
        data = oci.extractfile("blobs/sha256/" + digest.split(":", 1)[1]).read()
        assert "sha256:" + hashlib.sha256(data).hexdigest() == digest
        return data

    image_index = json.loads(blob(image_index_digest))
    amd64 = next(
        x for x in image_index["manifests"]
        if x["platform"]["os"] == "linux"
        and x["platform"]["architecture"] == "amd64"
    )
    manifest_digest = amd64["digest"]
    manifest = json.loads(blob(manifest_digest))

    # Layer 1 contains the hardlink and its surviving backing content.
    with tarfile.open(fileobj=io.BytesIO(blob(manifest["layers"][1]["digest"])), mode="r:*") as layer:
        link = layer.getmember("etc/service/key-version.json")
        assert link.islnk() and link.linkname == "opt/dispatch/.state/b97e8564"
        state = json.load(layer.extractfile(link.linkname))
        assert state["service_id"] == service_id
        key_version = state["key_version"]

    # The later opaque whiteout hides /etc/service entries in the final image.
    with tarfile.open(fileobj=io.BytesIO(blob(manifest["layers"][3]["digest"])), mode="r:*") as layer:
        assert "etc/service/.wh..wh..opq" in layer.getnames()

vault = json.loads((root / "vault.json").read_text())
aad = json.dumps(
    [service_id, key_version, manifest_digest, event_id],
    ensure_ascii=True, separators=(",", ":")
).encode("ascii")

matches = []
for key_index, key_hex in enumerate(vault["keys"]):
    cipher = AESGCM(bytes.fromhex(key_hex))
    for note_index, note in enumerate(vault["notes"]):
        try:
            token = cipher.decrypt(
                bytes.fromhex(note["nonce"]), bytes.fromhex(note["data"]), aad
            ).decode("ascii")
            matches.append((key_index, note_index, token))
        except Exception:  # Invalid GCM tag for nonmatching key/note
            pass

assert len(matches) == 1
key_index, note_index, token = matches[0]
print("VAULT MATCH", key_index, note_index, token)

evidence = [event_id, manifest_digest, service_id, key_version, token]
E = json.dumps(evidence, ensure_ascii=True, separators=(",", ":")).encode("ascii")
key = hashlib.scrypt(
    b"isfcr-forensics\x00" + E,
    salt=bytes.fromhex("8b57a161139a064a196625972f7e602d"),
    n=131072, r=8, p=1, maxmem=2**28, dklen=32
)
flag = AESGCM(key).decrypt(
    bytes.fromhex("244cb048e982870d71f68dfe"),
    bytes.fromhex(
        "02e462042292a430220d3959e46c379b7f96d44726c6c390"
        "338ed11b7ee9878875de07ad212f4dbbda1994c3e2574c"
    ),
    b"the-image-that-forgot"
).decode("ascii")
print("FLAG", flag)
```

Expected output:

```text
VAULT MATCH 2 92 e411af706f77101364ccdf6b0cb59e75eb8b3cc34342a94c
FLAG isfcr{57cfd556fca281af64d920ef}
```
